import io
import tempfile
import unittest
from pathlib import Path
from urllib.error import URLError

from PIL import Image

from atlas_enhance import AtlasClient, AtlasError, build_payload, enhance_image


PROPERTIES = {
    "model": {"type": "string"},
    "prompt": {"type": "string"},
    "images": {"type": "array"},
    "aspect_ratio": {"type": "string", "enum": ["9:16", "16:9"]},
    "resolution": {"type": "string", "enum": ["1k", "2k", "4k"]},
    "output_format": {"type": "string", "enum": ["default", "png", "jpeg"]},
}


class FakeClient:
    def __init__(self):
        self.uploads = []
        self.submissions = []

    def discover_model(self, model):
        self.model = model
        return PROPERTIES

    def upload_media(self, path):
        self.uploads.append(path)
        return f"https://uploads.example/{path.name}"

    def submit_image(self, payload):
        self.submissions.append(payload)
        return "prediction-123"

    def wait_for_output(self, prediction_id, timeout_seconds, poll_interval):
        self.poll = (prediction_id, timeout_seconds, poll_interval)
        return "https://outputs.example/result.png"

    def download(self, url, output, output_format):
        self.download_call = (url, output, output_format)
        output.write_bytes(b"fake-png")


class AtlasEnhanceTests(unittest.TestCase):
    def test_build_payload_uses_live_schema_fields(self):
        payload = build_payload(
            PROPERTIES,
            model="google/nano-banana-pro/edit",
            prompt="Preserve the text",
            images=["https://example.test/scaffold.png"],
            aspect_ratio="9:16",
            resolution="2k",
            output_format="png",
        )

        self.assertEqual(payload["aspect_ratio"], "9:16")
        self.assertEqual(payload["resolution"], "2k")
        self.assertEqual(payload["output_format"], "png")
        self.assertEqual(set(payload), set(PROPERTIES))

    def test_enhance_submits_generation_once(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            scaffold = root / "scaffold.png"
            reference = root / "reference.png"
            output = root / "enhanced.png"
            scaffold.write_bytes(b"scaffold")
            reference.write_bytes(b"reference")
            client = FakeClient()

            result = enhance_image(
                client,
                input_paths=[scaffold, reference],
                output=output,
                prompt="Keep the layout and polish the device frame",
                model="google/nano-banana-pro/edit",
                aspect_ratio="9:16",
                resolution="2k",
                output_format="png",
                timeout_seconds=120,
                poll_interval=1,
            )

            self.assertEqual(client.uploads, [scaffold, reference])
            self.assertEqual(len(client.submissions), 1)
            self.assertEqual(client.submissions[0]["images"], [
                "https://uploads.example/scaffold.png",
                "https://uploads.example/reference.png",
            ])
            self.assertEqual(output.read_bytes(), b"fake-png")
            self.assertEqual(result["prediction_id"], "prediction-123")

    def test_post_transport_is_not_retried(self):
        calls = []

        def failing_opener(request, timeout):
            calls.append((request.get_method(), timeout))
            raise URLError("network down")

        client = AtlasClient(
            api_key="test-key",
            opener=failing_opener,
            sleep_fn=lambda _: None,
        )
        with self.assertRaises(AtlasError):
            client.submit_image({"model": "m", "prompt": "p", "images": ["u"]})

        self.assertEqual(calls, [("POST", 90)])

    def test_download_normalizes_provider_format(self):
        source = io.BytesIO()
        Image.new("RGB", (8, 12), "blue").save(source, format="JPEG")
        calls = []

        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self):
                return source.getvalue()

        def opener(request, timeout):
            calls.append((request.get_method(), timeout))
            return Response()

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "enhanced.png"
            client = AtlasClient(api_key="test-key", opener=opener)
            client.download("https://outputs.example/result", output, "png")

            with Image.open(output) as image:
                self.assertEqual(image.format, "PNG")
                self.assertEqual(image.size, (8, 12))

        self.assertEqual(calls, [("GET", 90)])


if __name__ == "__main__":
    unittest.main()

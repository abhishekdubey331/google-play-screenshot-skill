# Contributing

Thanks for contributing to this skill.

## Development Setup

1. Clone the repository.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Regenerate frame assets if needed:

```bash
python3 generate_frame.py
```

4. Test local platform installation:

```bash
./scripts/install-skill.sh both
```

## Pull Request Guidelines

1. Keep changes focused and small.
2. Update `README.md` when behavior or setup changes.
3. If you modify prompt logic, update `SKILL.md` and include examples.
4. Do not commit private screenshots, secrets, or local config.

## Style

- Python: keep scripts dependency-light and readable.
- Prompts: be explicit, deterministic where possible, and resume-safe.

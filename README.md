# StaticRoute

User-configured route creation to interact with json5 data stores.

## Installation

```bash
pip install staticroute
```

## Usage

1. Define routes in `routes.json`
2. Place data stores in `data_stores/` directory
3. Run the server: `python -m router`

## Publishing

Push events trigger auto-publish when a commit message starts with a version
(e.g., `3A - Bug fixes`). The version format is `MAJOR + LETTER`, converted to
SemVer (e.g., `3A` → `3.1.0`).

Manual publishing via the "Publish" workflow button will bump the patch version
automatically, allowing multiple manual builds.

## Development

Format and lint:
```bash
ruff format .
ruff check .
```

Run tests:
```bash
pytest
```

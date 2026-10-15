# Installation

## Prerequisites

- Python >= 3.14
- pip

## Install from PyPI

```bash
pip install staticroute
```

## Install from Source

```bash
git clone https://github.com/Omena0/StaticRoute.git
cd StaticRoute
pip install -e .
```

## Install Dev Dependencies

For development, testing, and linting:

```bash
pip install pytest pytest-watch ruff
```

## Project Setup

1. Create a `routes.json` describing your data stores and routes.
2. Create a `data_stores/` directory (created automatically on first run).
3. Call `load_data_stores(app, "data_stores", routes)` in your Flask app.
4. Run the app.

See the [Quickstart](quickstart.md) guide.
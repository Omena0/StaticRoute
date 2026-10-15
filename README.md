# StaticRoute

[![Lint](https://github.com/Omena0/StaticRoute/actions/workflows/lint.yml/badge.svg)](https://github.com/Omena0/StaticRoute/actions/workflows/lint.yml)
[![Tests](https://github.com/Omena0/StaticRoute/actions/workflows/tests.yml/badge.svg)](https://github.com/Omena0/StaticRoute/actions/workflows/tests.yml)
[![Docs](https://github.com/Omena0/StaticRoute/actions/workflows/pages.yml/badge.svg)](https://github.com/Omena0/StaticRoute/actions/workflows/pages.yml)
[![Publish](https://github.com/Omena0/StaticRoute/actions/workflows/publish.yml/badge.svg)](https://github.com/Omena0/StaticRoute/actions/workflows/publish.yml)

User-configured route creation to interact with json5 data stores.

## Documentation

Full documentation is generated with [fr-docs](https://omena0.dev/fr-docs/) and
deployed to the project website:

- [Installation](https://omena0.dev/StaticRoute/installation/)
- [Quickstart](https://omena0.dev/StaticRoute/quickstart/)
- [Routes](https://omena0.dev/StaticRoute/routes/)
- [Configuration](https://omena0.dev/StaticRoute/configuration/)
- [API](https://omena0.dev/StaticRoute/api/)
- [Error Handling](https://omena0.dev/StaticRoute/error_handling/)

Build locally:

```bash
cd docs && python -m fr_docs build
```

## Installation

```bash
pip install staticroute
```

## Development

Install dev dependencies and run the test suite:

```bash
pip install pytest pytest-watch ruff
pytest -v
```

### TDD

Run tests in watch mode so they re-run automatically on every save:

```bash
ptw
```

Or run the VS Code task `pytest: watch` (`Ctrl+Shift+P` → `Tasks: Run Task`).

Run lint:

```bash
ruff check . && ruff format --check .
```

## Usage

Literally just call `load_data_stores` with the routes.

You can get routes from `load_routes_json` which by default reads `routes.json`.

```py
import flask

from router.load import load_data_stores, load_routes_json

# Load routes
routes = load_routes_json()

data_stores_dir = "data_stores"
os.makedirs(data_stores_dir, exist_ok=True)

# Define app
app = flask.Flask(__name__)
app.secret_key = "1234"  # Need a key for auth

load_data_stores(app, data_stores_dir, routes)

app.run(debug=True)
```

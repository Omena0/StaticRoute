# StaticRoute

User-configured route creation to interact with json5 data stores.

## Installation

```bash
pip install staticroute
```

## Usage

Literally just call `load_data_stores` with the routes.

You can get routes from `load_routes_json` which by default reads `routes.json`.

```py
import flask

from .load import load_data_stores, load_routes_json

# Load routes
routes = load_routes_json()

data_stores_dir = "data_stores"
os.makedirs(data_stores_dir, exist_ok=True)

# Define app
app = flask.Flask(__name__)
app.secret_key = "1234" # Need a key for auth

load_data_stores(app, data_stores_dir, routes)

app.run(debug=True)
```

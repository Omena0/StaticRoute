# Quickstart

## 1. Define your routes

Create a `routes.json` (JSON5) file mapping store names to store configs:

```json5
{
    "items.json": {
        "idx_name": "$item",
        "routes": {
            "list": {
                "type": "range",
                "args": {
                    "$offset": { "type": "integer", "optional": 0 },
                    "$count": { "type": "integer", "optional": 50 }
                },
                "range": ["$offset", "$count"],
                "max": 50,
                "max_error": "You can only request up to 50 items."
            },
            "get": {
                "type": "get",
                "args": { "$id": { "type": "ID" } },
                "id": "$id"
            },
            "new": {
                "type": "create",
                "args": {
                    "name": { "type": "content" },
                    "value": { "type": "content" }
                },
                "values": { "id": "#new_id", "name": "$name", "value": "$value" }
            },
            "delete": {
                "type": "delete",
                "args": { "$id": { "type": "ID" } },
                "id": "$id",
                "error": "Item not found."
            }
        }
    }
}
```

## 2. Wire it into a Flask app

```py
import os

import flask

from router.load import load_data_stores, load_routes_json

routes = load_routes_json()
data_stores_dir = "data_stores"
os.makedirs(data_stores_dir, exist_ok=True)

app = flask.Flask(__name__)
app.secret_key = "change-me"

load_data_stores(app, data_stores_dir, routes)

app.run(debug=True)
```

## 3. Run it

```bash
python -m router
```

## 4. Try the routes

```bash
# List items (offset 0, count 50)
curl "http://localhost:5000/items/list"

# Get a single item by ID
curl "http://localhost:5000/items/get?id=0"

# Create a new item
curl "http://localhost:5000/items/new?name=thing&value=hello"

# Delete an item
curl "http://localhost:5000/items/delete?id=0"
```

## Next Steps

- Read the [Routes](routes.md) guide to learn about route types and config options.
- Read the [Configuration](configuration.md) page for full reference.
- Read the [API](api.md) page for the Python interface.
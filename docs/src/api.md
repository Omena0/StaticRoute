# API

The public Python interface lives in the `router` package.

## `router.load`

### `load_routes_json(file="routes.json")`

Load a routes configuration from a JSON5 file.

```py
from router.load import load_routes_json

routes = load_routes_json()
```

Returns the parsed dict on success, or an `Error` if the file cannot be read
or parsed.

### `load_data_stores(app, stores_dir, routes, max_datastores=20, max_routes=100)`

Register all data stores and their routes on a Flask `app`.

```py
import flask
from router.load import load_data_stores, load_routes_json

app = flask.Flask(__name__)
app.secret_key = "change-me"
load_data_stores(app, "data_stores", load_routes_json())
```

- `app` — the Flask application to register routes on.
- `stores_dir` — directory containing the data store JSON5 files.
- `routes` — dict of store name → store config.
- `max_datastores` — maximum number of stores (default `20`).
- `max_routes` — maximum number of routes per store (default `100`).

Returns `None` on success, or an `Error` on the first failure.

## `router.route`

### `Route(store_name, config, idx_name="")`

A route handler. `store_name` is the base name (e.g. `items`), `config` is the
route config dict, and `idx_name` is the row variable name without the leading
`$`.

### `save_data_store(store_name)`

Persist an in-memory data store to disk.

```py
from router.route import save_data_store

save_data_store("items")
```

Returns `None` on success, or an `Error` if the store path is unknown.

## `router.error`

### `error(msg)`

Create an error dict.

```py
from router.error import error

e = error("Something went wrong")
# {"error": "Something went wrong"}
```

### `is_error(v)`

Return `True` if `v` is an error dict (`{"error": "..."}`).

```py
from router.error import is_error

is_error(error("test"))  # True
is_error({"data": 1})  # False
```

### `Error`

A type alias: `dict[Literal["error"], str]`.

## `router.util`

### `MISSING`

A sentinel object used to distinguish "argument not provided" from `None`.

## Data Store Globals

`router.route` exposes two module-level registries:

- `data_stores` — `dict[str, dict]` of in-memory store data.
- `data_store_paths` — `dict[str, str]` of store name → file path.

These are populated by `load_data_stores` and used by `Route` and
`save_data_store`.
# Configuration

StaticRoute is configured through a single `routes.json` file (JSON5) plus
optional limits passed to `load_data_stores`.

## routes.json

Top-level keys are store names (e.g. `"items.json"`). Each value is a store
config:

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
            }
        }
    }
}
```

### Store Config Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `idx_name` | string | `""` | Name of the row variable, e.g. `"$item"`. Used in dotted expressions. |
| `type` | string | `"table"` | Store type. Currently informational. |
| `columns` | object | `{}` | Column name → type map. Currently informational. |
| `routes` | object | `{}` | Map of route name → route config. |

### Route Config Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | yes | One of `get`, `create`, `delete`, `range`. |
| `args` | object | no | Request argument definitions. |
| `id` | string | `get`/`delete` | Value expression for the row key. |
| `values` | object | `create` | Key → value expression map for the new row. |
| `error` | string | `delete` | Error message when the row is not found. |
| `max` | integer | `range` | Cap on `count`. |
| `max_error` | string | `range` | Error message when `count` exceeds `max`. |
| `require` | object | no | Predicate dict (see [Routes](routes.md)). |
| `require_auth` | boolean | no | Require a logged-in user. |
| `auth_error` | string | no | Error message when not authenticated. |

## load_data_stores Limits

`load_data_stores(app, stores_dir, routes, max_datastores=20, max_routes=100)`
enforces:

- `max_datastores` — maximum number of stores in `routes`.
- `max_routes` — maximum number of routes per store.

Exceeding either returns an error.

## Data Stores

Each store is a JSON5 file named after the store key (e.g. `items.json`),
located in `stores_dir`. The file is created as `{}` if missing, loaded into
memory, and written back to disk on every `create`/`delete`.

## Type System

| Type | Validation |
|------|------------|
| `string` | Must be a `str`. |
| `number` | Must be a number (int or float). |
| `integer` | Must be an integer. |
| `ID` | Must be a non-negative integer. |
| `content` | Must be printable (newlines stripped). |

## Example: Full Config

```json5
{
    "posts.json": {
        "idx_name": "$post",
        "routes": {
            "list": {
                "type": "range",
                "args": {
                    "$offset": { "type": "integer", "optional": 0 },
                    "$count": { "type": "integer", "optional": 50 }
                },
                "max": 50,
                "max_error": "You can only request up to 50 posts."
            },
            "get": {
                "type": "get",
                "args": { "$id": { "type": "ID" } },
                "id": "$id"
            },
            "new": {
                "type": "create",
                "require_auth": true,
                "auth_error": "You are not logged in.",
                "args": {
                    "title": {
                        "type": "content",
                        "validator": { "type": "length", "max_value": 30, "error": "Post title too long!" }
                    },
                    "content": {
                        "type": "content",
                        "validator": { "type": "length", "max_value": 250, "error": "Post content too long!" }
                    }
                },
                "values": {
                    "id": "#new_id",
                    "title": "$title",
                    "content": "$content",
                    "author": "#Identity",
                    "created_at": "#now"
                }
            },
            "delete": {
                "type": "delete",
                "require_auth": true,
                "auth_error": "You are not logged in.",
                "args": { "$id": { "type": "ID" } },
                "require": {
                    "type": "Identity",
                    "value": "$post.author",
                    "error": "Cannot delete someone else's post!"
                },
                "id": "$id",
                "error": "Post not found."
            }
        }
    }
}
```
# Routes

A **route** is a URL endpoint registered on your Flask app. Routes are defined
per data store in `routes.json`. Each route has a `type` that determines what
it does, plus optional `args`, `values`, `require`, and `require_auth` fields.

Routes are registered at `/{store_name}/{route_name}`.

## Route Types

### `get`

Fetch a single row by ID.

```json5
"get": {
    "type": "get",
    "args": { "$id": { "type": "ID" } },
    "id": "$id"
}
```

- `args` — request arguments to parse and validate.
- `id` — a value expression resolved against `args` and used as the row key.

Returns the row with that ID, or an error if it does not exist.

### `create`

Insert a new row and persist it to disk.

```json5
"new": {
    "type": "create",
    "args": {
        "name": { "type": "content" },
        "value": { "type": "content" }
    },
    "values": {
        "id": "#new_id",
        "name": "$name",
        "value": "$value"
    }
}
```

- `args` — request arguments to parse and validate.
- `values` — a dict of key → value expression. Each value is resolved and
  stored under that key in the new row.

The `id` key is required (it is used as the row key). Returns the new row, or
an error.

### `delete`

Remove a row by ID.

```json5
"delete": {
    "type": "delete",
    "args": { "$id": { "type": "ID" } },
    "id": "$id",
    "error": "Item not found."
}
```

- `args` — request arguments to parse and validate.
- `id` — value expression resolved against `args`, used as the row key.
- `error` — custom error message returned when the row does not exist.

Returns `{"result": "ok"}` on success, or an error.

### `range`

Return a slice of rows by index (not ID).

```json5
"list": {
    "type": "range",
    "args": {
        "$offset": { "type": "integer", "optional": 0 },
        "$count": { "type": "integer", "optional": 50 }
    },
    "range": ["$offset", "$count"],
    "max": 50,
    "max_error": "You can only request up to 50 items."
}
```

- `args` — request arguments. `offset` and `count` are validated automatically.
- `max` — optional cap on `count`. If exceeded, `max_error` is returned.
- `range` — a list of value expressions (currently informational).

Returns a list of rows.

## Arguments

Each entry in `args` is either:

- A string shorthand: `"name": "content"` — type is `content`, no options.
- A dict: `"name": { "type": "content", "optional": 0 }` — full config.

Argument names may start with `$` (the prefix is stripped). The leading `$`
indicates the argument is required; omit it for an optional argument with a
default.

| Field | Type | Description |
|-------|------|-------------|
| `type` | string | One of `string`, `number`, `integer`, `ID`, `content`. |
| `optional` | any | Default value when the argument is not provided. |

## Value Expressions

Values in `id` and `values` are resolved by `Route.resolve_value`:

- `$name` — resolve a named argument (supports dotted access, e.g. `$item.author`).
- `#now` — the current Unix timestamp (float).
- `#new_id` — the next integer ID, based on the highest existing numeric key.
- `#Identity` — the logged-in user's username (from Flask session).
- `#session:foo` — the value of session key `foo`.
- Any other string is returned as-is.

## Require & Auth

Routes can be gated:

- `require_auth: true` — the user must be logged in (`username` in session).
- `require` — a predicate dict. Currently supports `type: "Identity"` with a
  `value` expression compared against the session username.

```json5
"delete": {
    "type": "delete",
    "require_auth": true,
    "auth_error": "You are not logged in.",
    "require": {
        "type": "Identity",
        "value": "$post.author",
        "error": "Cannot delete someone else's post!"
    }
}
```

## Store Config

Each store entry in `routes.json` may include:

| Field | Description |
|-------|-------------|
| `idx_name` | Name of the "row" variable, e.g. `"$post"`. Used in dotted expressions. |
| `type` | Store type (default `table`). |
| `columns` | Column name → type map (informational). |
| `routes` | Map of route name → route config. |

## Errors

Any error is returned as a JSON object with a single `error` key:

```json
{ "error": "Item not found." }
```

See [Error Handling](error_handling.md) for details.
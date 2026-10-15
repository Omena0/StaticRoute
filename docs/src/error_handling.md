# Error Handling

StaticRoute uses a uniform error shape: a JSON object with a single `error`
key mapping to a human-readable message.

```json
{ "error": "Item not found." }
```

## Detecting Errors

Use `is_error` to check whether a value is an error:

```py
from router.error import is_error

result = route.get_return(args)
if is_error(result):
    print(result["error"])
```

`is_error` returns `True` only for dicts with exactly one key, `"error"`, so
plain strings, lists, and normal data dicts are never mistaken for errors.

## Error Categories

Errors are returned as `{"error": "<message>"}`. Messages fall into a few
prefix categories:

| Prefix | Meaning |
|--------|---------|
| `InvalidRoute` | Misconfiguration in `routes.json` or argument parsing. |
| `NotDefinedError` | A referenced argument or variable was not provided. |
| `TypeError` / `KeyError` | A dotted expression referenced a non-dict or missing key. |
| `DataStoreError` | A problem with the data store file or its contents. |
| `DataStoreNotFound` | The requested store was never loaded. |
| `InvalidPredicate` | A `require` predicate was malformed. |
| `NotImplemented` | A feature or type is not yet supported. |

## HTTP Status

All route responses are serialized with `flask.jsonify`. Errors are returned
with a **200** status code by default — the JSON body itself signals the
failure. This keeps clients simple: always check `is_error` on the parsed
body rather than relying on status codes.

## Examples

### Missing argument

```bash
curl "http://localhost:5000/items/new?name=thing"
```

```json
{ "error": "Argument not specified: value" }
```

### Type validation failure

```bash
curl "http://localhost:5000/items/get?id=abc"
```

```json
{ "error": "Not an ID: abc" }
```

### Range limit exceeded

```bash
curl "http://localhost:5000/items/list?count=99999"
```

```json
{ "error": "You can only request up to 50 items." }
```

### Not found

```bash
curl "http://localhost:5000/items/get?id=999"
```

```json
{ "error": "Not found: 999" }
```

### Not authenticated

```bash
curl "http://localhost:5000/posts/new?title=hi&content=body"
```

```json
{ "error": "You are not logged in." }
```
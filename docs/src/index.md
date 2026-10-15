# StaticRoute

User-configured route creation to interact with json5 data stores.

StaticRoute lets you define REST-like routes in a JSON5 config file. Each route
reads from, writes to, or lists rows in a JSON5 data store, with built-in type
validation, authentication, and authorization.

## Features

- **Declarative routes** — define `get`, `create`, `delete`, and `range` routes in
  a single config file.
- **Type validation** — validate arguments as `string`, `number`, `integer`,
  `ID`, or `content`.
- **Pluggable data stores** — each store is a JSON5 file on disk, loaded into
  memory and persisted on write.
- **Auth & authorization** — gate routes behind login (`require_auth`) and
  per-row ownership checks (`require` predicates).
- **Builtins** — reference the current time (`#now`), the next ID (`#new_id`),
  the logged-in user (`#Identity`), or any Flask session key (`#session:foo`).

## Quick Links

- [Installation](installation.md)
- [Quickstart](quickstart.md)
- [Routes](routes.md)
- [API](api.md)

## Source

Browse the [source code](https://github.com/Omena0/StaticRoute) on GitHub.

import os

import flask
import json5
from flask import request

from .error import Error, error
from .route import Route, data_store_paths, data_stores
from .util import MISSING


def load_routes_json(file="routes.json"):
    with open(file) as f:
        return json5.load(f)


def _validate_name(name, kind):
    """Validate that a name is safe for use in paths or URLs."""
    if not isinstance(name, str) or not name:
        return error(f"InvalidRoute: {kind} must be a non-empty string.")
    if any(c in name for c in ("/", "\\", "\0", "..")):
        return error(f"InvalidRoute: {kind} contains invalid characters.")
    return None


def load_data_stores(app, stores_dir, routes, max_datastores=20, max_routes=100):
    if not isinstance(routes, dict):
        return error("InvalidRoute: routes must be a dict.")

    if len(routes) > max_datastores:
        return error(f"InvalidRoute: Too many data stores. Maximum is {max_datastores}.")

    for store_name, store_config in routes.items():
        print(f"Loading: {store_name}")
        if err := _validate_name(store_name, "store name"):
            return err

        if not isinstance(store_config, dict):
            return error(f"InvalidRoute: Store config for '{store_name}' must be a dict.")

        store_routes = store_config.get("routes", {})
        if not isinstance(store_routes, dict):
            return error(f"InvalidRoute: routes for '{store_name}' must be a dict.")

        if len(store_routes) > max_routes:
            return error(f"InvalidRoute: Too many routes in '{store_name}'. Maximum is {max_routes}.")

        if err := load_data_store(app, stores_dir, store_name, store_config):
            return err


def load_data_store(app, stores_dir, store_name, store_config):
    path = os.path.join(stores_dir, store_name)
    # Create if not exists
    if not os.path.exists(path):
        with open(path, "w") as f:
            f.write("{}")

    base_name = store_name.rsplit(".", 1)[0]
    data_store_paths[base_name] = path

    # Load data store
    with open(path) as f:
        data_stores[base_name] = json5.load(f)

    # Define routes
    for route_name, route_config in store_config.get("routes", {}).items():
        if err := _validate_name(route_name, "route name"):
            return err

        route_config["idx_name"] = store_config.get("idx_name", "")
        print(f"  Loading route: /{base_name}/{route_name}")
        load_route(app, base_name, route_name, store_config, route_config)


def load_route(app, store_name, route_name, store_config, route_config):
    route = Route(store_name, route_config, store_config.get("idx_name", ""))

    def func() -> dict | list | Error:
        args = {}
        for name, arg_config in route_config.get("args", {}).items():
            # Dict type
            if isinstance(arg_config, dict):
                if "type" not in arg_config:
                    return error(f"InvalidRoute: Invalid type: {type}")
                type = arg_config.get("type")

            else:
                type = arg_config
                arg_config = {}

            name = name.removeprefix("$")
            value = request.args.get(name, MISSING)

            if value is MISSING:  # ruff: ignore[SIM102]
                if (value := arg_config.get("optional", MISSING)) is MISSING:
                    return error(f"Argument not specified: {name}")

            valid, msg = route.validate_type(type, value)
            if not valid:
                return error(msg)

            args[name] = {"value": value, "type": type}

        return route.get_return(args)

    app.add_url_rule(
        f"/{store_name}/{route_name}",
        endpoint=f"{store_name}_{route_name}",
        view_func=lambda c=route_config, *a, **kw: flask.jsonify(func()),
    )

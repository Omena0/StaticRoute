import os
import threading
from typing import Dict, Optional

import json5
from flask import Response, jsonify, request
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer, ObserverType

from .error import error, is_error
from .route import Route, data_store_paths, data_stores

_user_routes_cache: Dict[str, Dict] = {}
_cache_mtimes: Dict[str, float] = {}
_cache_lock = threading.RLock()
_observer: Optional[ObserverType] = None
_watched_dirs: Dict[str, str] = {}


class RoutesFileHandler(FileSystemEventHandler):
    def __init__(self, base_stores_dir: str):
        self.base_stores_dir = base_stores_dir

    def on_modified(self, event):
        if event.is_directory:
            return
        if event.src_path.endswith("routes.json"):
            username = self._extract_username(event.src_path)
            if username:
                with _cache_lock:
                    _user_routes_cache.pop(username, None)
                    _cache_mtimes.pop(username, None)

    def on_created(self, event):
        self.on_modified(event)

    def on_deleted(self, event):
        if event.is_directory:
            return
        if event.src_path.endswith("routes.json"):
            username = self._extract_username(event.src_path)
            if username:
                with _cache_lock:
                    _user_routes_cache.pop(username, None)
                    _cache_mtimes.pop(username, None)

    def _extract_username(self, path: str) -> Optional[str]:
        rel = os.path.relpath(path, self.base_stores_dir)
        parts = rel.split(os.sep)
        if parts:
            return parts[0]
        return None


def start_file_watcher(base_stores_dir: str) -> None:
    global _observer
    if _observer is not None:
        return

    if not os.path.exists(base_stores_dir):
        os.makedirs(base_stores_dir, exist_ok=True)

    _observer = Observer()
    handler = RoutesFileHandler(base_stores_dir)
    _observer.schedule(handler, base_stores_dir, recursive=True)
    _observer.daemon = True
    _observer.start()


def stop_file_watcher() -> None:
    global _observer
    if _observer is not None:
        _observer.stop()
        _observer.join(timeout=2)
        _observer = None


def _get_user_routes(username: str, base_stores_dir: str) -> Optional[Dict]:
    path = os.path.join(base_stores_dir, username, "routes.json")
    if not os.path.exists(path):
        return None

    mtime = os.path.getmtime(path)
    with _cache_lock:
        if _cache_mtimes.get(username) == mtime:
            return _user_routes_cache.get(username)

        with open(path) as f:
            config = json5.load(f)
        _user_routes_cache[username] = config
        _cache_mtimes[username] = mtime
        return config


def _ensure_data_store_loaded(username: str, store_name: str, base_stores_dir: str) -> str:
    store_key = f"{store_name}.json"
    store_base = store_key.rsplit(".", 1)[0]
    store_path = os.path.join(base_stores_dir, username, store_key)
    data_store_paths[store_base] = store_path
    if store_base not in data_stores:
        if os.path.exists(store_path):
            with open(store_path) as f:
                data_stores[store_base] = json5.load(f)
        else:
            data_stores[store_base] = {}
    return store_base

def _resolve_args(route_obj: Route, route_config: Dict) -> tuple[Dict, Optional[Response]]:
    args = {}
    for name, arg_config in route_config.get("args", {}).items():
        if isinstance(arg_config, dict):
            if "type" not in arg_config:
                resp = jsonify(error("InvalidRoute: Invalid type"))
                resp.status_code = 400
                return {}, resp
            type_ = arg_config.get("type")
        else:
            type_ = arg_config
            arg_config = {}

        name = name.removeprefix("$")
        value = request.args.get(name)

        if value is None:
            if (value := arg_config.get("optional")) is None:
                resp = jsonify(error(f"Argument not specified: {name}"))
                resp.status_code = 400
                return {}, resp

        valid, msg = route_obj.validate_type(type_, value)
        if not valid:
            resp = jsonify(error(msg))
            resp.status_code = 400
            return {}, resp

        args[name] = {"value": value, "type": type_}

    return args, None


def dispatch_user_route(path: str, username: str, base_stores_dir: str = "data_stores") -> Optional[Response]:
    parts = path.strip("/").split("/")
    if len(parts) < 3:
        return None

    path_username, store, route = parts[0], parts[1], parts[2]
    if path_username != username:
        return None

    routes_config = _get_user_routes(username, base_stores_dir)
    if not routes_config:
        return None

    store_key = f"{store}.json"
    store_config = routes_config.get(store_key)
    if not store_config:
        return None

    route_config = store_config.get("routes", {}).get(route)
    if not route_config:
        return None

    store_base = _ensure_data_store_loaded(username, store, base_stores_dir)

    route_obj = Route(store_base, route_config, store_config.get("idx_name", ""))

    args, err_resp = _resolve_args(route_obj, route_config)
    if err_resp is not None:
        return err_resp

    result = route_obj.get_return(args)
    if is_error(result):
        resp = jsonify(result)
        resp.status_code = 400
        return resp

    return jsonify(result)


def invalidate_user_cache(username: str) -> None:
    with _cache_lock:
        _user_routes_cache.pop(username, None)
        _cache_mtimes.pop(username, None)


def load_user_routes_manual(username: str, base_stores_dir: str) -> Optional[Dict]:
    invalidate_user_cache(username)
    return _get_user_routes(username, base_stores_dir)

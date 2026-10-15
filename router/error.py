from typing import Literal, TypeGuard

type Error = dict[Literal["error"], str]


def is_error(v: object) -> TypeGuard[Error]:
    return isinstance(v, dict) and "error" in v and len(v) == 1 and isinstance(v["error"], str)


def error(msg: str) -> Error:
    return {"error": msg}

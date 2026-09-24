import time
from itertools import islice
from typing import Any

from flask import session

from .error import Error, error, is_error
from .util import MISSING

data_stores:dict[str, dict] = {}

class Route:
    def __init__(self, store_name, config, idx_name=''):
        self.store_name = store_name
        self.config = config
        self.idx_name = idx_name.removeprefix('$')

    @property
    def data_store(self):
        return data_stores[self.store_name]

    def validate_type(self, type, value) -> tuple[bool, str]:
        if isinstance(type, dict) and 'type' in type:
            type = type['type']

        if type == 'string':
            return isinstance(value, str), f'Not a string: {value}'
        elif type == 'number': # Can be int or float
            return str(value).replace('.','',1).removeprefix('-').isdigit(), f'Not a number: {value}'
        elif type == 'integer': # Must be int
            return str(value).removeprefix('-').isdigit(), f'Not an integer: {value}'
        elif type == 'ID': # Must be positive int
            return str(value).isdigit(), f'Not an ID: {value}'
        elif type == 'content': # Must be printable or newline
            return str(value).replace('\n','').isprintable(), f'Not printable: {value}'

        return False, f"NotImplemented: Type validation for '{type}'"

    def resolve_type(self, value) -> Any | Error:
        if not isinstance(value, dict) or 'type' not in value:
            return value

        type = value['type']
        value = value['value']

        if type in ('string', 'content'):
            return str(value)

        elif type in ('number', 'integer','ID'): # Parsed the same way
            if isinstance(value, (int, float)):
                return value

            if not isinstance(value, str):
                return error(f"Could not parse as number: {value}")

            # Is float?
            if '.' in value and value.replace('.','',1).removeprefix('-').isdigit():
                return float(value)

            # Is it int?
            if value.removeprefix('-').isdigit():
                return int(value)

            return error(f"Could not parse as number: {value}")

        return error(f"NotImplemented: Type resolution for '{type}'")

    def resolve_builtin(self, name):
        if name == 'now':
            return time.time()
        elif name == 'new_id':
            if not self.data_store:
                return 0
            return int(next(reversed(self.data_store))) + 1
        elif name == 'Identity':
            return session.get('username')
        elif name.startswith('session:'):
            return session.get(name.split(':',1)[1])

        return error(f"NotImplemented: Builtin '{name}'")

    def resolve_value(self, args: dict, value: Any) -> Any | Error:
        if value.startswith('$'):
            value = value.removeprefix('$')

            if '.' in value:
                value, *parts = value.split('.')
            else:
                parts = []

            if value not in args:
                return error(f"NotDefinedError: ${value} is not defined.")

            value = args.get(value)

            for part in parts:
                if not isinstance(value, dict):
                    return error(f"TypeError: Cannot get '{part}' of {value}")

                if part not in value:
                    return error(f'KeyError: {part}')

                print(value, part)

                value = value[part]

            return self.resolve_type(value)

        elif value.startswith('#'):
            value = value.removeprefix('#')
            return self.resolve_builtin(value)

        return value

    def resolve_predicate(self, args, predicate) -> bool | Error:
        type = predicate.get('type', MISSING)
        if type is MISSING:
            return error("InvalidPredicate: Type not specified.")

        value = predicate.get('value', MISSING)
        if value is MISSING:
            return error("InvalidPredicate: Value not specified.")

        if type == 'Identity':
            value = self.resolve_value(args, value)
            if is_error(value):
                return value

            return session.get('username') == value

        return error(f"NotImplemented: Predicate type '{type}'")

    def check_require(self, args):
        if 'require' in self.config:
            require = self.config['require']
            allowed = self.resolve_predicate(args, require)
            if is_error(allowed):
                return allowed

            if not allowed:
                return error(require.get('error', 'Require failed.'))

        if 'require_auth' in self.config and 'username' not in session:
            return error(self.config.get('auth_error', 'Not logged in.'))

        return None

    def get_return(self, args) -> dict | list | Error:
        type = self.config.get('type')
        if not type:
            return error("InvalidRoute: No route type specified.")

        v = None
        if "id" in self.config:
            id = self.resolve_value(args,self.config['id'])
            if is_error(id):
                return id

            v = self.data_store.get(str(id))

        args[self.idx_name] = v

        # Gets a row
        if type == 'get':
            id = self.config.get('id')
            if not id:
                return error("InvalidRoute: No get ID specified.")

            id = self.resolve_value(args, id)
            if is_error(id):
                return id

            if err := self.check_require(args):
                return err

            return self.data_store.get(str(id), error(f"Not found: {id}"))

        # Adds row
        elif type == 'create':
            values = self.config.get('values')
            if not values:
                return error("InvalidRoute: Create endpoint missing values.")
            if not isinstance(values, dict):
                return error("InvalidRoute: Values must be dict.")

            new = {}
            for k, v in values.items():
                v = self.resolve_value(args, v)
                if is_error(v):
                    return v

                new[k] = v

            if err := self.check_require(args):
                return err

            self.data_store[str(new['id'])] = new

            return new

        # Deletes row
        elif type == 'delete':
            id = self.config.get('id')
            if not id:
                return error("InvalidRoute: Delete endpoint missing ID.")

            id = self.resolve_value(args, id)

            if str(id) not in self.data_store:
                return error(self.config.get('error', 'Not found'))

            if err := self.check_require(args):
                return err

            self.data_store.pop(str(id))

            return {"result": "ok"}

        # Returns n rows
        elif type == 'range':
            offset = self.resolve_type(args.get('offset'))
            count  = self.resolve_type(args.get('count'))
            max    = self.config.get('max')

            # Check errors
            if is_error(offset): return offset
            if is_error(count):  return count

            assert isinstance(offset, int)
            assert isinstance(count, int)

            if offset < 0: return error('Offset must be positive')
            if count < 0:  return error('Count must be positive')

            # Only allow up to max rows
            if max and count > max:
                return error(self.config.get('max_error', 'Requested too many rows.'))

            return list(islice(self.data_store.values(), offset, offset + count))

        return error(f"NotImplemented: Route type '{type}'")


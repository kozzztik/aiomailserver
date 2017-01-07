from typing import Optional
from aiomailserver.conf import default


class Settings(dict):
    def __init__(self, base_object: Optional[dict]):
        super(Settings, self).__init__()
        self.update_from_module(default)
        if base_object:
            self.update(base_object)

    def update_from_module(self, obj):
        for name in dir(obj):
            if name.startswith('_'):
                continue
            value = getattr(obj, name)
            if value is None or isinstance(value, (str, int, dict, list, tuple)):
                self[name] = value

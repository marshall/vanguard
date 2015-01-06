import json
import os
import sys

this_dir = os.path.dirname(os.path.abspath(__file__))
config_dir = os.path.abspath(os.path.join(this_dir, '..', 'config'))

class DictObject(dict):
    def __getattr__(self, attr):
        if attr in self:
            value = self[attr]
            if isinstance(value, dict):
                return DictObject(value)
            return value

        raise AttributeError()

class Config(DictObject):
    def __init__(self, path=None, data=None):
        path = path or os.path.join(config_dir, 'config.json')
        data = data or json.load(open(path))
        super(DictObject, self).__init__(data)


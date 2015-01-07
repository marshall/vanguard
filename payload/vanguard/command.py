import importlib
import logging

_commands = {}
logger = logging.getLogger('command')

class CommandException(Exception): pass

def command(name):
    global _commands
    def wrapper(cls):
        _commands[name] = cls
        return cls
    return wrapper

def import_command(name):
    global _commands
    try:
        module = __import__(name, globals(), locals(), ['*'])
        cls = _commands.get(name)
        if not cls:
            raise CommandException('No command class found: %s' % name)
        return cls
    except ImportError, e:
        raise CommandException('Error importing package "%s": %s' % (name, str(e)))

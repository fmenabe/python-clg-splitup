# coding: utf-8

import os
import sys
import imp
import warnings
from collections import OrderedDict
import yaml
import yamlloader
import clg

# The module itself.
_SELF = sys.modules[__name__]

CLG_CUSTOMISATIONS = (
    'types',        # custom types for options and arguments
    'actions',      # custom actions for options and arguments
    'completers'    # custom completers for argcomplete
)

CMD_CONF = """
anchors:
{anchors:s}

{command_conf:s}
"""

#DEFAULTS = {
#    # Main configuration file of the CLI.
#    # default: cmd.yml file in main program directory
#    'cmd_file': os.path.join(sys.path[0], 'cmd.yml'),
#    # File containing reusable parts of configuration.
#    # default: anchors.yml file in main program directory
#    'anchors_file': os.path.join(sys.path[0], 'anchors.yml'),
#    # Directory containing subcommands CLI configuration.
#    # default: cmd/ directory in main program directory
#    'cmd_dir': os.path.join(sys.path[0], 'cmd'),
#    # Directory containing clg helpers (types, actions, ...)
#    # default: lib/clg directory in main program directory
#    'lib_dir': os.path.join(sys.path[0], 'lib', 'clg'),
#    # Directory containing commands logic.
#    # default: commands/ directory in main program directory
#    'commands_dir': os.path.join(sys.path[0], 'commands')
#}

# Exception raised by this module.
class CLGSplitupError(Exception):
    pass

def init(cmd_dir=os.path.join(sys.path[0], 'cmd'),
         #anchors_filename='_anchors.yml'),
         commands_dir=os.path.join(sys.path[0], 'commands'),
         lib_dir=os.path.join(sys.path[0], 'lib/clg'),
         completion=False,
         modules=[]):
    setattr(_SELF, 'CMD_DIR', cmd_dir)
    setattr(_SELF, 'COMMANDS_DIR', commands_dir)

    #Load clg customizations from files in lib directory
    load_clg_customizations(lib_dir)

    # Load main configuration file.
    conf = load_parser()

    # Initialize clg and return command-line arguments.
    args = clg.init(format='raw', data=conf, completion=completion)
    for module in modules:
        module.init(args)
    return args

def load_clg_customizations(lib_dir):
    for const in CLG_CUSTOMISATIONS:
        filepath = os.path.join(lib_dir, '%s.py' % const)
        if os.path.exists(filepath):
            mdl = imp.load_source(const, filepath)
            elts = {elt: getattr(mdl, elt)
                    for elt in dir(mdl)
                    if not elt.startswith('__') and not elt.endswith('__')}
            getattr(clg, const.upper()).update(elts)

def load_parser(cur=[], anchors={}):
    root = os.path.join(CMD_DIR, '/'.join(cur))
    files = os.listdir(root)

    if '_anchors.yml' in files:
        anchors.update(load_command(os.path.join(root, '_anchors.yml')))
        files.pop(files.index('_anchors.yml'))

    conf = {}
    if '_cmd.yml' in files:
        conf = load_command(os.path.join(root, '_cmd.yml'), anchors)
        files.pop(files.index('_cmd.yml'))

    order = conf.pop('_order', [])
    subcommands = [from_order(c, cur, root, files) for c in order]
    subcommands.extend(
        from_path(f, cur, root)
        for f in files
        if not any(f.startswith(ch) for ch in ('_', '.')))

    for c in subcommands:
        cur_conf = (load_command(c['path'], anchors)
            if c['type'] == 'command'
            else load_parser(c['future'], anchors))

        if 'mdl' in c:
            cur_conf['execute'] = {'module': c['mdl']}

        (conf.setdefault('subparsers', {})
             .setdefault('parsers', {})
             .setdefault(c['name'], cur_conf))

    return conf

def from_order(cmd, cur, root, files):
    cmd_filename = '%s.yml' % cmd
    cmd_filepath = os.path.join(root, cmd_filename)
    if os.path.exists(cmd_filepath):
        files.pop(files.index(cmd_filename))
        mdl = '.'.join(['commands'] + cur + [cmd])
        return {'name': cmd, 'type': 'command', 'path': cmd_filepath, 'mdl': mdl}

    parser_path = os.path.join(root, cmd)
    if os.path.exists(parser_path):
        files.pop(files.index(cmd))
        return {'name': cmd, 'type': 'parser', 'future': cur + [cmd]}

def from_path(filename, cur, root):
    filepath = os.path.join(root, filename)

    if os.path.isfile(filepath):
        cmd, ext = os.path.splitext(filename)
        if ext != '.yml':
            warnings.warn("clg: not a valid file: %s" % filepath)
        mdl = '.'.join(['commands'] + cur + [cmd])
        return {'name': cmd, 'type': 'command', 'path': filepath, 'mdl': mdl}

    if os.path.isdir(filepath):
        return {'name': filename, 'type': 'parser', 'future': cur + [filename]}

def load_command(path, anchors=None):
    try:
        with open(path) as fh:
            c = yaml.load(fh, Loader=yamlloader.ordereddict.CLoader)

            return replace_anchors(c, anchors) if anchors is not None else c
    except (IOError, yaml.YAMLError) as err:
        raise CLGSplitupError("error while loading configuration file '%s'" % path) from err

def replace_anchors(value, anchors):
    '''Recursively replace anchors patterns by their values in _anchors.yml files.'''
    if isinstance(value, str):
        try:
            return (anchors[value[1:-1].lower()]
                    if all((value.startswith('_'), not value.startswith('__'),
                            value.endswith('_'), not value.endswith('__')))
                    else value)
        except KeyError as err:
            raise CLGSplitupError("invalid anchor") from err
    elif isinstance(value, dict):
        new_value = OrderedDict()
        for param, value in value.items():
            if param == '<<<':
                if not value.startswith('_') or not value.endswith('_'):
                    raise CLGSplitupError("%s: invalid anchor '%s'" % (path, value))
                new_value.update(replace_anchors(value, anchors))
            else:
                new_value[param] = replace_anchors(value, anchors)
        return new_value
    elif isinstance(value, (list, tuple)):
        return [replace_anchors(elt, anchors) for elt in value]
    else:
        return value

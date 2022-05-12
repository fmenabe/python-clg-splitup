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

YAML_EXTS = ('yml', 'yaml', 'YML', 'YAML')

CLG_CUSTOMISATIONS = (
    'types',        # custom types for options and arguments
    'actions',      # custom actions for options and arguments
    'completers'    # custom completers for argcomplete
)

# Exception raised by this module.
class CLGSplitupException(Exception):
    '''
    `clg-splitup` exception.
    '''
    pass

def init(cmd_dir=os.path.join(sys.path[0], 'cmd'),
         commands_dir=os.path.join(sys.path[0], 'commands'),
         lib_dir=os.path.join(sys.path[0], 'lib/clg'),
         completion=True):
    '''
    Initialize the command-line.

    A `clg` configuration is generated. `cmd_dir` and `commands_dir` are recursively
    parsed to generate the configuration. Customizations (types, actions and completers)
    can be set in `lib_dir`, in a Python file named as the customization. `completion`
    through `argcomplete` is set by default (put as dependency in *setup.py*) even it
    may required manual configuration to be fully operational.
    '''
    setattr(_SELF, 'CMD_DIR', cmd_dir)
    setattr(_SELF, 'COMMANDS_DIR', commands_dir)
    setattr(_SELF, 'MDL_ROOT', os.path.basename(COMMANDS_DIR))
    sys.path.append(os.path.dirname(COMMANDS_DIR))

    load_clg_customizations(lib_dir)
    clg_conf = load_parser(parents=[])
    #import json
    #print(json.dumps(clg_conf, indent=2))
    return clg.init(format='raw', data=clg_conf, completion=completion)

def dirname(parents):
    return os.path.join(CMD_DIR, '/'.join(parents))

def load_clg_customizations(lib_dir):
    '''
    Load `clg` custom types, actions and completers.
    '''
    for const in CLG_CUSTOMISATIONS:
        filepath = os.path.join(lib_dir, f'{const}.py')
        if os.path.exists(filepath):
            mdl = imp.load_source(const, filepath)
            functions = {f: getattr(mdl, f)
                         for f in dir(mdl)
                         if not f.startswith('__') and not f.endswith('__')}
            getattr(clg, const.upper()).update(functions)

def load_anchors(root):
    filepath = os.path.join(root, '_anchors.yml')
    return {k: v for k, v in load_file(filepath).items() if k.startswith('x-')}

def load_parser(parents=[], anchors={}):
    '''
    Recursively parse the CLI configuration directory to generate `clg` configuration.

    It expects to find *_cmd.yml* and *_anchors.yml* for each parser, respectively
    containing parser configuration and anchors (valid for all childs commands of
    a parser). As files in a filesystem has no order, an *_order* key can be set in a
    parser configuration to indicate the order of commands (usefull in help messages).
    '''
    #root = os.path.join(CMD_DIR, '/'.join(cur_parser))
    root = dirname(parents)
    files = os.listdir(root)

    if '_anchors.yml' in files:
        anchors.update(load_anchors(root))
        files.pop(files.index('_anchors.yml'))

    conf = {}
    if '_cmd.yml' in files:
        conf = load_file(os.path.join(root, '_cmd.yml'), anchors)
        files.pop(files.index('_cmd.yml'))

    subcommands = list(from_order(parents, conf.pop('_order', []), files))
    subcommands.extend(from_files(parents, files))

    for c in subcommands:
        if c['type'] == 'parser':
            cur_conf = load_parser(c['future'], anchors)
        else: # c['type'] == 'command'
            cur_conf = load_file(c['path'], anchors)
            cur_conf['execute'] = {'module': c['mdl']}

        (conf.setdefault('subparsers', {})
             .setdefault('parsers', {})
             .setdefault(c['name'], cur_conf))

    return conf

def is_command(root, cmd):
    '''
    Look if a command file exist in `root` for command `cmd`.
    '''
    for ext in YAML_EXTS:
        filename = f'{cmd}.{ext}'
        filepath = os.path.join(root, filename)
        if os.path.exists(filepath):
            return filepath

def is_parser(root, cmd):
    '''
    Look if the command `cmd` has a parser configuration in `root`.
    '''
    return os.path.exists(os.path.join(root, cmd))

def mdl_path(parents, cmd):
    return '.'.join([MDL_ROOT] + parents + [cmd])

def from_order(parents, cmds, files):
    '''
    Look for commands or parsers configuration in `parents` based on ordered
    commands in `cmds` (from ``order``` parameter in *_cmd.yml*). A list of
    subcommands, containing a few parameters based on the command type, is
    returned.
    '''
    root = dirname(parents)

    for cmd in cmds:
        if filepath := is_command(root, cmd):
            files.pop(files.index(os.path.basename(filepath)))
            mdl = mdl_path(parents, cmd)
            yield dict(name=cmd, type='command', path=filepath, mdl=mdl)
        elif is_parser(root, cmd):
            files.pop(files.index(cmd))
            future = parents + [cmd]
            yield dict(name=cmd, type='parser', future=future)
        else:
            warnings.warn(
                f"clg-splitup: (.{'.'.join(parents)}) ordered command '{cmd}' not found")

def from_files(parents, files):
    '''
    Parse remaining `files` in `parents` and return a list of subcommands.
    '''
    root = dirname(parents)

    for filename in files:
        if any(filename.startswith(c) for c in ('_', '.')):
            continue

        filepath = os.path.join(root, filename)
        if os.path.isfile(filepath):
            cmd, ext = os.path.splitext(filename)
            if ext[1:] not in YAML_EXTS:
                warnings.warn(f"clg-splitup: not a valid command file: {filepath}")
            mdl = mdl_path(parents, cmd)
            yield dict(name=cmd, type='command', path=filepath, mdl=mdl)

        if os.path.isdir(filepath):
            yield dict(name=filename, type='parser', future=parents+[filename])

def load_file(path, anchors=None):
    '''
    Load a YAML and catch errors.
    '''
    try:
        with open(path) as fh:
            c = yaml.load(fh, Loader=yamlloader.ordereddict.CLoader) or {}
            return replace_anchors(c, anchors) if anchors is not None else c
    except (IOError, yaml.YAMLError) as err:
        raise CLGSplitupException(f"error while loading configuration file '{path}'") from err

def replace_anchors(value, anchors):
    '''
    Recursively replace anchors patterns by their values in _anchors.yml files.
    '''
    if isinstance(value, str):
        try:
            is_anchor = value.startswith('x-')
            return anchors[value] if is_anchor else value
        except KeyError as err:
            raise CLGSplitupException(f"unknown anchor: {err}")

    if isinstance(value, dict):
        new_value = OrderedDict()
        for param, value in value.items():
            if param == '<<<':
                if not value.startswith('x-'):
                    raise CLGSplitupException(f"invalid anchor syntax: {value}")
                new_value.update(replace_anchors(value, anchors))
            else:
                new_value[param] = replace_anchors(value, anchors)
        return new_value

    if isinstance(value, (list, tuple)):
        return [replace_anchors(v, anchors) for v in value]

    return value

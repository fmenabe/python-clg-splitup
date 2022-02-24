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
    if os.path.isabs(commands_dir):
        raise CLGSplitupException('commands dir should be relative to main program')

    setattr(_SELF, 'CMD_DIR', cmd_dir)
    setattr(_SELF, 'COMMANDS_DIR', commands_dir)

    load_clg_customizations(lib_dir)
    conf = load_parser(parents=[])
    return clg.init(format='raw', data=clg_conf, completion=completion)

def dirname(parents):
    return os.path.join(CMD_DIR, '/'.join(cur_parser))

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
        anchors.update(load_file(os.path.join(root, '_anchors.yml')))
        files.pop(files.index('_anchors.yml'))

    conf = {}
    if '_cmd.yml' in files:
        conf = load_file(os.path.join(root, '_cmd.yml'), anchors)
        files.pop(files.index('_cmd.yml'))

    subcommands = from_order(parents, conf.pop('_order', []), files)
    subcommands.extend(from_files(parents, files))
    #subcommands = [from_order(cur_parser, c, files) for c in order]
    #subcommands.extend(
    #    from_path(cur_parser, f, root)
    #    for f in files
    #    if not any(f.startswith(ch) for ch in ('_', '.')))

    for c in subcommands:
        if c['type'] == 'parser':
            load_parser(c['future'], anchors)
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
            mdl = '.'.join(COMMANDS_DIR.split('/') + parents + [cmd])
            yield dict(name=cmd, type='command', path=filepath, mdl=mdl)

        if is_parser(root, cmd):
            files.pop(files.index(cmd))
            future = parents + [cmd]
            yield dict(name=cmd, type='parser', future=future)

        warnings.warn(
            f"clg-splitup: ({'.'.join(parents + cmd)}) ordered command '{cmd}' not found")

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
            if ext not in YAML_EXTS:
                warnings.warn("clg-splitup: not a valid command file: %s" % filepath)
            mdl = '.'.join(COMMANDS_DIR.split('/') + parents + [cmd])
            yield dict(name=cmd, type='command', path=filepath, mdl=mdl)

        if os.path.isdir(filepath):
            yield dict()
            return {'name': filename, 'type': 'parser', 'future': cur_parser + [filename]}

##def from_order(cur_parser, cmd, root, files):
#def from_order(cur_parser, cmd, files):
#    '''
#    Parse
#    '''
#    root = os.path.join(CMD_DIR, '/'.join(cur_parser))
#    cmd_filename = '%s.yml' % cmd
#    cmd_filepath = os.path.join(root, cmd_filename)
#    if os.path.exists(cmd_filepath):
#        files.pop(files.index(cmd_filename))
#        mdl = '.'.join(['commands'] + cur_parser + [cmd])
#        return {'name': cmd, 'type': 'command', 'path': cmd_filepath, 'mdl': mdl}
#
#    parser_path = os.path.join(root, cmd)
#    if os.path.exists(parser_path):
#        files.pop(files.index(cmd))
#        return {'name': cmd, 'type': 'parser', 'future': cur_parser + [cmd]}
#
##def from_path(cur_parser, filename, root):
#def from_path(cur_parser, filename):
#    '''
#    Gene
#    '''
#    root = os.path.join(CMD_DIR, '/'.join(cur_parser))
#    filepath = os.path.join(root, filename)
#
#    if os.path.isfile(filepath):
#        cmd, ext = os.path.splitext(filename)
#        if ext != '.yml':
#            warnings.warn("clg: not a valid file: %s" % filepath)
#        mdl = '.'.join(['commands'] + cur_parser + [cmd])
#        return {'name': cmd, 'type': 'command', 'path': filepath, 'mdl': mdl}
#
#    if os.path.isdir(filepath):
#        return {'name': filename, 'type': 'parser', 'future': cur_parser + [filename]}

def load_file(path, anchors=None):
    '''
    Load a YAML and catch errors.
    '''
    try:
        with open(path) as fh:
            c = yaml.load(fh, Loader=yamlloader.ordereddict.CLoader)
            return replace_anchors(c, anchors) if anchors is not None else c
    except (IOError, yaml.YAMLError) as err:
        raise CLGSplitupException(f"error while loading configuration file '{path}'") from err

def replace_anchors(value, anchors):
    '''
    Recursively replace anchors patterns by their values in _anchors.yml files.
    '''
    if isinstance(value, str):
        try:
            is_anchor = all((value.startswith('_'), not value.startswith('__'),
                             value.endswith('_'), not value.endswith('__')))
            return anchors[value[1:-1].lower()] if is_anchor else value
        except KeyError as err:
            raise CLGSplitupException(f"unknown anchor") from err

    if isinstance(value, dict):
        new_value = OrderedDict()
        for param, value in value.items():
            if param == '<<<':
                if not value.startswith('_') or not value.endswith('_'):
                    raise CLGSplitupException(f"invalid anchor syntax: {value}")
                new_value.update(replace_anchors(value, anchors))
            else:
                new_value[param] = replace_anchors(value, anchors)
        return new_value

    if isinstance(value, (list, tuple)):
        return [replace_anchors(v, anchors) for v in value]

    return value

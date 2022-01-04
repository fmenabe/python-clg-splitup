# coding: utf-8

import os
import sys
import imp
import clg
import yaml
import yamlloader
from collections import OrderedDict

# The module itself.
_SELF = sys.modules[__name__]

CLG_CUSTOMISATIONS = (
    'types',        # custom types for options and arguments
    'actions',      # custom actions for options and arguments
    'completers'    # custom completers for argcomplete
)

DEFAULTS = {
    # Main configuration file of the CLI.
    # default: cmd.yml file in main program directory
    'cmd_file': os.path.join(sys.path[0], 'cmd.yml'),
    # File containing reusable parts of configuration.
    # default: anchors.yml file in main program directory
    'anchors_file': os.path.join(sys.path[0], 'anchors.yml'),
    # Directory containing subcommands CLI configuration.
    # default: cmd/ directory in main program directory
    'cmd_dir': os.path.join(sys.path[0], 'cmd'),
    # Directory containing clg helpers (types, actions, ...)
    # default: lib/clg directory in main program directory
    'lib_dir': os.path.join(sys.path[0], 'lib', 'clg'),
    # Directory containing commands logic.
    # default: commands/ directory in main program directory
    'commands_dir': os.path.join(sys.path[0], 'commands')
}
# Exception raised by this module.
class CLGSplitupError(Exception):
    pass


def init(cmd_file=None, anchors_file=None, cmd_dir=None,
         lib_dir=None, commands_dir=None, completion=False):
    """Load command
    """
    # Get files paths.
    setattr(_SELF, 'CMD_FILE', cmd_file or DEFAULTS['cmd_file'])
    setattr(_SELF, 'ANCHORS_FILE', anchors_file or DEFAULTS['anchors_file'])
    setattr(_SELF, 'CMD_DIR', cmd_dir or DEFAULTS['cmd_dir'])
    setattr(_SELF, 'LIB_DIR', lib_dir or DEFAULTS['lib_dir'])
    setattr(_SELF, 'COMMANDS_DIR', commands_dir or DEFAULTS['commands_dir'])

    # Load clg customizations (types, actions, completers).
    load_clg_customizations()

    # Load anchors.
    anchors = load_anchors()

    # Load main configuration file.
    try:
        conf = load_file(CMD_FILE, anchors) or OrderedDict()
    except IOError:
        raise CLGSplitupError('main file (%s) does not exists' % CMD_FILE)

    # Load commands configuration.
    if os.path.exists(CMD_DIR):
        conf.update(load_dir(CMD_DIR))

    # Add commands directory to sys.path if necessary
    sys.path.append(os.path.join('/'.join((COMMANDS_DIR.split('/')[:-1]))))

    # Initialize clg and return command-line arguments.
    return clg.init(format='raw', data=conf, completion=completion)

def load_clg_customizations():
    for const in CLG_CUSTOMISATIONS:
        filepath = os.path.join(LIB_DIR, '%s.py' % const)
        if os.path.exists(filepath):
            mdl = imp.load_source(const, filepath)
            elts = {elt: getattr(mdl, elt)
                    for elt in dir(mdl)
                    if not elt.startswith('__') and not elt.endswith('__')}
            getattr(clg, const.upper()).update(elts)

def load_anchors():
    return (yaml.load(open(ANCHORS_FILE), Loader=yamlloader.ordereddict.CLoader)
            if os.path.exists(ANCHORS_FILE)
            else {})

def load_file(path, anchors):
    def replace_anchors(conf):
        if isinstance(conf, str):
            try:
                return (anchors[conf[1:-1].lower()]
                        if all((conf.startswith('_'), not conf.startswith('__'),
                                conf.endswith('_'), not conf.endswith('__')))
                        else conf)
            except KeyError:
                raise CLGSplitupError("(%s) invalid anchor '%s'" % (path, conf))
        elif isinstance(conf, dict):
            new_conf = OrderedDict()
            for param, value in conf.items():
                if param == '<<<':
                    if not value.startswith('_') or not value.endswith('_'):
                        raise CLGSplitupError("%s: invalid anchor '%s'" % (path, value))
                    new_conf.update(replace_anchors(value))
                else:
                    new_conf[param] = replace_anchors(value)
            return new_conf
        elif isinstance(conf, (list, tuple)):
            return [replace_anchors(elt) for elt in conf]
        else:
            return conf
    conf = yaml.load(open(path), Loader=yamlloader.ordereddict.CLoader)
    return replace_anchors(conf or {})

def load_dir(dirpath):
    conf = load_subparsers(dirpath)

    subcommands = (
        [command
         for filename in sorted(os.listdir(dirpath))
         for command, fileext in [os.path.splitext(filename)]
         if (not os.path.isdir(os.path.join(dirpath, filename))
             and fileext == '.yml')
             and filename not in ('_order.yml', '_subparsers.yml')]
        if not os.path.exists(os.path.join(dirpath, '_order.yml'))
        else yaml.load(open(os.path.join(dirpath, '_order.yml'))))

    for command in subcommands:
        filepath = os.path.join(dirpath, '{:s}.yml'.format(command))

        (conf.setdefault('subparsers', {})
             .setdefault('parsers', OrderedDict())
             .update({command: load_file(filepath)}))

        parsers_path = os.path.join(dirpath, command)
        if os.path.exists(parsers_path):
            conf['subparsers']['parsers'][command].update(load_dir(parsers_path))
        else:
            mdl = ('.'.join((os.path.basename(COMMANDS_DIR),
                            os.path.relpath(dirpath, CMD_DIR).replace('/', '.'),
                            command))
		      .replace('-', '_'))
            conf['subparsers']['parsers'][command]['execute'] = {'module': mdl}

    return conf

def load_subparsers(path):
    filepath = os.path.join(path, '_subparsers.yml')
    return {'subparsers': load_file(filepath)} if os.path.exists(filepath) else {}

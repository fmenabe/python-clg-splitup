# coding: utf-8

import os
import sys
import imp
import clg
import yaml
import yamlordereddictloader
from collections import OrderedDict
from pprint import pprint


_SELF = sys.modules[__name__]

ANCHORS = {}
CLG_CONSTS = ('types', 'actions', 'completers')

class ClifError(Exception):
    pass


def init(cmd_file=None, anchors_file=None, cmd_dir=None,
         lib_dir=None, commands_dir=None, completion=False):
    # Get files paths.
    setattr(_SELF, 'CMD_FILE', cmd_file or os.path.join(sys.path[0], 'cmd.yml'))
    setattr(_SELF, 'ANCHORS_FILE',  anchors_file or os.path.join(sys.path[0], 'anchors.yml'))
    setattr(_SELF, 'CMD_DIR', cmd_dir or os.path.join(sys.path[0], 'cmd'))
    setattr(_SELF, 'LIB_DIR', lib_dir or os.path.join(sys.path[0], 'lib', 'clg'))
    setattr(_SELF, 'COMMANDS_DIR', commands_dir or os.path.join(sys.path[0], 'commands'))

    # Load clg customizations (types, actions, completers).
    load_clg_customizations()

    # Load anchors.
    load_anchors()

    # Load main configuration file.
    try:
        conf = load_file(CMD_FILE) or OrderedDict()
    except FileNotFoundError:
        raise ClifError('main file (cmd/cmd.yml) does not exists')

    # Load commands configuration.
    if os.path.exists(CMD_DIR):
        conf.update(load_dir(CMD_DIR))

    # Add commands directory to sys.path if necessary)
    sys.path.append(os.path.join('/'.join((COMMANDS_DIR.split('/')[:-1]))))

    # Initialize clg and return command-line arguments.
    return clg.init(format='raw', data=conf, completion=completion)

def load_clg_customizations():
    for const in CLG_CONSTS:
        filepath = os.path.join(LIB_DIR, '%s.py' % const)
        if os.path.exists(filepath):
            mdl = imp.load_source(const, filepath)
            elts = {elt: getattr(mdl, elt)
                    for elt in dir(mdl)
                    if not elt.startswith('__') and not elt.endswith('__')}
            getattr(clg, const.upper()).update(elts)

def load_anchors():
    ANCHORS.update(yaml.load(open(ANCHORS_FILE), Loader=yamlordereddictloader.Loader)
                   if os.path.exists(ANCHORS_FILE)
                   else {})

def load_file(path):
    def replace_anchors(conf):
        if isinstance(conf, str):
            try:
                return (ANCHORS[conf[1:-1].lower()]
                        if all((conf.startswith('_'), not conf.startswith('__'),
                                conf.endswith('_'), not conf.endswith('__')))
                        else conf)
            except KeyError:
                raise ClifError("(%s) invalid anchor '%s'" % (path, conf))
        elif isinstance(conf, dict):
            new_conf = OrderedDict()
            for param, value in conf.items():
                if param == '<<<':
                    if not value.startswith('_') or not value.endswith('_'):
                        raise ClifError("%s: invalid anchor '%s'" % (path, value))
                    new_conf.update(replace_anchors(value))
                else:
                    new_conf[param] = replace_anchors(value)
            return new_conf
        elif isinstance(conf, (list, tuple)):
            return [replace_anchors(elt) for elt in conf]
        else:
            return conf
    conf = yaml.load(open(path), Loader=yamlordereddictloader.Loader)
    return replace_anchors(conf or {})

def load_dir(dirpath):
    conf = load_subparsers(dirpath)

    for filename in sorted(os.listdir(dirpath)):
        filepath = os.path.join(dirpath, filename)
        cmd, fileext = os.path.splitext(filename)
        if os.path.isdir(filepath) or filename == '_subparsers.yml' or fileext != '.yml':
            continue

        (conf.setdefault('subparsers', {})
             .setdefault('parsers', OrderedDict())
             .update({cmd: load_file(filepath)}))

        parsers_path = os.path.join(dirpath, cmd)
        if os.path.exists(parsers_path):
            conf['subparsers']['parsers'][cmd].update(load_dir(parsers_path))
        else:
            mdl = '.'.join((os.path.basename(COMMANDS_DIR),
                            os.path.relpath(dirpath, CMD_DIR).replace('/', '.'),
                            cmd))
            conf['subparsers']['parsers'][cmd]['execute'] = {'module': mdl}

    return conf

def load_subparsers(path):
    filepath = os.path.join(path, '_subparsers.yml')
    return {'subparsers': load_file(filepath)} if os.path.exists(filepath) else {}

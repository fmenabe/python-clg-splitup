import os
import sys
import imp
import clg
import yaml
from yamlordereddictloader import Loader as YamlOrderedLoader
from collections import OrderedDict
from pprint import pprint

_SELF = sys.modules[__name__]
_IGNORE = ('_anchors.yml', '_cmd.yml', '_subparsers.yml',  '_types.py')

ANCHORS = {}

class CliError(Exception):
    pass


def init(path, hooks=None):
    conf = _load_dir(path)
    setattr(_SELF, 'cmd', clg.CommandLine(conf))
    setattr(_SELF, 'hooks', hooks or [])


def parse():
    return cmd.parse()


def _load_dir(path):
    _load_types(path)
    _load_anchors(path)
    cmd_file = os.path.join(path, '_cmd.yml')
    subparsers_file = os.path.join(path, '_subparsers.yml')
    conf = _load_file(cmd_file) if os.path.exists(cmd_file) else OrderedDict()
    if os.path.exists(subparsers_file):
        conf.setdefault('subparsers', _load_file(subparsers_file))
    for filename in sorted(os.listdir(path)):
        filepath = os.path.join(path, filename)
        cmd, fileext = os.path.splitext(filename)
        if os.path.isdir(filepath) or filename in _IGNORE or fileext != '.yml':
            continue

        (conf.setdefault('subparsers', {})
             .setdefault('parsers', OrderedDict())
             .update({cmd: _load_file(filepath)}))

        parsers_path = os.path.join(path, cmd)
        if os.path.exists(parsers_path):
            conf['subparsers']['parsers'][cmd].update(_load_dir(parsers_path))
    return conf


def _load_types(path):
    filepath = os.path.join(path, '_types.py')
    if not os.path.exists(filepath):
        return
    mdl = imp.load_source('_types', filepath)
    for elt in dir(mdl):
        if elt.startswith('__') and elt.endswith('__'):
            continue
        clg.TYPES[elt] = getattr(mdl, elt)


def _load_anchors(path):
    filepath = os.path.join(path, '_anchors.yml')
    ANCHORS.update(yaml.load(open(filepath), Loader=YamlOrderedLoader)
                   if os.path.exists(filepath)
                   else {})


def _load_file(path):
    def load_conf(conf):
        if isinstance(conf, str):
            try:
                return (ANCHORS[conf[1:-1].lower()]
                        if all((conf.startswith('_'), not conf.startswith('__'),
                                conf.endswith('_'), not conf.endswith('__')))
                        else conf)
            except KeyError:
                raise CliError("(%s) invalid anchor '%s'" % (path, conf))
        elif isinstance(conf, dict):
            new_conf = OrderedDict()
            for param, value in conf.items():
                if param == '<<<':
                    if not value.startswith('_') or not value.endswith('_'):
                        raise CliError("%s: invalid anchor '%s'" % (path, value))
                    new_conf.update(load_conf(value))
                else:
                    new_conf[param] = load_conf(value)
            return new_conf
        elif isinstance(conf, (list, tuple)):
            return [load_conf(elt) for elt in conf]
        else:
            return conf
    return load_conf(yaml.load(open(path), Loader=YamlOrderedLoader)) or {}

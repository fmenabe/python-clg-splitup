#!/usr/bin/env python
# coding: utf-8

"""Entry point for launching backup's utils."""

import clif
import os.path as path

# Add custom types (in lib.types).
import lib.types as types
clif.clg.TYPES.update({func_name: func
                       for func_name, func in vars(types).items()
                       if not func_name.startswith('_')})

if __name__ == '__main__':
    clif.init(path.abspath(path.join(path.dirname(__file__), 'conf', 'cmd')))
    clif.parse()

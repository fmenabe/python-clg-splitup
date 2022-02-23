# coding: utf-8

"""Command for listing platforms."""

import clif.conf as conf
import clif.logger as logger
from pprint import pformat

def main(args):
    conf.init(args)
    logger.info('command-line arguments:\n%s' % pformat(vars(args)))
    logger.info('columns definition from configuration file (conf/platforms/list.yml):\n%s'
                 % (pformat(conf.COLUMNS)))

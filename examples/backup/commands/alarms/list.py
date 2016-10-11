# coding: utf-8

"""Command for listing alarms of catalogs."""

import clif.conf as conf
import clif.logger as logger
from pprint import pformat

def main(args):
    conf.init(args)
    logger.info('command-line argments:\n%s' % pformat(vars(args)))
    logger.info('columns definition from configuration file (conf/alarms/list.yml):\n%s'
                 % (pformat(conf.COLUMNS)))

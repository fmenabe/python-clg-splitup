# coding: utf-8

"""Command for deleting alarms on catalogs."""

import clif.conf as conf
import clif.logger as logger
from pprint import pformat

def main(args):
    conf.init(args)
    logger.info('command-line arguments:\n%s' % pformat(vars(args)))

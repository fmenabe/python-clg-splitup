# coding: utf-8

"""Dump catalog's data to an Elasticsearch database."""

import clif.conf as conf
import clif.logger as logger
from pprint import pformat

def main(args):
    conf.init(args)
    logger.info("command-line arguments:\n%s" % pformat(vars(args)))
    logger.info("alarms fields from configuration file (conf/dump.yml):\n%s"
                 % pformat(conf.ALARMS_FIELDS))

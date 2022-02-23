# coding: utf-8

"""Command for listing a summary of jobs that have run the last hours."""

import clif.conf as conf
import clif.logger as logger
from pprint import pformat

def main(args):
    conf.init(args)

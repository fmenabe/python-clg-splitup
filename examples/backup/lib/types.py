import re
import argparse
from collections import namedtuple

_PLATFORM_RE = re.compile(r'^(?P<type>host|app):(?P<name>[^@]*)@(?P<catalog>.*)$')
Platform = namedtuple('Platform', ('uri', 'catalog', 'type', 'name'))

_ALARMS_RE = re.compile(r'^(?P<ids>[*]|(:?\d+)*)@(?P<catalog>.*)$')
Alarms = namedtuple('Alarm', ('uri', 'catalog', 'ids'))

def Date(value):
    """Custom type for managing dates in the command-line."""
    from datetime import datetime
    try:
        return datetime(*reversed([int(val) for val in value.split('/')]))
    except Exception as err:
        raise argparse.ArgumentTypeError("invalid date '%s'" % value)

def PlatformURI(value):
    try:
        return Platform(uri=value, **_PLATFORM_RE.search(value).groupdict())
    except Exception as err:
        raise argparse.ArgumentTypeError("invalid platform URI '%s'" % value)

def AlarmsURI(value):
    try:
        regex = _ALARMS_RE.search(value).groupdict()
        alarm_ids = ([int(alarm) for alarm in regex['ids'].split(':')]
                    if regex['ids'] != '*'
                    else regex['ids'])
        return Alarms(uri=value, catalog=regex['catalog'], ids=alarm_ids)
    except Exception as err:
        print(err)
        raise argparse.ArgumentTypeError("invalid alarm URI '%s'" % value)

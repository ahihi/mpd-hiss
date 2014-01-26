from __future__ import division
from datetime import datetime
import sys


def msg(text):
    dt = datetime.now()
    timestamp = dt.strftime("[%Y-%m-%d %H:%M:%S] ")
    sys.stderr.write(timestamp + text + '\n')


def hms(seconds):
    h, m, s = seconds // 3600, seconds % 3600 // 60, seconds % 60
    result = "{minutes:02d}:{seconds:02d}".format(minutes = m, seconds = s)
    if h > 0:
        result = "{hours:02d}:".format(hours = h) + result
    return result

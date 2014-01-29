# mpd-hiss

Growl notifier for MPD (Music Player Daemon) written in Python.
Also supports DBUS based notifiers.

## Requirements

General:
- [MPD](http://mpd.wikia.com/)
- [Python](http://python.org/) (tested on 2.6, 2.7, and 3.3)
- Python 2.6 users will also need to install [argparse](http://code.google.com/p/argparse/), which is part of the standard library since 2.7.
- [python-mpd](http://pypi.python.org/pypi/python-mpd/)
- Optional: [Pillow](https://github.com/python-imaging/Pillow) or PIL for album art and icon scaling support

On Mac OS X:
- [Growl](http://growl.info/)
- [Python support for Growl](http://growl.info/documentation/developer/python-support.php) (for Growl 1.2.2) or [GNTP](https://pypi.python.org/pypi/gntp) (for Growl 1.3+)

On other platforms:
- dbus-python (and a notification daemon)

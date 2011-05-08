#!/usr/bin/env python
import argparse
from datetime import datetime
import os
from os.path import abspath, expanduser
from select import select
import socket
import sys
import time

import Growl
import mpd

def msg(text):
    dt = datetime.now()
    timestamp = dt.strftime("[%Y-%m-%d %H:%M:%S] ")
    print timestamp + text

def disconnect(client):
    try:
        client.disconnect()
    except ConnectionError:
        pass

class AuthError(Exception):
    pass

env_host = os.environ.get("MPD_HOST", "localhost")
env_port = os.environ.get("MPD_PORT", "6600")

env_password = None
if env_host.find("@") >= 0:
    (env_password, env_host) = env_host.split("@", 1)

parser = argparse.ArgumentParser(
    formatter_class = argparse.RawTextHelpFormatter,
    epilog = "\n".join((
        "Format string syntax: http://docs.python.org/library/string.html#format-string-syntax",
        "Available fields as of MPD 0.16.2: album artist track title pos last-modified file time date genre id"   
    ))
)
parser.add_argument(
    "--host",
    dest = "host",
    help = "MPD host",
    default = env_host
)
parser.add_argument(
    "--port",
    dest = "port",
    help = "MPD port",
    default = env_port
)
parser.add_argument(
    "--password",
    dest = "password",
    help = "MPD password",
    default = env_password
)
parser.add_argument(
    "--reconnect-interval",
    dest = "reconnect_interval",
    help = "seconds to wait before reconnecting on connection failure (default: 30)",
    type = float,
    default = 30
)
parser.add_argument(
    "--title-format",
    dest = "title_format",
    help = "Growl notification title format",
    default = "{title}"
)
parser.add_argument(
    "--description-format",
    dest = "description_format",
    help = "Growl notification description format",
    default = "{artist}\n{album}"
)
parser.add_argument(
    "--icon",
    dest = "icon_path",
    help = "path to Growl notification icon",
    default = "~/.mpd-hiss.png"
)

args = parser.parse_args()

msg("Registering Growl notifier...")
growler = Growl.GrowlNotifier(
    applicationName = "mpd-hiss",
    notifications = ["Now Playing"]
)
growler.register()
msg("Registered.")

icon_path = abspath(expanduser(args.icon_path))

try:
    msg("Loading icon from %s..." % icon_path)
    growl_icon = Growl.Image.imageFromPath(icon_path)
    msg("Loaded.")
except:
    msg("Failed to load icon, falling back to default.")
    growl_icon = None

client = mpd.MPDClient()
try:
    while True:
        try:
            msg("Connecting to MPD...")
            client.connect(args.host, args.port)
            msg("Connected.")
            if args.password != None:
                try:
                    msg("Authenticating...")
                    client.password(args.password)
                    msg("Authenticated.")
                except mpd.CommandError, e:
                    raise AuthError(e)
            while True:
                client.send_idle("player")
                select((client,), (), ())
                client.fetch_idle()
                status = client.status()
                if status["state"] == "play":
                    song = client.currentsong()
                    msg("Sending Now Playing notification for %s - [%s] %s." % (song["artist"], song["album"], song["title"]))
                    growler.notify(
                        noteType = "Now Playing",
                        title = args.title_format.format(**song),
                        description = args.description_format.format(**song),
                        icon = growl_icon
                    )
        except (mpd.ConnectionError, AuthError, socket.error), e:
            msg("Error: %s" % e)
            msg("Reconnecting in %d seconds..." % args.reconnect_interval)
            time.sleep(args.reconnect_interval)
        finally:
            disconnect(client)
except KeyboardInterrupt, e:
    pass

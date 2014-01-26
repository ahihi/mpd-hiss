#!/usr/bin/env python
import argparse
import os
import re
import socket
import sys
from os.path import dirname, basename, abspath, expanduser
from time import sleep

import mpd

from utils import msg, hms


if sys.platform == "darwin":
    from growl_notify import notify, load_image
else:
    from dbus_notify import notify, load_image


def disconnect(client):
    try:
        client.disconnect()
    except mpd.ConnectionError:
        pass


class AuthError(Exception):
    pass


r_cover = re.compile(r'(album.?art|cover|front)\.(jpe?g|png)$', re.I)

def album_art(previous, filename, scale_icons):
    name = dirname(filename)

    if name == previous[0]:
        return previous

    try:
        files = os.listdir(name)
    except Exception as e:
        msg("Failed to list %s: %s" % (name, e))
        return name, None

    for cover in files:
        if r_cover.search(cover):
            msg("Album art: %s/%s" % (name, cover))
            return name, load_image(os.path.join(name, cover), scale_icons)

    return name, None

def mpd_hiss(client, args):
    msg("Connecting to MPD...")
    client.connect(args.host, args.port)
    msg("Connected.")

    if args.password is not None:
        try:
            msg("Authenticating...")
            client.password(args.password)
            msg("Authenticated.")
        except mpd.CommandError as e:
            raise AuthError(e)

    last_status = client.status()
    last_art = (None, None)

    while True:
        client.send_idle("player")
        client.fetch_idle()

        status = client.status()
        started_playing = (last_status["state"] != "play"
                           and status["state"] == "play")
        last_songid = last_status.get("songid", None)
        songid = status.get("songid", None)
        track_changed = songid not in (None, last_songid)

        if started_playing or track_changed:
            song = client.currentsong()

            if args.album_art:
                filename = os.path.join(args.album_art, song.get("file"))
                last_art = album_art(last_art, filename, args.scale_icons)
                icon = last_art[1] or growl_icon
            else:
                icon = growl_icon

            song_data = {
                "artist": song.get("artist", "Unknown artist"),
                "title": (song.get("title") or basename(song.get("file"))
                          or "Unknown track"),
                "album": song.get("album", ""),
                "duration": hms(int(song.get("time", 0)))
            }
            msg("Sending Now Playing notification for "
                "{artist} - [{album}] {title}.".format(**song_data))
            description = args.description_format.format(**song_data)
            notify(title=args.title_format.format(**song_data),
                   description=description.rstrip("\n"),
                   icon=icon)
        last_status = status


EPILOG = ("Format string syntax: "
          "http://docs.python.org/library/string.html#format-string-syntax\n"
          "Available fields: artist, title, album, duration")

env_host = os.environ.get("MPD_HOST", "localhost")
env_port = os.environ.get("MPD_PORT", "6600")

env_password = None
if env_host.find("@") >= 0:
    (env_password, env_host) = env_host.split("@", 1)

parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter,
                                 epilog=EPILOG)
parser.add_argument("--host",
                    dest="host",
                    help="MPD host",
                    default=env_host)
parser.add_argument("--port",
                    dest="port",
                    help="MPD port",
                    default=env_port)
parser.add_argument("--password",
                    dest="password",
                    help="MPD password",
                    default=env_password)
parser.add_argument("--reconnect-interval",
                    dest="reconnect_interval",
                    help="seconds to wait before reconnecting on connection "
                         "failure (default: 30)",
                    type=float,
                    default=30)
parser.add_argument("--title-format",
                    dest="title_format",
                    help="notification title format",
                    default="{title}")
parser.add_argument("--description-format",
                    dest="description_format",
                    help="notification description format",
                    default="{artist}\n{album}")
parser.add_argument("--icon",
                    dest="icon_path",
                    help="path to notification icon",
                    default="./mpd-hiss.png")
parser.add_argument("--album-art",
                    dest="album_art",
                    help="value of MPD's music_directory to load album art, "
                         " when available",
                    default="")
parser.add_argument("--scale-icons",
                    dest="scale_icons",
                    action="store_true",
                    help="scale icons if the notifier doesn't do it for us",
                    default=False)


if __name__ == '__main__':
    args = parser.parse_args()

    icon_path = abspath(expanduser(args.icon_path))

    try:
        msg("Loading icon from %s..." % icon_path)
        growl_icon = load_image(icon_path, args.scale_icons)
        msg("Loaded.")
    except:
        msg("Failed to load icon, falling back to default.")
        growl_icon = None

    client = mpd.MPDClient()

    while True:
        try:
            mpd_hiss(client, args)
        except KeyboardInterrupt as e:
            break
        except (mpd.ConnectionError, AuthError, socket.error) as e:
            msg("Error: %s" % e)
        finally:
            disconnect(client)

        msg("Reconnecting in %d seconds..." % args.reconnect_interval)
        sleep(args.reconnect_interval)

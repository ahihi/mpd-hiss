#!/usr/bin/env python
import argparse
import logging
import mpd
import os
import re
import socket
import sys
from os.path import dirname, basename
from time import sleep

from utils import hms, load_scaled_image, full_path


if sys.platform == "darwin":
    from growl_notify import notify, native_load_image
else:
    from dbus_notify import notify, native_load_image


def load_image(filename, scale):
    if scale:
        return load_scaled_image(filename)

    return native_load_image(filename)


def disconnect(client):
    try:
        client.disconnect()
    except mpd.ConnectionError:
        pass


class AuthError(Exception):
    pass


r_cover = re.compile(r'(album.?art|folder|cover|front)\.(jpe?g|png)$', re.I)


def get_album_dir(filename, mpd_dir):
    if filename.startswith('/'):
        return dirname(filename)

    elif mpd_dir:
        return dirname(os.path.join(mpd_dir, filename))

    return None


def album_art(cache, name, scale):
    # If a file was added with an absolute filenames, it will start
    # with / -- we shouldn't have to add our album art path
    # (This conflicts with --album-art being an option, since it might
    #  now show album art even without the MPD music dir being set)
    if name is None:
        return cache['default']

    logging.debug("Looking for album art in %r", name)

    if cache['last_dir'] == name:
        return cache['last_image']

    cache['last_dir'] = name
    cache['last_image'] = cache['default']

    try:
        files = os.listdir(name)
    except:
        logging.exception("Failed to list %s", name)
        return cache['default']

    for cover in files:
        if r_cover.search(cover):
            logging.debug("Album art: %s/%s", name, cover)
            cache['last_image'] = load_image(os.path.join(name, cover),
                                             scale)
            break

    return cache['last_image']


def mpd_hiss(client, args):
    logging.info("Connecting to MPD...")
    client.connect(args.host, args.port)
    logging.debug("Connected.")

    if args.password is not None:
        try:
            logging.debug("Authenticating...")
            client.password(args.password)
            logging.debug("Authenticated.")
        except mpd.CommandError as e:
            raise AuthError(e)

    last_status = client.status()

    icon_cache = {
        'last_dir': None,
        'last_image': None,
        'default': growl_icon,
    }

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
            icon = album_art(icon_cache, get_album_dir(song.get("file"),
                                                       args.album_art),
                             args.scale_icons)

            song_data = {
                "artist": song.get("artist", "Unknown artist"),
                "title": (song.get("title") or basename(song.get("file"))
                          or "Unknown track"),
                "album": song.get("album", ""),
                "duration": hms(int(song.get("time", 0)))
            }
            logging.info("Sending Now Playing notification for "
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
parser.add_argument("--debug",
                    dest="debug",
                    action="store_true",
                    help="Enable debug logging",
                    default=False)
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

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    if args.album_art:
        args.album_art = full_path(args.album_art)

    icon_path = full_path(args.icon_path)

    try:
        logging.info("Loading icon from %s...", icon_path)
        growl_icon = load_image(icon_path, args.scale_icons)
        logging.debug("Icon loaded.")
    except:
        logging.exception("Failed to load icon, falling back to default.")
        growl_icon = None

    client = mpd.MPDClient()

    while True:
        try:
            mpd_hiss(client, args)
        except KeyboardInterrupt as e:
            break
        except (mpd.ConnectionError, AuthError, socket.error) as e:
            logging.exception("Connection error")
        finally:
            disconnect(client)

        logging.info("Reconnecting in %d seconds...", args.reconnect_interval)
        sleep(args.reconnect_interval)

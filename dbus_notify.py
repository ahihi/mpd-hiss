from cgi import escape
import dbus
from utils import is_string



ITEM = "org.freedesktop.Notifications"
PATH = "/org/freedesktop/Notifications"
INTERFACE = "org.freedesktop.Notifications"
APP_NAME = "mpd-hiss"


def dbus_raw_image(im):
    """Convert image for DBUS"""
    raw = im.tobytes("raw", "RGBA")
    alpha, bps, channels = 0, 8, 4
    stride = channels * im.size[0]
    return (im.size[0], im.size[1], stride, alpha, bps, channels,
            dbus.ByteArray(raw))


def native_load_image(image):
    return image


def notify(title, description, icon):
    actions = ""
    hint = {"suppress-sound": True, "urgency": 0}
    time = 5000
    icon_file = ""

    if is_string(icon):
        # File path
        icon_file = icon
    elif icon:
        # Not all notifiers support this
        # Some require "icon" and an image on disk
        hint["icon_data"] = dbus_raw_image(icon)

    bus = dbus.SessionBus()
    notif = bus.get_object(ITEM, PATH)
    notify = dbus.Interface(notif, INTERFACE)
    notify.Notify(APP_NAME, 1, icon_file, title, escape(description), actions,
                  hint, time)

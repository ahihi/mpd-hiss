from cgi import escape
import dbus

try:
    from PIL import Image
except ImportError:
    Image = None

ITEM = "org.freedesktop.Notifications"
PATH = "/org/freedesktop/Notifications"
INTERFACE = "org.freedesktop.Notifications"
APP_NAME = "mpd-hiss"


def load_image(image, scale_icons):
    if scale_icons:
        if Image is None:
            return ''

        return load_scaled_image(image)

    return image

# Probably should be a commandline option
SIZE = (128, 64)

def load_scaled_image(image):
    # I've opted to not support transparency here, because it's broken on
    # (at least) awesome-wm  -- TODO
    im = Image.open(image)
    im.thumbnail(SIZE, Image.ANTIALIAS)
    raw = im.tobytes('raw', 'RGB')
    alpha, bps, channels = 0, 8, 3
    stride = channels * im.size[0]
    return (im.size[0], im.size[1], stride, alpha, bps, channels,
            dbus.ByteArray(raw))


def notify(title, description, icon):
    actions = ""
    hint = {"suppress-sound": True, "urgency": 0}
    time = 5000

    if icon:
        # Not all notifiers support this
        # Some require "icon" and an image on disk
        hint["icon_data"] = icon

    bus = dbus.SessionBus()
    notif = bus.get_object(ITEM, PATH)
    notify = dbus.Interface(notif, INTERFACE)
    notify.Notify(APP_NAME, 1, '', title, escape(description), actions, hint,
                  time)


if __name__ == "__main__":
    notify()

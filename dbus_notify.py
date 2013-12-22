import dbus

try:
    from PIL import Image
except ImportError:
    Image = None

ITEM = "org.freedesktop.Notifications"
PATH = "/org/freedesktop/Notifications"
INTERFACE = "org.freedesktop.Notifications"
APP_NAME = "mpd-hiss"


def load_image(image, experimental=False):
    if Image is not None and experimental:
        return experimental_load_image(image)

    # The icon is too big!
    return ''


SIZE = (64, 64)

def experimental_load_image(image):
    # Transparent icons are broken on awesome, or am I stupid?
    im = Image.open(image)
    im.thumbnail(SIZE, Image.ANTIALIAS)
    raw = im.tobytes('raw', 'RGB')
    stride = 4 * im.size[0]
    alpha, bps, channels = 1, 24, 3
    return (im.size[0], im.size[1], stride, alpha, bps, channels,
            dbus.ByteArray(raw))


def notify(title, description, icon):
    actions = ""
    hint = {"suppress-sound": True, "urgency": 0}
    time = 5000

    if icon:
        hint["icon_data"] = icon

    bus = dbus.SessionBus()
    notif = bus.get_object(ITEM, PATH)
    notify = dbus.Interface(notif, INTERFACE)
    notify.Notify(APP_NAME, 1, '', title, description, actions, hint, time)


if __name__ == "__main__":
    notify()

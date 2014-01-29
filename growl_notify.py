import logging
from utils import is_string

try:
    from io import BytesIO as Buffer
except:
    from StringIO import StringIO as Buffer


def growl_raw_image(image):
    """Convert image for Growl"""
    b = Buffer()
    image.save(b, 'PNG')
    return b.getvalue()


def load_image_legacy(image):
    return growl.Image.imageFromPath(image)


def load_image_gntp(image):
    with open(image, "rb") as handle:
        return handle.read()


try:
    import gntp.notifier as growl
    native_load_image = load_image_gntp
    logging.debug("Growl version: gntp")

except ImportError:
    import Growl as growl
    native_load_image = load_image_legacy
    logging.debug("Growl version: legacy")


logging.debug("Registering Growl notifier...")

growler = growl.GrowlNotifier(applicationName="mpd-hiss",
                              notifications=["Now Playing"])
growler.register()
logging.debug("Registered.")


def notify(title, description, icon):
    if icon and not is_string(icon):
        icon = growl_raw_image(icon)

    growler.notify(noteType="Now Playing",
                   title=title,
                   description=description,
                   icon=icon)

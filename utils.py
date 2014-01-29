from __future__ import division
import logging
from os.path import abspath, expanduser

try:
    from PIL import Image
except ImportError:
    Image = None


logging.basicConfig(format='[%(asctime)s] %(levelname)s: %(message)s',
                    date_format = '%Y-%m-%d %H:%M:%S',
                    level=logging.INFO)


# Python 2/3 compat
try:
    unicode
    def is_string(obj):
        return isinstance(obj, (str, unicode))
except NameError:
    def is_string(obj):
        return isinstance(obj, (str, bytes))


def full_path(rel_path):
    return abspath(expanduser(rel_path))


def hms(seconds):
    h, m, s = seconds // 3600, seconds % 3600 // 60, seconds % 60
    result = "{minutes:02d}:{seconds:02d}".format(minutes = m, seconds = s)
    if h > 0:
        result = "{hours:02d}:".format(hours = h) + result
    return result


def load_scaled_image(image, scale=(128, 64)):
    if Image is None:
        # Not supported
        return None

    im = Image.open(image)
    im.thumbnail(scale, Image.ANTIALIAS)

    # Transparent PNGs were broken without this?
    # Who knows why.
    if im.mode == "RGBA":
        fixed = Image.new("RGBA", im.size)
        fixed.paste(im, (0, 0), mask=im)
        im = fixed
    else:
        im = im.convert("RGBA")

    return im

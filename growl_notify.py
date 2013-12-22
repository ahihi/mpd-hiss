import platform
from utils import msg

osx_version = platform.mac_ver()[0]
legacy = osx_version != "" and osx_version < "10.7"

if legacy:
    import Growl as growl
    load_image = lambda path, _: growl.Image.imageFromPath(path)
else:
    import gntp.notifier as growl

    def load_image(path, _):
        with open(path, "rb") as handle:
            return handle.read()

msg("Registering Growl notifier...")

growler = growl.GrowlNotifier(applicationName="mpd-hiss",
                              notifications=["Now Playing"])
growler.register()
msg("Registered.")


def notify(title, description, icon):
    growler.notify(noteType="Now Playing",
                   title=title,
                   description=description,
                   icon=icon)

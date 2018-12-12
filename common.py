SETTINGS_NAME = "SublimeBookmarks.sublime-settings"
VERSION = "3.0.0"


def log(x):
    import datetime
    print("%s %s" % (datetime.datetime.now(), x))


def get_current_line_region(view):
    return view.line(view.sel()[0])

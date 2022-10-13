import sys

sys.path.append("./binary/Python-minimum/site-packages")
sys.path.append("../")
sys.path.append("./")

try:
    from backports.datetime_fromisoformat import MonkeyPatch
    MonkeyPatch.patch_fromisoformat()
except ModuleNotFoundError or NameError as e:
    pass


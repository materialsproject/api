# coding: utf-8
""" Primary MAPI module """
from pkg_resources import get_distribution, DistributionNotFound
from monty.serialization import loadfn

try:
    __version__ = get_distribution(__name__).version
except DistributionNotFound:
    # package is not installed
    pass

from mp_api.core.settings import MAPISettings

try:
    settings = MAPISettings()
    mapi = loadfn(settings.app_path)
    app = mapi.app
except Exception as e:
    # Something went wrong with loading default app
    print("Failed loadning App")
    print(e)
    pass

# coding: utf-8
""" Primary MAPI module """
import os
from pkg_resources import get_distribution, DistributionNotFound
from mp_api.client import MPRester

try:  # pragma: no cover
    from setuptools_scm import get_version

    __version__ = get_version(root="../../", relative_to=__file__)
except (ImportError, LookupError):  # pragma: no cover
    try:
        __version__ = get_distribution(__package__).version
    except DistributionNotFound:  # pragma: no cover
        __version__ = os.environ.get("SETUPTOOLS_SCM_PRETEND_VERSION", None)

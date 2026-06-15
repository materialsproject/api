import pytest
from packaging.version import Version

try:
    from mp_api.client.contribs import ContribsClient
except ImportError:
    ContribsClient = None


_pytest_version = Version(pytest.__version__)
PYTEST_GE_8_0 = any(
    [
        _pytest_version.is_devrelease,
        _pytest_version.is_prerelease,
        _pytest_version >= Version("8.0"),
    ]
)


if PYTEST_GE_8_0:

    def pytest_ignore_collect(collection_path, config):
        # Skip tests if contribs client isn't installed
        if ContribsClient is None and "contribs" in str(collection_path):
            return True
        return False

else:

    def pytest_ignore_collect(path, config):
        # Skip tests if contribs client isn't installed
        if ContribsClient is None and "contribs" in str(path):
            return True
        return False

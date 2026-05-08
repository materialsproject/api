try:
    from mp_api.client.contribs import ContribsClient
except ImportError:
    ContribsClient = None


def pytest_ignore_collect(path, config):
    # Skip tests if contribs client isn't installed
    if ContribsClient is None and "contribs" in str(path):
        return True
    return False

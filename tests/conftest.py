import logging
from unittest.mock import patch

import aiohttp
import pytest
import pytest_asyncio
from aioresponses import aioresponses
from syrupy import SnapshotAssertion

from pyenphase.ssl import NO_VERIFY_SSL_CONTEXT
from tests.syrupy import EnphaseSnapshotExtension


@pytest.fixture
def mock_aioresponse():
    """
    Provides an aioresponses context manager for mocking aiohttp HTTP requests in tests.

    All aiohttp ClientSession requests are mocked except those to "http://127.0.0.1:8123". Yields the mock object for use within the test.
    """
    # Note: aioresponses will mock all ClientSession instances by default
    with aioresponses(passthrough=["http://127.0.0.1:8123"]) as m:
        yield m


@pytest_asyncio.fixture
async def test_client_session():
    """
    Provides an aiohttp ClientSession with short timeouts and disabled SSL verification for testing.

    Yields:
        An aiohttp ClientSession instance configured for fast test execution.

    """
    timeout = aiohttp.ClientTimeout(total=5.0, connect=1.0, sock_read=1.0)
    connector = aiohttp.TCPConnector(ssl=NO_VERIFY_SSL_CONTEXT)
    session = aiohttp.ClientSession(timeout=timeout, connector=connector)
    yield session
    await session.close()


@pytest.fixture
def snapshot(snapshot: SnapshotAssertion) -> SnapshotAssertion:
    """
    Returns a snapshot assertion fixture enhanced with the EnphaseSnapshotExtension.

    Args:
        snapshot: The base snapshot assertion fixture.

    Returns:
        The snapshot assertion fixture with the Enphase extension applied.

    """
    return snapshot.use_extension(EnphaseSnapshotExtension)


@pytest.fixture(autouse=True)
def fast_tenacity():
    """
    Speeds up tenacity retries in tests by patching sleep functions to return immediately.

    This fixture automatically mocks `tenacity.nap.time` and `asyncio.sleep` so that retry delays do not slow down test execution.
    """
    with patch("tenacity.nap.time"), patch("asyncio.sleep", return_value=None):
        yield


@pytest.fixture(autouse=True)
def setup_logging():
    """
    Configures the "pyenphase" logger to use DEBUG level for all tests.
    """
    logging.getLogger("pyenphase").setLevel(logging.DEBUG)

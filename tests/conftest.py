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
    """Return aioresponses fixture."""
    # Note: aioresponses will mock all ClientSession instances by default
    with aioresponses(passthrough=["http://127.0.0.1:8123"]) as m:
        yield m


@pytest_asyncio.fixture
async def test_client_session():
    """Create an aiohttp ClientSession with low timeout for tests."""
    timeout = aiohttp.ClientTimeout(total=5.0, connect=1.0, sock_read=1.0)
    connector = aiohttp.TCPConnector(ssl=NO_VERIFY_SSL_CONTEXT)
    session = aiohttp.ClientSession(timeout=timeout, connector=connector)
    yield session
    await session.close()


@pytest.fixture
def snapshot(snapshot: SnapshotAssertion) -> SnapshotAssertion:
    """Return snapshot assertion fixture with the Enphase extension."""
    return snapshot.use_extension(EnphaseSnapshotExtension)


@pytest.fixture(autouse=True)
def fast_tenacity():
    """Make tenacity retries fast by mocking time.sleep."""
    with patch("tenacity.nap.time"), patch("asyncio.sleep", return_value=None):
        yield


@pytest.fixture(autouse=True)
def setup_logging():
    """Set up logging for all tests."""
    logging.getLogger("pyenphase").setLevel(logging.DEBUG)

import inspect
import logging
from unittest.mock import Mock, patch

import aiohttp
import pytest
import pytest_asyncio
from aioresponses import aioresponses
from syrupy import SnapshotAssertion

from pyenphase.ssl import NO_VERIFY_SSL_CONTEXT
from tests.syrupy import EnphaseSnapshotExtension

# bandaid for aiorsponses https://github.com/pnuckowski/aioresponses/issues/289
# until https://github.com/pnuckowski/aioresponses/pull/288/changes
# is merged and published. Remove whenever aioresponses is updated.
# sourced from https://github.com/j7an/dep-rank/pull/123/changes
#
# aiohttp 3.14 added a required keyword-only ``stream_writer`` argument to
# ``ClientResponse.__init__``. aioresponses (<=0.7.8) builds mocked responses
# without it, so every mocked request raises ``TypeError: ... missing 1
# required keyword-only argument: 'stream_writer'``. aiohttp only reads
# ``stream_writer.output_size``, so a ``Mock(output_size=0)`` suffices.
#
# This mirrors the upstream fix (aioresponses#288, tracking aioresponses#289).
# The signature guard makes it a no-op on aiohttp < 3.14 and once aioresponses
# ships a release that supplies the argument itself; remove this shim then.
_response_init = aiohttp.ClientResponse.__init__
if "stream_writer" in inspect.signature(_response_init).parameters:

    def _patched_response_init(self, *args, **kwargs):
        kwargs.setdefault("stream_writer", Mock(output_size=0))
        _response_init(self, *args, **kwargs)

    aiohttp.ClientResponse.__init__ = _patched_response_init


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

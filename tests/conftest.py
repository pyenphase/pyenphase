import pytest
from syrupy import SnapshotAssertion

from tests.syrupy import EnphaseSnapshotExtension


@pytest.fixture
def snapshot(snapshot: SnapshotAssertion) -> SnapshotAssertion:
    """Return snapshot assertion fixture with the Enphase extension."""
    return snapshot.use_extension(EnphaseSnapshotExtension)

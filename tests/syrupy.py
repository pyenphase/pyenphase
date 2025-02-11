from dataclasses import asdict, is_dataclass
from typing import Any

from syrupy.extensions import AmberSnapshotExtension
from syrupy.extensions.amber import AmberDataSerializer
from syrupy.types import PropertyFilter, PropertyMatcher, PropertyPath, SerializableData


class EnphaseSnapshotSerializer(AmberDataSerializer):
    """
    Enphase snapshot serializer for Syrupy.

    Handles special cases for Enphase data structures.
    """

    @classmethod
    def _serialize(
        cls,
        data: SerializableData,
        *,
        depth: int = 0,
        exclude: PropertyFilter | None = None,
        include: PropertyFilter | None = None,
        matcher: PropertyMatcher | None = None,
        path: PropertyPath = (),
        visited: set[Any] | None = None,
    ) -> str:
        """
        Pre-process data before serializing.

        This allows us to handle specific cases for Enphase data structures.
        """
        serializable_data = data
        if is_dataclass(type(data)):
            serializable_data = asdict(data)

        return super()._serialize(
            serializable_data,
            depth=depth,
            exclude=exclude,
            include=include,
            matcher=matcher,
            path=path,
            visited=visited,
        )


class EnphaseSnapshotExtension(AmberSnapshotExtension):
    """Enphase extension for Syrupy."""

    VERSION = "1"
    """Current version of serialization format.

    Need to be bumped when we change the EnphasenapshotSerializer.
    """

    serializer_class: type[AmberDataSerializer] = EnphaseSnapshotSerializer

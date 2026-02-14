"""Share entities for resource sharing.

Represents sharing relationships between users and resources (experiments, synth_groups).
"""
import enum
from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4


class PermissionLevel(str, enum.Enum):
    """Permission level for shared resources."""

    VIEWER = "viewer"
    EDITOR = "editor"


@dataclass
class ExperimentShare:
    """Experiment sharing relationship.

    Attributes:
        id: Unique share identifier
        experiment_id: ID of shared experiment
        user_id: ID of user receiving access
        permission_level: Level of access (viewer/editor)
        granted_at: When access was granted
        granted_by_id: ID of user who granted access
    """

    experiment_id: str
    user_id: UUID
    permission_level: PermissionLevel
    granted_by_id: UUID
    id: UUID = field(default_factory=uuid4)
    granted_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def __post_init__(self):
        """Validate share data."""
        if not self.experiment_id or not self.experiment_id.strip():
            raise ValueError("experiment_id is required")

        if not isinstance(self.user_id, (UUID, str)):
            raise ValueError("user_id must be UUID or string")

        if not isinstance(self.granted_by_id, (UUID, str)):
            raise ValueError("granted_by_id must be UUID or string")

        # Convert to PermissionLevel enum if string
        if isinstance(self.permission_level, str):
            self.permission_level = PermissionLevel(self.permission_level)

        # Convert UUIDs to strings if needed
        if isinstance(self.id, UUID):
            self.id = str(self.id)
        if isinstance(self.user_id, UUID):
            self.user_id = str(self.user_id)
        if isinstance(self.granted_by_id, UUID):
            self.granted_by_id = str(self.granted_by_id)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "experiment_id": self.experiment_id,
            "user_id": str(self.user_id),
            "permission_level": self.permission_level.value,
            "granted_at": self.granted_at,
            "granted_by_id": str(self.granted_by_id),
        }


@dataclass
class SynthGroupShare:
    """Synth group sharing relationship.

    Attributes:
        id: Unique share identifier
        synth_group_id: ID of shared synth group
        user_id: ID of user receiving access
        permission_level: Level of access (viewer/editor)
        granted_at: When access was granted
        granted_by_id: ID of user who granted access
    """

    synth_group_id: str
    user_id: UUID
    permission_level: PermissionLevel
    granted_by_id: UUID
    id: UUID = field(default_factory=uuid4)
    granted_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def __post_init__(self):
        """Validate share data."""
        if not self.synth_group_id or not self.synth_group_id.strip():
            raise ValueError("synth_group_id is required")

        if not isinstance(self.user_id, (UUID, str)):
            raise ValueError("user_id must be UUID or string")

        if not isinstance(self.granted_by_id, (UUID, str)):
            raise ValueError("granted_by_id must be UUID or string")

        # Convert to PermissionLevel enum if string
        if isinstance(self.permission_level, str):
            self.permission_level = PermissionLevel(self.permission_level)

        # Convert UUIDs to strings if needed
        if isinstance(self.id, UUID):
            self.id = str(self.id)
        if isinstance(self.user_id, UUID):
            self.user_id = str(self.user_id)
        if isinstance(self.granted_by_id, UUID):
            self.granted_by_id = str(self.granted_by_id)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "synth_group_id": self.synth_group_id,
            "user_id": str(self.user_id),
            "permission_level": self.permission_level.value,
            "granted_at": self.granted_at,
            "granted_by_id": str(self.granted_by_id),
        }

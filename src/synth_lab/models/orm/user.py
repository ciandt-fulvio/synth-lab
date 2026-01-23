"""SQLAlchemy ORM model for users.

Maps to the 'users' table for authenticated users.

References:
    - SQLAlchemy 2.0 ORM: https://docs.sqlalchemy.org/en/20/orm/
"""
from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from synth_lab.models.orm.base import Base, TimestampMixin

if TYPE_CHECKING:
    from synth_lab.models.orm.experiment import Experiment
    from synth_lab.models.orm.synth import SynthGroup


class User(Base, TimestampMixin):
    """User model for authenticated users.

    Attributes:
        id: UUID of the user
        google_user_id: Google OAuth user ID
        email: User email address
        display_name: User display name
        profile_picture_url: URL to user's profile picture
        created_at: ISO timestamp of creation
        updated_at: ISO timestamp of last update

    Relationships:
        owned_experiments: Experiments owned by this user
        owned_synth_groups: Synth groups owned by this user
    """

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    google_user_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    profile_picture_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Relationships (to be filled by related models via back_populates)
    owned_experiments: Mapped[list["Experiment"]] = relationship(
        "Experiment",
        back_populates="owner",
        foreign_keys="[Experiment.owner_id]",
    )
    owned_synth_groups: Mapped[list["SynthGroup"]] = relationship(
        "SynthGroup",
        back_populates="owner",
        foreign_keys="[SynthGroup.owner_id]",
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id!r}, email={self.email!r})>"

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, UniqueConstraint
from datetime import datetime, timezone
from .db import Base

class Work(Base):
    __tablename__ = "works"

    id: Mapped[int] = mapped_column(primary_key=True)
    isbn13: Mapped[str] = mapped_column(unique=True)
    title: Mapped[str | None]
    description: Mapped[str | None]
    # which waterfall source supplied the metadata (e.g. "google_books",
    # "open_library+web_search") — reviewers weigh web_search lower
    metadata_source: Mapped[str | None]
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )
    runs: Mapped[list["Run"]] = relationship(back_populates="work", order_by='Run.id')

class Run(Base):
    __tablename__ = "runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    work_id: Mapped[int] = mapped_column(ForeignKey("works.id", ondelete="CASCADE"))
    status: Mapped[str] = mapped_column(default="queued")
    error: Mapped[str | None]
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )
    finished_at: Mapped[datetime | None]
    work: Mapped["Work"] = relationship(back_populates='runs')
    headings: Mapped[list["Heading"]] = relationship(back_populates='run', order_by="Heading.id")
    decisions: Mapped[list["ReviewDecision"]] = relationship(back_populates="run")

class Heading(Base):
    __tablename__ = "headings"

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("runs.id", ondelete="CASCADE"))
    proposed_label: Mapped[str]
    label: Mapped[str | None]
    fast_id: Mapped[str | None]
    facet: Mapped[str]
    tier: Mapped[str]
    source_model: Mapped[str] 
    position: Mapped[int]
    run: Mapped["Run"] = relationship(back_populates='headings')

class ReviewDecision(Base):
    __tablename__ = "review_decisions"
    __table_args__ = (UniqueConstraint("run_id", "fast_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("runs.id", ondelete="CASCADE"))
    fast_id: Mapped[str]
    decision: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )
    run: Mapped["Run"] = relationship(back_populates="decisions")
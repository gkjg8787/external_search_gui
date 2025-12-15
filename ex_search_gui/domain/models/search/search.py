import json

from sqlmodel import Field, Relationship
from sqlalchemy import Column, event
from sqlalchemy.orm import Mapper
from sqlalchemy.types import TypeDecorator, VARCHAR
from sqlalchemy.ext.mutable import MutableDict

from domain.models.base_model import SQLBase, SQLModel, datetime, timezone


class JSONEncodedDictNoEnsureAscii(TypeDecorator):
    """Represents an immutable structure as a json-encoded string.

    Usage:

        JSONEncodedDict(255)

    """

    impl = VARCHAR

    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = json.dumps(value, ensure_ascii=False)

        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = json.loads(value)
        return value


class SearchURLConfig(SQLBase, table=True):
    label_name: str = Field(index=True)
    base_url: str
    query: str
    query_encoding: str = Field(default="utf-8")
    download_type: str = Field(default="")
    download_config: dict = Field(
        default_factory=dict,
        sa_column=Column(MutableDict.as_mutable(JSONEncodedDictNoEnsureAscii())),
    )
    # Relationships
    groups_link: list["GroupLabelLink"] = Relationship(back_populates="label")


class GroupLabelLink(SQLModel, table=True):
    """Link Model / 中間テーブル for Group and SearchURLConfig."""

    group_id: int | None = Field(default=None, foreign_key="group.id", primary_key=True)
    label_id: int | None = Field(
        default=None, foreign_key="searchurlconfig.id", primary_key=True
    )
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Relationships for back-populating
    group: "Group" = Relationship(back_populates="labels_link")
    label: "SearchURLConfig" = Relationship(back_populates="groups_link")

    @event.listens_for(Mapper, "before_update")
    def receive_before_update(mapper, connection, target):
        target.updated_at = datetime.now(timezone.utc)


class Group(SQLBase, table=True):
    name: str = Field(index=True)

    # Relationships
    labels_link: list[GroupLabelLink] = Relationship(
        back_populates="group", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


class ProductPageConfig(SQLBase, table=True):
    label_name: str = Field(index=True)
    url_pattern: str
    pattern_type: str
    download_type: str = Field(default="")
    download_config: dict = Field(
        default_factory=dict,
        sa_column=Column(MutableDict.as_mutable(JSONEncodedDictNoEnsureAscii())),
    )

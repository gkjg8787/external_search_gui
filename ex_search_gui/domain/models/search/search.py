from typing import Optional

from sqlmodel import Field, Relationship
from sqlalchemy import JSON, Column
from sqlalchemy.ext.mutable import MutableDict

from domain.models.base_model import SQLBase


class SearchURLConfig(SQLBase, table=True):
    label_name: str = Field(index=True)
    base_url: str
    query: str
    query_encoding: str = Field(default="utf-8")
    download_type: str = Field(default="")
    download_config: dict = Field(
        default_factory=dict, sa_column=Column(MutableDict.as_mutable(JSON))
    )

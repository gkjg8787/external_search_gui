import json

from sqlmodel import Field, Relationship
from sqlalchemy import JSON, Column
from sqlalchemy.types import TypeDecorator, VARCHAR
from sqlalchemy.ext.mutable import MutableDict

from domain.models.base_model import SQLBase


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


class ProductPageConfig(SQLBase, table=True):
    label_name: str = Field(index=True)
    url_pattern: str
    pattern_type: str
    download_type: str = Field(default="")
    download_config: dict = Field(
        default_factory=dict,
        sa_column=Column(MutableDict.as_mutable(JSONEncodedDictNoEnsureAscii())),
    )

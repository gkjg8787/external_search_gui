from typing import Any, Optional, Literal
from urllib.parse import urlparse

from pydantic import BaseModel, Field, field_validator


class SearchURLConfigSchema(BaseModel):
    id: int | None = None
    label_name: str
    base_url: str
    query: str
    query_encoding: str = Field(default="utf-8")
    download_type: Literal["", "httpx", "selenium", "nodriver"] = Field(default="")
    download_config: dict = Field(default_factory=dict)

    @field_validator("query")
    @classmethod
    def validate_query(cls, v: any) -> str:
        if v is not None and isinstance(v, str):
            # ?と=を削除する処理
            v = v.replace("?", "").replace("=", "")
        return v

    @field_validator("base_url", mode="after")
    @classmethod
    def validate_base_url(cls, v: str) -> str:
        parsed_url = urlparse(v)
        if not parsed_url.netloc or parsed_url.scheme not in ["http", "https"]:
            ValueError(f"Invalid base_url: {v}")
        return v


class SearchLabelResponse(SearchURLConfigSchema):
    pass


class SearchURLConfigRequest(SearchURLConfigSchema):
    pass


class BasicResponse(BaseModel):
    success: bool
    messagage: str | None = None
    data: Optional[Any] = None


class SearchURLConfigResponse(BasicResponse):
    pass


class SearchURLConfigPreviewRequest(SearchURLConfigSchema):
    learning_url: str | None = Field(default=None)
    target_urls: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)


class SearchResult(BaseModel):
    title: str | None = None
    price: int | None = None
    taxin: bool = False
    condition: str | None = None
    on_sale: bool = False
    salename: str | None = None
    is_success: bool = False
    url: str | None = None
    sitename: str | None = None
    image_url: str | None = None
    stock_msg: str | None = None
    stock_quantity: int | None = None
    sub_urls: list[str] | None = Field(default=None)
    shops_with_stock: str | None = None
    others: dict | None = Field(default=None)


class SearchResults(BaseModel):
    results: list[SearchResult] = Field(default_factory=list)
    error_msg: str = Field(default="")


class SearchURLConfigPreviewResponse(BaseModel):
    results: dict[str, SearchResults] = Field(default_factory=dict)

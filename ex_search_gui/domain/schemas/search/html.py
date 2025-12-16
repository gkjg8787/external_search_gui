from fastapi import Form
from pydantic import BaseModel, Field
from .search import (
    SearchURLConfigSchema,
    SearchURLConfigPreviewRequest,
    ProductPageConfigPreviewRequest,
)
from typing import Annotated, Union


class SearchLabels(BaseModel):
    labels: list[SearchURLConfigSchema] = Field(default_factory=list)


class SearchLabelAddForm(BaseModel):
    label_name: Annotated[str, Form(...)]
    base_url: Annotated[str, Form(...)]
    query: Annotated[str, Form(...)]
    query_encoding: Annotated[str, Form("utf-8")]
    download_type: Annotated[str, Form("")]
    download_config: Annotated[str, Form("")]  # JSON文字列として扱う


class SearchLabelPreviewContext(BaseModel):
    preview: SearchURLConfigPreviewRequest
    is_edit_mode: bool = False


class ProductPageLabelPreviewContext(BaseModel):
    preview: ProductPageConfigPreviewRequest
    is_edit_mode: bool = False
    watch_url: str = ""

from fastapi import Form
from pydantic import BaseModel, Field
from .search import SearchURLConfigSchema, SearchURLConfigPreviewRequest
from typing import Annotated


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

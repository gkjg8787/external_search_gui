from pydantic import BaseModel


class SearchURLConfigCommand(BaseModel):
    id: int | None = None
    label_name: str | None = None
    base_url: str | None = None
    download_type: str | None = None


class ProductPageConfigCommand(BaseModel):
    id: int | None = None
    label_name: str | None = None
    url_pattern: str | None = None
    pattern_type: str | None = None
    download_type: str | None = None


class ProductPageURLPatternCommand(BaseModel):
    url: str

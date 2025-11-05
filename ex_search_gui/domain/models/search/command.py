from pydantic import BaseModel


class SearchURLConfigCommand(BaseModel):
    id: int | None = None
    label_name: str | None = None
    base_url: str | None = None
    download_type: str | None = None

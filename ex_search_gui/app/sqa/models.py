from pydantic import BaseModel, Field
from typing import Optional, Any


class ErrorDetail(BaseModel):
    error_msg: str = ""
    error_type: str = ""


class Cookie(BaseModel):
    cookie_dict_list: Optional[list[dict[str, Any]]] = None
    return_cookies: Optional[bool] = False
    save: Optional[bool] = False
    load: Optional[bool] = False
    filename: Optional[str] = None


class UserAgent(BaseModel):
    major: int = 141  # chrome major version
    platform: str = "Windows"  # e.g., "Windows", "macOS", "Linux"
    os_version: str = "10.0.0"


class ParameterDetail(BaseModel):
    position: str  # "path" or "query"
    key: str | None = None
    index: int | None = None
    consumed_segments: int = 1
    delimiter: str | None = None
    encoding: str = "utf-8"
    value_type: str  # "keyword" or "category"
    is_json: bool | None = None
    json_key_path: str | None = None


class URLAnalysisModel(BaseModel):
    base_url: str
    fixed_path: str
    structure_type: str
    url_template: str
    parameters: dict[str, ParameterDetail]


class SearchURLProbeRequest(BaseModel):
    url: str
    search_word: str | None = None
    cookie: Optional[Cookie] = None
    page_wait_time: Optional[float] = None
    useragent: UserAgent | None = UserAgent()


class OptionData(BaseModel):
    value: Optional[str] = Field(
        description="Value attribute of the option", max_length=200
    )
    text: str = Field(description="Text content of the option", max_length=200)


class SelectData(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    class_list: list[str] = Field(default_factory=list)
    options: list[OptionData] = Field(default_factory=list)
    visible: bool = True


class SearchURLProbeResponse(BaseModel):
    url_info: URLAnalysisModel | None = None
    categories: SelectData | None = None
    error: ErrorDetail | None = None


class GenerateSearchURLRequest(BaseModel):
    url_info: URLAnalysisModel
    search_keyword: str
    category_value: Optional[str] = None
    category_name: Optional[str] = None


class GenerateSearchURLResponse(BaseModel):
    url: str = Field(
        default="",
        description="Generated search URL based on the input parameters",
        max_length=500,
    )
    error: ErrorDetail | None = None


class GenerateSearchURLTemplateRequest(BaseModel):
    url_info: URLAnalysisModel
    search_keyword: str | None = None
    category_value: Optional[str] = None
    category_name: Optional[str] = None

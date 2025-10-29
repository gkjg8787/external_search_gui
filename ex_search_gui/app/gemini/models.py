from pydantic import BaseModel
from typing import Optional, Any


class Cookie(BaseModel):
    cookie_dict_list: Optional[list[dict[str, Any]]] = None
    return_cookies: Optional[bool] = False


class OnError(BaseModel):
    action_type: str = "raise"  # "raise" or "retry"
    max_retries: int | None = None
    wait_time: float | None = None
    check_exist_tag: str = ""  # CSS selector


class WaitCSSSelector(BaseModel):
    selector: str
    timeout: Optional[int] = 10  # seconds
    on_error: Optional[OnError] = OnError()
    pre_wait_time: Optional[float] = 0.0  # seconds


class NodriverOptions(BaseModel):
    cookie: Optional[Cookie] = None
    wait_css_selector: Optional[WaitCSSSelector] = None
    page_wait_time: Optional[float] = None


class GeminiWaitOptions(BaseModel):
    wait_css_selector: str = ""
    page_load_timeout: int | None = None
    tag_wait_timeout: int | None = None
    page_wait_time: float | None = None


class AskGeminiOptions(BaseModel, extra="ignore"):
    sitename: str = ""
    label: str = ""
    selenium: GeminiWaitOptions | None = None
    nodriver: NodriverOptions | None = None
    recreate_parser: bool = False
    exclude_script: bool = True
    compress_whitespace: bool = False

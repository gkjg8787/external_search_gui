from pydantic import BaseModel, Field
from typing import Optional, Any, Literal


class Cookie(BaseModel):
    cookie_dict_list: Optional[list[dict[str, Any]]] = None
    save: Optional[bool] = False
    load: Optional[bool] = False


class OnError(BaseModel):
    action_type: Literal["raise", "retry"] = "raise"
    max_retries: int | None = None
    wait_time: float | None = None
    check_exist_tag: str = ""  # CSS selector


class WaitCSSSelector(BaseModel):
    selector: str
    timeout: Optional[int] = 10  # seconds
    on_error: Optional[OnError] = OnError()
    pre_wait_time: Optional[float] = 0.0  # seconds


class Wait(BaseModel):
    time: int = 0  # seconds


class Scroll(BaseModel):
    to_bottom: bool = False
    amount: Optional[int] = None  # pixels
    pause_time: Optional[float] = 0.5  # seconds


class NodriverOptions(BaseModel):
    cookie: Optional[Cookie] = None
    wait_css_selector: Optional[WaitCSSSelector] = None
    page_wait_time: Optional[float] = None
    actions: list[Wait | Scroll] = Field(default_factory=list)
    useragent: dict | None = None


class SeleniumWaitOptions(BaseModel):
    cookie: Optional[Cookie] = None
    wait_css_selector: str = ""
    page_load_timeout: int | None = None
    tag_wait_timeout: int | None = None
    page_wait_time: float | None = None


class HttpxOptions(BaseModel):
    cookie: Optional[Cookie] = None


class PromptOptions(BaseModel):
    add_prompt: str = ""


class AskGeminiOptions(BaseModel, extra="ignore"):
    sitename: str = ""
    label: str = ""
    selenium: SeleniumWaitOptions | None = None
    nodriver: NodriverOptions | None = None
    httpx: HttpxOptions | None = None
    recreate_parser: bool = False
    exclude_script: bool = True
    compress_whitespace: bool = False
    prompt: PromptOptions | None = None

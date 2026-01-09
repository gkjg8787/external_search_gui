from pydantic import BaseModel

from app.gemini.models import (
    AskGeminiOptions,
    SeleniumWaitOptions,
    NodriverOptions,
    Cookie,
    WaitCSSSelector,
    OnError,
    PromptOptions,
    HttpxOptions,
)


class SearchLabelDownLoadConfigTemplateService:
    option_type: str

    def __init__(self, option_type: str):
        self.option_type = option_type

    async def execute(self):
        response = AskGeminiOptions(
            sitename="sitename",
            label="labelname",
            recreate_parser=False,
            exclude_script=True,
            compress_whitespace=True,
            prompt=PromptOptions(add_prompt=""),
        )
        example_cookie = Cookie(
            cookie_dict_list=[
                {
                    "name": "cookie_name",
                    "value": "cookie_value",
                    "domain": "www.example.com",
                    "path": "/",
                }
            ],
            save=True,
            load=True,
        )
        match self.option_type:
            case "nodriver":
                response.nodriver = NodriverOptions(
                    cookie=example_cookie,
                    wait_css_selector=WaitCSSSelector(
                        selector="body",
                        timeout=10,
                        on_error=OnError(
                            action_type="retry",
                            max_retries=3,
                            wait_time=2.0,
                            check_exist_tag=".example-selector",
                        ),
                        pre_wait_time=0.0,
                    ),
                    page_wait_time=5.0,
                )
            case "selenium":
                response.selenium = SeleniumWaitOptions(
                    cookie=example_cookie,
                    wait_css_selector=".example-selector",
                    page_load_timeout=30,
                    tag_wait_timeout=15,
                    page_wait_time=5.0,
                )
            case "httpx":
                response.httpx = HttpxOptions(cookie=example_cookie)
        return response

from pydantic import BaseModel

from app.gemini.models import (
    AskGeminiOptions,
    GeminiWaitOptions,
    NodriverOptions,
    Cookie,
    WaitCSSSelector,
    OnError,
    PromptOptions,
)


class SearchLabelDownLoadConfigTemplateService:
    option_type: str

    def __init__(self, option_type: str):
        self.option_type = option_type

    async def execute(self):
        response = AskGeminiOptions(
            sitename="example_site",
            label="example_label",
            recreate_parser=False,
            exclude_script=True,
            compress_whitespace=True,
            prompt=PromptOptions(add_prompt=""),
        )
        match self.option_type:
            case "nodriver":
                response.nodriver = NodriverOptions(
                    cookie=Cookie(
                        cookie_dict_list=[{"example_cookie": "example_value"}],
                        save=True,
                        load=True,
                    ),
                    wait_css_selector=WaitCSSSelector(
                        selector="body",
                        timeout=10,
                        on_error=OnError(
                            action_type="retry",
                            max_retries=3,
                            wait_time=2.0,
                            check_exist_tag=".example-error",
                        ),
                        pre_wait_time=0.0,
                    ),
                    page_wait_time=5.0,
                )
            case "selenium":
                response.selenium = GeminiWaitOptions(
                    wait_css_selector=".example-selector",
                    page_load_timeout=30,
                    tag_wait_timeout=15,
                    page_wait_time=5.0,
                )
        return response

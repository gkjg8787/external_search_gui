from urllib.parse import urlparse, quote

from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.sqa.client import probe_url
from app.search.search_api import generate_download_config_via_api
from domain.schemas.search import (
    DownloadConfigGenerateRequest,
    DownloadConfigGenerateResponse,
)
from domain.models.search import search as search_model
from app.sqa.models import SearchURLProbeResponse
from app.sqa import client as sqa_client

log = structlog.get_logger(__name__)


async def create_labels(
    ses: AsyncSession, url: str, search_keyword: str = "", no_useragent: bool = False
) -> list[search_model.SearchURLConfig]:
    """
    渡されたURLを解析し、検索ラベル設定を作成する

    Args:
        ses: DBセッション
        url: 解析対象のURL
        search_keyword: download_configを自動作成する場合の検索キーワード

    Returns:
        作成されたSearchURLConfigのリスト

    Raises:
        ValueError: URLの解析に失敗した場合
        TypeError: 予期しないレスポンスタイプの場合
    """
    # 1. 渡されたURLから解析結果を取得
    ok, probe_result = await probe_url(
        url=url, search_keyword=search_keyword, no_useragent=no_useragent
    )
    if not ok:
        raise ValueError(f"Failed to probe URL: {probe_result}")
    if not isinstance(probe_result, SearchURLProbeResponse):
        raise TypeError(
            f"Unexpected response type from probe_url: {type(probe_result)}"
        )

    # 2. URL解析結果のurl_templateに{keyword}がなければ解析失敗
    if (
        not probe_result.url_info
        or "{keyword}" not in probe_result.url_info.url_template
    ):
        raise ValueError(
            "URL analysis failed: '{keyword}' placeholder not found in url_template."
        )

    url_info = probe_result.url_info

    # 3. カテゴリ処理
    url_templates_with_category: list[tuple[str, str | None]] = []
    if probe_result.categories and "{category}" in url_info.url_template:
        for option in probe_result.categories.options:
            if option.value:
                ok, temp_res = await sqa_client.generate_url_template(
                    url_info=url_info,
                    category_value=option.value,
                    category_name=option.text,
                )
                if ok and temp_res.url:
                    url_templates_with_category.append((temp_res.url, option.text))
                else:
                    if isinstance(temp_res, str):
                        error = temp_res
                    else:
                        error = temp_res.model_dump()
                    log.warning(
                        "Failed to generate URL template with category.",
                        error=error,
                    )
    else:
        url_templates_with_category.append((url_info.url_template, None))

    # 4. search_keywordがある場合、download_configを作成
    generated_dl_type = None
    generated_dl_config = None
    if search_keyword and url_templates_with_category:
        template_for_dl_config, _ = url_templates_with_category[0]

        keyword_param = next(
            (p for p in url_info.parameters.values() if p.value_type == "keyword"), None
        )
        encoding = keyword_param.encoding if keyword_param else "utf-8"

        # URL エンコードを適用
        encoded_keyword = quote(search_keyword, encoding=encoding)
        test_url = template_for_dl_config.replace("{keyword}", encoded_keyword)
        dl_req = DownloadConfigGenerateRequest(
            url=test_url, search_keyword=search_keyword
        )
        ok, dl_result = await generate_download_config_via_api(ses, dl_req)
        if ok and isinstance(dl_result, DownloadConfigGenerateResponse):
            generated_dl_type = dl_result.download_type
            generated_dl_config = dl_result.download_config
            log.info(
                "Successfully generated download_config.", config=generated_dl_config
            )
        else:
            log.warning(
                "Failed to generate download_config, falling back to default.",
                error=dl_result,
            )

    # 5. ラベル作成
    created_labels = []
    domain = urlparse(url_info.base_url).netloc
    keyword_param = url_info.parameters.get("keyword")
    query_encoding = (
        keyword_param.encoding if keyword_param and keyword_param.encoding else "utf-8"
    )

    for url_template, category_name in url_templates_with_category:
        label_name = f"{domain}_{category_name}" if category_name else domain

        download_type = generated_dl_type if generated_dl_config else "httpx"
        download_config = generated_dl_config or {
            "label": f"{domain}_search",
            "sitename": domain,
        }

        new_label = search_model.SearchURLConfig(
            label_name=label_name,
            base_url=url_template,
            query="",
            query_encoding=query_encoding,
            download_type=download_type,
            download_config=download_config,
        )
        created_labels.append(new_label)

    return created_labels

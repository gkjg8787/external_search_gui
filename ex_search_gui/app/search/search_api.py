from urllib.parse import urlparse, quote
import copy

from sqlalchemy.ext.asyncio import AsyncSession

from domain.schemas import search as search_schema
from app.gemini.web_scraper import download_with_api, search_model


async def generate_target_urls(
    base_url: str, query_pattern: str, keywords: list[str], encoding: str
) -> list[str]:
    target_urls = []
    parsed_url = urlparse(base_url)
    if not encoding:
        encoding = "utf-8"
    for keyword in keywords:
        if not keyword or not query_pattern:
            continue
        encoded_keyword = f"{query_pattern}={quote(keyword, encoding=encoding)}"
        if parsed_url.query:
            encoded_keyword = f"{parsed_url.query}&{encoded_keyword}"
        url = parsed_url._replace(query=encoded_keyword).geturl()
        target_urls.append(url)
    return target_urls


async def search_via_api_for_preview(
    ses: AsyncSession, searchreq: search_schema.SearchURLConfigPreviewRequest
):
    results_dict: dict[str, search_schema.SearchResults] = {}
    target_urls = []
    no_recreate_config = None

    if (
        "recreate_parser" in searchreq.download_config
        and searchreq.download_config["recreate_parser"] is True
    ):
        no_recreate_config = copy.deepcopy(searchreq.download_config)
        no_recreate_config["recreate_parser"] = False

    if searchreq.learning_url:
        target_urls.append(searchreq.learning_url)

    if searchreq.target_urls:
        target_urls.extend(searchreq.target_urls)

    if searchreq.keywords:
        target_urls.extend(
            await generate_target_urls(
                base_url=searchreq.base_url,
                query_pattern=searchreq.query,
                keywords=searchreq.keywords,
                encoding=searchreq.query_encoding,
            )
        )

    count = 0
    for url in target_urls:
        if results_dict.get(url):
            continue
        if no_recreate_config and count > 0:
            options = no_recreate_config
        else:
            options = searchreq.download_config
        searchreq_model = search_model.SearchRequest(
            url=url,
            sitename="gemini",
            options=options,
        )
        ok, result = await download_with_api(ses, searchreq_model)
        count += 1
        if not ok:
            if isinstance(result, str):
                results_dict[url] = search_schema.SearchResults(error_msg=result)
                continue
        if not isinstance(result, search_schema.SearchResults):
            results_dict[url] = search_schema.SearchResults(
                error_msg=f"type is not SearchResult, type:{type(result)}, value:{result}",
            )
            continue
        results_dict[url] = result

    return search_schema.SearchURLConfigPreviewResponse(results=results_dict)


async def get_product_via_api_for_preview(
    ses: AsyncSession, productreq: search_schema.ProductPageConfigPreviewRequest
):
    results_dict: dict[str, search_schema.SearchResults] = {}
    target_urls = []
    no_recreate_config = None

    if (
        "recreate_parser" in productreq.download_config
        and productreq.download_config["recreate_parser"] is True
    ):
        no_recreate_config = copy.deepcopy(productreq.download_config)
        no_recreate_config["recreate_parser"] = False

    if productreq.learning_url:
        target_urls.append(productreq.learning_url)

    if productreq.target_urls:
        target_urls.extend(productreq.target_urls)

    count = 0
    for url in target_urls:
        if results_dict.get(url):
            continue
        if no_recreate_config and count > 0:
            options = no_recreate_config
        else:
            options = productreq.download_config
        searchreq_model = search_model.SearchRequest(
            url=url,
            sitename="gemini",
            options=options,
        )
        ok, result = await download_with_api(ses, searchreq_model)
        count += 1
        if not ok:
            if isinstance(result, str):
                results_dict[url] = search_schema.SearchResults(error_msg=result)
                continue
        if not isinstance(result, search_schema.SearchResults):
            results_dict[url] = search_schema.SearchResults(
                error_msg=f"type is not SearchResult, type:{type(result)}, value:{result}",
            )
            continue
        results_dict[url] = result

    return search_schema.ProductPageConfigPreviewResponse(results=results_dict)

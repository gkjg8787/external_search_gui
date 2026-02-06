from sqlalchemy.ext.asyncio import AsyncSession


from . import convert
from app.getdata.models import (
    search as search_model,
    downloadconfig as downloadconfig_model,
)
from app.getdata import get_search, generate_download_config
from domain.schemas import search as search_schema


async def download_with_api(ses: AsyncSession, searchreq: search_model.SearchRequest):
    if not searchreq.url:
        return False, f"url is required."
    ok, result = await get_search(searchreq=searchreq)
    if not ok:
        return ok, result
    if not isinstance(result, search_model.SearchResults):
        return False, f"type is not SearchResults, type:{type(result)}, value:{result}"
    schema_result = convert.ModelConvert.searchresult_to_schema(results=result)
    return ok, schema_result


async def generate_download_config_with_api(
    downloadconfigreq: downloadconfig_model.DownloadConfigGenerateRequest,
) -> tuple[bool, search_schema.DownloadConfigGenerateResponse | str]:
    if not downloadconfigreq.url:
        return False, "url is required."
    ok, result = await generate_download_config(
        sitename="gemini",
        url=downloadconfigreq.url,
        search_keyword=downloadconfigreq.search_keyword,
        timeout=downloadconfigreq.timeout,
        optimize=downloadconfigreq.optimize,
        init_nodriver_page_wait_time=downloadconfigreq.init_nodriver_page_wait_time,
    )
    if not ok:
        return ok, result
    if not isinstance(result, downloadconfig_model.DownloadConfigGenerateResponse):
        return (
            False,
            f"type is not DownloadConfigGenerateResponse, type:{type(result)}, value:{result}",
        )
    schema_result = convert.ModelConvert.downloadconfiggenerate_response_to_schema(
        result=result
    )
    return ok, schema_result

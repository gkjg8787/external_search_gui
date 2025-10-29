from urllib.parse import urlparse

from sqlalchemy.ext.asyncio import AsyncSession


from . import convert
from app.getdata.models import search as search_model
from app.getdata import get_search


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

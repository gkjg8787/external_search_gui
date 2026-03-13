from urllib.parse import urljoin

import httpx


from common.read_config import get_api_options
from .models import (
    SearchURLProbeRequest,
    SearchURLProbeResponse,
    GenerateSearchURLRequest,
    GenerateSearchURLResponse,
    URLAnalysisModel,
)


API_OPTIONS = {
    "probe": {"path": "/searchurl/probe", "method": "post"},
    "generate": {"path": "/searchurl/generate", "method": "post"},
}


async def _get_api_result(url: str, method: str, timeout: float, data: dict):
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            match method.lower():
                case "post":
                    res = await client.post(url, json=data)
                case _:
                    raise ValueError(f"no support method, {method.lower()}")
            res.raise_for_status()
        except Exception as e:
            return False, f"failed to api, type:{type(e).__name__}, {e}", None
    res_json = res.json()
    if not isinstance(res_json, dict):
        return False, f"invalid type response, type:{type(res_json)}, {res_json}", None
    return True, "", res_json


async def probe_url(url: str, search_keyword: str = "", no_useragent=False):
    opts = get_api_options()
    api_url = urljoin(opts.url_analysis.url, API_OPTIONS["probe"]["path"])
    timeout = opts.url_analysis.timeout
    method = API_OPTIONS["probe"]["method"]
    data_model = SearchURLProbeRequest(url=url, search_word=search_keyword)
    if no_useragent:
        data_model.useragent = None
    data = data_model.model_dump(mode="json", exclude_unset=True)

    ok, msg, result = await _get_api_result(
        url=api_url, method=method, timeout=timeout, data=data
    )
    if not ok:
        return ok, msg
    res_model = SearchURLProbeResponse(**result)
    return True, res_model


async def generate_url(
    url_info: URLAnalysisModel,
    search_keyword: str,
    category_value: str,
    category_name: str = "",
):
    opts = get_api_options()
    api_url = urljoin(opts.url_generate.url, API_OPTIONS["generate"]["path"])
    timeout = opts.url_generate.timeout
    method = API_OPTIONS["generate"]["method"]
    data = GenerateSearchURLRequest(
        url_info=url_info,
        search_keyword=search_keyword,
        category_value=category_value,
        category_name=category_name,
    ).model_dump(mode="json", exclude_unset=True)

    ok, msg, result = await _get_api_result(
        url=api_url, method=method, timeout=timeout, data=data
    )
    if not ok:
        return ok, msg
    res_model = GenerateSearchURLResponse(**result)
    return True, res_model

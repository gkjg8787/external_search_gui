import httpx

from common import read_config
from .factory import APIPathOptionFactory
from .enums import APIURLName
from .util import create_api_url
from .models.info import InfoRequest, InfoResponse
from .models.search import SearchRequest, SearchResponse
from .models.error import ErrorMsg


async def _get_search_result(apiurlname: APIURLName, data: dict, timeout: float):
    apiopt = APIPathOptionFactory().create(apiurlname=apiurlname)
    api_url = create_api_url(apiopt=apiopt)
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            match apiopt.method.lower():
                case "post":
                    res = await client.post(api_url, json=data)
                case _:
                    raise ValueError(f"no support method, {apiopt.method.lower()}")
            res.raise_for_status()
        except Exception as e:
            return False, f"failed to api, type:{type(e).__name__}, {e}", None
    res_json = res.json()
    if not isinstance(res_json, dict):
        return False, f"invalid type response, type:{type(res_json)}, {res_json}", None
    return True, "", res_json


async def _convert_to_response_model(data: dict, class_type: type):
    try:
        result = class_type(**data)
    except Exception as e:
        try:
            result = ErrorMsg(**data)
            return False, result
        except Exception as e2:
            return False, f"failed convert response to class : {data}"
    return True, result


async def _get_request_timeout(sitename: str, top_key: str = "get_data") -> float:
    get_data_opt = read_config.get_api_options().model_dump()[top_key]
    if get_data_opt.get(sitename) and get_data_opt[sitename].get("timeout"):
        return get_data_opt[sitename]["timeout"]
    return get_data_opt["timeout"]


async def get_search_info(inforeq: InfoRequest):
    ok, msg, result = await _get_search_result(
        apiurlname=APIURLName.SEARCH_INFO,
        data=inforeq.model_dump(mode="json"),
        timeout=read_config.get_api_options().get_data.timeout,
    )
    if not ok:
        return ok, msg
    convert_ok, convert_result = await _convert_to_response_model(
        data=result, class_type=InfoResponse
    )
    if not convert_ok:
        if isinstance(convert_result, str):
            return False, convert_result
        if isinstance(convert_result, ErrorMsg):
            return False, convert_result.detail
        return False, convert_result
    if not isinstance(convert_result, InfoResponse):
        return False, convert_result
    if convert_result.error_msg:
        return False, convert_result.error_msg
    return True, convert_result


async def get_search(searchreq: SearchRequest):
    ok, msg, result = await _get_search_result(
        apiurlname=APIURLName.SEARCH,
        data=searchreq.model_dump(mode="json"),
        timeout=await _get_request_timeout(sitename=searchreq.sitename),
    )
    if not ok:
        return ok, msg
    convert_ok, convert_result = await _convert_to_response_model(
        data=result, class_type=SearchResponse
    )
    if not convert_ok:
        if isinstance(convert_result, str):
            return False, convert_result
        if isinstance(convert_result, ErrorMsg):
            return False, convert_result.detail
        return False, convert_result
    if not isinstance(convert_result, SearchResponse):
        return False, convert_result
    if convert_result.error_msg:
        return False, convert_result.error_msg
    return True, convert_result

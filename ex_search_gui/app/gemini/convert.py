from domain.schemas import search as search_schema
from app.getdata.models import (
    search as search_model,
    downloadconfig as downloadconfig_model,
)


class ModelConvert:
    @classmethod
    def searchresult_to_schema(
        cls, results: search_model.SearchResults
    ) -> search_schema.SearchResults:
        return search_schema.SearchResults(**results.model_dump())

    @classmethod
    def downloadconfiggenerate_response_to_schema(
        cls, result: downloadconfig_model.DownloadConfigGenerateResponse
    ) -> search_schema.DownloadConfigGenerateResponse:
        if result.download_config.get("nodriver"):
            download_type = "nodriver"
        elif result.download_config.get("selenium"):
            download_type = "selenium"
        elif result.download_config.get("httpx"):
            download_type = "httpx"
        else:
            download_type = ""
        response = search_schema.DownloadConfigGenerateResponse(
            download_config=result.download_config, download_type=download_type
        )
        return response

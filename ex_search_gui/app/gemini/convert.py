from domain.schemas import search as search_schema
from app.getdata.models import search as search_model


class ModelConvert:
    @classmethod
    def searchresult_to_schema(
        cls, results: search_model.SearchResults
    ) -> search_schema.SearchResults:
        return search_schema.SearchResults(**results.model_dump())

from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from databases.sql.search import repository as search_repository
from domain.models.search import command as search_command
from domain.schemas.search.html import SearchLabels
from domain.schemas.search.search import SearchURLConfigSchema


class SearchLabelViewTemplageService:
    def __init__(self, db_session: AsyncSession, label: str | None = None):
        self.db_session = db_session
        self.label = label

    async def execute(self, label: str | None = None) -> SearchLabels:
        repo = search_repository.SearchURLConfigRepositorySQL(self.db_session)
        command = search_command.SearchURLConfigCommand(label_name=label)
        labels = await repo.get_all(command)
        return SearchLabels(
            labels=[
                SearchURLConfigSchema(
                    id=db_label.id,
                    label_name=db_label.label_name,
                    base_url=db_label.base_url,
                    query=db_label.query,
                    query_encoding=db_label.query_encoding,
                    download_type=db_label.download_type,
                    download_config=db_label.download_config,
                )
                for db_label in labels
            ]
        )

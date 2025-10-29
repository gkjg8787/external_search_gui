from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from domain.models.search import (
    search as m_search,
    command as search_command,
    repository as search_repo,
)


class SearchURLConfigRepositorySQL(search_repo.SearchURLConfigRepository):
    session: AsyncSession

    def __init__(self, ses: AsyncSession):
        self.session = ses

    async def save_all(self, configs: list[m_search.SearchURLConfig]):
        ses = self.session
        for config in configs:
            if not config.id:
                ses.add(config)
                await ses.flush()
                continue
            db_config: m_search.SearchURLConfig = await ses.get(
                m_search.SearchURLConfig, config.id
            )
            if not db_config:
                raise ValueError(f"not found config.id ,{db_config.id}")
            db_config.label_name = config.label_name
            db_config.base_url = config.base_url
            db_config.query = config.query
            db_config.query_encoding = config.query_encoding
            db_config.download_type = config.download_type
            db_config.download_config = config.download_config
            continue
        await ses.commit()
        for config in configs:
            await ses.refresh(config)
        return

    async def get_all(
        self, command: search_command.SearchURLConfigCommand
    ) -> list[m_search.SearchURLConfig]:
        stmt = select(m_search.SearchURLConfig)
        if command.label_name:
            stmt = stmt.where(m_search.SearchURLConfig.label_name == command.label_name)
        if command.base_url:
            stmt = stmt.where(m_search.SearchURLConfig.base_url == command.base_url)
        if command.download_type:
            stmt = stmt.where(
                m_search.SearchURLConfig.download_type == command.download_type
            )
        result = await self.session.execute(stmt)
        return result.scalars().all()

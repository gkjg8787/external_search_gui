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
        saved_configs = []
        for config in configs:
            if not config.id:
                ses.add(config)
                saved_configs.append(config)
                continue
            db_config: m_search.SearchURLConfig = await ses.get(
                m_search.SearchURLConfig, config.id
            )
            if not db_config:
                raise ValueError(f"not found config.id ,{config.id}")
            db_config.label_name = config.label_name
            db_config.base_url = config.base_url
            db_config.query = config.query
            db_config.query_encoding = config.query_encoding
            db_config.download_type = config.download_type
            db_config.download_config = config.download_config
            saved_configs.append(db_config)
        await ses.commit()
        for saved_config in saved_configs:
            await ses.refresh(saved_config)

    async def get_all(
        self, command: search_command.SearchURLConfigCommand
    ) -> list[m_search.SearchURLConfig]:
        stmt = select(m_search.SearchURLConfig)
        if command.label_name:
            stmt = stmt.where(
                m_search.SearchURLConfig.label_name.icontains(command.label_name)
            )
        if command.base_url:
            stmt = stmt.where(
                m_search.SearchURLConfig.base_url.icontains(command.base_url)
            )
        if command.download_type:
            stmt = stmt.where(
                m_search.SearchURLConfig.download_type == command.download_type
            )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def delete_by_id(self, id: int):
        ses = self.session
        db_config: m_search.SearchURLConfig = await ses.get(
            m_search.SearchURLConfig, id
        )
        if not db_config:
            raise ValueError(f"not found config.id ,{id}")
        await ses.delete(db_config)
        await ses.commit()
        return

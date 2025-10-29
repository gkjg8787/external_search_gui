from abc import ABC, abstractmethod
from .search import SearchURLConfig
from .command import SearchURLConfigCommand


class SearchURLConfigRepository(ABC):
    @abstractmethod
    async def save_all(self, configs: list[SearchURLConfig]):
        pass

    @abstractmethod
    async def get_all(self, command: SearchURLConfigCommand) -> list[SearchURLConfig]:
        pass

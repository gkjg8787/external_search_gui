from abc import ABC, abstractmethod
from .search import SearchURLConfig, ProductPageConfig
from .command import (
    SearchURLConfigCommand,
    ProductPageConfigCommand,
    ProductPageURLPatternCommand,
)


class SearchURLConfigRepository(ABC):
    @abstractmethod
    async def save_all(self, configs: list[SearchURLConfig]):
        pass

    @abstractmethod
    async def get_all(self, command: SearchURLConfigCommand) -> list[SearchURLConfig]:
        pass

    @abstractmethod
    async def delete_by_id(self, id: int):
        pass


class ProductPageConfigRepository(ABC):
    @abstractmethod
    async def save_all(self, configs: list[ProductPageConfig]):
        pass

    @abstractmethod
    async def get_all(
        self, command: ProductPageConfigCommand
    ) -> list[ProductPageConfig]:
        pass

    @abstractmethod
    async def delete_by_id(self, id: int):
        pass


class ProductPageURLPatternRepository(ABC):
    @abstractmethod
    async def find_best_match(self, command: ProductPageURLPatternCommand) -> str:
        pass

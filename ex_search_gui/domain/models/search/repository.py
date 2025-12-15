from abc import ABC, abstractmethod
from typing import List, Optional
from .search import SearchURLConfig, ProductPageConfig, Group, GroupLabelLink
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


class GroupRepository(ABC):
    @abstractmethod
    async def create_group(self, group: Group) -> Group:
        pass

    @abstractmethod
    async def get_group_by_id(self, group_id: int) -> Optional[Group]:
        pass

    @abstractmethod
    async def get_all_groups(self) -> List[Group]:
        pass

    @abstractmethod
    async def update_group_name(self, group_id: int, new_name: str) -> Optional[Group]:
        pass

    @abstractmethod
    async def delete_group(self, group_id: int) -> bool:
        pass

    @abstractmethod
    async def add_label_to_group(
        self, group_id: int, label_id: int
    ) -> Optional[GroupLabelLink]:
        pass

    @abstractmethod
    async def remove_label_from_group(self, group_id: int, label_id: int) -> bool:
        pass

    @abstractmethod
    async def get_labels_for_group(self, group_id: int) -> List[SearchURLConfig]:
        pass

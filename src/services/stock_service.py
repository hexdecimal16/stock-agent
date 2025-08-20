from abc import ABC, abstractmethod
from typing import List
from models.stock import Stock

class StockService(ABC):
    @abstractmethod
    def find_matches(self, query: str, limit: int = 5) -> List[Stock]:
        pass

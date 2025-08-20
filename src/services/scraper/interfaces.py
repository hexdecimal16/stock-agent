from abc import ABC, abstractmethod
from typing import List, Any


class ScraperInterface(ABC):
    """Interface for a web scraper."""

    @abstractmethod
    def scrape(self) -> List[List[Any]]:
        """Scrape data and return it as a list of lists."""
        pass


class DataWriterInterface(ABC):
    """Interface for a data writer."""

    @abstractmethod
    def write_data(self, data: List[List[Any]], output_filename: str):
        """Write data to a specified output."""
        pass

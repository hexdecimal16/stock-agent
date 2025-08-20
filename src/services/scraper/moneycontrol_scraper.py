import logging
import requests
from bs4 import BeautifulSoup, Tag
from urllib.parse import urljoin
from typing import List, Any
from .interfaces import ScraperInterface
from fake_useragent import UserAgent

logger = logging.getLogger(__name__)


class MoneyControlScraper(ScraperInterface):
    """A class to scrape stock data tables from Moneycontrol."""

    DEFAULT_URL = "https://www.moneycontrol.com/markets/indian-indices/changeTableData?deviceType=web&exName=N&indicesID=136&selTab=o&subTabOT=o&subTabOPL=cl&selPage=marketTerminal&classic=true"

    def __init__(self, url: str = ""):
        """Initialize the scraper with a target URL."""
        self.url = url or self.DEFAULT_URL
        ua = UserAgent()
        self.headers = {
            "User-Agent": ua.random,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Referer": "https://www.moneycontrol.com/markets/indian-indices/",
        }

    def scrape(self) -> List[List[Any]]:
        """Scrape the table and return it as a list of lists."""
        try:
            logger.info("Fetching data from %s...", self.url)
            response = requests.get(self.url, headers=self.headers)
            response.raise_for_status()
            logger.info("Data fetched successfully.")

            soup = BeautifulSoup(response.content, "html.parser")
            table = soup.find("table")

            if not isinstance(table, Tag):
                logger.error("Could not find the data table on the page.")
                return []

            header_row = [th.get_text(strip=True) for th in table.find_all("th")]
            header_row.append("URL")

            data = [header_row]

            tbody = table.find("tbody")
            if isinstance(tbody, Tag):
                for row in tbody.find_all("tr"):
                    if not isinstance(row, Tag):
                        continue
                    cells = row.find_all("td")
                    if not cells:
                        continue

                    first_cell = cells[0]
                    link_tag = first_cell.find("a") if isinstance(first_cell, Tag) else None

                    stock_name = (
                        link_tag.get_text(strip=True)
                        if isinstance(link_tag, Tag)
                        else first_cell.get_text(strip=True)
                    )

                    relative_url = link_tag.get("href", "") if isinstance(link_tag, Tag) else ""
                    absolute_url = (
                        urljoin(self.url, str(relative_url)) if relative_url else ""
                    )

                    other_cells_data = [
                        cell.get_text(strip=True) for cell in cells[1:]
                    ]

                    csv_row_data = [stock_name] + other_cells_data + [absolute_url]
                    data.append(csv_row_data)
            
            return data

        except requests.exceptions.RequestException as e:
            logger.error("An error occurred while fetching the URL: %s", e)
            raise
        except Exception as e:
            logger.error("An unexpected error occurred: %s", e)
            raise
            
        return []

import requests
from bs4 import BeautifulSoup
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode, BrowserConfig
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from crawl4ai.content_filter_strategy import PruningContentFilter
from abc import ABC, abstractmethod

from abc import ABC, abstractmethod

class Scraper(ABC):
    @abstractmethod
    def scrape(self) -> str:
        pass

class AsyncScraper(ABC):
    @abstractmethod
    async def scrape(self) -> str:
        pass

class CompanyScraper(AsyncScraper):
    def __init__(self, url: str):
        self.url = url
        self.browserConfig = BrowserConfig(headless=True)
        self.crawler_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            excluded_tags=["nav", "footer", "aside"],
            remove_overlay_elements=True,
            markdown_generator=DefaultMarkdownGenerator(
                content_filter=PruningContentFilter(
                    threshold=0.48, threshold_type="fixed", min_word_threshold=0
                ),
                options={"ignore_links": True},
            ),
        )

    async def scrape(self) -> str:
        async with AsyncWebCrawler(config=self.browserConfig) as crawler:
            result = await crawler.arun(url=self.url, config=self.crawler_config)
            return result.markdown # type: ignore


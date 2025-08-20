from .interfaces import ScraperInterface, DataWriterInterface
import logging

logger = logging.getLogger(__name__)


class ScrapingService:
    """A service to orchestrate scraping and data writing."""

    def __init__(
        self, scraper: ScraperInterface, data_writer: DataWriterInterface
    ):
        """Initialize the service with a scraper and a data writer."""
        self.scraper = scraper
        self.data_writer = data_writer

    def run(self, output_filename: str):
        """Run the scraping and writing process."""
        try:
            logger.info("Scraping service started.")
            data = self.scraper.scrape()
            if data:
                self.data_writer.write_data(data, output_filename)
                logger.info("Scraping service finished successfully.")
            else:
                logger.warning("No data was scraped.")
        except Exception as e:
            logger.error("An error occurred in the scraping service: %s", e)
            raise


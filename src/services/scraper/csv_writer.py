import csv
import logging
from typing import List, Any
from .interfaces import DataWriterInterface

logger = logging.getLogger(__name__)


class CsvDataWriter(DataWriterInterface):
    """A class to write data to a CSV file."""

    def write_data(self, data: List[List[Any]], output_filename: str):
        """Write data to a CSV file."""
        if not data:
            logger.warning("No data provided to write.")
            return

        try:
            with open(output_filename, "w", newline="", encoding="utf-8") as csvfile:
                csv_writer = csv.writer(csvfile)
                csv_writer.writerows(data)
            logger.info("Successfully wrote data to '%s'.", output_filename)
        except IOError as e:
            logger.error("An error occurred while writing to the file: %s", e)
            raise

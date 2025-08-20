import os
import csv
import logging
from typing import Dict, List, Optional
from models.trie import Trie
from models.stock import Stock
from services.stock_service import StockService
from langgraph.checkpoint.base import BaseCheckpointSaver, Checkpoint
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class StockServiceImpl(StockService):
    def __init__(self, assets_dir: str, csv_name: str = "moneycontrol_stocks.csv"):
        self.assets_dir = assets_dir
        self.csv_path = os.path.join(self.assets_dir, csv_name)
        self.stocks: Dict[str, Dict[str, str]] = {}
        self.trie = Trie()
        self.last_boot_time = None

    def boot(self, checkpointer: Optional[BaseCheckpointSaver] = None):
        if not os.path.exists(self.csv_path):
            logger.warning(
                "CSV file not found at %s. The agent may not have stock data. You can try running the 'update_stock_data' command.",
                self.csv_path,
            )
            return
        self._load_csv()

    def _load_csv(self):
        self.stocks = {}
        try:
            with open(self.csv_path, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    clean_row = {
                        k.strip(): (v.strip() if isinstance(v, str) else v)
                        for k, v in row.items()
                    }
                    name = clean_row.get("Name", "").strip().lower()
                    if name:
                        self.trie.insert(name)
                        logger.debug("Inserted '%s' into Trie.", name)
                        self.stocks[name] = clean_row
        except FileNotFoundError:
            logger.warning(
                "CSV file not found when trying to load. Have you run boot()?"
            )
        except Exception as e:
            logger.exception("Failed to read CSV: %s", e)

        logger.info("Loaded %d rows into memory.", len(self.stocks))

    def find_matches(self, query: str, limit: int = 5) -> List[Stock]:
        if not query:
            return []
        q = query.lower()
        companies = self.trie.autocomplete(q)
        logger.info("Autocomplete suggestions for '%s': %s", q, companies)

        matches: List[Stock] = []
        for name in companies:
            row = self.stocks.get(name)
            if row:
                matches.append(Stock.from_dict(row))
            if len(matches) >= limit:
                break
        return matches

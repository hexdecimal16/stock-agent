import re
import weakref
import hashlib
import logging
import asyncio
from typing import Dict, Any, Optional
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, Future
from datetime import datetime
import threading

from utils.scrapper import CompanyScraper

logger = logging.getLogger(__name__)


class Stock:
    _executor = ThreadPoolExecutor(max_workers=4)

    def __init__(self, **sanitized_fields: Any):
        self._lock = threading.Lock()
        self._data: Dict[str, Any] = {}
        self._key_map: Dict[str, str] = {}
        self._url: str = ""
        self._scrape_future: Optional[Future] = None
        self._content_ready = threading.Event()
        self._content_ready.set()  # Initially set since no URL means no scraping needed

        # set sanitized attributes for convenience
        for k, v in sanitized_fields.items():
            setattr(self, k, v)

    @property
    def url(self) -> str:
        """Get the current URL."""
        return self._url

    @url.setter
    def url(self, value: str):
        """Set the URL and trigger asynchronous scraping if valid."""
        if value != self._url and self._is_valid_url(value):
            self._url = value
            self._content_ready.clear()  # Reset the event
            self._start_scraping()

    def _start_scraping(self):
        """Start asynchronous scraping task."""
        if self._scrape_future and not self._scrape_future.done():
            self._scrape_future.cancel()
        
        self._scrape_future = self._executor.submit(self._sync_scrape_wrapper)

    def _sync_scrape_wrapper(self):
        """Synchronous wrapper for the async scraping method."""
        loop = None
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._scrape_and_update())
        finally:
            if loop:
                loop.close()

    async def _scrape_and_update(self):
        """Scrape content and update data."""
        try:
            scrapper = CompanyScraper(self._url)
            content = await scrapper.scrape()
            
            with self._lock:
                self._data["content"] = content
                self._data["scraped_at"] = datetime.now().isoformat()
            
            self._content_ready.set()  # Signal that content is ready
            logger.info(f"Successfully scraped content from {self._url}")
            
        except Exception as e:
            logger.error(f"Failed to scrape content from {self._url}: {e}")
            with self._lock:
                self._data["scrape_error"] = str(e)
                self._data["scraped_at"] = datetime.now().isoformat()
            self._content_ready.set()  # Signal completion even on error

    @staticmethod
    def _sanitize_key(key: str) -> str:
        if key is None:
            return "_"
        s = key.strip().lower()
        s = re.sub(r"[^0-9a-zA-Z_]", "_", s)
        if s and s[0].isdigit():
            s = "_" + s
        if not s:
            s = "_"
        return s

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Stock":
        """Factory: sanitize keys and return a Stock instance."""

        original = dict(d)
        sanitized: Dict[str, Any] = {}
        key_map: Dict[str, str] = {}
        for key, val in original.items():
            safe = cls._sanitize_key(key)
            base = safe
            i = 1
            while safe in sanitized:
                safe = f"{base}_{i}"
                i += 1
            sanitized[safe] = val
            key_map[key] = safe

        inst = cls(**sanitized)
        inst._data = original
        inst._key_map = key_map

        # assign backing url using property to trigger scraping
        for candidate in ("URL", "Url", "Link"):
            if candidate in original and original[candidate] and cls._is_valid_url(original[candidate]):
                inst.url = original[candidate]  # Use property instead of direct assignment
                break

        return inst

    @classmethod
    def shutdown_executor(cls, wait: bool = True):
        try:
            cls._executor.shutdown(wait=wait)
        except Exception:
            pass

    @staticmethod
    def _is_valid_url(u: str) -> bool:
        try:
            p = urlparse(u or "")
            return p.scheme in ("http", "https") and bool(p.netloc)
        except Exception:
            return False

    def to_dict(self) -> Dict[str, Any]:
        return dict(self._data)

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def is_scraping(self) -> bool:
        """Check if scraping is currently in progress."""
        return self._scrape_future is not None and not self._scrape_future.done()

    def wait_for_content(self, timeout: Optional[float] = None) -> bool:
        """Wait for scraping to complete. Returns True if content is ready, False if timeout."""
        if not self.is_scraping():
            return True
        return self._content_ready.wait(timeout=timeout)

    def pretty(self) -> str:
        """Return a pretty-printed string representation of the stock data."""
        # If scraping is in progress, wait for it to complete
        if self._scrape_future and not self._scrape_future.done():
            logger.info("Waiting for content scraping to complete...")
            self._content_ready.wait(timeout=30)  # Wait up to 30 seconds
        
        # Get the lock
        with self._lock:
            if not self._data:
                return "(no data)"
            lines = []
            for k, v in self._data.items():
                lines.append(f"{k}: {v}")
            # if we have fetched content, include a short indicator
            if "content" in self._data:
                lines.append("\n--- Extracted content snippet (truncated) ---")
                lines.append((self._data["content"][:500] + ("..." if len(self._data["content"]) > 500 else "")))
            return "\n".join(lines)

    def __str__(self) -> str:
        return self.pretty()

    def __repr__(self) -> str:
        return f"Stock({list(self._data.keys())})"

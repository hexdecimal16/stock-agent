import os
import csv
import sys
import logging
import json
from typing import List, Dict, Optional, Any
from langchain_core.messages import AIMessage
from langchain_core.runnables.config import RunnableConfig

from services.stock_service import StockService
from services.stock_service_impl import StockServiceImpl
from models.stock import Stock
from models.trie import Trie
from services.scraper.scraping_service import ScrapingService
from services.scraper.moneycontrol_scraper import MoneyControlScraper
from services.scraper.csv_writer import CsvDataWriter
from langgraph.prebuilt import create_react_agent
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.tools import tool

from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class StockAgent:
    def __init__(
        self,
        stock_service: StockServiceImpl,
    ):
        self.stock_service = stock_service
        self.scraping_service = ScrapingService(
            scraper=MoneyControlScraper(), data_writer=CsvDataWriter()
        )

    def get_stock_data(self, company_name: str) -> str:
        rows = self.stock_service.find_matches(company_name, limit=5)
        if not rows:
            return "I couldn't find any stock matching your query. Try a company name or symbol."

        if len(rows) == 1:
            return "Found 1 matching stock:\n" + rows[0].pretty()
        response = ""
        for s in rows:
            response += s.pretty() + "\n\n"
        return response

    def update_stock_data(self) -> str:
        """Update the stock data from the source."""
        try:
            self.scraping_service.run(
                output_filename=os.path.join(
                    self.stock_service.assets_dir, "moneycontrol_stocks.csv"
                )
            )
            # Re-initialize the stock service to load the new data
            self.stock_service.boot(checkpointer)
            return "Stock data updated successfully."
        except Exception as e:
            logger.exception("Error updating stock data")
            return f"An error occurred while updating stock data: {e}"


base_dir = os.path.dirname(__file__)
assets_dir = os.path.join(base_dir, "assets")
stock_service = StockServiceImpl(assets_dir=assets_dir)
checkpointer = InMemorySaver()
stock_service.boot(checkpointer)
sa = StockAgent(stock_service=stock_service)

@tool
def get_stock_data(company_name: str) -> str:
    """
    Get stock data for a specific company.
    """
    return sa.get_stock_data(company_name)


@tool
def update_stock_data() -> str:
    """
    Update the stock data from the source. This is useful if the user suspects the data is stale.
    """
    return sa.update_stock_data()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s"
    )

    # Update the stock data on startup
    logger.info("Updating stock data on startup...")
    update_response = sa.update_stock_data()
    logger.info(update_response)

    if not os.environ.get("GOOGLE_API_KEY"):
        raise ValueError(
            "GOOGLE_API_KEY environment variable must be set for StockAgent to work."
        )

    model = init_chat_model(
        "gemini-2.5-flash", model_provider="google_genai", temperature=0
    )
    checkpointer = InMemorySaver()
    agent = create_react_agent(
        model=model,
        tools=[get_stock_data, update_stock_data],
        checkpointer=checkpointer,
        prompt="You are an stock market assistant.",
    )

    config: RunnableConfig = {"configurable": {"thread_id": "1"}}

    try:
        if "--test" in sys.argv:
            sample_queries = ["Tata", "Infosys", "reliance", "BANK", "NSE"]
            for q in sample_queries:
                print("\nQuery:", q)

        else:
            print("StockAgent ready. Type a query (Ctrl-C to exit):")
            while True:
                q = input("> ").strip()
                if not q:
                    continue
                response = agent.invoke(
                    {"messages": [{"role": "user", "content": q}]}, config
                )
                messages = response.get("messages", [])
                if messages and isinstance(messages[-1], AIMessage):
                    ai_response = messages[-1].content
                    print(f"\n{ai_response}\n")
                    with open("response.md", "w", encoding="utf-8") as f:
                        f.write(ai_response)
                else:
                    # Fallback to printing all messages for debugging
                    print("Could not get a final answer. Dumping all messages:")
                    for m in messages:
                        m.pretty_print()

    except (KeyboardInterrupt, EOFError):
        print("\nGoodbye")
    finally:
        try:
            Stock.shutdown_executor()
        except Exception:
            logger.exception("Error shutting down executor")

# Stock Agent

A conversational AI agent for retrieving real-time stock market data. This agent uses Google's Gemini models through LangChain to provide an interactive experience for querying stock information.

## Features

- **Conversational Interface**: Ask for stock data in natural language.
- **Real-time Data**: Scrapes the latest stock information on startup.
- **Modular Design**: Built with a service-oriented architecture for easy extension.

## Getting Started

### Prerequisites

- Python 3.10+
- A Google API key

### Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/hexdecimal16/stock-agent
   cd stock-agent
   ```

2. **Set up a virtual environment:**

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure your environment:**

   Create a `.env` file in the project root and add your Google API key:

   ```env
   GOOGLE_API_KEY="YOUR_GOOGLE_API_KEY"
   ```

## How to Run

Execute the following command from the project's root directory:

```bash
PYTHONPATH=. python3 src/agent.py
```

The agent will initialize, fetch the latest stock data, and prompt you for your query.

# Solana Wallet Tracker Bot 🚀

A professional Telegram bot designed for real-time monitoring of the Solana blockchain. It identifies "clean" (newly created) wallets the moment they receive their first SOL deposit from specified source addresses (e.g., Exchange Hot Wallets) and tracks all their subsequent activities.

## 🌟 Key Features

- **Real-time Discovery:** Leverages Helius Webhooks to detect transactions instantly.
- **Clean Wallet Verification:** Automatically verifies if a wallet is truly new by checking its transaction history and asset holdings (tokens/NFTs) via DAS API.
- **Smart Filtering:** Configurable minimum and maximum SOL thresholds for the initial funding transaction.
- **Activity Tracking:** Once a wallet is "captured," the bot monitors all its future SOL and SPL token movements.
- **Organization Tools:** Assign custom tags (e.g., 🐋 Whale, 🚀 Insider) and labels to tracked wallets.
- **Interactive UI:** Fully managed through a sleek Telegram interface with inline keyboards and FSM (Finite State Machine) flows.

## 📺 Demo

Check out the bot in action:

![Bot Demo](docs/assets/demo.mp4)

*(Note: If viewing on GitHub, you can find the video file at `docs/assets/demo.mp4`)*

## 🛠 Tech Stack

- **Language:** Python 3.10+
- **Bot Framework:** [Aiogram 3.x](https://docs.aiogram.dev/) (Asynchronous Telegram Bot API)
- **API Framework:** [FastAPI](https://fastapi.tiangolo.com/) (To receive Helius Webhooks)
- **Database:** [SQLAlchemy](https://www.sqlalchemy.org/) with **aiosqlite** (Asynchronous SQLite)
- **Blockchain Data:** [Helius API](https://www.helius.dev/) (RPC & Enhanced Webhooks)
- **Server:** Uvicorn (ASGI server)

## 📋 Prerequisites

- Python 3.10 or higher
- A Telegram Bot Token (from [@BotFather](https://t.me/botfather))
- A [Helius API Key](https://dashboard.helius.dev/)
- A public URL for webhooks (use [ngrok](https://ngrok.com/) for local development or a VPS for production)

## 🚀 Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/SolanaBot.git
   cd SolanaBot
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # Linux/macOS:
   source .venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## ⚙️ Configuration

Create a `.env` file in the root directory and fill in your credentials as shown below:

```env
# Telegram Settings
BOT_TOKEN=your_bot_token_here
ADMIN_ID=123456789

# Database Settings
DB_PATH=data/bot.db

# Helius Settings
HELIUS_API_KEY=your_helius_api_key_here
SOURCE_WEBHOOK_ID=your_source_webhook_uuid
TRACKED_WEBHOOK_ID=your_tracked_webhook_uuid

# Logic Defaults
DEFAULT_MIN_SOL=0.1
DEFAULT_MAX_SOL=100.0
TIMEZONE_OFFSET=0

# Server Settings
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
```

## 🏗 Architecture

The bot operates using a hybrid push/pull model:
1. **Helius** monitors the Solana blockchain for specific addresses.
2. When a transaction occurs at a **Source Address**, Helius sends a POST request to the **FastAPI** `/webhook/sources` endpoint.
3. The **Processor** checks if the receiver is a "clean" wallet (0 history, 0 assets).
4. If verified, the wallet is saved to **SQLite** and its address is programmatically added to the **Tracked Webhook** list in Helius.
5. The **Telegram Bot** sends an instant notification to the admin with a Solscan link.

## 🤖 Bot Commands & Navigation

- `/start` - Open the main menu.
- **📊 Status** - View current statistics (active sources, total captured wallets).
- **📡 Sources** - Add or remove Solana addresses to monitor (e.g., Binance, Coinbase).
- **👛 Wallets** - Browse, rename, and manage discovered wallets with pagination.
- **🏷️ Tags** - Create and manage category tags for better organization.
- **⚙️ Settings** - Configure global SOL filters and timezone offsets for notificat
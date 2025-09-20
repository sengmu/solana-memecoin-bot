# Solana Memecoin Trading Bot

A comprehensive Python trading bot for Solana memecoins with advanced features including discovery, analysis, and automated trading.

## Features

### 🔍 Token Discovery
- **DexScreener WebSocket Integration**: Real-time monitoring of trending Solana memecoins
- **Smart Filtering**: Filters tokens by volume (>$1M), FDV (>$100K), and memecoin keywords
- **Pattern Recognition**: Detects common memecoin naming patterns

### 📊 Analysis & Quality Scoring
- **Twitter Analysis**: Scrapes profiles and tweets to compute quality scores (>70 required)
- **RugCheck Integration**: Uses Selenium to verify token safety and "Good" ratings
- **Multi-factor Scoring**: Combines social media, safety, and token metrics for confidence scoring

### 💱 Advanced Trading
- **Jupiter V6 Integration**: High-performance DEX aggregation for optimal trades
- **Dynamic Priority Fees**: Uses `getRecentPrioritizationFees` for optimal transaction timing
- **Volatility-based Slippage**: Adjusts slippage based on token volatility and volume
- **Risk Management**: Configurable position sizes and stop-loss mechanisms

### 👥 Copy Trading
- **Leader Wallet Monitoring**: Tracks successful traders' wallets
- **Confidence-based Copying**: Only copies trades with >70% confidence
- **Smart Position Sizing**: Scales copy trades based on available balance

### 📈 Portfolio Management
- **Wallet Monitoring**: Real-time tracking of new tokens and portfolio changes
- **Position Tracking**: Monitors active positions and exit conditions
- **Performance Analytics**: Comprehensive trading statistics and reporting

## Installation

1. **Clone the repository**:
```bash
git clone <repository-url>
cd solana-memecoin-bot
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Install Chrome for Selenium** (for RugCheck analysis):
```bash
# macOS
brew install --cask google-chrome

# Ubuntu/Debian
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
sudo sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'
sudo apt-get update
sudo apt-get install google-chrome-stable
```

4. **Configure environment variables**:
```bash
cp env.example .env
# Edit .env with your configuration
```

## Configuration

Create a `.env` file with the following variables:

```env
# Solana Configuration
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com
SOLANA_WS_URL=wss://api.mainnet-beta.solana.com
PRIVATE_KEY=your_wallet_private_key_here

# Trading Configuration
MAX_POSITION_SIZE=0.1
MIN_VOLUME_24H=1000000
MIN_FDV=100000
MAX_SLIPPAGE=0.05
DEFAULT_SLIPPAGE=0.01

# Twitter Configuration
TWITTER_BEARER_TOKEN=your_twitter_bearer_token_here

# Copy Trading
LEADER_WALLET_ADDRESS=leader_wallet_address_here
COPY_TRADING_ENABLED=true
MIN_CONFIDENCE_SCORE=70

# Logging
LOG_LEVEL=INFO
LOG_TO_FILE=true

# Risk Management
MAX_DAILY_LOSS=0.1
STOP_LOSS_PERCENTAGE=0.2
TAKE_PROFIT_PERCENTAGE=0.5
```

## Usage

### Basic Usage

```python
import asyncio
from memecoin_bot import MemecoinBot

async def main():
    async with MemecoinBot() as bot:
        await bot.run_bot()

if __name__ == "__main__":
    asyncio.run(main())
```

### Advanced Usage

```python
import asyncio
from memecoin_bot import MemecoinBot

async def main():
    # Initialize bot with custom config
    bot = MemecoinBot("custom.env")
    
    # Initialize components
    await bot.initialize()
    
    # Run specific components
    await bot.dexscreener_client.start()
    await bot.copy_trader.start_monitoring()
    
    # Get bot status
    status = bot.get_status()
    print(f"Bot Status: {status}")
    
    # Clean shutdown
    await bot.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
```

### Command Line Usage

```bash
python memecoin_bot.py
```

## Architecture

### Core Components

1. **MemecoinBot**: Main orchestrator class
2. **DexScreenerClient**: WebSocket-based token discovery
3. **TwitterAnalyzer**: Social media analysis and scoring
4. **RugCheckAnalyzer**: Token safety verification
5. **JupiterTrader**: DEX trading execution
6. **CopyTrader**: Leader wallet monitoring and copying
7. **WalletMonitor**: Portfolio tracking and management
8. **TradeLogger**: Comprehensive logging and error handling

### Data Flow

```
Token Discovery → Analysis → Quality Scoring → Trading Decision → Execution → Monitoring
     ↓              ↓            ↓              ↓              ↓           ↓
DexScreener → Twitter/RugCheck → Confidence → Jupiter V6 → Position Mgmt → Portfolio
```

## API Keys Required

1. **Solana RPC**: Use a reliable RPC provider (Helius, QuickNode, etc.)
2. **Twitter API**: Get Bearer Token from Twitter Developer Portal
3. **DexScreener**: No API key required (public API)

## Risk Management

- **Position Sizing**: Configurable maximum position size per trade
- **Stop Loss**: Automatic position exit on adverse price movements
- **Take Profit**: Profit-taking at configured levels
- **Daily Loss Limits**: Maximum daily loss protection
- **Confidence Thresholds**: Only trade high-confidence opportunities

## Logging

The bot provides comprehensive logging:

- **Console Output**: Real-time status and trade information
- **File Logging**: Detailed logs saved to `logs/` directory
- **Trade History**: All trades saved to `trades.json`
- **Statistics**: Performance metrics saved to `trading_stats.json`

## Monitoring

Monitor bot performance through:

1. **Console Output**: Real-time status updates
2. **Log Files**: Detailed operation logs
3. **Trade Files**: Complete trade history
4. **Status API**: Programmatic status checking

## Safety Features

- **RugCheck Integration**: Verifies token safety before trading
- **Whale Detection**: Avoids tokens with high whale concentration
- **Liquidity Checks**: Ensures sufficient liquidity for trading
- **Slippage Protection**: Dynamic slippage based on market conditions

## Performance Optimization

- **Async Architecture**: Non-blocking operations for maximum efficiency
- **Connection Pooling**: Reused HTTP connections for API calls
- **Batch Processing**: Efficient handling of multiple tokens
- **Smart Caching**: Reduced redundant API calls

## Troubleshooting

### Common Issues

1. **RPC Connection Errors**: Check your Solana RPC URL and rate limits
2. **Twitter API Errors**: Verify your Bearer Token is valid
3. **Selenium Issues**: Ensure Chrome is installed and WebDriver is available
4. **Trading Failures**: Check wallet balance and token liquidity

### Debug Mode

Enable debug logging by setting `LOG_LEVEL=DEBUG` in your `.env` file.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Disclaimer

This software is for educational purposes only. Trading cryptocurrencies involves substantial risk of loss. The authors are not responsible for any financial losses. Use at your own risk.

## License

MIT License - see LICENSE file for details.

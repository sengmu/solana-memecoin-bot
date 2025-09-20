# 🚀 Memecoin Trading Bot Dashboard

A comprehensive Streamlit dashboard for monitoring and controlling the Solana Memecoin Trading Bot.

## Features

### 📊 **Dashboard Tabs**

#### 🔍 **Discovery Tab**
- **Token Table**: Real-time table of discovered memecoins with filtering
- **Summary Metrics**: Total tokens, memecoins, approved, and trading counts
- **Interactive Charts**:
  - Volume 24h distribution histogram
  - Token status distribution pie chart
- **Advanced Filters**:
  - Filter by status (Pending, Analyzing, Approved, etc.)
  - Filter by type (Memecoins Only, Non-Memecoins)
  - Minimum volume threshold

#### 📈 **Trades Tab**
- **Trading History**: Complete table of all executed trades
- **Performance Metrics**: Total trades, success rate, volume
- **Interactive Charts**:
  - Trading volume over time (line chart)
  - Success rate by trade type (bar chart)
- **Advanced Filters**:
  - Filter by trade type (BUY/SELL)
  - Filter by success status
  - Date range selection

#### 💼 **Positions Tab**
- **Active Positions**: Real-time table of current holdings
- **Position Metrics**: Total value, hold time, profitability
- **Interactive Charts**:
  - Position confidence distribution
  - Hold time distribution
- **Position Management**: View entry prices, current prices, P&L

#### 🛡️ **Safety Tab**
- **RugCheck Analysis**: Safety ratings distribution
- **Safety Metrics**: Total analyzed, good/bad ratings, safety rate
- **Interactive Charts**:
  - RugCheck safety ratings pie chart
- **Safety Alerts**: Real-time warnings for unsafe tokens
- **Safety Tips**: Guidelines for safe trading

### 🎛️ **Sidebar Controls**

#### 🤖 **Bot Controls**
- **Status Display**: Real-time bot status (Running/Stopped/Not Initialized)
- **Discovery Controls**:
  - Start Discovery button
  - Stop Discovery button
- **Manual Trading**:
  - Token address input
  - Amount input (SOL)
  - Buy/Sell buttons
- **Settings**:
  - Refresh interval slider (10-60 seconds)
  - Force refresh button

### ⚡ **Real-time Features**
- **Auto-refresh**: Dashboard updates every 30 seconds
- **Live Data**: Real-time token discovery and trading data
- **Session State**: Maintains bot state across refreshes
- **Responsive Design**: Works on desktop and mobile

## Installation

1. **Install Dependencies**:
```bash
pip install streamlit plotly pandas
```

2. **Configure Environment**:
```bash
cp env.example .env
# Edit .env with your configuration
```

## Usage

### Quick Start
```bash
python run_dashboard.py
```

### Manual Start
```bash
streamlit run dashboard.py
```

### Access Dashboard
Open your browser and go to: `http://localhost:8501`

## Dashboard Components

### 🔧 **DashboardManager Class**
- Manages bot state and data
- Handles data transformation for display
- Provides real-time refresh functionality

### 📊 **Data Sources**
- **Discovered Tokens**: From bot's `discovered_tokens` dictionary
- **Trades**: From `trades.json` file
- **Positions**: From bot's `active_positions` dictionary
- **Safety Data**: From RugCheck analysis results

### 🎨 **Visualization Libraries**
- **Plotly**: Interactive charts and graphs
- **Pandas**: Data manipulation and analysis
- **Streamlit**: Web interface and widgets

## Configuration

### Environment Variables
The dashboard uses the same environment variables as the bot:
- `PRIVATE_KEY`: Your wallet private key
- `SOLANA_RPC_URL`: Solana RPC endpoint
- `TWITTER_BEARER_TOKEN`: Twitter API token (optional)
- `LEADER_WALLET_ADDRESS`: Copy trading wallet (optional)

### Dashboard Settings
- **Refresh Interval**: 10-60 seconds (default: 30)
- **Auto-refresh**: Enabled by default
- **Theme**: Streamlit default with custom CSS

## Features in Detail

### 🔍 **Discovery Tab Features**
- **Real-time Token Discovery**: Shows tokens as they are discovered
- **Smart Filtering**: Multiple filter options for data analysis
- **Volume Analysis**: Histogram showing volume distribution
- **Status Tracking**: Visual representation of token analysis status

### 📈 **Trades Tab Features**
- **Complete Trade History**: All trades with detailed information
- **Performance Analytics**: Success rates and volume metrics
- **Time Series Analysis**: Trading volume over time
- **Error Tracking**: Failed trades with error messages

### 💼 **Positions Tab Features**
- **Active Position Monitoring**: Real-time position tracking
- **P&L Analysis**: Profit/loss calculations (when implemented)
- **Hold Time Tracking**: Position duration analysis
- **Confidence Scoring**: Position confidence distribution

### 🛡️ **Safety Tab Features**
- **RugCheck Integration**: Safety analysis visualization
- **Risk Assessment**: Safety ratings and alerts
- **Safety Guidelines**: Trading safety recommendations
- **Alert System**: Real-time safety warnings

## Troubleshooting

### Common Issues

1. **Dashboard Not Loading**:
   - Check if all dependencies are installed
   - Verify environment variables are set
   - Check console for error messages

2. **No Data Showing**:
   - Ensure bot is initialized
   - Check if discovery is running
   - Verify data files exist (trades.json)

3. **Charts Not Displaying**:
   - Check if Plotly is installed
   - Verify data format
   - Check browser console for errors

### Debug Mode
Enable debug logging by setting:
```python
logging.basicConfig(level=logging.DEBUG)
```

## Customization

### Adding New Tabs
1. Create a new render function (e.g., `render_analytics_tab`)
2. Add the tab to the main function
3. Update the tab list in `st.tabs()`

### Adding New Charts
1. Use Plotly Express or Graph Objects
2. Add to the appropriate tab function
3. Ensure data is properly formatted

### Styling
- Modify the CSS in the `st.markdown()` section
- Use Streamlit's theming options
- Add custom HTML/CSS as needed

## Security Notes

- **Private Keys**: Never commit private keys to version control
- **Environment Variables**: Use `.env` file for sensitive data
- **Network Access**: Dashboard runs on localhost by default
- **Data Privacy**: All data stays on your local machine

## Performance

### Optimization Tips
- **Refresh Interval**: Adjust based on your needs
- **Data Filtering**: Use filters to reduce data load
- **Chart Complexity**: Limit number of charts for better performance
- **Memory Usage**: Monitor memory usage with large datasets

### Scaling
- **Large Datasets**: Implement pagination for large tables
- **Real-time Updates**: Use WebSocket for faster updates
- **Caching**: Implement data caching for better performance

## Support

For issues and questions:
1. Check the console output for errors
2. Verify all dependencies are installed
3. Check environment configuration
4. Review the bot logs for related issues

## License

Same as the main bot project - MIT License.

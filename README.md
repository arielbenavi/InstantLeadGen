# InstantLeadGen 🚀

InstantLeadGen is a tool originally made for music producers to gather and analyze data from industry-leading platforms like Genius.com, Instagram, and Muso.ai.

## 🔥 Features

- **Reverse-Engineered API Access**: Utilizes undocumented endpoints for deeper, more comprehensive data retrieval
- **Multi-Platform Integration**: Seamlessly combines data from Genius.com, Instagram, and Muso.ai
- **Advanced Data Standardization**: Transforms diverse data sources into a unified, actionable format
- **Real-time Google Sheets Integration**: Instantly populates your spreadsheets with fresh data
- **Intelligent Telegram Notifications**: Keeps you updated with smart, context-aware messages

## 🛠 Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/InstantLeadGen.git
   cd InstantLeadGen
   ```

2. Install required packages:
   ```
   pip install -r requirements.txt
   ```

3. Set up your secret weapons:
   - `vetricio_api_key.txt`: your Vetric.io API key
   - `telegram_token_id.txt`: your Telegram bot token
   - `client_secret.json`: Your Google Sheets API secret json thingy

## 🚀 Usage

Unleash the power with a single command:

```
python main.py
```

This will execute the scraping workflows for Genius.com, Instagram, and Muso.ai, and store the results in a Google Sheet.

## ⚙️ Configuration

- `MAX_RECORDS_PER_SOURCE`: Set in `main.py` to limit the number of records scraped from each source
- `SHEET_NAME`: name of Google Sheets Spreadsheet where results are stored
- `RESULTS_SHEET_ID`: Google Sheets ID where results are stored

## 📁 File Structure

- `main.py`: Main script that orchestrates the entire workflow
- `networker_genius.py`: Handles scraping from Genius.com
- `inner_instagram_flow.py`: Manages Instagram data collection for pre-determined monitored accounts
- `networker_muso.py`: Scrapes data from Muso.ai
- `vetricio_ig_wrapper.py`: Wrapper for Vetric.io Instagram API
- `gsheet_handler.py`: Handles interaction with Google Sheets
- `telegram_wrapper.py`: Manages Telegram notifications

## 💡 Examples

### Tapping into Genius.com's Goldmine

```python
from networker_genius import scrape_genius

future_hits = scrape_genius(2024, 7, release_type='singles', limit=10)
print(future_hits.head())
```

### Unlocking Instagram's Hidden Potential

```python
from inner_instagram_flow import main_workflow

instagram_intel = main_workflow()
print(instagram_intel.head())
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📜 License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.

## ⚠️ Disclaimer

InstantLeadGen is a powerful tool, Use it ethically and in compliance with all applicable laws and platform terms of service.

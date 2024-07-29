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

2. Install the cutting-edge dependencies:
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

Watch as InstantLeadGen orchestrates a symphony of data collection, processing, and delivery.

## ⚙️ Configuration

- `MAX_RECORDS_PER_SOURCE`: Control the firehose of data
- `RESULTS_SHEET_ID`: Your Google Sheets command center

## 📁 File Structure

- `main.py`: The maestro conducting the entire operation
- `networker_genius.py`: Your insider at Genius.com
- `inner_instagram_flow.py`: Instagram's hidden pathways
- `networker_muso.py`: Muso.ai's secret informant
- `vetricio_ig_wrapper.py`: The skeleton key to Instagram's API
- `gsheet_handler.py`: Your Google Sheets puppet master
- `telegram_wrapper.py`: Your personal Telegram whisperer

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

Got what it takes to enhance InstantLeadGen? We dare you to submit a Pull Request.

## 📜 License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details. Use it wisely.

## ⚠️ Disclaimer

InstantLeadGen is a powerful tool. With great power comes great responsibility. Use it ethically and in compliance with all applicable laws and platform terms of service.

---

Built with 💻 and 🎵 by music industry hackers, for music industry visionaries.
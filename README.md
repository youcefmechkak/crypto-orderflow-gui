# crypto-orderflow-gui

A lightweight **real-time order flow visualizer** for Binance spot markets.
This tool tracks **aggressive buyers and sellers** (taker trades) and displays:

* **Order flow table** → grouped trades by time/price/quantity.
* **Volume bar chart** → rolling snapshot of taker buy vs taker sell pressure.
* **Custom controls** → change trading pair, adjust aggregation interval, scale chart interactively.

If you want to actually *see* who’s pushing the market in the last second, this is it.


## What is Order Flow?

Order flow = the stream of **executed trades**.

* **Aggressive buyers** = market orders lifting the ask.
* **Aggressive sellers** = market orders hitting the bid.
  Watching this flow tells you short-term pressure in the market — who’s in control right now.


## Features

* Live Binance integration (via `python-binance`)
* GUI built with **Tkinter** + embedded **Matplotlib**
* Adjustable aggregation interval (default: 1s)
* Supports any Binance spot symbol (e.g., `BTCUSDT`, `ETHUSDT`)


## Usage

1. Open `main.py` (or whatever filename you saved it as).
2. Add your **Binance API key + secret** at the top of the file:

   ```python
   api_key = "YOUR_API_KEY"
   api_secret = "YOUR_API_SECRET"
   ```

3. Run the script:

   ```bash
   python main.py
   ```

### GUI Controls:

* **Symbol box** → change trading pair (e.g. BTCUSDT → ETHUSDT)
* **Interval box** → set aggregation window (seconds)
* **Quit** → exits app


## Screenshot

<img width="601" height="1028" alt="Screenshot 2025-08-22 120557" src="https://github.com/user-attachments/assets/2f955ab4-7cf5-46fe-92fb-407ef6c49c6e" />


## Developer Notes
- **Tech Stack:** Python, Tkinter, Matplotlib, Pandas, python-binance.
- **Data Source:** Binance API (historical trades endpoint).
- **Error Handling:** Includes basic retry logic for API failures and input validation.
- **Customization:** Modify qty_trades (default: 100) or volume_bar_number (default: 30) in main.py to adjust data limits.

## Disclaimer

* For **educational/research purposes only**.
* Do **not** rely on this tool for live trading decisions.
* Use at your own risk.

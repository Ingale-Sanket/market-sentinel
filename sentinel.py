import websocket
import json
import time
import os
import numpy as np
from collections import deque
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client

# --- CONFIGURATION ---
load_dotenv() # This loads the variables from the .env file
SYMBOL = "btcusdt"
THRESHOLD_MULTIPLIER = 10 
WINDOW_SIZE = 100 

# --- SUPABASE CONNECTION (FIXED) ---
# We ask for the NAME of the variable, not the value.
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")

if not url or not key:
    print("❌ ERROR: Missing Supabase credentials in .env file")
    # Debugging help:
    print(f"DEBUG: Found URL: {url}") 
    print(f"DEBUG: Found KEY: {key}")
    exit()

supabase: Client = create_client(url, key)

# --- STATE MANAGEMENT ---
trade_volumes = deque(maxlen=WINDOW_SIZE)

def log_whale_to_db(price, volume, avg_vol):
    """Sends the alert to the cloud database"""
    try:
        data = {
            "symbol": SYMBOL,
            "price": price,
            "volume": volume,
            "average_volume": avg_vol,
            "is_whale": True
        }
        # Insert into Supabase
        supabase.table("whale_alerts").insert(data).execute()
        print("✅ Alert sent to Cloud Database!")
    except Exception as e:
        print(f"⚠️ Failed to upload alert: {e}")

def on_message(ws, message):
    try:
        data = json.loads(message)
        price = float(data['p'])
        quantity = float(data['q'])
        usd_volume = price * quantity
        
        trade_volumes.append(usd_volume)
        
        if len(trade_volumes) == WINDOW_SIZE:
            avg_vol = np.mean(trade_volumes)
            
            if usd_volume > (avg_vol * THRESHOLD_MULTIPLIER):
                timestamp = datetime.fromtimestamp(data['T'] / 1000).strftime('%H:%M:%S')
                print("\n" + "="*50)
                print(f"🚨 WHALE DETECTED AT {timestamp}")
                print(f"💰 Trade Value: ${usd_volume:,.2f}")
                print("="*50 + "\n")
                
                # TRIGGER THE CLOUD SYNC
                log_whale_to_db(price, usd_volume, avg_vol)

            else:
                print(".", end="", flush=True)

    except Exception as e:
        print(f"Error: {e}")

def on_error(ws, error):
    print(f"Connection Error: {error}")

def on_close(ws, close_status_code, close_msg):
    print("Connection lost. Reconnecting...")
    time.sleep(5)
    start_sentinel()

def on_open(ws):
    print(f"✅ CONNECTED: Listening to {SYMBOL.upper()}...")

def start_sentinel():
    socket_url = f"wss://stream.binance.com:9443/ws/{SYMBOL}@trade"
    ws = websocket.WebSocketApp(
        socket_url,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    ws.run_forever()

if __name__ == "__main__":
    print("--- MARKET SENTINEL v2.0 (Cloud Connected) ---")
    start_sentinel()
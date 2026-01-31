import websocket
import json
import threading
import time
import numpy as np
from collections import deque
from datetime import datetime

# --- CONFIGURATION ---
SYMBOL = "btcusdt"
THRESHOLD_MULTIPLIER = 10  # If volume is 10x the average, flag it.
WINDOW_SIZE = 100          # Keep track of the last 100 trades for average.

# --- STATE MANAGEMENT ---
# specific efficient list that automatically removes old data
trade_volumes = deque(maxlen=WINDOW_SIZE) 

def on_message(ws, message):
    """
    This function runs EVERY time a trade happens (milliseconds).
    """
    try:
        data = json.loads(message)
        
        # 'p' is Price, 'q' is Quantity (Amount of BTC)
        price = float(data['p'])
        quantity = float(data['q'])
        usd_volume = price * quantity
        
        # 1. Update our history
        trade_volumes.append(usd_volume)
        
        # 2. Calculate the "Invisible Hand" Metrics
        if len(trade_volumes) == WINDOW_SIZE:
            # Calculate average volume of last 100 trades
            avg_vol = np.mean(trade_volumes)
            
            # 3. THE DETECTION LOGIC
            # If this specific trade is HUGE compared to the average...
            if usd_volume > (avg_vol * THRESHOLD_MULTIPLIER):
                timestamp = datetime.fromtimestamp(data['T'] / 1000).strftime('%H:%M:%S')
                
                # --- VISUAL ALERT ---
                print("\n" + "="*50)
                print(f"🚨 WHALE DETECTED AT {timestamp}")
                print(f"💰 Trade Value: ${usd_volume:,.2f}")
                print(f"📊 Average was: ${avg_vol:,.2f}")
                print(f"📈 Price: ${price:,.2f}")
                print("="*50 + "\n")
                
                # TODO: In Phase 2, we will send this to Supabase/Flutter here.
            else:
                # Print a small dot to show the system is alive and breathing
                print(".", end="", flush=True)

    except Exception as e:
        print(f"Error parsing message: {e}")

def on_error(ws, error):
    print(f"Connection Error: {error}")

def on_close(ws, close_status_code, close_msg):
    print("Connection lost. Reconnecting in 5 seconds...")
    time.sleep(5)
    start_sentinel() # Auto-restart logic

def on_open(ws):
    print(f"✅ CONNECTED: Listening to the {SYMBOL.upper()} Invisible Hand...")
    print("Waiting for data stream to fill buffer...")

def start_sentinel():
    # Binance Public Stream URL (No API Key needed for public data)
    socket_url = f"wss://stream.binance.com:9443/ws/{SYMBOL}@trade"
    
    ws = websocket.WebSocketApp(
        socket_url,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    
    # Run forever implies it blocks the terminal, which is what we want for a daemon
    ws.run_forever()

if __name__ == "__main__":
    print("--- MARKET SENTINEL v1.0 STARTING ---")
    start_sentinel()
import os
from dotenv import load_dotenv
from supabase import create_client, Client
from datetime import datetime

# Load your keys
load_dotenv()
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

def trigger_fake_whale():
    print("🧪 Injecting FAKE Whale Alert...")
    
    data = {
        "symbol": "TEST-COIN", # Distinct name so you know it's a test
        "price": 99999.99,
        "volume": 5000000.00,  # $5 Million
        "average_volume": 10000.00,
        "is_whale": True,
        # Supabase adds 'created_at' automatically
    }
    
    supabase.table("whale_alerts").insert(data).execute()
    print("✅ FAKE Whale sent! Check your phone immediately.")

if __name__ == "__main__":
    trigger_fake_whale()
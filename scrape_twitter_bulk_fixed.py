import subprocess
import os
from datetime import datetime

def scrape_bulk():
    queries = [
        'spotify discovery weekly (bad OR sucks OR stuck)',
        'spotify recommendations suck OR same playlist',
        'stuck listening old songs spotify',
        'spotify new music hard OR struggle',
        'spotify algorithm bad OR no discovery'
    ]
    
    for i, q in enumerate(queries):
        print(f"🔍 Bulk search {i+1}: {q}")
        try:
            result = subprocess.run(['twitter', 'search', q, '-n', '50'], 
                                  capture_output=True, text=True, timeout=30)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M')
            filename = f"data/raw/twitter_bulk_{timestamp}_{i}.json"
            with open(filename, 'w') as f:
                f.write(result.stdout or result.stderr or '[]')
            print(f"  → Saved to {filename} ({len(result.stdout)} chars)")
        except Exception as e:
            print(f"  Error: {e}")
    
    print("✅ Bulk scrape complete.")

if __name__ == "__main__":
    os.makedirs("data/raw", exist_ok=True)
    scrape_bulk()
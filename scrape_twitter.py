import subprocess
import pandas as pd
from datetime import datetime
import os

def scrape_twitter_live_india(search_term="spotify india", limit=100):
    """Live Twitter scraper focused on Indian users"""
    print(f"🔍 Live India Twitter search: '{search_term}' (limit: {limit})")
    
    # India-specific keywords to boost relevance
    india_keywords = [
        f"{search_term} (india OR hindi OR bollywood OR mumbai OR delhi OR bangalore OR hyderabad OR chennai)",
        f"{search_term} (jiosaavn OR saavn OR gaana OR wynk)",
        f"{search_term} (data saver OR cheap OR affordable OR regional)"
    ]
    
    all_posts = []
    
    for q in india_keywords[:2]:  # Limit to 2 queries to avoid rate limits
        try:
            result = subprocess.run(['twitter', 'search', q, '-n', str(limit//2)], 
                                  capture_output=True, text=True, timeout=60)
            
            raw_output = result.stdout or result.stderr or ''
            timestamp = datetime.now().strftime('%Y%m%d_%H%M')
            raw_file = f"data/raw/twitter_india_{timestamp}.json"
            os.makedirs("data/raw", exist_ok=True)
            with open(raw_file, 'w') as f:
                f.write(raw_output)
            
            print(f"  → Saved batch for '{q}'")
            
            # Basic parsing for immediate use
            lines = raw_output.split('\n')
            for line in lines:
                if len(line.strip()) > 50 and '│' in line:
                    try:
                        text = line.split('│')[2].strip() if len(line.split('│')) > 2 else line
                        if text and len(text) > 30:
                            all_posts.append({
                                'text': text,
                                'source': 'twitter_india',
                                'date': datetime.now().isoformat(),
                                'is_discovery_related': True,
                                'theme': 'discovery_india'
                            })
                    except:
                        pass
        except Exception as e:
            print(f"  Error with query: {e}")
    
    # Save parsed
    if all_posts:
        df = pd.DataFrame(all_posts)
        parsed_file = f"data/raw/twitter_india_parsed_{timestamp}.csv"
        df.to_csv(parsed_file, index=False)
        print(f"✅ Parsed {len(all_posts)} India-relevant tweets to {parsed_file}")
        return df
    return pd.DataFrame()

if __name__ == "__main__":
    # Test with India focus
    scrape_twitter_live_india("spotify discovery", 100)
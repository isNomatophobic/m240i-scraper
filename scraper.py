import os
import sqlite3
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from dotenv import load_dotenv
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)

# Load environment variables
load_dotenv()

# Database setup
def setup_database():
    conn = sqlite3.connect('listings.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS listings
        (id TEXT PRIMARY KEY,
         title TEXT,
         price TEXT,
         url TEXT,
         date_added TIMESTAMP)
    ''')
    conn.commit()
    conn.close()

def get_existing_listings():
    conn = sqlite3.connect('listings.db')
    c = conn.cursor()
    c.execute('SELECT id FROM listings')
    existing_ids = {row[0] for row in c.fetchall()}
    conn.close()
    return existing_ids

def save_listing(listing_id, title, price, url):
    conn = sqlite3.connect('listings.db')
    c = conn.cursor()
    c.execute('''
        INSERT OR IGNORE INTO listings 
        (id, title, price, url, date_added)
        VALUES (?, ?, ?, ?, ?)
    ''', (listing_id, title, price, url, datetime.now()))
    conn.commit()
    conn.close()

def send_telegram_notification(new_listings):
    if not new_listings:
        return

    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    if not bot_token or not chat_id:
        logging.error("Telegram credentials not found in environment variables")
        return

    message = f"🚗 New BMW 240 Listings Found - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
    
    for listing in new_listings:
        message += f"📌 {listing['title']}\n"
        message += f"💰 Price: {listing['price']}\n"
        message += f"🔗 {listing['url']}\n"
        message += "-" * 30 + "\n"

    # Split message if it's too long (Telegram has a 4096 character limit)
    max_length = 4000
    messages = [message[i:i+max_length] for i in range(0, len(message), max_length)]
    
    for msg in messages:
        try:
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            data = {
                "chat_id": chat_id,
                "text": msg,
                "parse_mode": "HTML",
                "disable_web_page_preview": True
            }
            response = requests.post(url, data=data)
            response.raise_for_status()
            logging.info("Telegram notification sent successfully")
        except Exception as e:
            logging.error(f"Failed to send Telegram notification: {str(e)}")

def scrape_listings():
    url = "https://www.mobile.bg/obiavi/avtomobili-dzhipove/bmw/240"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all listings
        listings = soup.find_all('div', class_='item')
        existing_ids = get_existing_listings()
        new_listings = []

        for listing in listings:
            try:
                # Skip if it's not a car listing (e.g., news items)
                if 'fakti' in listing.get('class', []):
                    continue

                # Get listing ID from the URL
                listing_link = listing.find('a', class_='title')
                if not listing_link:
                    logging.warning("Listing link not found, skipping...")
                    continue
                    
                listing_id = listing_link['href'].split('-')[1]
                if listing_id in existing_ids:
                    continue

                # Extract basic info
                title = listing_link.text.strip()
                
                # Extract price safely
                price_div = listing.find('div', class_='price')
                price = 'N/A'
                if price_div:
                    price_div_inner = price_div.find('div')
                    if price_div_inner:
                        price = price_div_inner.text.strip()
                
                url =  listing_link['href']

                # Save to database
                save_listing(listing_id, title, price, url)
                
                # Add to new listings for notification
                new_listings.append({
                    'title': title,
                    'price': price,
                    'url': url
                })
                
                logging.info(f"New listing found: {title}")
            except Exception as e:
                logging.error(f"Error processing listing: {str(e)}")
                continue

        if new_listings:
            send_telegram_notification(new_listings)

    except Exception as e:
        logging.error(f"Error scraping listings: {str(e)}")

def main():
    setup_database()
    scrape_listings()

if __name__ == "__main__":
    main() 
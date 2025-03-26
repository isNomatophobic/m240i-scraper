import os
import logging
import sqlite3
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def setup_database():
    db_path = 'listings.db'
    logging.info(f"Setting up database at {os.path.abspath(db_path)}")
    
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS listings
            (id TEXT PRIMARY KEY,
             title TEXT,
             price TEXT,
             url TEXT,
             image_url TEXT,
             date_added TIMESTAMP)
        ''')
        conn.commit()
        conn.close()
        logging.info("Database setup completed successfully")
        
        # Verify the file exists and log its size
        if os.path.exists(db_path):
            size = os.path.getsize(db_path)
            logging.info(f"Database file created successfully. Size: {size} bytes")
        else:
            logging.error("Database file was not created!")
            
    except Exception as e:
        logging.error(f"Error setting up database: {str(e)}")
        raise

def get_existing_listings():
    db_path = 'listings.db'
    if not os.path.exists(db_path):
        logging.info(f"Database file does not exist at {os.path.abspath(db_path)}")
        setup_database()
        return set()
    
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute('SELECT id FROM listings')
        existing_ids = {row[0] for row in c.fetchall()}
        conn.close()
        logging.info(f"Found {len(existing_ids)} existing listings in database")
        
        # Log database file info
        size = os.path.getsize(db_path)
        logging.info(f"Current database size: {size} bytes")
        return existing_ids
        
    except Exception as e:
        logging.error(f"Error reading from database: {str(e)}")
        raise

def save_listing(listing_id, title, price, url, image_url):
    try:
        conn = sqlite3.connect('listings.db')
        c = conn.cursor()
        c.execute('''
            INSERT OR IGNORE INTO listings 
            (id, title, price, url, image_url, date_added)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (listing_id, title, price, url, image_url, datetime.now()))
        
        if c.rowcount > 0:
            logging.info(f"Successfully saved new listing: {title}")
        else:
            logging.debug(f"Listing already exists: {title}")
            
        conn.commit()
        conn.close()
    except Exception as e:
        logging.error(f"Error saving listing: {str(e)}")
        raise

def send_telegram_notification(new_listings):
    if not new_listings:
        return

    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    if not bot_token or not chat_id:
        logging.error("Telegram credentials not found in environment variables")
        raise Exception("Telegram credentials not found in environment variables")

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
                save_listing(listing_id, title, price, url, '')
                
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
    logging.info("Starting scraper...")
    
    # Load environment variables
    load_dotenv()
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    if not bot_token or not chat_id:
        logging.error("Telegram credentials not found in environment variables")
        return
    
    # Log current working directory and files
    logging.info(f"Current working directory: {os.getcwd()}")
    logging.info(f"Files in directory: {os.listdir('.')}")
    
    try:
        scrape_listings()
        
        # Log final database state
        if os.path.exists('listings.db'):
            size = os.path.getsize('listings.db')
            logging.info(f"Final database size: {size} bytes")
        else:
            logging.error("Database file not found after scraping!")
            
    except Exception as e:
        logging.error(f"Error during scraping: {str(e)}")
        raise

if __name__ == "__main__":
    main() 
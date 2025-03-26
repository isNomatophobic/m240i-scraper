import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_telegram_bot():
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    print(f"Bot Token: {bot_token[:5]}...")  # Only print first 5 chars for security
    print(f"Chat ID: {chat_id}")
    
    if not bot_token or not chat_id:
        print("Error: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not found in .env file")
        return
    
    # Test message
    message = "🔄 This is a test message from the BMW 240 Scraper"
    
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML"
        }
        response = requests.post(url, data=data)
        response.raise_for_status()
        print("✅ Test message sent successfully!")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"❌ Error sending message: {str(e)}")
        if hasattr(e, 'response'):
            print(f"Response content: {e.response.text}")

if __name__ == "__main__":
    test_telegram_bot() 
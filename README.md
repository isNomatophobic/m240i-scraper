# BMW 240 Mobile.bg Scraper

This script automatically scrapes BMW 240 listings from mobile.bg and sends email notifications when new listings are found.

## Features

- Scrapes BMW 240 listings from mobile.bg
- Stores listings in SQLite database
- Sends email notifications for new listings
- Runs automatically every hour using GitHub Actions
- Logs all activities and errors

## Setup

1. Fork this repository to your GitHub account

2. Set up environment variables in your GitHub repository:

   - Go to Settings > Secrets and variables > Actions
   - Add the following secrets:
     - `EMAIL_USER`: Your Gmail address
     - `EMAIL_PASSWORD`: Your Gmail app password (not your regular password)
     - `NOTIFICATION_EMAIL`: Email address where you want to receive notifications

3. Enable GitHub Actions:
   - Go to the Actions tab in your repository
   - Click "I understand my workflows, go ahead and enable them"

## Local Development

1. Clone the repository:

```bash
git clone <your-repo-url>
cd <repo-name>
```

2. Create a virtual environment and activate it:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Create a `.env` file with your email credentials:

```
EMAIL_USER=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
NOTIFICATION_EMAIL=your-notification-email@gmail.com
```

5. Run the scraper:

```bash
python scraper.py
```

## How it Works

- The scraper runs every hour using GitHub Actions
- It checks for new BMW 240 listings on mobile.bg
- New listings are stored in a SQLite database
- Email notifications are sent only for new listings
- All activities are logged to `scraper.log`

## Notes

- Make sure to use an App Password if you're using Gmail (regular passwords won't work)
- The database is stored as a GitHub Actions artifact
- The scraper respects rate limiting and includes proper headers
- All errors are logged and won't crash the script

## License

MIT License

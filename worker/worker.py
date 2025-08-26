import os
import time
import logging
import psycopg2
import yfinance as yf
import requests
from datetime import datetime, timedelta
from textblob import TextBlob
from bs4 import BeautifulSoup
import schedule

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://finance:financepass@localhost:5432/finance_db')
WORKER_INTERVAL = int(os.environ.get('WORKER_INTERVAL', 300))  # 5 minutes default

# Popular tickers to monitor
DEFAULT_TICKERS = [
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX', 
    'ADBE', 'CRM', 'ORCL', 'IBM', 'INTC', 'AMD', 'UBER', 'LYFT',
    'SPY', 'QQQ', 'IWM', 'GLD', 'SLV', 'TLT', 'VTI', 'VXUS'
]

def get_db_connection():
    """Get database connection"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return None

def fetch_news_sentiment(ticker, max_articles=5):
    """Fetch news articles and analyze sentiment for a given ticker"""
    try:
        # Simple news scraping from Yahoo Finance
        url = f"https://finance.yahoo.com/quote/{ticker}/news"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            logger.warning(f"Failed to fetch news for {ticker}: {response.status_code}")
            return []
            
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find news headlines (this selector might need adjustment based on Yahoo's current structure)
        headlines = []
        news_items = soup.find_all('h3', class_='Mb(5px)')[:max_articles]
        
        for item in news_items:
            headline = item.get_text(strip=True)
            if headline and len(headline) > 10:  # Filter out very short headlines
                # Analyze sentiment using TextBlob
                blob = TextBlob(headline)
                sentiment_score = blob.sentiment.polarity
                
                headlines.append({
                    'headline': headline,
                    'sentiment_score': sentiment_score,
                    'published_at': datetime.now()  # Simplified - in real app, extract actual date
                })
        
        return headlines
        
    except Exception as e:
        logger.error(f"Error fetching news for {ticker}: {e}")
        return []

def update_stock_data(ticker):
    """Update stock data in database"""
    try:
        # Fetch stock data
        stock = yf.Ticker(ticker)
        info = stock.info
        hist = stock.history(period="5d")  # Get recent data
        
        if hist.empty:
            logger.warning(f"No historical data for {ticker}")
            return False
            
        current_price = hist['Close'].iloc[-1]
        
        # Get basic metrics
        pe_ratio = info.get('trailingPE', 0) or 0
        market_cap = info.get('marketCap', 0) or 0
        company_name = info.get('longName', ticker)
        
        # Calculate simple scores (simplified version)
        garp_score = min(5, max(0, (3 if 0 < pe_ratio < 20 else 1)))
        growth_score = min(5, max(0, (3 if info.get('revenueGrowth', 0) > 0.1 else 1)))
        value_score = min(5, max(0, (3 if 0 < pe_ratio < 15 else 1)))
        
        # Update database
        conn = get_db_connection()
        if not conn:
            return False
            
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO stocks (ticker, company_name, current_price, pe_ratio, market_cap, 
                              garp_score, growth_score, value_score, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (ticker) DO UPDATE SET
                company_name = EXCLUDED.company_name,
                current_price = EXCLUDED.current_price,
                pe_ratio = EXCLUDED.pe_ratio,
                market_cap = EXCLUDED.market_cap,
                garp_score = EXCLUDED.garp_score,
                growth_score = EXCLUDED.growth_score,
                value_score = EXCLUDED.value_score,
                updated_at = EXCLUDED.updated_at
        """, (
            ticker,
            company_name,
            float(current_price),
            pe_ratio,
            market_cap,
            garp_score,
            growth_score,
            value_score,
            datetime.now()
        ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Updated stock data for {ticker}: ${current_price:.2f}")
        return True
        
    except Exception as e:
        logger.error(f"Error updating stock data for {ticker}: {e}")
        return False

def update_news_sentiment(ticker):
    """Update news sentiment for a ticker"""
    try:
        news_items = fetch_news_sentiment(ticker)
        
        if not news_items:
            logger.info(f"No news found for {ticker}")
            return False
            
        conn = get_db_connection()
        if not conn:
            return False
            
        cursor = conn.cursor()
        
        for item in news_items:
            # Check if this headline already exists
            cursor.execute("""
                SELECT id FROM news WHERE ticker = %s AND headline = %s
            """, (ticker, item['headline']))
            
            if cursor.fetchone():
                continue  # Skip duplicate headlines
                
            # Insert new news item
            cursor.execute("""
                INSERT INTO news (ticker, headline, sentiment_score, published_at)
                VALUES (%s, %s, %s, %s)
            """, (
                ticker,
                item['headline'],
                item['sentiment_score'],
                item['published_at']
            ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Updated {len(news_items)} news items for {ticker}")
        return True
        
    except Exception as e:
        logger.error(f"Error updating news sentiment for {ticker}: {e}")
        return False

def cleanup_old_data():
    """Clean up old data to prevent database bloat"""
    try:
        conn = get_db_connection()
        if not conn:
            return
            
        cursor = conn.cursor()
        
        # Remove news older than 30 days
        cutoff_date = datetime.now() - timedelta(days=30)
        cursor.execute("""
            DELETE FROM news WHERE published_at < %s
        """, (cutoff_date,))
        
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()
        
        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} old news items")
            
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")

def worker_job():
    """Main worker job - updates all stock data and news"""
    logger.info("Starting worker job...")
    
    # Get tickers from database, fall back to default list
    conn = get_db_connection()
    tickers = DEFAULT_TICKERS.copy()
    
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT ticker FROM stocks")
            db_tickers = [row[0] for row in cursor.fetchall()]
            # Combine database tickers with default ones
            tickers = list(set(tickers + db_tickers))
            conn.close()
        except Exception as e:
            logger.error(f"Error fetching tickers from database: {e}")
            if conn:
                conn.close()
    
    logger.info(f"Processing {len(tickers)} tickers...")
    
    # Update each ticker
    for ticker in tickers:
        try:
            logger.info(f"Processing {ticker}...")
            
            # Update stock data
            update_stock_data(ticker)
            
            # Update news sentiment
            update_news_sentiment(ticker)
            
            # Small delay to be respectful to APIs
            time.sleep(1)
            
        except Exception as e:
            logger.error(f"Error processing {ticker}: {e}")
            continue
    
    # Cleanup old data
    cleanup_old_data()
    
    logger.info("Worker job completed")

def main():
    """Main worker loop"""
    logger.info("Finance Data Worker starting...")
    logger.info(f"Worker interval: {WORKER_INTERVAL} seconds")
    
    # Run initial job
    worker_job()
    
    # Schedule recurring jobs
    schedule.every(WORKER_INTERVAL).seconds.do(worker_job)
    
    # Keep the worker running
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            logger.info("Worker stopped by user")
            break
        except Exception as e:
            logger.error(f"Unexpected error in worker loop: {e}")
            time.sleep(60)  # Wait before retrying

if __name__ == "__main__":
    main()
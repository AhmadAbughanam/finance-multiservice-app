from flask import Flask, jsonify, request
from flask_cors import CORS
import psycopg2
import psycopg2.extras
import yfinance as yf
import os
from datetime import datetime, timedelta
import logging
from textblob import TextBlob
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database connection
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://finance:financepass@localhost:5432/finance_db')

def get_db_connection():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return None

def calculate_screening_scores(ticker_data):
    """Calculate GARP, Growth, and Value scores for a stock"""
    try:
        info = ticker_data.info
        
        # Get basic metrics
        pe_ratio = info.get('trailingPE', 0) or 0
        peg_ratio = info.get('pegRatio', 0) or 0
        price_to_book = info.get('priceToBook', 0) or 0
        roe = info.get('returnOnEquity', 0) or 0
        debt_to_equity = info.get('debtToEquity', 0) or 0
        revenue_growth = info.get('revenueGrowth', 0) or 0
        
        # GARP Score (Growth at Reasonable Price)
        garp_score = 0
        if 0 < pe_ratio < 20 and 0 < peg_ratio < 1.5:
            garp_score += 3
        elif 0 < pe_ratio < 25 and 0 < peg_ratio < 2:
            garp_score += 2
        elif pe_ratio > 0 and peg_ratio > 0:
            garp_score += 1
            
        if revenue_growth > 0.1:  # 10% revenue growth
            garp_score += 2
        elif revenue_growth > 0.05:
            garp_score += 1
            
        # Growth Score
        growth_score = 0
        if revenue_growth > 0.15:  # 15%+ growth
            growth_score += 3
        elif revenue_growth > 0.1:
            growth_score += 2
        elif revenue_growth > 0.05:
            growth_score += 1
            
        if roe > 0.15:  # 15%+ ROE
            growth_score += 2
        elif roe > 0.1:
            growth_score += 1
            
        # Value Score
        value_score = 0
        if 0 < pe_ratio < 15:
            value_score += 3
        elif 0 < pe_ratio < 20:
            value_score += 2
        elif 0 < pe_ratio < 25:
            value_score += 1
            
        if 0 < price_to_book < 1.5:
            value_score += 2
        elif 0 < price_to_book < 2.5:
            value_score += 1
            
        return {
            'garp_score': min(garp_score, 5),
            'growth_score': min(growth_score, 5), 
            'value_score': min(value_score, 5),
            'pe_ratio': pe_ratio,
            'peg_ratio': peg_ratio,
            'price_to_book': price_to_book,
            'roe': roe,
            'revenue_growth': revenue_growth
        }
    except Exception as e:
        logger.error(f"Error calculating screening scores: {e}")
        return {
            'garp_score': 0,
            'growth_score': 0,
            'value_score': 0,
            'pe_ratio': 0,
            'peg_ratio': 0,
            'price_to_book': 0,
            'roe': 0,
            'revenue_growth': 0
        }

@app.route('/health')
def health_check():
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

@app.route('/screen/<ticker>')
def screen_stock(ticker):
    """Screen a stock using GARP, Growth, and Value strategies"""
    try:
        # Fetch stock data
        stock = yf.Ticker(ticker.upper())
        
        # Get stock info and historical data
        info = stock.info
        hist = stock.history(period="1y")
        
        if hist.empty:
            return jsonify({"error": "No data found for ticker"}), 404
            
        # Calculate screening scores
        scores = calculate_screening_scores(stock)
        
        # Get current price
        current_price = hist['Close'].iloc[-1] if not hist.empty else 0
        
        # Calculate 52-week high/low
        week_52_high = hist['High'].max()
        week_52_low = hist['Low'].min()
        
        # Store in database
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO stocks (ticker, company_name, current_price, pe_ratio, market_cap, 
                                      garp_score, growth_score, value_score, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (ticker) DO UPDATE SET
                        current_price = EXCLUDED.current_price,
                        pe_ratio = EXCLUDED.pe_ratio,
                        market_cap = EXCLUDED.market_cap,
                        garp_score = EXCLUDED.garp_score,
                        growth_score = EXCLUDED.growth_score,
                        value_score = EXCLUDED.value_score,
                        updated_at = EXCLUDED.updated_at
                """, (
                    ticker.upper(),
                    info.get('longName', ticker.upper()),
                    float(current_price),
                    scores['pe_ratio'],
                    info.get('marketCap', 0),
                    scores['garp_score'],
                    scores['growth_score'],
                    scores['value_score'],
                    datetime.now()
                ))
                conn.commit()
            except Exception as e:
                logger.error(f"Database insert error: {e}")
            finally:
                conn.close()
        
        return jsonify({
            "ticker": ticker.upper(),
            "company_name": info.get('longName', ticker.upper()),
            "current_price": round(current_price, 2),
            "52_week_high": round(week_52_high, 2),
            "52_week_low": round(week_52_low, 2),
            "scores": scores,
            "recommendation": get_recommendation(scores),
            "last_updated": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error screening {ticker}: {e}")
        return jsonify({"error": str(e)}), 500

def get_recommendation(scores):
    """Get investment recommendation based on scores"""
    total_score = scores['garp_score'] + scores['growth_score'] + scores['value_score']
    
    if total_score >= 12:
        return {"rating": "Strong Buy", "confidence": "High"}
    elif total_score >= 9:
        return {"rating": "Buy", "confidence": "Medium"}
    elif total_score >= 6:
        return {"rating": "Hold", "confidence": "Low"}
    else:
        return {"rating": "Sell", "confidence": "Low"}

@app.route('/sentiment/<ticker>')
def get_sentiment(ticker):
    """Get sentiment analysis for a stock"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
            
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("""
            SELECT headline, sentiment_score, published_at 
            FROM news 
            WHERE ticker = %s 
            ORDER BY published_at DESC 
            LIMIT 10
        """, (ticker.upper(),))
        
        news_items = cursor.fetchall()
        conn.close()
        
        if not news_items:
            return jsonify({
                "ticker": ticker.upper(),
                "sentiment": {
                    "overall_score": 0,
                    "sentiment_label": "Neutral",
                    "news_count": 0
                },
                "recent_news": []
            })
        
        # Calculate overall sentiment
        total_sentiment = sum(item['sentiment_score'] for item in news_items)
        avg_sentiment = total_sentiment / len(news_items)
        
        # Determine sentiment label
        if avg_sentiment > 0.1:
            sentiment_label = "Positive"
        elif avg_sentiment < -0.1:
            sentiment_label = "Negative"
        else:
            sentiment_label = "Neutral"
        
        return jsonify({
            "ticker": ticker.upper(),
            "sentiment": {
                "overall_score": round(avg_sentiment, 3),
                "sentiment_label": sentiment_label,
                "news_count": len(news_items)
            },
            "recent_news": [
                {
                    "headline": item['headline'],
                    "sentiment_score": round(item['sentiment_score'], 3),
                    "published_at": item['published_at'].isoformat() if item['published_at'] else None
                }
                for item in news_items
            ]
        })
        
    except Exception as e:
        logger.error(f"Error getting sentiment for {ticker}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/data/<ticker>')
def get_stock_data(ticker):
    """Retrieve stored stock data from database"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
            
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("""
            SELECT * FROM stocks WHERE ticker = %s
        """, (ticker.upper(),))
        
        stock_data = cursor.fetchone()
        conn.close()
        
        if not stock_data:
            return jsonify({"error": "No data found for ticker"}), 404
        
        # Convert datetime to string for JSON serialization
        if stock_data['updated_at']:
            stock_data['updated_at'] = stock_data['updated_at'].isoformat()
            
        return jsonify(dict(stock_data))
        
    except Exception as e:
        logger.error(f"Error retrieving data for {ticker}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/stocks')
def get_all_stocks():
    """Get all stocks in database"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
            
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("""
            SELECT ticker, company_name, current_price, garp_score, 
                   growth_score, value_score, updated_at
            FROM stocks 
            ORDER BY updated_at DESC
        """)
        
        stocks = cursor.fetchall()
        conn.close()
        
        # Convert datetime to string
        for stock in stocks:
            if stock['updated_at']:
                stock['updated_at'] = stock['updated_at'].isoformat()
                
        return jsonify(stocks)
        
    except Exception as e:
        logger.error(f"Error retrieving all stocks: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
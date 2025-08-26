-- Initialize the finance database

-- Create stocks table
CREATE TABLE IF NOT EXISTS stocks (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) UNIQUE NOT NULL,
    company_name VARCHAR(255),
    current_price DECIMAL(10, 2),
    pe_ratio DECIMAL(10, 2),
    market_cap BIGINT,
    garp_score INTEGER DEFAULT 0,
    growth_score INTEGER DEFAULT 0,
    value_score INTEGER DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create news table for sentiment analysis
CREATE TABLE IF NOT EXISTS news (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    headline TEXT NOT NULL,
    sentiment_score DECIMAL(5, 3),
    published_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_stocks_ticker ON stocks(ticker);
CREATE INDEX IF NOT EXISTS idx_stocks_updated_at ON stocks(updated_at);
CREATE INDEX IF NOT EXISTS idx_news_ticker ON news(ticker);
CREATE INDEX IF NOT EXISTS idx_news_published_at ON news(published_at);

-- Create unique constraint to prevent duplicate news
CREATE UNIQUE INDEX IF NOT EXISTS idx_news_unique ON news(ticker, headline);

-- Insert some sample data
INSERT INTO stocks (ticker, company_name, current_price, pe_ratio, market_cap, garp_score, growth_score, value_score) 
VALUES 
    ('AAPL', 'Apple Inc.', 175.00, 28.5, 2750000000000, 4, 3, 2),
    ('MSFT', 'Microsoft Corporation', 338.00, 35.2, 2510000000000, 3, 4, 2),
    ('GOOGL', 'Alphabet Inc.', 125.00, 22.1, 1580000000000, 4, 4, 3),
    ('AMZN', 'Amazon.com Inc.', 145.00, 52.8, 1500000000000, 2, 5, 1),
    ('TSLA', 'Tesla Inc.', 248.00, 75.4, 780000000000, 2, 5, 1)
ON CONFLICT (ticker) DO NOTHING;

-- Insert some sample news
INSERT INTO news (ticker, headline, sentiment_score) 
VALUES 
    ('AAPL', 'Apple Reports Strong Quarterly Earnings Beat Expectations', 0.8),
    ('AAPL', 'Apple Announces New iPhone with Revolutionary Features', 0.6),
    ('MSFT', 'Microsoft Azure Cloud Revenue Surges 30% Year Over Year', 0.7),
    ('GOOGL', 'Google AI Breakthrough Could Transform Search Experience', 0.5),
    ('AMZN', 'Amazon Prime Day Sales Hit Record High This Year', 0.6),
    ('TSLA', 'Tesla Delivers Record Number of Vehicles in Q3', 0.4)
ON CONFLICT DO NOTHING;
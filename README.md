# 📈 Finance Multi-Service App (Dockerized)

A comprehensive containerized system for analyzing stock market data, applying screening strategies, and providing sentiment insights from financial news.

## 🌟 Features

- **Multi-container orchestration** with Docker Compose
- **Modular architecture** (backend, worker, database, dashboard)
- **Real-time stock screening** (GARP, Growth, Value strategies)
- **Sentiment analysis** from financial news
- **Interactive dashboard** with data visualizations
- **Automated data collection** via background worker

## 🏗️ Architecture

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│  Dashboard  │───▶│  Backend API │───▶│  Database   │
│ (Streamlit) │    │   (Flask)    │    │(PostgreSQL) │
└─────────────┘    └──────────────┘    └─────────────┘
                           │                    ▲
                           ▼                    │
                   ┌──────────────┐             │
                   │    Worker    │─────────────┘
                   │  (Python)    │
                   └──────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Docker
- Docker Compose
- Git

### Installation & Setup

1. **Clone the repository**

   ```bash
   git clone <your-repo-url>
   cd finance-multiservice-app
   ```

2. **Build and start all services**

   ```bash
   docker-compose up --build
   ```

3. **Access the services**
   - **Dashboard**: http://localhost:8501
   - **Backend API**: http://localhost:5000
   - **Database**: localhost:5432

### First Run

The system will automatically:

- Initialize the PostgreSQL database with sample data
- Start collecting real-time stock data via the worker service
- Make the interactive dashboard available

## 📁 Project Structure

```
finance-multiservice-app/
├── backend/
│   ├── app.py              # Flask API server
│   ├── Dockerfile          # Backend container config
│   └── requirements.txt    # Python dependencies
├── worker/
│   ├── worker.py           # Data collection service
│   ├── Dockerfile          # Worker container config
│   └── requirements.txt    # Python dependencies
├── dashboard/
│   ├── dashboard.py        # Streamlit dashboard
│   ├── Dockerfile          # Dashboard container config
│   └── requirements.txt    # Python dependencies
├── docker-compose.yml      # Service orchestration
├── init.sql               # Database initialization
└── README.md              # This file
```

## 🔧 Services

### 1. Backend API (Flask)

**Port**: 5000

**Endpoints**:

- `GET /health` - Health check
- `GET /screen/<ticker>` - Screen stock with GARP, Growth, Value strategies
- `GET /sentiment/<ticker>` - Get sentiment analysis for stock
- `GET /data/<ticker>` - Retrieve stored stock data
- `GET /stocks` - Get all stocks in database

### 2. Data Worker

**Background service** that:

- Fetches stock data from Yahoo Finance API
- Scrapes financial news headlines
- Performs sentiment analysis using TextBlob
- Updates database every 5 minutes (configurable)
- Cleans up old data automatically

### 3. Database (PostgreSQL)

**Port**: 5432

**Tables**:

- `stocks` - Stock data and screening scores
- `news` - News headlines and sentiment scores

### 4. Dashboard (Streamlit)

**Port**: 8501

**Pages**:

- **Market Overview** - Key metrics and top performers
- **Stock Screener** - Interactive stock analysis
- **Sentiment Analysis** - News sentiment tracking
- **Portfolio View** - Portfolio building and comparison

## 🎯 Usage Examples

### Screen a Stock

```bash
curl http://localhost:5000/screen/AAPL
```

### Get Sentiment Data

```bash
curl http://localhost:5000/sentiment/TSLA
```

### View All Stocks

```bash
curl http://localhost:5000/stocks
```

## 🔧 Configuration

### Environment Variables

**Backend & Worker**:

- `DATABASE_URL` - PostgreSQL connection string
- `FLASK_ENV` - Flask environment (development/production)

**Worker**:

- `WORKER_INTERVAL` - Data collection interval in seconds (default: 300)

**Dashboard**:

- `BACKEND_URL` - Backend API URL (default: http://backend:5000)

### Customizing Stock List

The worker monitors a default list of popular stocks. To customize:

1. Edit `DEFAULT_TICKERS` in `worker/worker.py`
2. Or add stocks via the dashboard - they'll be automatically monitored

## 📊 Investment Scoring

### GARP (Growth at Reasonable Price)

- **5 points**: PE < 20, PEG < 1.5, Revenue Growth > 15%
- **4 points**: PE < 25, PEG < 2, Revenue Growth > 10%
- **Lower scores**: Less attractive GARP metrics

### Growth Score

- **5 points**: Revenue Growth > 15%, ROE > 15%
- **4 points**: Revenue Growth > 10%, ROE > 10%
- **Lower scores**: Lower growth metrics

### Value Score

- **5 points**: PE < 15, P/B < 1.5
- **4 points**: PE < 20, P/B < 2.5
- **Lower scores**: Higher valuation ratios

## 🧪 Development

### Running Individual Services

**Backend only**:

```bash
cd backend
pip install -r requirements.txt
python app.py
```

**Worker only**:

```bash
cd worker
pip install -r requirements.txt
python worker.py
```

**Dashboard only**:

```bash
cd dashboard
pip install -r requirements.txt
streamlit run dashboard.py
```

### Adding New Features

1. **New API endpoints**: Add to `backend/app.py`
2. **New data sources**: Modify `worker/worker.py`
3. **New dashboard pages**: Extend `dashboard/dashboard.py`
4. **Database changes**: Update `init.sql`

## 🚀 Deployment

### Local Development

```bash
docker-compose up --build
```

### Production Deployment

```bash
# Use production override file
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Cloud Deployment

The project is ready for deployment on:

- **AWS ECS/Fargate**
- **Azure Container Instances**
- **Google Cloud Run**
- **DigitalOcean App Platform**

## 📈 Future Enhancements

- [ ] **Authentication & Authorization** (JWT tokens)
- [ ] **Machine Learning Predictions** (stock trend classifier)
- [ ] **Real-time WebSocket Updates** for live data
- [ ] **Advanced Technical Analysis** (RSI, MACD, Bollinger Bands)
- [ ] **Portfolio Backtesting** with historical performance
- [ ] **Alert System** for price/sentiment thresholds
- [ ] **API Rate Limiting** and caching with Redis
- [ ] **Data Export** (CSV, Excel, PDF reports)
- [ ] **Mobile-responsive Design** improvements
- [ ] **Integration with Brokers** (paper trading)

## 🛠️ Troubleshooting

### Common Issues

**Services won't start**:

```bash
# Check if ports are already in use
netstat -tulpn | grep -E ':(5000|5432|8501)'

# Stop conflicting services
docker-compose down
docker system prune -f
```

**Database connection errors**:

```bash
# Wait for database to fully initialize
docker-compose logs db

# Reset database
docker-compose down -v
docker-compose up --build
```

**Worker not collecting data**:

```bash
# Check worker logs
docker-compose logs worker

# Restart worker service
docker-compose restart worker
```

**Dashboard shows no data**:

- Wait 5-10 minutes for worker to collect initial data
- Check backend API is responding: `curl http://localhost:5000/stocks`

### Performance Optimization

**For better performance**:

```yaml
# Add to docker-compose.yml services
deploy:
  resources:
    limits:
      memory: 512M
    reservations:
      memory: 256M
```

**Database optimization**:

```sql
-- Add indexes for better query performance
CREATE INDEX CONCURRENTLY idx_stocks_scores ON stocks(garp_score, growth_score, value_score);
CREATE INDEX CONCURRENTLY idx_news_sentiment ON news(sentiment_score, published_at);
```

## 🔐 Security Considerations

### Production Security Checklist

- [ ] Change default database credentials
- [ ] Use environment files for secrets
- [ ] Enable SSL/TLS for external connections
- [ ] Implement API rate limiting
- [ ] Add input validation and sanitization
- [ ] Regular security updates for base images
- [ ] Network isolation between services
- [ ] Monitor and log security events

### Environment Variables for Production

```bash
# Create .env file
DATABASE_URL=postgresql://secure_user:strong_password@db:5432/finance_db
FLASK_SECRET_KEY=your-secret-key-here
FLASK_ENV=production
```

## 📋 API Reference

### Stock Screening Response

```json
{
  "ticker": "AAPL",
  "company_name": "Apple Inc.",
  "current_price": 175.43,
  "52_week_high": 198.23,
  "52_week_low": 124.17,
  "scores": {
    "garp_score": 4,
    "growth_score": 3,
    "value_score": 2,
    "pe_ratio": 28.5,
    "peg_ratio": 1.4,
    "price_to_book": 5.2,
    "roe": 0.26,
    "revenue_growth": 0.08
  },
  "recommendation": {
    "rating": "Buy",
    "confidence": "Medium"
  },
  "last_updated": "2025-01-15T10:30:00"
}
```

### Sentiment Analysis Response

```json
{
  "ticker": "AAPL",
  "sentiment": {
    "overall_score": 0.245,
    "sentiment_label": "Positive",
    "news_count": 8
  },
  "recent_news": [
    {
      "headline": "Apple Reports Strong Q4 Earnings",
      "sentiment_score": 0.8,
      "published_at": "2025-01-15T09:00:00"
    }
  ]
}
```

## 🤝 Contributing

### Development Setup

```bash
# Fork and clone the repo
git clone https://github.com/yourusername/finance-multiservice-app.git

# Create feature branch
git checkout -b feature/amazing-feature

# Make your changes and test
docker-compose up --build

# Commit and push
git commit -m "Add amazing feature"
git push origin feature/amazing-feature

# Create Pull Request
```

### Code Style

- Follow PEP 8 for Python code
- Use meaningful variable names
- Add docstrings for functions
- Include error handling
- Write tests for new features

### Testing

```bash
# Run backend tests
cd backend
python -m pytest tests/

# Test API endpoints
curl -X GET http://localhost:5000/health
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Yahoo Finance API** for stock data
- **TextBlob** for sentiment analysis
- **Streamlit** for the dashboard framework
- **Docker** for containerization
- **PostgreSQL** for robust data storage

## 📞 Support

If you encounter any issues or have questions:

1. Check the [Troubleshooting](#troubleshooting) section
2. Review the logs: `docker-compose logs [service-name]`
3. Open an issue on GitHub
4. Contact the maintainers

## 🎯 Project Goals Achieved

✅ **Multi-service Architecture**: Demonstrates microservices with Docker  
✅ **Real-time Data Processing**: Automated data collection and analysis  
✅ **Interactive Visualization**: User-friendly dashboard with charts  
✅ **Financial Analysis**: Multiple investment screening strategies  
✅ **Sentiment Analysis**: NLP integration for market sentiment  
✅ **Database Integration**: Persistent data storage and retrieval  
✅ **API Development**: RESTful API with comprehensive endpoints  
✅ **Containerization**: Full Docker deployment with orchestration

---

**Ready to analyze the markets! 📊💰**

Start exploring stocks, building portfolios, and making data-driven investment decisions with your new Finance Multi-Service App!

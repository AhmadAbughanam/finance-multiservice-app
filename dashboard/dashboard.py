import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import time

# Page configuration
st.set_page_config(
    page_title="Finance Multi-Service Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuration
BACKEND_URL = st.secrets.get("BACKEND_URL", "http://backend:5000")

@st.cache_data(ttl=60)
def fetch_all_stocks():
    """Fetch all stocks from backend API"""
    try:
        response = requests.get(f"{BACKEND_URL}/stocks", timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to fetch stocks: {response.status_code}")
            return []
    except Exception as e:
        st.error(f"Error connecting to backend: {e}")
        return []

def fetch_stock_screening(ticker):
    """Fetch stock screening data"""
    try:
        response = requests.get(f"{BACKEND_URL}/screen/{ticker}", timeout=15)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        st.error(f"Error screening {ticker}: {e}")
        return None

def fetch_sentiment_data(ticker):
    """Fetch sentiment data for a ticker"""
    try:
        response = requests.get(f"{BACKEND_URL}/sentiment/{ticker}", timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        st.error(f"Error fetching sentiment for {ticker}: {e}")
        return None

def create_score_gauge(score, title, max_score=5):
    """Create a gauge chart for scores"""
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = score,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': title},
        gauge = {
            'axis': {'range': [None, max_score]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 2], 'color': "lightgray"},
                {'range': [2, 4], 'color': "gray"},
                {'range': [4, max_score], 'color': "lightgreen"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': max_score * 0.9
            }
        }
    ))
    fig.update_layout(height=200)
    return fig

def main():
    """Main dashboard application"""
    
    # Header
    st.title("📈 Finance Multi-Service Dashboard")
    st.markdown("---")
    
    # Sidebar
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Choose a page:",
        ["Market Overview", "Stock Screener", "Sentiment Analysis", "Portfolio View"]
    )
    
    if page == "Market Overview":
        show_market_overview()
    elif page == "Stock Screener":
        show_stock_screener()
    elif page == "Sentiment Analysis":
        show_sentiment_analysis()
    elif page == "Portfolio View":
        show_portfolio_view()

def show_market_overview():
    """Show market overview page"""
    st.header("📊 Market Overview")
    
    # Fetch all stocks
    stocks = fetch_all_stocks()
    
    if not stocks:
        st.warning("No stock data available. The worker service might still be collecting data.")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(stocks)
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Stocks", len(df))
    
    with col2:
        avg_garp = df['garp_score'].mean() if 'garp_score' in df.columns else 0
        st.metric("Avg GARP Score", f"{avg_garp:.2f}")
    
    with col3:
        avg_growth = df['growth_score'].mean() if 'growth_score' in df.columns else 0
        st.metric("Avg Growth Score", f"{avg_growth:.2f}")
    
    with col4:
        avg_value = df['value_score'].mean() if 'value_score' in df.columns else 0
        st.metric("Avg Value Score", f"{avg_value:.2f}")
    
    st.markdown("---")
    
    # Top performers
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🏆 Top GARP Stocks")
        if 'garp_score' in df.columns:
            top_garp = df.nlargest(5, 'garp_score')[['ticker', 'company_name', 'current_price', 'garp_score']]
            st.dataframe(top_garp, hide_index=True)
    
    with col2:
        st.subheader("📈 Top Growth Stocks")
        if 'growth_score' in df.columns:
            top_growth = df.nlargest(5, 'growth_score')[['ticker', 'company_name', 'current_price', 'growth_score']]
            st.dataframe(top_growth, hide_index=True)
    
    # Score distribution charts
    st.subheader("📊 Score Distributions")
    
    if len(df) > 0:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if 'garp_score' in df.columns:
                fig = px.histogram(df, x='garp_score', title='GARP Score Distribution', 
                                 color_discrete_sequence=['#1f77b4'])
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            if 'growth_score' in df.columns:
                fig = px.histogram(df, x='growth_score', title='Growth Score Distribution',
                                 color_discrete_sequence=['#ff7f0e'])
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)
        
        with col3:
            if 'value_score' in df.columns:
                fig = px.histogram(df, x='value_score', title='Value Score Distribution',
                                 color_discrete_sequence=['#2ca02c'])
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)
    
    # Full data table
    st.subheader("📋 All Stocks")
    if len(df) > 0:
        # Format the dataframe for display
        display_df = df.copy()
        if 'current_price' in display_df.columns:
            display_df['current_price'] = display_df['current_price'].apply(lambda x: f"${x:.2f}")
        if 'updated_at' in display_df.columns:
            display_df['updated_at'] = pd.to_datetime(display_df['updated_at']).dt.strftime('%Y-%m-%d %H:%M')
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)

def show_stock_screener():
    """Show stock screener page"""
    st.header("🔍 Stock Screener")
    
    # Input section
    col1, col2 = st.columns([2, 1])
    
    with col1:
        ticker = st.text_input("Enter Stock Ticker:", value="AAPL", help="e.g., AAPL, MSFT, GOOGL")
    
    with col2:
        if st.button("🔍 Screen Stock", type="primary"):
            if ticker:
                with st.spinner(f"Screening {ticker.upper()}..."):
                    result = fetch_stock_screening(ticker.upper())
                    
                if result:
                    st.session_state['screening_result'] = result
                else:
                    st.error("Failed to screen stock. Please check the ticker symbol.")
    
    # Display results
    if 'screening_result' in st.session_state:
        result = st.session_state['screening_result']
        
        st.markdown("---")
        st.subheader(f"📊 Screening Results: {result['ticker']}")
        
        # Basic info
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Company", result.get('company_name', 'N/A'))
        
        with col2:
            st.metric("Current Price", f"${result.get('current_price', 0):.2f}")
        
        with col3:
            st.metric("52W High", f"${result.get('52_week_high', 0):.2f}")
        
        with col4:
            st.metric("52W Low", f"${result.get('52_week_low', 0):.2f}")
        
        # Scores section
        st.subheader("📈 Investment Scores")
        
        scores = result.get('scores', {})
        col1, col2, col3 = st.columns(3)
        
        with col1:
            fig_garp = create_score_gauge(scores.get('garp_score', 0), "GARP Score")
            st.plotly_chart(fig_garp, use_container_width=True)
        
        with col2:
            fig_growth = create_score_gauge(scores.get('growth_score', 0), "Growth Score")
            st.plotly_chart(fig_growth, use_container_width=True)
        
        with col3:
            fig_value = create_score_gauge(scores.get('value_score', 0), "Value Score")
            st.plotly_chart(fig_value, use_container_width=True)
        
        # Financial metrics
        st.subheader("💰 Financial Metrics")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            pe_ratio = scores.get('pe_ratio', 0)
            st.metric("P/E Ratio", f"{pe_ratio:.2f}" if pe_ratio > 0 else "N/A")
        
        with col2:
            peg_ratio = scores.get('peg_ratio', 0)
            st.metric("PEG Ratio", f"{peg_ratio:.2f}" if peg_ratio > 0 else "N/A")
        
        with col3:
            pb_ratio = scores.get('price_to_book', 0)
            st.metric("P/B Ratio", f"{pb_ratio:.2f}" if pb_ratio > 0 else "N/A")
        
        with col4:
            roe = scores.get('roe', 0)
            st.metric("ROE", f"{roe*100:.1f}%" if roe > 0 else "N/A")
        
        # Recommendation
        recommendation = result.get('recommendation', {})
        if recommendation:
            st.subheader("💡 Investment Recommendation")
            
            col1, col2 = st.columns(2)
            
            with col1:
                rating = recommendation.get('rating', 'N/A')
                color = {
                    'Strong Buy': 'success',
                    'Buy': 'success', 
                    'Hold': 'warning',
                    'Sell': 'error'
                }.get(rating, 'info')
                
                st.success(f"**Rating:** {rating}")
            
            with col2:
                confidence = recommendation.get('confidence', 'N/A')
                st.info(f"**Confidence:** {confidence}")

def show_sentiment_analysis():
    """Show sentiment analysis page"""
    st.header("😊 Sentiment Analysis")
    
    # Input section
    col1, col2 = st.columns([2, 1])
    
    with col1:
        ticker = st.text_input("Enter Stock Ticker for Sentiment:", value="AAPL")
    
    with col2:
        if st.button("📰 Get Sentiment", type="primary"):
            if ticker:
                with st.spinner(f"Analyzing sentiment for {ticker.upper()}..."):
                    result = fetch_sentiment_data(ticker.upper())
                    
                if result:
                    st.session_state['sentiment_result'] = result
                else:
                    st.error("Failed to fetch sentiment data.")
    
    # Display results
    if 'sentiment_result' in st.session_state:
        result = st.session_state['sentiment_result']
        
        st.markdown("---")
        st.subheader(f"📰 Sentiment Analysis: {result['ticker']}")
        
        sentiment = result.get('sentiment', {})
        
        # Overall sentiment metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            overall_score = sentiment.get('overall_score', 0)
            st.metric("Overall Sentiment", f"{overall_score:.3f}")
        
        with col2:
            sentiment_label = sentiment.get('sentiment_label', 'Neutral')
            color = {
                'Positive': '🟢',
                'Negative': '🔴',
                'Neutral': '🟡'
            }.get(sentiment_label, '⚪')
            st.metric("Sentiment", f"{color} {sentiment_label}")
        
        with col3:
            news_count = sentiment.get('news_count', 0)
            st.metric("News Articles", news_count)
        
        # Sentiment gauge
        if overall_score != 0:
            st.subheader("📊 Sentiment Score")
            fig = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = overall_score,
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "Sentiment Score"},
                gauge = {
                    'axis': {'range': [-1, 1]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [-1, -0.1], 'color': "lightcoral"},
                        {'range': [-0.1, 0.1], 'color': "lightyellow"},
                        {'range': [0.1, 1], 'color': "lightgreen"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 0.5
                    }
                }
            ))
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        # Recent news
        recent_news = result.get('recent_news', [])
        if recent_news:
            st.subheader("📰 Recent News Headlines")
            
            for i, news in enumerate(recent_news):
                with st.expander(f"News {i+1}: {news['headline'][:100]}..."):
                    st.write(f"**Headline:** {news['headline']}")
                    st.write(f"**Sentiment Score:** {news['sentiment_score']:.3f}")
                    st.write(f"**Published:** {news.get('published_at', 'Unknown')}")

def show_portfolio_view():
    """Show portfolio view page"""
    st.header("💼 Portfolio View")
    
    # Get all stocks for portfolio simulation
    stocks = fetch_all_stocks()
    
    if not stocks:
        st.warning("No stock data available for portfolio analysis.")
        return
    
    df = pd.DataFrame(stocks)
    
    st.subheader("🎯 Portfolio Builder")
    st.write("Select stocks to build a hypothetical portfolio:")
    
    # Multi-select for stocks
    if 'ticker' in df.columns:
        selected_tickers = st.multiselect(
            "Choose stocks for your portfolio:",
            options=df['ticker'].tolist(),
            default=df['ticker'].head(5).tolist() if len(df) >= 5 else df['ticker'].tolist()
        )
        
        if selected_tickers:
            # Filter selected stocks
            portfolio_df = df[df['ticker'].isin(selected_tickers)].copy()
            
            # Portfolio metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_value = portfolio_df['current_price'].sum()
                st.metric("Total Portfolio Value", f"${total_value:.2f}")
            
            with col2:
                avg_garp = portfolio_df['garp_score'].mean()
                st.metric("Avg GARP Score", f"{avg_garp:.2f}")
            
            with col3:
                avg_growth = portfolio_df['growth_score'].mean()
                st.metric("Avg Growth Score", f"{avg_growth:.2f}")
            
            with col4:
                avg_value = portfolio_df['value_score'].mean()
                st.metric("Avg Value Score", f"{avg_value:.2f}")
            
            # Portfolio composition
            st.subheader("📊 Portfolio Composition")
            
            # Pie chart by value
            fig = px.pie(portfolio_df, values='current_price', names='ticker', 
                        title='Portfolio Allocation by Stock Price')
            st.plotly_chart(fig, use_container_width=True)
            
            # Score comparison
            st.subheader("📈 Score Comparison")
            
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                name='GARP Score',
                x=portfolio_df['ticker'],
                y=portfolio_df['garp_score']
            ))
            
            fig.add_trace(go.Bar(
                name='Growth Score',
                x=portfolio_df['ticker'],
                y=portfolio_df['growth_score']
            ))
            
            fig.add_trace(go.Bar(
                name='Value Score',
                x=portfolio_df['ticker'],
                y=portfolio_df['value_score']
            ))
            
            fig.update_layout(barmode='group', title='Investment Scores by Stock')
            st.plotly_chart(fig, use_container_width=True)
            
            # Portfolio table
            st.subheader("📋 Portfolio Holdings")
            display_df = portfolio_df[['ticker', 'company_name', 'current_price', 
                                     'garp_score', 'growth_score', 'value_score']].copy()
            display_df['current_price'] = display_df['current_price'].apply(lambda x: f"${x:.2f}")
            st.dataframe(display_df, use_container_width=True, hide_index=True)

if __name__ == "__main__":
    main()
from flask import Flask, render_template, request, jsonify
import requests
from config import Config
import yfinance as yf
from datetime import datetime, timedelta
import pandas as pd

app = Flask(__name__)
app.config.from_object(Config)

# Popular stocks for easy access
POPULAR_STOCKS = {
    # Technology
    'AAPL': 'Apple Inc.',
    'MSFT': 'Microsoft Corporation',
    'GOOGL': 'Alphabet Inc.',
    'AMZN': 'Amazon.com Inc.',
    'META': 'Meta Platforms Inc.',
    'NVDA': 'NVIDIA Corporation',
    'AMD': 'Advanced Micro Devices',
    'INTC': 'Intel Corporation',
    'CRM': 'Salesforce Inc.',
    'ADBE': 'Adobe Inc.',
    
    # Electric Vehicles & Clean Energy
    'TSLA': 'Tesla Inc.',
    'NIO': 'NIO Inc.',
    'RIVN': 'Rivian Automotive',
    'PLUG': 'Plug Power Inc.',
    'ENPH': 'Enphase Energy',
    
    # Financial Services
    'JPM': 'JPMorgan Chase & Co.',
    'V': 'Visa Inc.',
    'MA': 'Mastercard Inc.',
    'PYPL': 'PayPal Holdings',
    'SQ': 'Block Inc.',
    'GS': 'Goldman Sachs Group',
    'MS': 'Morgan Stanley',
    'AXP': 'American Express',
    
    # Consumer Goods & Retail
    'WMT': 'Walmart Inc.',
    'MCD': "McDonald's Corporation",
    'NKE': 'Nike Inc.',
    'KO': 'The Coca-Cola Company',
    'PEP': 'PepsiCo Inc.',
    'DIS': 'The Walt Disney Company',
    'NFLX': 'Netflix Inc.',
    'SBUX': 'Starbucks Corporation',
    
    # Healthcare & Biotech
    'JNJ': 'Johnson & Johnson',
    'PFE': 'Pfizer Inc.',
    'MRNA': 'Moderna Inc.',
    'ABBV': 'AbbVie Inc.',
    'UNH': 'UnitedHealth Group',
    
    # Industrial & Manufacturing
    'CAT': 'Caterpillar Inc.',
    'BA': 'Boeing Co.',
    'GE': 'General Electric',
    'MMM': '3M Company',
    'HON': 'Honeywell International',
    
    # Telecommunications
    'VZ': 'Verizon Communications',
    'T': 'AT&T Inc.',
    'TMUS': 'T-Mobile US',
    'CMCSA': 'Comcast Corporation',
    
    # Energy
    'XOM': 'Exxon Mobil Corporation',
    'CVX': 'Chevron Corporation',
    'COP': 'ConocoPhillips',
    'SLB': 'Schlumberger Limited',
    
    # Real Estate
    'AMT': 'American Tower Corporation',
    'PLD': 'Prologis Inc.',
    'EQIX': 'Equinix Inc.',
    
    # Materials
    'LIN': 'Linde plc',
    'APD': 'Air Products & Chemicals',
    'ECL': 'Ecolab Inc.'
}

def get_stock_data(symbol):
    try:
        stock = yf.Ticker(symbol)
        hist = stock.history(period="1d")
        if hist.empty:
            return {'error': 'No data found for this symbol'}
        
        current_price = hist['Close'].iloc[-1]
        prev_close = hist['Open'].iloc[0]
        change = current_price - prev_close
        change_percent = (change / prev_close) * 100
        
        return {
            'symbol': symbol,
            'price': round(current_price, 2),
            'change': round(change, 2),
            'change_percent': round(change_percent, 2)
        }
    except Exception as e:
        return {'error': str(e)}

def get_news(company_name):
    try:
        url = 'https://newsapi.org/v2/everything'
        params = {
            'q': company_name,
            'language': 'en',
            'sortBy': 'publishedAt',
            'pageSize': 20,
            'apiKey': Config.NEWS_API_KEY,
            'from': (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')  # Only last 7 days
        }
        response = requests.get(url, params=params)
        data = response.json()
        
        if data.get('status') != 'ok':
            return {'error': data.get('message', 'News not found')}
        
        articles = []
        for article in data.get('articles', []):
            if article.get('title') and article.get('description'):  # Only include articles with both title and description
                articles.append({
                    'title': article['title'],
                    'description': article['description'],
                    'url': article['url'],
                    'publishedAt': article['publishedAt'],
                    'source': article.get('source', {}).get('name', 'Unknown')
                })
        return articles
    except Exception as e:
        print(f"Error fetching news: {str(e)}")
        return {'error': str(e)}

@app.route('/')
def index():
    return render_template('index.html', stocks=POPULAR_STOCKS)

@app.route('/stocks')
def stocks():
    return render_template('stocks.html', stocks=POPULAR_STOCKS)

@app.route('/news')
def news():
    try:
        # Get news for all popular stocks in one query
        query = ' OR '.join(POPULAR_STOCKS.keys())
        news_data = get_news(query)
        
        if isinstance(news_data, dict) and 'error' in news_data:
            return render_template('news.html', news={'error': news_data['error']}, stocks=POPULAR_STOCKS)
        
        # Sort news by date
        news_data.sort(key=lambda x: x['publishedAt'], reverse=True)
        
        return render_template('news.html', news=news_data, stocks=POPULAR_STOCKS)
    except Exception as e:
        print(f"Error fetching news: {str(e)}")
        return render_template('news.html', news={'error': str(e)}, stocks=POPULAR_STOCKS)

@app.route('/news/<symbol>')
def stock_news(symbol):
    company_name = POPULAR_STOCKS.get(symbol.upper(), symbol.upper())
    news_data = get_news(company_name)
    return render_template('news.html', stocks=POPULAR_STOCKS, news=news_data)

@app.route('/compare')
def compare():
    return render_template('compare.html', stocks=POPULAR_STOCKS)

@app.route('/stock/<symbol>')
def stock_details(symbol):
    stock_data = get_stock_data(symbol)
    if 'error' in stock_data:
        return jsonify(stock_data), 404
    
    company_name = POPULAR_STOCKS.get(symbol.upper(), symbol.upper())
    news_data = get_news(company_name)
    
    return jsonify({
        'stock': stock_data,
        'news': news_data
    })

@app.route('/search')
def search():
    query = request.args.get('q', '').upper()
    if not query:
        return jsonify({'error': 'No search query provided'}), 400
    
    matching_stocks = {
        symbol: name for symbol, name in POPULAR_STOCKS.items()
        if query in symbol.upper() or query in name.upper()
    }
    
    return jsonify(matching_stocks)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
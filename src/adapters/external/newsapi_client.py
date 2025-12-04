# src/adapters/external/newsapi_client.py
import json
import time
from datetime import datetime
from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup

from src.utilities.logger import get_logger

logger = get_logger(__name__)


class CryptoNewsScraper:
    def __init__(self, serper_api_key: str = None, serpapi_key: str = None):
        """
        Initialize the crypto news scraper with API keys
        
        Args:
            serper_api_key: Serper.dev API key for enhanced search
            serpapi_key: SerpAPI key for Google Finance scraping
        """
        self.serper_api_key = serper_api_key
        self.serpapi_key = serpapi_key
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        self.subreddits = [
            "Bitcoin",
            "Cryptocurrency",
            "CryptoCurrency",
            "CryptoMarkets",
            "CryptoMoonShots",
            "Altcoin",
            "ethereum",
            "ethtrader",
            "btc",
            "binance",
            "cardano",
            "solana",
            "Ripple",
            "defi",
            "DeFiChain",
            "NFT",
            "blockchain",
            "Crypto_General",
            "CryptoCurrencyTrading",
            "CryptoCurrencyNews"
        ]
    
    def scrape_reddit(self) -> List[Dict]:
        """
        Scrape cryptocurrency news from multiple Reddit subreddits
        """
        reddit_news = []
        
        for subreddit in self.subreddits:
            try:
                # Using reddit.com/r/{subreddit}/new.json for latest posts
                url = f"https://www.reddit.com/r/{subreddit}/new.json?limit=25"
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                
                data = response.json()
                posts = data.get('data', {}).get('children', [])
                
                for post in posts:
                    post_data = post.get('data', {})
                    reddit_news.append({
                        'source': 'Reddit',
                        'subreddit': subreddit,
                        'title': post_data.get('title', ''),
                        'url': f"https://reddit.com{post_data.get('permalink', '')}",
                        'score': post_data.get('score', 0),
                        'comments': post_data.get('num_comments', 0),
                        'timestamp': datetime.fromtimestamp(post_data.get('created_utc', 0)).isoformat(),
                        'selftext': post_data.get('selftext', '')[:300],
                        'category': 'Crypto'
                    })
                
                logger.info(f"Fetched {len(posts)} posts from r/{subreddit}")
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error scraping r/{subreddit}: {str(e)}")
        
        return reddit_news
    
    def scrape_investing_com(self) -> List[Dict]:
        """Scrape cryptocurrency news from Investing.com UK"""
        investing_news = []
        
        try:
            url = "https://uk.investing.com/news"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find news items on Investing.com
            articles = soup.find_all('article') or soup.find_all('div', {'class': ['article', 'news-item']})
            
            for article in articles[:25]:
                try:
                    link = article.find('a', href=True)
                    title = article.find(['h2', 'h3'])
                    
                    # Filter for crypto-related content
                    title_text = title.get_text(strip=True).lower() if title else ""
                    crypto_keywords = ['crypto', 'bitcoin', 'ethereum', 'eth', 'btc', 'altcoin', 'defi', 'nft', 'blockchain']
                    
                    if link and title and any(keyword in title_text for keyword in crypto_keywords):
                        investing_news.append({
                            'source': 'Investing.com',
                            'title': title.get_text(strip=True),
                            'url': link.get('href', ''),
                            'timestamp': datetime.now().isoformat(),
                            'snippet': article.get_text(strip=True)[:300],
                            'category': 'Crypto'
                        })
                except Exception as e:
                    logger.debug(f"Error parsing article: {str(e)}")
            
            logger.info(f"Fetched {len(investing_news)} crypto articles from Investing.com")
            
        except Exception as e:
            logger.error(f"Error scraping Investing.com: {str(e)}")
        
        return investing_news
    
    def scrape_sandmark_crypto(self) -> List[Dict]:
        """Scrape crypto news and markets from Sandmark"""
        sandmark_news = []
        
        try:
            # Scrape markets/deals section for crypto
            url = "https://www.sandmark.com/markets-deals/crypto"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find articles/content on Sandmark crypto page
            articles = soup.find_all(['article', 'div'], {'class': ['news-item', 'article', 'market-item', 'deal']})
            
            for article in articles[:20]:
                try:
                    link = article.find('a', href=True)
                    title = article.find(['h2', 'h3', 'h4'])
                    price_elem = article.find(['span', 'div'], {'class': ['price', 'value']})
                    
                    if link and title:
                        sandmark_news.append({
                            'source': 'Sandmark',
                            'title': title.get_text(strip=True),
                            'url': link.get('href', ''),
                            'timestamp': datetime.now().isoformat(),
                            'snippet': article.get_text(strip=True)[:300],
                            'price': price_elem.get_text(strip=True) if price_elem else None,
                            'category': 'Crypto'
                        })
                except Exception as e:
                    logger.debug(f"Error parsing article: {str(e)}")
            
            logger.info(f"Fetched {len(sandmark_news)} items from Sandmark Crypto Markets")
            
        except Exception as e:
            logger.error(f"Error scraping Sandmark: {str(e)}")
        
        return sandmark_news
    
    def scrape_google_finance_crypto(self) -> List[Dict]:
        """Scrape crypto market data from Google Finance via SerpAPI"""
        finance_news = []
        
        if not self.serpapi_key:
            logger.warning("SerpAPI key not provided, skipping Google Finance scrape")
            return []
        
        try:
            # Popular crypto assets to track
            crypto_assets = ['Bitcoin', 'Ethereum', 'Cardano', 'Solana', 'Ripple', 'Binance Coin', 'Dogecoin']
            
            for asset in crypto_assets:
                try:
                    url = "https://serpapi.com/search"
                    params = {
                        "q": f"{asset} price news",
                        "type": "finance",
                        "api_key": self.serpapi_key,
                        "num": 10
                    }
                    
                    response = requests.get(url, params=params, timeout=10)
                    response.raise_for_status()
                    data = response.json()
                    
                    # Extract finance news
                    if 'news' in data:
                        for item in data['news']:
                            finance_news.append({
                                'source': 'Google Finance',
                                'title': item.get('title', ''),
                                'url': item.get('link', ''),
                                'source_name': item.get('source', ''),
                                'timestamp': item.get('date', datetime.now().isoformat()),
                                'snippet': item.get('snippet', '')[:300],
                                'asset': asset,
                                'category': 'Crypto'
                            })
                    
                    time.sleep(1)
                    
                except Exception as e:
                    logger.debug(f"Error fetching {asset}: {str(e)}")
            
            logger.info(f"Fetched {len(finance_news)} items from Google Finance")
            
        except Exception as e:
            logger.error(f"Error using SerpAPI: {str(e)}")
        
        return finance_news
    
    def search_with_serper(self, queries: List[str] = None) -> List[Dict]:
        """
        Use Serper.dev API for enhanced crypto news search
        
        Args:
            queries: Search queries for crypto news
        """
        if not self.serper_api_key:
            logger.warning("Serper API key not provided, skipping Serper search")
            return []
        
        if queries is None:
            queries = [
                'cryptocurrency news',
                'bitcoin news',
                'ethereum news',
                'crypto market news',
                'altcoin news',
                'DeFi news'
            ]
        
        serper_results = []
        
        try:
            url = "https://google.serper.dev/search"
            
            for query in queries:
                try:
                    # Build search with site restrictions
                    sites = ['reddit.com', 'investing.com', 'sandmark.com']
                    site_query = " OR ".join([f"site:{site}" for site in sites])
                    full_query = f"({query}) ({site_query})"
                    
                    payload = {
                        "q": full_query,
                        "num": 15,
                        "tbs": "qdr:d"  # Last 24 hours
                    }
                    
                    headers = {
                        "X-API-KEY": self.serper_api_key,
                        "Content-Type": "application/json"
                    }
                    
                    response = requests.post(url, json=payload, headers=headers, timeout=10)
                    response.raise_for_status()
                    
                    data = response.json()
                    
                    for result in data.get('organic', []):
                        serper_results.append({
                            'source': 'Serper Search',
                            'title': result.get('title', ''),
                            'url': result.get('link', ''),
                            'snippet': result.get('snippet', ''),
                            'timestamp': datetime.now().isoformat(),
                            'query': query,
                            'position': result.get('position', 0),
                            'category': 'Crypto'
                        })
                    
                    time.sleep(1)
                    
                except Exception as e:
                    logger.debug(f"Error searching '{query}': {str(e)}")
            
            logger.info(f"Fetched {len(serper_results)} results from Serper")
            
        except Exception as e:
            logger.error(f"Error using Serper API: {str(e)}")
        
        return serper_results
    
    def scrape_all(self, use_serper: bool = True, use_serpapi: bool = True) -> Dict:
        """
        Scrape all crypto news sources and compile results
        
        Args:
            use_serper: Whether to use Serper API
            use_serpapi: Whether to use SerpAPI for Google Finance
        """
        logger.info("Starting cryptocurrency news scraping cycle...")
        
        all_news = {
            'timestamp': datetime.now().isoformat(),
            'category': 'Cryptocurrency',
            'sources': {}
        }
        
        # Scrape Reddit (broadest coverage)
        logger.info("Scraping Reddit...")
        all_news['sources']['reddit'] = self.scrape_reddit()
        time.sleep(2)
        
        # Scrape Investing.com for crypto news
        logger.info("Scraping Investing.com...")
        all_news['sources']['investing'] = self.scrape_investing_com()
        time.sleep(2)
        
        # Scrape Sandmark crypto markets
        logger.info("Scraping Sandmark Crypto Markets...")
        all_news['sources']['sandmark'] = self.scrape_sandmark_crypto()
        time.sleep(2)
        
        # Use Google Finance via SerpAPI
        if use_serpapi and self.serpapi_key:
            logger.info("Scraping Google Finance (SerpAPI)...")
            all_news['sources']['google_finance'] = self.scrape_google_finance_crypto()
            time.sleep(2)
        
        # Use Serper for additional coverage
        if use_serper and self.serper_api_key:
            logger.info("Searching with Serper...")
            all_news['sources']['serper'] = self.search_with_serper()
        
        # Calculate totals
        total = sum(len(v) for v in all_news['sources'].values())
        logger.info(f"Scraping complete! Total articles fetched: {total}")
        
        return all_news
    
    def save_to_file(self, data: Dict, filename: str = 'crypto_news.json'):
        """Save scraped data to JSON file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"Data saved to {filename}")
        except Exception as e:
            logger.error(f"Error saving file: {str(e)}")
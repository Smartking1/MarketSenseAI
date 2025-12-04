# src/application/agents/sentiment_analyst.py
"""
Sentiment Analyst - Analyzes market sentiment from crypto news sources
"""
import json
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field

from src.application.agents.base_agent import BaseAgent
from src.application.services.rag_service import RAGService
from src.application.services.translation_service import TranslationService
from src.infrastructure.cache import get_cache
from src.utilities.logger import get_logger

# Import your crypto news scraper
try:
    from src.adapters.external.newsapi_client import CryptoNewsScraper
    CRYPTO_NEWS_AVAILABLE = True
except ImportError:
    CRYPTO_NEWS_AVAILABLE = False

logger = get_logger(__name__)


@dataclass
class SentimentAnalysis:
    """Sentiment analysis entity"""
    query: str
    asset_symbol: str
    summary: str = ""
    sentiment_score: int = 50
    sentiment_label: str = "neutral"
    dominant_narratives: Dict[str, List[str]] = field(default_factory=lambda: {"bullish": [], "bearish": []})
    news_flow: str = "mixed"
    contrarian_signals: List[str] = field(default_factory=list)
    key_factors: List[str] = field(default_factory=list)
    confidence: float = 0.5
    risks: List[str] = field(default_factory=list)
    detailed_analysis: Dict = field(default_factory=dict)
    data_sources: Dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "query": self.query,
            "asset_symbol": self.asset_symbol,
            "summary": self.summary,
            "sentiment_score": self.sentiment_score,
            "sentiment_label": self.sentiment_label,
            "dominant_narratives": self.dominant_narratives,
            "news_flow": self.news_flow,
            "contrarian_signals": self.contrarian_signals,
            "key_factors": self.key_factors,
            "confidence": self.confidence,
            "risks": self.risks,
            "detailed_analysis": self.detailed_analysis,
            "data_sources": self.data_sources,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }


class SentimentAnalyst(BaseAgent):
    """Analyzes market sentiment from crypto news sources"""
    
    def __init__(self, model: str = "llama-3.3-70b-versatile"):
        super().__init__(
            name="Sentiment Analyst",
            model=model,
            system_prompt=self._get_system_prompt()
        )
        self.rag_service = RAGService()
        self.translation_service = TranslationService()
        self.cache = get_cache()
        
        # Initialize crypto news scraper if available
        self.crypto_scraper = None
        if CRYPTO_NEWS_AVAILABLE:
            from src.config.settings import get_settings
            settings = get_settings()
            
            if settings.serper_api_key or settings.serpapi_key:
                self.crypto_scraper = CryptoNewsScraper(
                    serper_api_key=settings.serper_api_key,
                    serpapi_key=settings.serpapi_key
                )
                logger.info("CryptoNewsScraper initialized with API keys")
            else:
                logger.warning("No Serper/SerpAPI keys found, crypto news scraping disabled")
        
        # Sentiment analysis parameters
        self.min_confidence = 0.6
        self.max_articles = 50
        self.recency_hours = 24
        
    def _get_system_prompt(self) -> str:
        """Get the system prompt for sentiment analysis"""
        return """You are a Sentiment Analyst specializing in cryptocurrency markets.
        
        Your task is to analyze news articles, social media posts, and market discussions
        to determine the overall market sentiment for a given cryptocurrency.
        
        ANALYSIS FRAMEWORK:
        1. Extract sentiment from each piece of content
        2. Identify dominant narratives (bullish/bearish)
        3. Calculate sentiment score (0-100 scale)
        4. Provide actionable insights
        
        OUTPUT FORMAT: Return a JSON object with this exact structure:
        {
            "summary": "Brief summary of overall sentiment",
            "sentiment_score": 0-100 (0=extremely bearish, 100=extremely bullish),
            "sentiment_label": "bullish" | "bearish" | "neutral",
            "dominant_narratives": {
                "bullish": ["list of bullish themes"],
                "bearish": ["list of bearish themes"]
            },
            "news_flow": "positive" | "negative" | "mixed",
            "contrarian_signals": ["list of contrarian indicators"],
            "key_factors": ["list of key influencing factors"],
            "confidence": 0.0-1.0 (confidence in analysis),
            "risks": ["list of key risks"]
        }
        
        IMPORTANT: Only respond with valid JSON. No explanations, no markdown formatting.
        """
    
    async def analyze(self, query: str, context: Optional[Dict] = None) -> SentimentAnalysis:
        """
        Analyze sentiment for a given cryptocurrency
        
        Args:
            query: User query (e.g., "Should I buy Bitcoin now?")
            context: Additional context including asset_symbol
            
        Returns:
            SentimentAnalysis object
        """
        try:
            asset_symbol = context.get('asset_symbol', '').upper() if context else ''
            if not asset_symbol:
                asset_symbol = self._extract_asset_symbol(query)
            
            logger.info(f"Sentiment Analyst analyzing: {asset_symbol}")
            
            # Translate query to English if needed
            query_in_english = await self.translation_service.translate_to_english(query)
            
            # Get sentiment data from multiple sources
            sentiment_data = await self._collect_sentiment_data(
                query_in_english, 
                asset_symbol
            )
            
            # Generate analysis using LLM
            analysis_result = await self._generate_sentiment_analysis(
                query_in_english,
                asset_symbol,
                sentiment_data
            )
            
            # Create and return SentimentAnalysis object
            return self._create_sentiment_analysis(
                query=query,
                asset_symbol=asset_symbol,
                analysis_result=analysis_result,
                source_data=sentiment_data
            )
            
        except Exception as e:
            logger.error(f"Error in sentiment analysis: {str(e)}")
            raise
    
    async def _collect_sentiment_data(self, query: str, asset_symbol: str) -> Dict[str, Any]:
        """
        Collect sentiment data from multiple sources
        """
        sentiment_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "asset_symbol": asset_symbol,
            "query": query,
            "sources": {}
        }
        
        # 1. Get fresh crypto news from scraper (highest priority)
        if self.crypto_scraper:
            fresh_news = await self._get_fresh_crypto_news(asset_symbol)
            sentiment_data["sources"]["fresh_news"] = fresh_news
            logger.info(f"Collected {len(fresh_news)} fresh news articles")
        
        # 2. Query RAG service for historical context
        rag_documents = await self._get_rag_documents(query, asset_symbol)
        sentiment_data["sources"]["rag_documents"] = rag_documents
        logger.info(f"Retrieved {len(rag_documents)} documents from RAG")
        
        return sentiment_data
    
    async def _get_fresh_crypto_news(self, asset_symbol: str) -> List[Dict]:
        """
        Get fresh crypto news using the CryptoNewsScraper
        """
        if not self.crypto_scraper:
            return []
        
        try:
            # Run scraper in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            
            # Scrape all crypto news (use Serper/SerpAPI if keys available)
            use_serper = bool(self.crypto_scraper.serper_api_key)
            use_serpapi = bool(self.crypto_scraper.serpapi_key)
            
            news_data = await loop.run_in_executor(
                None,
                self.crypto_scraper.scrape_all,
                use_serper,
                use_serpapi
            )
            
            # Filter for relevant asset_symbol and recency
            relevant_articles = []
            cutoff_time = datetime.utcnow() - timedelta(hours=self.recency_hours)
            
            for source_name, articles in news_data.get('sources', {}).items():
                for article in articles:
                    if self._is_article_relevant(article, asset_symbol):
                        article['scrape_source'] = source_name
                        article['scrape_timestamp'] = datetime.utcnow().isoformat()
                        relevant_articles.append(article)
            
            return relevant_articles[:self.max_articles]
            
        except Exception as e:
            logger.error(f"Error getting fresh crypto news: {str(e)}")
            return []
    
    def _is_article_relevant(self, article: Dict, asset_symbol: str) -> bool:
        """
        Check if an article is relevant to the given asset symbol
        """
        if not asset_symbol:
            return True
        
        symbol_mappings = {
            'BTC': ['bitcoin', 'btc'],
            'ETH': ['ethereum', 'eth'],
            'XRP': ['ripple', 'xrp'],
            'ADA': ['cardano', 'ada'],
            'SOL': ['solana', 'sol'],
            'DOGE': ['dogecoin', 'doge'],
            'USD': ['dollar', 'usd', 'us dollar'],
        }
        
        target_terms = symbol_mappings.get(asset_symbol, [asset_symbol.lower()])
        
        title = article.get('title', '').lower()
        snippet = article.get('snippet', '').lower()
        selftext = article.get('selftext', '').lower()
        
        content = f"{title} {snippet} {selftext}"
        
        for term in target_terms:
            if term and term in content:
                return True
        
        return False
    
    async def _get_rag_documents(self, query: str, asset_symbol: str) -> List[Dict]:
        """Get relevant documents from RAG service"""
        try:
            await self.rag_service.initialize()
            documents = await self.rag_service.query_collection(
                query=query,
                collection_name="news_sentiment",
                n_results=10
            )
            return documents
        except Exception as e:
            logger.warning(f"Error getting RAG documents: {str(e)}")
            return []
    
    async def _generate_sentiment_analysis(
        self, 
        query: str, 
        asset_symbol: str, 
        sentiment_data: Dict
    ) -> Dict:
        """
        Generate sentiment analysis using LLM based on collected data
        """
        try:
            prompt = self._create_analysis_prompt(query, asset_symbol, sentiment_data)
            response = await self.generate_response(prompt)
            analysis_result = self._parse_llm_response(response)
            enhanced_result = self._enhance_analysis(analysis_result, sentiment_data)
            return enhanced_result
            
        except Exception as e:
            logger.error(f"Error generating sentiment analysis: {str(e)}")
            return self._create_fallback_analysis(asset_symbol)
    
    def _create_analysis_prompt(self, query: str, asset_symbol: str, sentiment_data: Dict) -> str:
        """
        Create detailed prompt for LLM analysis
        """
        # Extract and format news articles
        fresh_news = sentiment_data.get("sources", {}).get("fresh_news", [])
        rag_documents = sentiment_data.get("sources", {}).get("rag_documents", [])
        
        news_summary = []
        for i, article in enumerate(fresh_news[:10], 1):
            news_summary.append(f"{i}. {article.get('title', 'No title')}")
            if article.get('snippet'):
                news_summary.append(f"   Summary: {article.get('snippet', '')[:200]}...")
            news_summary.append(f"   Source: {article.get('source', 'Unknown')}")
            news_summary.append("")
        
        # Create prompt - using chr(10) instead of \n in f-string expressions
        prompt = f"""Analyze the sentiment for {asset_symbol} based on the following data:

QUERY: {query}

RECENT NEWS ARTICLES:
{"- No recent news articles available" if not fresh_news else chr(10).join(news_summary)}

HISTORICAL CONTEXT (RAG Documents):
{"- No historical context available" if not rag_documents else f"Found {len(rag_documents)} relevant documents"}

ADDITIONAL DATA:
- Social Media: {sentiment_data.get('sources', {}).get('social_media', {}).get('message', 'Not available')}
- Market Indicators: {sentiment_data.get('sources', {}).get('market_indicators', {}).get('message', 'Not available')}

ANALYSIS INSTRUCTIONS:
1. Based on the news articles, determine overall sentiment
2. Identify key bullish and bearish narratives
3. Assess news flow (positive/negative/mixed)
4. Look for contrarian signals
5. Identify key risks
6. Provide confidence score based on data quality

Respond with JSON only, using the exact format specified in the system prompt."""
        
        return prompt
    
    def _parse_llm_response(self, response: str) -> Dict:
        """Parse LLM response into structured JSON"""
        try:
            response = response.strip()
            
            if '```json' in response:
                response = response.split('```json')[1].split('```')[0].strip()
            elif '```' in response:
                response = response.split('```')[1].split('```')[0].strip()
            
            result = json.loads(response)
            
            required_fields = ['summary', 'sentiment_score', 'sentiment_label']
            for field in required_fields:
                if field not in result:
                    logger.warning(f"Missing required field in LLM response: {field}")
                    result[field] = "" if field == "summary" else 0 if "score" in field else "neutral"
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            
            return {
                "summary": "Failed to parse sentiment analysis response.",
                "sentiment_score": 50,
                "sentiment_label": "neutral",
                "dominant_narratives": {"bullish": [], "bearish": []},
                "news_flow": "mixed",
                "contrarian_signals": [],
                "key_factors": ["Data parsing error"],
                "confidence": 0.3,
                "risks": ["Analysis quality compromised"]
            }
    
    def _enhance_analysis(self, analysis_result: Dict, sentiment_data: Dict) -> Dict:
        """Enhance analysis with additional metrics"""
        
        fresh_news_count = len(sentiment_data.get("sources", {}).get("fresh_news", []))
        rag_docs_count = len(sentiment_data.get("sources", {}).get("rag_documents", []))
        
        data_quality_score = min(1.0, (fresh_news_count * 0.7 + rag_docs_count * 0.3) / 20)
        
        original_confidence = analysis_result.get("confidence", 0.5)
        enhanced_confidence = original_confidence * 0.7 + data_quality_score * 0.3
        
        analysis_result["metadata"] = {
            "data_sources_used": {
                "fresh_news": fresh_news_count,
                "rag_documents": rag_docs_count
            },
            "data_quality_score": round(data_quality_score, 2),
            "analysis_timestamp": datetime.utcnow().isoformat()
        }
        
        analysis_result["confidence"] = round(enhanced_confidence, 2)
        
        return analysis_result
    
    def _create_fallback_analysis(self, asset_symbol: str) -> Dict:
        """Create fallback analysis when LLM fails"""
        return {
            "summary": f"Limited sentiment analysis available for {asset_symbol} due to data constraints.",
            "sentiment_score": 50,
            "sentiment_label": "neutral",
            "dominant_narratives": {
                "bullish": ["Insufficient data for bullish analysis"],
                "bearish": ["Insufficient data for bearish analysis"]
            },
            "news_flow": "unknown",
            "contrarian_signals": ["Data limitations prevent contrarian analysis"],
            "key_factors": ["Data availability", "Market conditions"],
            "confidence": 0.3,
            "risks": ["Limited data", "Potential inaccuracies"],
            "metadata": {
                "data_sources_used": {"fresh_news": 0, "rag_documents": 0},
                "data_quality_score": 0.0,
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "fallback_analysis": True
            }
        }
    
    def _create_sentiment_analysis(
        self, 
        query: str, 
        asset_symbol: str, 
        analysis_result: Dict,
        source_data: Dict
    ) -> SentimentAnalysis:
        """Create SentimentAnalysis domain object"""
        
        overall_confidence = analysis_result.get("confidence", 0.5)
        
        sentiment_analysis = SentimentAnalysis(
            query=query,
            asset_symbol=asset_symbol,
            summary=analysis_result.get("summary", ""),
            sentiment_score=analysis_result.get("sentiment_score", 50),
            sentiment_label=analysis_result.get("sentiment_label", "neutral"),
            dominant_narratives=analysis_result.get("dominant_narratives", {"bullish": [], "bearish": []}),
            news_flow=analysis_result.get("news_flow", "mixed"),
            contrarian_signals=analysis_result.get("contrarian_signals", []),
            key_factors=analysis_result.get("key_factors", []),
            confidence=overall_confidence,
            risks=analysis_result.get("risks", []),
            detailed_analysis=analysis_result,
            data_sources=source_data.get("sources", {}),
            timestamp=datetime.utcnow()
        )
        
        logger.info(f"Sentiment analysis completed for {asset_symbol}: "
                   f"Score={sentiment_analysis.sentiment_score}, "
                   f"Label={sentiment_analysis.sentiment_label}, "
                   f"Confidence={sentiment_analysis.confidence}")
        
        return sentiment_analysis
    
    def _extract_asset_symbol(self, query: str) -> str:
        """Extract asset symbol from query"""
        query_lower = query.lower()
        
        symbol_mappings = {
            'bitcoin': 'BTC',
            'btc': 'BTC',
            'ethereum': 'ETH',
            'eth': 'ETH',
            'ripple': 'XRP',
            'xrp': 'XRP',
            'cardano': 'ADA',
            'ada': 'ADA',
            'solana': 'SOL',
            'sol': 'SOL',
            'dogecoin': 'DOGE',
            'doge': 'DOGE',
            'usd': 'USD',
            'dollar': 'USD',
        }
        
        for term, symbol in symbol_mappings.items():
            if term in query_lower:
                return symbol
        
        return "UNKNOWN"
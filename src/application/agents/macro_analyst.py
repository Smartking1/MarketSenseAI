"""
Macro Analyst Agent - Analyzes macroeconomic conditions
"""
import json
import asyncio
from typing import Dict, Any, Optional, List
from src.application.agents.base_agent import BaseAgent
from src.application.services.rag_service import RAGService
from src.application.services.translation_service import TranslationService
from src.adapters.external.fred_client import FREDClient
from src.utilities.logger import get_logger

# Import what's actually available
try:
    from src.adapters.external.newsapi_client import CryptoNewsScraper
    HAS_CRYPTO_NEWS_SCRAPER = True
except ImportError:
    HAS_CRYPTO_NEWS_SCRAPER = False

logger = get_logger(__name__)


class MacroAnalyst(BaseAgent):
    """Agent specialized in macroeconomic analysis"""
    
    def __init__(self, model: str = "llama-3.3-70b-versatile"):
        super().__init__(
            name="Macro Analyst",
            model=model,
            system_prompt=self._get_system_prompt()
        )
        self.rag_service = RAGService()
        self.translation_service = TranslationService()
        
        # Initialize FRED client
        self.fred_client = FREDClient()
        
        # Initialize crypto news scraper if available
        self.crypto_scraper = None
        if HAS_CRYPTO_NEWS_SCRAPER:
            from src.config.settings import get_settings
            settings = get_settings()
            
            # Use CryptoNewsScraper for news (it also has general financial news)
            self.crypto_scraper = CryptoNewsScraper(
                serper_api_key=settings.serper_api_key,
                serpapi_key=settings.serpapi_key
            )
            logger.info("Using CryptoNewsScraper for macroeconomic news")
        else:
            logger.warning("CryptoNewsScraper not available, will use only FRED data and RAG")
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for macro analysis"""
        return """You are a professional macroeconomic analyst with expertise in:
- Central bank monetary policy (Fed, ECB, BoE, etc.)
- Inflation trends and indicators (CPI, PCE, PPI)
- Employment data and labor markets
- GDP growth and economic cycles
- Interest rate impacts on currencies and assets

Your role is to analyze macroeconomic data and provide insights on how it affects
financial markets, particularly forex and cryptocurrency markets.

Provide analysis in JSON format with this exact structure:
{
    "summary": "Brief executive summary",
    "monetary_policy_stance": "hawkish/dovish/neutral",
    "inflation_outlook": "rising/falling/stable",
    "growth_indicators": "strong/moderate/weak",
    "currency_impact": "Analysis of impact on major currencies",
    "key_factors": ["factor1", "factor2", ...],
    "confidence": 0.0-1.0,
    "risks": ["risk1", "risk2", ...]
}

IMPORTANT: Only respond with valid JSON. No explanations, no markdown formatting."""
    
    async def analyze(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze macroeconomic conditions
        
        Args:
            query: Analysis query
            context: Additional context
            
        Returns:
            Macro analysis results
        """
        try:
            logger.info(f"Macro Analyst analyzing: {query}")
            
            # Extract asset symbol from context
            asset_symbol = context.get('asset_symbol', '').upper() if context else ''
            
            # Translate query to English if needed
            query_in_english = await self.translation_service.translate_text(query)
            
            # Collect data from multiple sources
            economic_data = await self._collect_economic_data()
            news_data = await self._collect_news_data(query_in_english, asset_symbol)
            rag_documents = await self._get_rag_documents(query_in_english, asset_symbol)
            
            # Generate analysis using LLM
            analysis_result = await self._generate_macro_analysis(
                query_in_english,
                asset_symbol,
                economic_data,
                news_data,
                rag_documents
            )
            
            # Create formatted output
            return self._format_output(
                analysis_result,
                economic_data,
                rag_documents
            )
            
        except Exception as e:
            logger.error(f"Error in Macro Analyst: {str(e)}")
            return self._create_fallback_analysis(query)
    
    async def _collect_economic_data(self) -> Dict[str, Any]:
        """Collect economic data from FRED"""
        try:
            # Get multiple economic indicators
            indicators = await self.fred_client.get_economic_indicators()
            return indicators
        except Exception as e:
            logger.error(f"Error collecting economic data from FRED: {str(e)}")
            return self._get_fallback_economic_data()
    
    def _get_fallback_economic_data(self) -> Dict[str, Any]:
        """Provide fallback economic data when FRED fails"""
        return {
            "fed_funds_rate": 5.5,
            "inflation_cpi": 324.0,
            "unemployment": 4.4,
            "gdp": 30485.0,
            "data_quality": "estimated_fallback",
            "timestamp": "2025-12-04T20:00:00Z"
        }
    
    async def _collect_news_data(self, query: str, asset_symbol: str) -> List[Dict]:
        """Collect relevant economic news using CryptoNewsScraper"""
        if not self.crypto_scraper:
            return []
        
        try:
            # Run scraper in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            
            # Get all news from CryptoNewsScraper
            use_serper = bool(self.crypto_scraper.serper_api_key)
            use_serpapi = bool(self.crypto_scraper.serpapi_key)
            
            all_news = await loop.run_in_executor(
                None,
                self.crypto_scraper.scrape_all,
                use_serper,
                use_serpapi
            )
            
            # Filter for macroeconomic news
            macro_news = []
            macroeconomic_keywords = [
                'fed', 'federal reserve', 'inflation', 'cpi', 'gdp', 'interest rate',
                'unemployment', 'economy', 'economic', 'central bank', 'monetary policy',
                'recession', 'growth', 'debt', 'deficit', 'finance minister', 'treasury',
                'rate hike', 'rate cut', 'quantitative easing', 'qe', 'tapering',
                'fiscal policy', 'budget', 'trade deficit', 'current account',
                'manufacturing', 'industrial production', 'retail sales', 'housing',
                'consumer confidence', 'business confidence', 'pmi', 'ism'
            ]
            
            for source_name, articles in all_news.get('sources', {}).items():
                for article in articles:
                    title = article.get('title', '').lower()
                    snippet = article.get('snippet', '').lower()
                    selftext = article.get('selftext', '').lower()
                    
                    content = f"{title} {snippet} {selftext}"
                    
                    # Check if article contains macroeconomic keywords
                    if any(keyword in content for keyword in macroeconomic_keywords):
                        article['scrape_source'] = source_name
                        article['scrape_timestamp'] = "2025-12-04T20:00:00Z"
                        macro_news.append(article)
            
            logger.info(f"Found {len(macro_news)} macroeconomic news articles")
            return macro_news[:10]  # Return top 10
            
        except Exception as e:
            logger.error(f"Error collecting news from CryptoNewsScraper: {str(e)}")
            return []
    
    async def _get_rag_documents(self, query: str, asset_symbol: str) -> List[Dict]:
        """Get relevant documents from RAG service"""
        try:
            await self.rag_service.initialize()
            documents = await self.rag_service.query_collection(
                query=query,
                collection_name="macro_data",
                n_results=10
            )
            return documents
        except Exception as e:
            logger.warning(f"Error getting RAG documents: {str(e)}")
            return []
    
    async def _generate_macro_analysis(
        self,
        query: str,
        asset_symbol: str,
        economic_data: Dict,
        news_data: List[Dict],
        rag_documents: List[Dict]
    ) -> Dict:
        """
        Generate macro analysis using LLM based on collected data
        """
        try:
            # Prepare prompt with collected data
            prompt = self._create_analysis_prompt(
                query, asset_symbol, economic_data, news_data, rag_documents
            )
            
            # Generate analysis
            response = await self.generate_response(prompt)
            
            # Parse JSON response
            analysis_result = self._parse_llm_response(response)
            
            # Enhance with metadata
            enhanced_result = self._enhance_analysis(
                analysis_result, 
                economic_data,
                len(news_data),
                len(rag_documents)
            )
            
            return enhanced_result
            
        except Exception as e:
            logger.error(f"Error generating macro analysis: {str(e)}")
            return self._create_fallback_macro_analysis(asset_symbol)
    
    def _create_analysis_prompt(
        self,
        query: str,
        asset_symbol: str,
        economic_data: Dict,
        news_data: List[Dict],
        rag_documents: List[Dict]
    ) -> str:
        """
        Create detailed prompt for LLM analysis
        """
        # Format economic data
        econ_summary = []
        for key, value in economic_data.items():
            if key not in ['data_quality', 'timestamp'] and isinstance(value, (int, float, str)):
                econ_summary.append(f"{key}: {value}")
        
        # Format news data
        news_summary = []
        for i, article in enumerate(news_data[:5], 1):
            title = article.get('title', 'No title')
            news_summary.append(f"{i}. {title}")
            
            snippet = article.get('snippet', '')
            if snippet:
                news_summary.append(f"   Summary: {snippet[:150]}...")
            
            source = article.get('source', article.get('scrape_source', 'Unknown'))
            news_summary.append(f"   Source: {source}")
            news_summary.append("")
        
        # Create prompt
        prompt = f"""Analyze the macroeconomic conditions for {asset_symbol if asset_symbol else 'the market'} based on the following data:

QUERY: {query}

ECONOMIC INDICATORS:
{chr(10).join(econ_summary) if econ_summary else "- No economic indicators available"}

RECENT ECONOMIC NEWS:
{"- No recent economic news available" if not news_summary else chr(10).join(news_summary)}

HISTORICAL CONTEXT (RAG Documents):
{"- No historical context available" if not rag_documents else f"Found {len(rag_documents)} relevant documents"}

ANALYSIS INSTRUCTIONS:
1. Analyze the current monetary policy stance based on interest rates and central bank actions
2. Assess inflation outlook based on CPI and other indicators
3. Evaluate growth indicators (GDP, unemployment, etc.)
4. Determine the impact on major currencies (USD, EUR, JPY, etc.)
5. Identify key macroeconomic factors affecting financial markets
6. Assess risks to the economic outlook
7. Provide confidence score based on data quality

Respond with JSON only, using the exact format specified in the system prompt."""
        
        return prompt
    
    def _parse_llm_response(self, response: str) -> Dict:
        """Parse LLM response into structured JSON"""
        try:
            response = response.strip()
            
            # Handle markdown code blocks
            if '```json' in response:
                response = response.split('```json')[1].split('```')[0].strip()
            elif '```' in response:
                response = response.split('```')[1].split('```')[0].strip()
            
            # Parse JSON
            result = json.loads(response)
            
            # Validate required fields
            required_fields = ['summary', 'monetary_policy_stance', 'inflation_outlook', 'growth_indicators']
            for field in required_fields:
                if field not in result:
                    logger.warning(f"Missing required field in LLM response: {field}")
                    result[field] = "" if field == "summary" else "neutral"
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            
            return {
                "summary": "Failed to parse macroeconomic analysis response.",
                "monetary_policy_stance": "neutral",
                "inflation_outlook": "stable",
                "growth_indicators": "moderate",
                "currency_impact": "Unable to determine impact due to data parsing error.",
                "key_factors": ["Data parsing error"],
                "confidence": 0.3,
                "risks": ["Analysis quality compromised"]
            }
    
    def _enhance_analysis(
        self, 
        analysis_result: Dict, 
        economic_data: Dict,
        news_count: int,
        rag_count: int
    ) -> Dict:
        """Enhance analysis with additional metrics"""
        
        # Calculate data quality score
        econ_indicators_count = len([k for k in economic_data.keys() if k not in ['data_quality', 'timestamp']])
        data_quality_score = min(1.0, (econ_indicators_count * 0.5 + news_count * 0.3 + rag_count * 0.2) / 15)
        
        # Adjust confidence based on data quality
        original_confidence = analysis_result.get("confidence", 0.5)
        enhanced_confidence = original_confidence * 0.7 + data_quality_score * 0.3
        
        # Add metadata
        analysis_result["metadata"] = {
            "data_sources_used": {
                "economic_indicators": econ_indicators_count,
                "news_articles": news_count,
                "rag_documents": rag_count
            },
            "data_quality_score": round(data_quality_score, 2),
            "analysis_timestamp": "2025-12-04T20:00:00Z"
        }
        
        analysis_result["confidence"] = round(min(enhanced_confidence, 1.0), 2)
        
        return analysis_result
    
    def _create_fallback_macro_analysis(self, asset_symbol: str) -> Dict:
        """Create fallback analysis when LLM fails"""
        return {
            "summary": f"Limited macroeconomic analysis available for {asset_symbol} due to data constraints.",
            "monetary_policy_stance": "neutral",
            "inflation_outlook": "stable",
            "growth_indicators": "moderate",
            "currency_impact": "Insufficient data to determine currency impact.",
            "key_factors": ["Data availability", "Market conditions", "Global economic trends"],
            "confidence": 0.3,
            "risks": ["Limited data", "Potential inaccuracies", "Market volatility"],
            "metadata": {
                "data_sources_used": {"economic_indicators": 0, "news_articles": 0, "rag_documents": 0},
                "data_quality_score": 0.0,
                "fallback_analysis": True
            }
        }
    
    def _format_output(
        self,
        analysis_result: Dict,
        economic_data: Dict,
        rag_documents: List[Dict]
    ) -> Dict[str, Any]:
        """Format the final output for the synthesis agent"""
        
        # Extract detailed analysis from metadata if available
        detailed_analysis = analysis_result.copy()
        metadata = detailed_analysis.pop("metadata", {})
        
        return {
            "agent_name": self.name,
            "summary": analysis_result.get("summary", ""),
            "confidence": analysis_result.get("confidence", 0.5),
            "key_factors": analysis_result.get("key_factors", []),
            "data_sources": {
                "fred_data": economic_data.get("data_quality", "unknown"),
                "rag_documents_count": len(rag_documents),
                "data_quality_score": metadata.get("data_quality_score", 0.0)
            },
            "detailed_analysis": detailed_analysis
        }
    
    def _create_fallback_analysis(self, query: str) -> Dict[str, Any]:
        """Create fallback analysis when everything fails"""
        return {
            "agent_name": self.name,
            "summary": f"Unable to perform macroeconomic analysis for '{query}' due to technical issues.",
            "confidence": 0.1,
            "key_factors": ["Technical error", "Data unavailability"],
            "data_sources": {
                "fred_data": "unavailable",
                "rag_documents_count": 0,
                "data_quality_score": 0.0
            },
            "detailed_analysis": {
                "summary": "Analysis failed due to technical issues.",
                "monetary_policy_stance": "unknown",
                "inflation_outlook": "unknown",
                "growth_indicators": "unknown",
                "currency_impact": "Unable to determine",
                "key_factors": ["Technical error"],
                "confidence": 0.1,
                "risks": ["System failure", "Data unavailability"]
            }
        }
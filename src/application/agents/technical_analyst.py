"""
Technical Analyst Agent - Analyzes price action and technical indicators
"""
import json
from typing import Dict, Any, Optional, List
from src.application.agents.base_agent import BaseAgent
from src.application.services.rag_service import RAGService
from src.application.services.tts_service import TTSService
from src.application.services.speech_service import SpeechService
from src.application.services.translation_service import TranslationService
from src.adapters.external.coingecko_client import CoinGeckoClient 
from src.utilities.logger import get_logger 
import pandas as pd
from ta import momentum, trend, volatility
from datetime import datetime, timedelta

logger = get_logger(__name__)


class TechnicalAnalyst(BaseAgent):
    """Agent specialized in technical analysis"""
    
    def __init__(self):
        super().__init__(
            name="Technical Analyst",
            description="Analyzes price action, technical indicators, and on-chain metrics"
        )
        self.rag_service = RAGService()
        self.tts_service = TTSService()
        self.speech_service = SpeechService()
        self.translation_service = TranslationService()
    
    def get_system_prompt(self) -> str:
        """Get system prompt for technical analysis"""
        return """You are an expert technical analyst specializing in:
- Price action and chart patterns
- Technical indicators (RSI, MACD, Moving Averages, Bollinger Bands)
- Support and resistance levels
- Trend analysis and momentum
- On-chain metrics for cryptocurrencies (when applicable)

Provide analysis in JSON format with:
{
    "summary": "Brief technical summary",
    "trend": "bullish/bearish/neutral",
    "momentum": "strong/moderate/weak",
    "support_levels": [level1, level2, ...],
    "resistance_levels": [level1, level2, ...],
    "technical_signals": {
        "rsi": "overbought/oversold/neutral",
        "macd": "bullish/bearish/neutral",
        "moving_averages": "golden_cross/death_cross/neutral"
    },
    "key_factors": ["factor1", "factor2", ...],
    "confidence": 0.0-1.0,
    "risks": ["risk1", "risk2", ...]
}"""
    
    async def analyze(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Perform technical analysis
        
        Args:
            query: Analysis query
            context: Additional context with asset info
            
        Returns:
            Technical analysis results
        """
        try:
            # Translate query to English if needed
            user_language = context.get("language", "en") if context else "en"
            query_in_english = self.translation_service.translate_text(query, src=user_language, dest="en")
            
            asset_symbol = context.get("asset_symbol", "BTC") if context else "BTC"
            include_historical = context.get("include_historical", False) if context else False
            specific_date = context.get("specific_date") if context else None
            
            logger.info(f"Technical Analyst analyzing: {asset_symbol}")
            
            # Retrieve context using RAGService
            documents = await self.rag_service.query_collection(query_in_english, "crypto")
            logger.info(f"Retrieved {len(documents)} documents for query: {query_in_english}")
            
            # Collect price data and calculate indicators
            technical_data = await self._collect_technical_data(asset_symbol)
            
            # Get historical data for specific date if requested
            historical_context = {}
            if specific_date:
                historical_context = await self._get_historical_context(asset_symbol, specific_date)
            
            # Format prompt with enhanced data
            user_prompt = f"""Analyze technical indicators for {asset_symbol}: {query_in_english}

Technical Data:
{json.dumps(technical_data, indent=2)}

Retrieved Context:
{json.dumps(documents, indent=2)}

{f"Historical Context ({specific_date}):" + json.dumps(historical_context, indent=2) if historical_context else ""}

Provide comprehensive technical analysis with specific price levels, considering:
- Multi-timeframe trends (1h, 24h, 7d, 14d, 30d)
- Liquidity metrics and orderbook depth
- Volume analysis across top exchanges
- Technical indicator confluence
"""
            
            # Execute LLM call
            response = await self.execute_llm_call(
                system_prompt=self.get_system_prompt(),
                user_prompt=user_prompt
            )
            
            # Parse response
            try:
                analysis = json.loads(response)
            except json.JSONDecodeError:
                analysis = {
                    "summary": response,
                    "confidence": 0.6,
                    "key_factors": []
                }
            
            # Add raw technical data to response
            analysis["raw_technical_data"] = {
                "current_price": technical_data.get("current_price"),
                "price_changes": technical_data.get("price_changes", {}),
                "liquidity_metrics": technical_data.get("liquidity_metrics", {}),
                "technical_indicators": technical_data.get("technical_indicators", {}),
                "data_source": technical_data.get("source"),
                "data_type": technical_data.get("data_type")
            }
            
            # Translate response back to user's language
            translated_response = self.translation_service.translate_text(
                analysis.get("summary", ""), src="en", dest=user_language
            )
            analysis["summary"] = translated_response
            
            # Convert response to speech if requested
            if context.get("audio_output", False):
                audio_path = self.tts_service.text_to_speech(translated_response, language=user_language)
                analysis["audio_path"] = audio_path
            
            return self.format_output(
                analysis=analysis,
                confidence=analysis.get("confidence", 0.7),
                key_factors=analysis.get("key_factors", [])
            )
            
        except Exception as e:
            logger.error(f"Error in Technical Analyst: {str(e)}")
            return {
                "agent_name": self.name,
                "error": str(e),
                "confidence": 0.0
            }
    
    async def _collect_technical_data(self, symbol: str) -> Dict[str, Any]:
        """Collect and calculate technical indicators using CoinGecko"""
        try:
            return await self._get_coingecko_data(symbol)
        except Exception as error:
            logger.error(f"CoinGecko data collection failed: {str(error)}")
            return {}
    
    async def _get_historical_context(self, symbol: str, date: str) -> Dict[str, Any]:
        """
        Get historical data for a specific date
        
        Args:
            symbol: Crypto symbol (e.g., BTC, ETH)
            date: Date in dd-mm-yyyy format (e.g., '30-12-2022')
            
        Returns:
            Historical data for comparison
        """
        try:
            async with CoinGeckoClient() as coingecko:
                coin_id = coingecko.normalize_symbol(symbol)
                history = await coingecko.get_coin_history(coin_id, date)
                
                market_data = history.get('market_data', {})
                return {
                    "date": date,
                    "price": market_data.get('current_price', {}).get('usd', 0),
                    "market_cap": market_data.get('market_cap', {}).get('usd', 0),
                    "total_volume": market_data.get('total_volume', {}).get('usd', 0),
                    "available": True
                }
        except Exception as e:
            logger.error(f"Failed to get historical context for {date}: {str(e)}")
            return {"available": False, "error": str(e)}
    
    def _analyze_liquidity(self, tickers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze liquidity metrics from ticker data"""
        if not tickers:
            return {
                "available": False,
                "note": "Liquidity data unavailable"
            }
        
        try:
            # Extract key liquidity metrics
            total_volume = sum(float(t.get('converted_volume', {}).get('usd', 0)) for t in tickers[:10])
            
            # Orderbook depth analysis (2% depth)
            depth_data = [t for t in tickers if 'cost_to_move_up_usd' in t and 'cost_to_move_down_usd' in t]
            
            if depth_data:
                avg_cost_up = sum(float(t.get('cost_to_move_up_usd', 0)) for t in depth_data) / len(depth_data)
                avg_cost_down = sum(float(t.get('cost_to_move_down_usd', 0)) for t in depth_data) / len(depth_data)
                
                # Calculate bid-ask spread for top exchanges
                spreads = []
                for t in tickers[:5]:
                    bid = float(t.get('bid_ask_spread_percentage', 0))
                    if bid > 0:
                        spreads.append(bid)
                
                avg_spread = sum(spreads) / len(spreads) if spreads else 0
                
                return {
                    "available": True,
                    "top_10_exchanges_volume": round(total_volume, 2),
                    "avg_cost_to_move_up_2pct": round(avg_cost_up, 2),
                    "avg_cost_to_move_down_2pct": round(avg_cost_down, 2),
                    "avg_bid_ask_spread_pct": round(avg_spread, 4),
                    "liquidity_score": "high" if avg_spread < 0.1 else "medium" if avg_spread < 0.5 else "low",
                    "exchanges_analyzed": len(depth_data)
                }
            else:
                return {
                    "available": True,
                    "top_10_exchanges_volume": round(total_volume, 2),
                    "note": "Orderbook depth data unavailable"
                }
                
        except Exception as e:
            logger.error(f"Error analyzing liquidity: {str(e)}")
            return {
                "available": False,
                "error": str(e)
            }
    
    async def _get_coingecko_data(self, symbol: str) -> Dict[str, Any]:
        """Get data from CoinGecko and calculate indicators with enhanced market data"""
        async with CoinGeckoClient() as coingecko:
            # Convert symbol to CoinGecko ID
            coin_id = coingecko.normalize_symbol(symbol)
            
            # Get enhanced market data with multiple timeframes
            markets_data = await coingecko.get_coins_markets(
                coin_ids=[coin_id],
                vs_currency="usd",
                sparkline=True,
                price_change_percentage=["1h", "24h", "7d", "14d", "30d"]
            )
            
            # Get current price and 24h data
            simple_price = await coingecko.get_simple_price(
                coin_ids=[coin_id],
                include_24h_change=True,
                include_market_cap=True,
                include_24h_volume=True
            )
            
            # Get OHLC data for accurate technical indicators (up to 365 days)
            try:
                ohlc_data = await coingecko.get_coin_ohlc(
                    coin_id=coin_id,
                    vs_currency="usd",
                    days= '7'
                )
                use_ohlc = True
                logger.info(f"Retrieved {len(ohlc_data)} OHLC candles for {symbol}")
            except Exception as e:
                logger.warning(f"OHLC data unavailable, falling back to market_chart: {str(e)}")
                use_ohlc = False
                # Fallback to market_chart for closing prices
                market_chart = await coingecko.get_market_chart(
                    coin_id=coin_id,
                    vs_currency="usd",
                    days=200
                )
            
            # Get comprehensive coin data
            coin_data = await coingecko.get_coin_data(coin_id)
            
            # Get top tickers with orderbook depth for liquidity analysis
            try:
                tickers_data = await coingecko.get_coin_tickers(
                    coin_id=coin_id,
                    depth=True,
                    page=1
                )
                logger.info(f"Retrieved {len(tickers_data.get('tickers', []))} tickers for {symbol}")
            except Exception as e:
                logger.warning(f"Tickers data unavailable: {str(e)}")
                tickers_data = {"tickers": []}
        
        # Convert to DataFrame based on data type
        if use_ohlc:
            # OHLC format: [timestamp, open, high, low, close]
            df = pd.DataFrame(ohlc_data, columns=['timestamp', 'open', 'high', 'low', 'close'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        else:
            # Market chart fallback - extract price data
            prices = market_chart.get('prices', [])
            if not prices:
                raise ValueError("No price data available from CoinGecko")
            
            # Convert to DataFrame
            df = pd.DataFrame(prices, columns=['timestamp', 'close'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            # Approximate OHLC from closing prices using rolling windows
            df['high'] = df['close'].rolling(window=24, min_periods=1).max()
            df['low'] = df['close'].rolling(window=24, min_periods=1).min()
            df['open'] = df['close'].shift(1).fillna(df['close'])
        
        # Calculate indicators
        indicators = self._calculate_indicators(df)
        
        # Extract current data
        coin_price_data = simple_price.get(coin_id, {})
        current_price = coin_price_data.get('usd', 0)
        price_change_24h = coin_price_data.get('usd_24h_change', 0)
        volume_24h = coin_price_data.get('usd_24h_vol', 0)
        
        # Get 24h high/low from coin data
        market_data = coin_data.get('market_data', {})
        high_24h = market_data.get('high_24h', {}).get('usd', current_price)
        low_24h = market_data.get('low_24h', {}).get('usd', current_price)
        
        # Extract multi-timeframe price changes from markets data
        price_changes = {}
        if markets_data and len(markets_data) > 0:
            market_info = markets_data[0]
            price_changes = {
                "1h": market_info.get('price_change_percentage_1h_in_currency'),
                "24h": market_info.get('price_change_percentage_24h_in_currency'),
                "7d": market_info.get('price_change_percentage_7d_in_currency'),
                "14d": market_info.get('price_change_percentage_14d_in_currency'),
                "30d": market_info.get('price_change_percentage_30d_in_currency')
            }
            # Get sparkline data (7-day mini chart)
            sparkline = market_info.get('sparkline_in_7d', {}).get('price', [])
        else:
            sparkline = []
        
        # Analyze liquidity from tickers data
        liquidity_analysis = self._analyze_liquidity(tickers_data.get('tickers', []))
        
        return {
            "source": "coingecko",
            "data_type": "ohlc" if use_ohlc else "closing_prices",
            "current_price": current_price,
            "24h_change": price_change_24h,
            "24h_volume": volume_24h,
            "24h_high": high_24h,
            "24h_low": low_24h,
            "market_cap": coin_price_data.get('usd_market_cap', 0),
            "price_changes": price_changes,
            "sparkline_7d": sparkline[:10] if sparkline else [],  # First 10 points as sample
            "technical_indicators": indicators,
            "liquidity_metrics": liquidity_analysis,
            "data_points": len(df),
            "note": "Technical indicators calculated from OHLC data" if use_ohlc else "Technical indicators calculated from daily closing prices (CoinGecko limitation)"
        }
    
    def _calculate_indicators(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate technical indicators from DataFrame"""
        try:
            close = df['close']
            
            # RSI
            rsi_indicator = momentum.RSIIndicator(close)
            rsi = rsi_indicator.rsi().iloc[-1]
            
            # MACD
            macd_indicator = trend.MACD(close)
            macd = macd_indicator.macd().iloc[-1]
            macd_signal = macd_indicator.macd_signal().iloc[-1]
            
            # Moving Averages
            sma_50 = trend.SMAIndicator(close, window=min(50, len(close))).sma_indicator().iloc[-1]
            sma_200 = trend.SMAIndicator(close, window=min(200, len(close))).sma_indicator().iloc[-1]
            
            # Bollinger Bands
            bb = volatility.BollingerBands(close)
            bb_upper = bb.bollinger_hband().iloc[-1]
            bb_lower = bb.bollinger_lband().iloc[-1]
            
            return {
                "rsi": round(float(rsi), 2) if pd.notna(rsi) else None,
                "macd": round(float(macd), 2) if pd.notna(macd) else None,
                "macd_signal": round(float(macd_signal), 2) if pd.notna(macd_signal) else None,
                "sma_50": round(float(sma_50), 2) if pd.notna(sma_50) else None,
                "sma_200": round(float(sma_200), 2) if pd.notna(sma_200) else None,
                "bb_upper": round(float(bb_upper), 2) if pd.notna(bb_upper) else None,
                "bb_lower": round(float(bb_lower), 2) if pd.notna(bb_lower) else None
            }
            
        except Exception as e:
            logger.error(f"Error calculating indicators: {str(e)}")
            return {}


# Example usage for testing
async def main():
    """Simple example to test the Technical Analyst agent"""
    print("=" * 60)
    print("Testing Technical Analyst Agent (CoinGecko Only)")
    print("=" * 60)
    
    # Initialize the agent
    analyst = TechnicalAnalyst()
    
    # Test query
    query = "What is the current technical outlook for Bitcoin?"
    
    # Context with asset symbol and additional features
    context = {
        "asset_symbol": "BTC",
        "language": "en",
        "audio_output": False,
        "include_historical": True,
        "specific_date": "01-12-2024"  # Optional: compare with specific historical date
    }
    
    print(f"\nQuery: {query}")
    print(f"Asset: {context['asset_symbol']}")
    print("\nAnalyzing...\n")
    
    # Perform analysis
    result = await analyst.analyze(query=query, context=context)
    
    # Display results
    print("=" * 60)
    print("ANALYSIS RESULTS")
    print("=" * 60)
    print(json.dumps(result, indent=2))
    print("\n" + "=" * 60)


if __name__ == "__main__":
    import asyncio
    
    # Run the example
    asyncio.run(main())
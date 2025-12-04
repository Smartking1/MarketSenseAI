from typing import Dict, Any, Optional, List
import aiohttp
import os
import sys
try:
    from src.config.settings import get_settings
    from src.utilities.logger import get_logger
    from src.error_trace.exceptions import ExternalAPIError
except ModuleNotFoundError:
    # Allow running this module directly (e.g. `python src/adapters/external/coingecko_client.py`)
    # by adding the repository root (parent of `src`) to `sys.path` and retrying imports.
    import sys
    import os

    _repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    if _repo_root not in sys.path:
        sys.path.insert(0, _repo_root)

    from src.config.settings import get_settings
    from src.utilities.logger import get_logger
    from src.error_trace.exceptions import ExternalAPIError

logger = get_logger(__name__)

# Defer loading application Settings until the client is instantiated.
# Also support loading a local `.env` file from the repository root so
# running this module directly picks up keys stored there.
settings = None


def _load_dotenv_at_repo_root() -> None:
    """Load `.env` from repository root into os.environ for missing keys.

    This is deliberately minimal (no external dependency) and will not
    overwrite existing environment variables.
    """
    try:
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        dotenv_path = os.path.join(repo_root, ".env")
        if not os.path.exists(dotenv_path):
            return

        with open(dotenv_path, "r", encoding="utf-8") as fh:
            for raw in fh:
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = val
    except Exception:
        # If anything goes wrong while reading .env, fail silently — the
        # application environment may be managed externally.
        return


class CoinGeckoClient:
    """Client for CoinGecko API"""
    
    BASE_URL = "https://pro-api.coingecko.com/api/v3"
    
    def __init__(self, api_key: Optional[str] = None):
        if api_key is not None:
            self.api_key = api_key
        else:
            # Load .env (if present) then attempt to read settings
            _load_dotenv_at_repo_root()
            try:
                self.api_key = get_settings().coingecko_api_key
            except Exception:
                # If settings validation fails or is unavailable, fall back
                # to None — CoinGecko public endpoints still work without a key.
                self.api_key = None

        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def _request(
        self,
        endpoint: str,
        params: Optional[Dict] = None
    ) -> Any:
        """Make API request"""
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        url = f"{self.BASE_URL}{endpoint}"
        headers = {}
        
        if self.api_key:
            headers["x-cg-pro-api-key"] = self.api_key
        
        try:
            async with self.session.get(
                url,
                params=params,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                
                if response.status == 429:
                    raise ExternalAPIError(
                        message="CoinGecko rate limit exceeded",
                        api_name="coingecko",
                        status_code=429
                    )
                
                if response.status != 200:
                    text = await response.text()
                    raise ExternalAPIError(
                        message=f"CoinGecko API error: {text}",
                        api_name="coingecko",
                        status_code=response.status
                    )
                
                return await response.json()
                
        except aiohttp.ClientError as e:
            logger.error(f"CoinGecko API request error: {str(e)}")
            raise ExternalAPIError(
                message=f"CoinGecko connection error: {str(e)}",
                api_name="coingecko"
            )
    
    async def get_coin_data(self, coin_id: str) -> Dict[str, Any]:
        """
        Get comprehensive data for a coin
        
        Args:
            coin_id: CoinGecko coin ID (e.g., 'bitcoin', 'ethereum')
            
        Returns:
            Coin data including price, market cap, volume, etc.
        """
        endpoint = f"/coins/{coin_id}"
        params = {
            "localization": "false",
            "tickers": "false",
            "market_data": "true",
            "community_data": "true",
            "developer_data": "false"
        }
        return await self._request(endpoint, params)
    
    async def get_coin_history(
        self,
        coin_id: str,
        date: str,
        localization: bool = False
    ) -> Dict[str, Any]:
        """
        Get historical data (name, price, market, stats) at a given date
        
        Args:
            coin_id: CoinGecko coin ID (e.g., 'bitcoin', 'ethereum')
            date: Date in dd-mm-yyyy format (e.g., '30-12-2022')
            localization: Include localized languages in response
            
        Returns:
            Historical coin data for the specified date
        """
        endpoint = f"/coins/{coin_id}/history"
        params = {
            "date": date,
            "localization": str(localization).lower()
        }
        return await self._request(endpoint, params)
    
    async def get_coin_market_chart_range(
        self,
        coin_id: str,
        vs_currency: str = "usd",
        from_timestamp: int = None,
        to_timestamp: int = None
    ) -> Dict[str, Any]:
        """
        Get historical market data within a date range
        
        Args:
            coin_id: CoinGecko coin ID
            vs_currency: Target currency (default: 'usd')
            from_timestamp: Unix timestamp (seconds) for start date
            to_timestamp: Unix timestamp (seconds) for end date
            
        Returns:
            Historical price, market cap, and volume data for date range
        """
        endpoint = f"/coins/{coin_id}/market_chart/range"
        params = {
            "vs_currency": vs_currency,
            "from": from_timestamp,
            "to": to_timestamp
        }
        return await self._request(endpoint, params)
    
    async def get_coin_ohlc(
        self,
        coin_id: str,
        vs_currency: str = "usd",
        days: int = 7
    ) -> List[List[float]]:
        """
        Get OHLC (Open, High, Low, Close) chart data
        
        Args:
            coin_id: CoinGecko coin ID
            vs_currency: Target currency (default: 'usd')
            days: Number of days (1/7/14/30/90/180/365/max)
            
        Returns:
            List of [timestamp, open, high, low, close] candles
        """
        endpoint = f"/coins/{coin_id}/ohlc"
        params = {
            "vs_currency": vs_currency,
            "days": days
            
        }
        return await self._request(endpoint, params)
    
    async def get_coin_tickers(
        self,
        coin_id: str,
        exchange_ids: Optional[List[str]] = None,
        include_exchange_logo: bool = False,
        page: int = 1,
        depth: bool = False
    ) -> Dict[str, Any]:
        """
        Get coin tickers (paginated to 100 items per page)
        
        Args:
            coin_id: CoinGecko coin ID
            exchange_ids: Filter by exchange IDs (optional)
            include_exchange_logo: Include exchange logo URLs
            page: Page number (default: 1)
            depth: Include 2% orderbook depth (cost_to_move_up_usd, cost_to_move_down_usd)
            
        Returns:
            Ticker data from various exchanges
        """
        endpoint = f"/coins/{coin_id}/tickers"
        params = {
            "include_exchange_logo": str(include_exchange_logo).lower(),
            "page": page,
            "depth": str(depth).lower()
        }
        
        if exchange_ids:
            params["exchange_ids"] = ",".join(exchange_ids)
        
        return await self._request(endpoint, params)
    
    async def get_coins_list(
        self,
        include_platform: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get list of all supported coins with id, name, and symbol
        
        Args:
            include_platform: Include platform contract addresses
            
        Returns:
            List of all coins [{'id': 'bitcoin', 'symbol': 'btc', 'name': 'Bitcoin'}, ...]
        """
        endpoint = "/coins/list"
        params = {
            "include_platform": str(include_platform).lower()
        }
        return await self._request(endpoint, params)
    
    async def get_coins_markets(
        self,
        vs_currency: str = "usd",
        coin_ids: Optional[List[str]] = None,
        category: Optional[str] = None,
        order: str = "market_cap_desc",
        per_page: int = 100,
        page: int = 1,
        sparkline: bool = False,
        price_change_percentage: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get current market data for multiple coins (paginated)
        
        Args:
            vs_currency: Target currency
            coin_ids: Filter by coin IDs (optional)
            category: Filter by category (optional)
            order: Sort order (market_cap_desc, volume_desc, id_asc, etc.)
            per_page: Results per page (1-250, default: 100)
            page: Page number
            sparkline: Include sparkline 7d data
            price_change_percentage: Include price change intervals (1h, 24h, 7d, 14d, 30d, 200d, 1y)
            
        Returns:
            List of coin market data
        """
        endpoint = "/coins/markets"
        params = {
            "vs_currency": vs_currency,
            "order": order,
            "per_page": per_page,
            "page": page,
            "sparkline": str(sparkline).lower()
        }
        
        if coin_ids:
            params["ids"] = ",".join(coin_ids)
        
        if category:
            params["category"] = category
        
        if price_change_percentage:
            params["price_change_percentage"] = ",".join(price_change_percentage)
        
        return await self._request(endpoint, params)
    
    async def get_coin_by_contract(
        self,
        platform_id: str,
        contract_address: str
    ) -> Dict[str, Any]:
        """
        Get coin data by contract address
        
        Args:
            platform_id: Platform ID (e.g., 'ethereum', 'binance-smart-chain')
            contract_address: Token contract address
            
        Returns:
            Coin data including price, market cap, volume, etc.
        """
        endpoint = f"/coins/{platform_id}/contract/{contract_address}"
        params = {
            "localization": "false",
            "tickers": "false",
            "market_data": "true",
            "community_data": "true",
            "developer_data": "false"
        }
        return await self._request(endpoint, params)
    
    async def get_simple_price(
        self,
        coin_ids: List[str],
        vs_currencies: List[str] = ["usd"],
        include_24h_change: bool = True,
        include_market_cap: bool = True,
        include_24h_volume: bool = True
    ) -> Dict[str, Any]:
        """
        Get simple price data for multiple coins
        
        Args:
            coin_ids: List of coin IDs
            vs_currencies: List of target currencies
            include_24h_change: Include 24h price change
            include_market_cap: Include market cap
            include_24h_volume: Include 24h volume
            
        Returns:
            Price data for requested coins
        """
        endpoint = "/simple/price"
        params = {
            "ids": ",".join(coin_ids),
            "vs_currencies": ",".join(vs_currencies),
            "include_24hr_change": str(include_24h_change).lower(),
            "include_market_cap": str(include_market_cap).lower(),
            "include_24hr_vol": str(include_24h_volume).lower()
        }
        return await self._request(endpoint, params)
    
    async def get_market_chart(
        self,
        coin_id: str,
        vs_currency: str = "usd",
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get historical market data
        
        Args:
            coin_id: CoinGecko coin ID
            vs_currency: Target currency
            days: Number of days of data
            
        Returns:
            Historical price, market cap, and volume data
        """
        endpoint = f"/coins/{coin_id}/market_chart"
        params = {
            "vs_currency": vs_currency,
            "days": days
        }
        return await self._request(endpoint, params)
    
    async def get_trending(self) -> Dict[str, Any]:
        """Get trending coins"""
        endpoint = "/search/trending"
        return await self._request(endpoint)
    
    async def get_global_data(self) -> Dict[str, Any]:
        """Get global cryptocurrency data"""
        endpoint = "/global"
        return await self._request(endpoint)
    
    def normalize_symbol(self, symbol: str) -> str:
        """
        Convert symbol to CoinGecko coin ID
        
        Args:
            symbol: Crypto symbol (e.g., BTC, ETH)
            
        Returns:
            CoinGecko coin ID
        """
        mapping = {
            "BTC": "bitcoin",
            "ETH": "ethereum",
            "BNB": "binancecoin",
            "ADA": "cardano",
            "SOL": "solana",
            "XRP": "ripple",
            "DOT": "polkadot",
            "DOGE": "dogecoin",
            "AVAX": "avalanche-2",
            "MATIC": "matic-network",
            "LINK": "chainlink",
            "UNI": "uniswap"
        }
        return mapping.get(symbol.upper(), symbol.lower())


if __name__ == "__main__":
    """
    Example usage:

    This small example demonstrates how to instantiate the async
    `CoinGeckoClient`, fetch simple prices for Bitcoin and Ethereum,
    and print a small global snapshot. Run the file directly to try it:

        python -m src.adapters.external.coingecko_client

    Note: the project typically runs these clients inside an async
    runtime (e.g. an application worker). This example is intentionally
    minimal and meant for local experimentation.
    """

    import asyncio

    async def _example():
        async with CoinGeckoClient() as client:
            # Get simple price for bitcoin and ethereum in USD
            prices = await client.get_simple_price(["bitcoin", "ethereum"], vs_currencies=["usd"])
            print("Simple prices:", prices)

            # Get a small global snapshot
            global_data = await client.get_global_data()
            print("Global market data (summary):", global_data.get("data") if isinstance(global_data, dict) else global_data)
            
            # Get historical data for Bitcoin on a specific date
            history = await client.get_coin_history("bitcoin", "30-12-2022")
            print("\nBitcoin history (30-12-2022):", history.get("name"), history.get("market_data", {}).get("current_price"))
            
            # Get OHLC data for Ethereum (7 days)
            ohlc = await client.get_coin_ohlc("ethereum", days=7)
            print(f"\nEthereum OHLC data points: {len(ohlc)}")
            
            # Get top 10 coins by market cap
            markets = await client.get_coins_markets(per_page=10, page=1)
            print("\nTop 10 coins by market cap:")
            for coin in markets[:5]:  # Print first 5
                print(f"  {coin['name']}: ${coin['current_price']:,.2f}")

    asyncio.run(_example())

# """
# DefiLlama Client Module
# Handles all API calls to DefiLlama for on-chain data retrieval
# Integrated with centralized configuration
# """

# import requests
# import json
# import logging
# from datetime import datetime, timedelta
# from typing import Dict, List, Optional, Tuple
# import time
# import sys
# import os

# # Add parent directory to path for imports
# sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# try:
#     from config.settings import (
#         DEFILLAMA_BASE_URL,
#         DEFILLAMA_TIMEOUT,
#         DEFILLAMA_RETRY_ATTEMPTS,
#         DEFILLAMA_RETRY_DELAY,
#         PRIMARY_PROTOCOLS,
#         MONITORED_PROTOCOLS,
#         PRIORITY_PROTOCOLS,
#         get_protocol_config,
#         validate_protocol_slug
#     )
# except ImportError:
#     # Fallback if config not available
#     DEFILLAMA_BASE_URL = "https://api.llama.fi"
#     DEFILLAMA_TIMEOUT = 10
#     DEFILLAMA_RETRY_ATTEMPTS = 3
#     DEFILLAMA_RETRY_DELAY = 2
#     PRIMARY_PROTOCOLS = {}
#     MONITORED_PROTOCOLS = []
#     PRIORITY_PROTOCOLS = []

# # Setup logging
# logger = logging.getLogger(__name__)


# class DefiLlamaClient:
#     """Client for interacting with DefiLlama API endpoints"""
    
#     def __init__(self, base_url: str = DEFILLAMA_BASE_URL, 
#                  timeout: int = DEFILLAMA_TIMEOUT,
#                  retry_attempts: int = DEFILLAMA_RETRY_ATTEMPTS,
#                  retry_delay: int = DEFILLAMA_RETRY_DELAY):
#         """
#         Initialize the DefiLlama client with configuration
        
#         Args:
#             base_url: Base URL for DefiLlama API
#             timeout: Request timeout in seconds
#             retry_attempts: Number of retry attempts for failed requests
#             retry_delay: Delay between retries in seconds
#         """
#         self.base_url = base_url
#         self.timeout = timeout
#         self.retry_attempts = retry_attempts
#         self.retry_delay = retry_delay
        
#         self.session = requests.Session()
#         self.session.headers.update({
#             'User-Agent': 'DeFiLiquidationMonitor/1.0'
#         })
        
#         logger.info(f"DefiLlamaClient initialized with base_url: {base_url}")
    
#     def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
#         """
#         Make HTTP request with retry logic and error handling
        
#         Args:
#             endpoint: API endpoint path
#             params: Optional query parameters
            
#         Returns:
#             JSON response as dictionary
#         """
#         url = f"{self.base_url}{endpoint}"
        
#         for attempt in range(self.retry_attempts):
#             try:
#                 logger.debug(f"Making request to {url} (attempt {attempt + 1}/{self.retry_attempts})")
#                 response = self.session.get(url, params=params, timeout=self.timeout)
#                 response.raise_for_status()
                
#                 logger.debug(f"Request successful: {endpoint}")
#                 return response.json()
                
#             except requests.exceptions.Timeout:
#                 logger.warning(f"Request timeout for {endpoint}")
#                 if attempt < self.retry_attempts - 1:
#                     logger.info(f"Retrying in {self.retry_delay}s...")
#                     time.sleep(self.retry_delay)
                    
#             except requests.exceptions.ConnectionError as e:
#                 logger.warning(f"Connection error for {endpoint}: {str(e)}")
#                 if attempt < self.retry_attempts - 1:
#                     logger.info(f"Retrying in {self.retry_delay}s...")
#                     time.sleep(self.retry_delay)
                    
#             except requests.exceptions.HTTPError as e:
#                 logger.error(f"HTTP error for {endpoint}: {str(e)}")
#                 return {}
                
#             except requests.exceptions.RequestException as e:
#                 logger.error(f"Request failed for {endpoint}: {str(e)}")
#                 if attempt < self.retry_attempts - 1:
#                     logger.info(f"Retrying in {self.retry_delay}s...")
#                     time.sleep(self.retry_delay)
                    
#             except ValueError as e:
#                 logger.error(f"Invalid JSON response from {endpoint}: {str(e)}")
#                 return {}
        
#         logger.error(f"Failed to fetch {endpoint} after {self.retry_attempts} attempts")
#         return {}
    
#     def get_all_protocols(self) -> List[Dict]:
#         """
#         Fetch list of all protocols from DefiLlama
        
#         Returns:
#             List of protocol objects with metadata
#         """
#         logger.info("Fetching all protocols from DefiLlama")
#         endpoint = "/protocols"
#         response = self._make_request(endpoint)
        
#         if isinstance(response, list):
#             logger.info(f"Retrieved {len(response)} protocols")
#             return response
        
#         logger.warning("Invalid response format for /protocols endpoint")
#         return []
    
#     def get_protocol_info(self, protocol_slug: str) -> Dict:
#         """
#         Get comprehensive protocol information
#         Endpoint: /protocol/{protocol}
        
#         Args:
#             protocol_slug: Protocol identifier (e.g., 'aave', 'compound')
            
#         Returns:
#             Dictionary containing:
#                 - name: Protocol name
#                 - symbol: Protocol ticker
#                 - description: Protocol description
#                 - tvl: Current TVL in USD
#                 - tvlChart: Historical TVL data [[timestamp, tvl], ...]
#                 - chains: List of chains protocol operates on
#                 - category: Protocol category (Lending, DEX, etc.)
#                 - audits: Audit information
#                 - website: Official website
#         """
#         logger.info(f"Fetching protocol info for {protocol_slug}")
        
#         if not validate_protocol_slug(protocol_slug):
#             logger.warning(f"Protocol {protocol_slug} not in configured protocols")
        
#         endpoint = f"/protocol/{protocol_slug}"
#         response = self._make_request(endpoint)
        
#         if not response:
#             logger.error(f"No data returned for protocol {protocol_slug}")
#             return {}
        
#         logger.debug(f"Protocol info retrieved for {protocol_slug}")
#         return response
    
#     def get_protocol_tvl(self, protocol_slug: str) -> List[Tuple[int, float]]:
#         """
#         Get historical TVL for a protocol
#         Endpoint: /tvl/{protocol}
        
#         Args:
#             protocol_slug: Protocol identifier
            
#         Returns:
#             List of [timestamp, tvl] pairs sorted chronologically
#         """
#         logger.info(f"Fetching TVL history for {protocol_slug}")
#         endpoint = f"/tvl/{protocol_slug}"
#         response = self._make_request(endpoint)
        
#         if isinstance(response, list):
#             logger.info(f"Retrieved {len(response)} TVL data points for {protocol_slug}")
#             return response
        
#         logger.warning(f"Invalid TVL response format for {protocol_slug}")
#         return []
    
#     def get_protocol_tvl_by_chain(self, protocol_slug: str) -> Dict:
#         """
#         Get TVL breakdown by blockchain for a protocol
        
#         Args:
#             protocol_slug: Protocol identifier
            
#         Returns:
#             Dictionary mapping chain names to TVL values
#         """
#         logger.info(f"Fetching TVL by chain for {protocol_slug}")
#         protocol_data = self.get_protocol_info(protocol_slug)
#         tvl_by_chain = {}
        
#         if 'chainTvls' in protocol_data and isinstance(protocol_data['chainTvls'], dict):
#             for chain, tvl in protocol_data['chainTvls'].items():
#                 tvl_by_chain[chain] = tvl
        
#         logger.debug(f"TVL breakdown retrieved for {len(tvl_by_chain)} chains")
#         return tvl_by_chain
    
#     def extract_metrics(self, protocol_slug: str) -> Dict:
#         """
#         Extract key fundamental metrics for a protocol
        
#         Args:
#             protocol_slug: Protocol identifier
            
#         Returns:
#             Dictionary containing:
#                 - name: Protocol name
#                 - current_tvl: Current TVL in billions USD
#                 - current_tvl_usd: Current TVL in USD
#                 - tvl_change_24h: % change in last 24 hours
#                 - tvl_change_7d: % change in last 7 days
#                 - tvl_history: List of [timestamp, tvl] pairs
#                 - chains: List of supported chains
#                 - chain_breakdown: TVL by chain
#                 - category: Protocol category
#                 - description: Protocol description
#                 - website: Official website
#                 - timestamp: When data was collected
#                 - status: 'success' or 'error'
#         """
#         logger.info(f"Extracting metrics for {protocol_slug}")
        
#         protocol_info = self.get_protocol_info(protocol_slug)
#         tvl_history = self.get_protocol_tvl(protocol_slug)
#         tvl_by_chain = self.get_protocol_tvl_by_chain(protocol_slug)
        
#         if not protocol_info or not tvl_history:
#             logger.error(f"Failed to extract metrics for {protocol_slug}: missing data")
#             return {
#                 'status': 'error',
#                 'protocol': protocol_slug,
#                 'timestamp': datetime.now().isoformat(),
#                 'error': 'Failed to fetch required data'
#             }
        
#         current_tvl = protocol_info.get('tvl', 0)
        
#         # Calculate TVL changes
#         tvl_change_24h = self._calculate_tvl_change(tvl_history, hours=24)
#         tvl_change_7d = self._calculate_tvl_change(tvl_history, days=7)
        
#         metrics = {
#             'status': 'success',
#             'name': protocol_info.get('name', 'Unknown'),
#             'symbol': protocol_info.get('symbol', ''),
#             'protocol_slug': protocol_slug,
#             'current_tvl': round(current_tvl / 1e9, 3),  # Convert to billions
#             'current_tvl_usd': current_tvl,
#             'tvl_change_24h': tvl_change_24h,
#             'tvl_change_7d': tvl_change_7d,
#             'tvl_history': tvl_history,
#             'tvl_history_count': len(tvl_history),
#             'chains': protocol_info.get('chains', []),
#             'chain_breakdown': tvl_by_chain,
#             'category': protocol_info.get('category', 'Unknown'),
#             'description': protocol_info.get('description', ''),
#             'website': protocol_info.get('url', ''),
#             'audit_links': protocol_info.get('audits', []),
#             'timestamp': datetime.now().isoformat()
#         }
        
#         logger.info(f"Metrics extracted for {protocol_slug}: TVL=${metrics['current_tvl']}B, "
#                    f"24h change={tvl_change_24h}%")
        
#         return metrics
    
#     def _calculate_tvl_change(self, tvl_history: List[Tuple[int, float]], 
#                               hours: Optional[int] = None, 
#                               days: Optional[int] = None) -> float:
#         """
#         Calculate percentage change in TVL over time period
        
#         Args:
#             tvl_history: List of [timestamp, tvl] pairs
#             hours: Number of hours to look back (optional)
#             days: Number of days to look back (optional)
            
#         Returns:
#             Percentage change (positive or negative)
#         """
#         if not tvl_history or len(tvl_history) < 2:
#             logger.debug("TVL history too short for change calculation")
#             return 0.0
        
#         # Calculate cutoff timestamp
#         now = datetime.now()
#         if hours:
#             cutoff = now - timedelta(hours=hours)
#         elif days:
#             cutoff = now - timedelta(days=days)
#         else:
#             return 0.0
        
#         cutoff_timestamp = int(cutoff.timestamp())
        
#         # Find TVL at cutoff time
#         past_tvl = None
#         for timestamp, tvl in tvl_history:
#             if timestamp <= cutoff_timestamp:
#                 past_tvl = tvl
        
#         # Current TVL is last entry
#         current_tvl = tvl_history[-1][1]
        
#         if past_tvl is None or past_tvl == 0:
#             logger.debug(f"No historical TVL data found for {hours}h or {days}d lookback")
#             return 0.0
        
#         change_percent = ((current_tvl - past_tvl) / past_tvl) * 100
#         return round(change_percent, 2)
    
#     def get_lending_protocols(self, limit: int = 20) -> List[Dict]:
#         """
#         Get top lending protocols by TVL
        
#         Args:
#             limit: Maximum number of protocols to return
            
#         Returns:
#             List of lending protocol objects sorted by TVL (descending)
#         """
#         logger.info(f"Fetching top {limit} lending protocols")
#         all_protocols = self.get_all_protocols()
#         lending_protocols = [p for p in all_protocols if p.get('category') == 'Lending']
#         result = sorted(lending_protocols, key=lambda x: x.get('tvl', 0), reverse=True)[:limit]
        
#         logger.info(f"Retrieved {len(result)} lending protocols")
#         return result
    
#     def get_monitored_protocols_metrics(self) -> Dict[str, Dict]:
#         """
#         Get metrics for all configured monitored protocols
        
#         Returns:
#             Dictionary mapping protocol slugs to their metrics
#         """
#         logger.info(f"Fetching metrics for {len(MONITORED_PROTOCOLS)} monitored protocols")
#         metrics_data = {}
        
#         for protocol_slug in MONITORED_PROTOCOLS:
#             try:
#                 metrics = self.extract_metrics(protocol_slug)
#                 metrics_data[protocol_slug] = metrics
#             except Exception as e:
#                 logger.error(f"Error extracting metrics for {protocol_slug}: {str(e)}")
#                 metrics_data[protocol_slug] = {
#                     'status': 'error',
#                     'error': str(e)
#                 }
        
#         logger.info(f"Retrieved metrics for {len([m for m in metrics_data.values() if m.get('status') == 'success'])} protocols")
#         return metrics_data
    
#     def get_priority_protocols_metrics(self) -> Dict[str, Dict]:
#         """
#         Get metrics for high-priority protocols only
        
#         Returns:
#             Dictionary mapping protocol slugs to their metrics
#         """
#         logger.info(f"Fetching metrics for {len(PRIORITY_PROTOCOLS)} priority protocols")
#         metrics_data = {}
        
#         for protocol_slug in PRIORITY_PROTOCOLS:
#             try:
#                 metrics = self.extract_metrics(protocol_slug)
#                 metrics_data[protocol_slug] = metrics
#             except Exception as e:
#                 logger.error(f"Error extracting metrics for {protocol_slug}: {str(e)}")
#                 metrics_data[protocol_slug] = {
#                     'status': 'error',
#                     'error': str(e)
#                 }
        
#         logger.info(f"Retrieved metrics for {len([m for m in metrics_data.values() if m.get('status') == 'success'])} priority protocols")
#         return metrics_data
    
#     def compare_protocols(self, protocol_slugs: List[str]) -> Dict[str, Dict]:
#         """
#         Compare metrics across multiple protocols
        
#         Args:
#             protocol_slugs: List of protocol identifiers to compare
            
#         Returns:
#             Dictionary mapping protocol slugs to their metrics
#         """
#         logger.info(f"Comparing {len(protocol_slugs)} protocols")
#         comparison = {}
        
#         for slug in protocol_slugs:
#             try:
#                 metrics = self.extract_metrics(slug)
#                 comparison[slug] = metrics
#             except Exception as e:
#                 logger.error(f"Error comparing {slug}: {str(e)}")
#                 comparison[slug] = {'status': 'error', 'error': str(e)}
        
#         return comparison
    
#     def export_to_json(self, data: Dict, filepath: str) -> bool:
#         """
#         Export collected metrics to JSON file
        
#         Args:
#             data: Dictionary of metrics to export
#             filepath: Output file path
            
#         Returns:
#             True if successful, False otherwise
#         """
#         try:
#             # Create directory if it doesn't exist
#             os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
#             with open(filepath, 'w') as f:
#                 json.dump(data, f, indent=2)
            
#             logger.info(f"Data exported to {filepath}")
#             return True
#         except Exception as e:
#             logger.error(f"Failed to export data: {str(e)}")
#             return False
    
#     def get_protocol_config(self, protocol_slug: str) -> Dict:
#         """
#         Get configuration for a specific protocol
        
#         Args:
#             protocol_slug: Protocol identifier
            
#         Returns:
#             Protocol configuration dictionary
#         """
#         return get_protocol_config(protocol_slug)


# # ==================== EXAMPLE USAGE ====================
# if __name__ == "__main__":
#     # Configure logging for demo
#     logging.basicConfig(
#         level=logging.INFO,
#         format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
#     )
    
#     client = DefiLlamaClient()
    
#     # Example 1: Fetch monitored protocols
#     print("\n" + "="*60)
#     print("📊 FETCHING MONITORED PROTOCOLS METRICS")
#     print("="*60)
#     monitored_metrics = client.get_monitored_protocols_metrics()
    
#     for protocol, metrics in monitored_metrics.items():
#         if metrics.get('status') == 'success':
#             print(f"\n{protocol.upper()}")
#             print(f"  TVL: ${metrics['current_tvl']:.3f}B")
#             print(f"  24h Change: {metrics['tvl_change_24h']:+.2f}%")
#             print(f"  7d Change: {metrics['tvl_change_7d']:+.2f}%")
#             print(f"  Chains: {', '.join(metrics['chains'][:3])}")
    
#     # Example 2: Get priority protocols
#     print("\n" + "="*60)
#     print("⭐ FETCHING PRIORITY PROTOCOLS")
#     print("="*60)
#     priority_metrics = client.get_priority_protocols_metrics()
    
#     print(f"\nPriority Protocols ({len(PRIORITY_PROTOCOLS)}):")
#     for protocol, metrics in priority_metrics.items():
#         if metrics.get('status') == 'success':
#             print(f"  • {metrics['name']}: ${metrics['current_tvl']:.3f}B")
    
#     # Example 3: Compare protocols
#     print("\n" + "="*60)
#     print("⚖️ COMPARING AAVE VS COMPOUND")
#     print("="*60)
#     comparison = client.compare_protocols(['aave', 'compound'])
    
#     for protocol, metrics in comparison.items():
#         if metrics.get('status') == 'success':
#             print(f"\n{metrics['name'].upper()}")
#             print(f"  TVL: ${metrics['current_tvl']:.3f}B")
#             print(f"  Category: {metrics['category']}")
#             print(f"  Website: {metrics['website']}")
    
#     # Example 4: Export to JSON
#     print("\n" + "="*60)
#     print("💾 EXPORTING DATA")
#     print("="*60)
#     export_success = client.export_to_json(
#         monitored_metrics,
#         'exports/json/monitored_protocols_metrics.json'
#     )


# import http.client

# conn = http.client.HTTPSConnection("api.llama.fi")

# conn.request("GET", "/protocols")

# res = conn.getresponse()
# data = res.read()

# print(data.decode("utf-8"))


import http.client

conn = http.client.HTTPSConnection("api.llama.fi")

conn.request("GET", "/protocol/uniswap")

res = conn.getresponse()
data = res.read()

print(data.decode("utf-8"))

#hsitorical price of tokens
import http.client

conn = http.client.HTTPSConnection("coins.llama.fi")

conn.request("GET", "/prices/historical/%7Btimestamp%7D/%7Bcoins%7D")

res = conn.getresponse()
data = res.read()

print(data.decode("utf-8"))


#current price of tokens
import http.client

conn = http.client.HTTPSConnection("coins.llama.fi")

conn.request("GET", "/prices/current/%7Bcoins%7D")

res = conn.getresponse()
data = res.read()

print(data.decode("utf-8"))
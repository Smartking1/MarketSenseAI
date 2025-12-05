"""
Cloud Run startup wrapper
Ensures app starts even if external services are unavailable
"""
import os
import sys
import logging

# Configure logging immediately
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Disable heavy logging during startup
os.environ.setdefault('LOG_LEVEL', 'WARNING')

# Ensure critical environment variables have defaults
os.environ.setdefault('PORT', '8080')
os.environ.setdefault('ENVIRONMENT', 'production')
os.environ.setdefault('DEBUG', 'False')

# Mock missing API keys with empty strings to prevent validation errors
api_keys = [
    'OPENAI_API_KEY', 'GROQ_API_KEY', 'GEMINI_API_KEY', 'CLAUDE_API_KEY',
    'FRED_API_KEY', 'NEWSAPI_KEY', 'COINGECKO_API_KEY', 
    'BINANCE_API_KEY', 'BINANCE_API_SECRET', 'SERPER_API_KEY', 'SERPAPI_KEY'
]

for key in api_keys:
    if key not in os.environ:
        os.environ[key] = ''

logger.info(f"Environment: {os.environ.get('ENVIRONMENT')}")
logger.info(f"Port: {os.environ.get('PORT')}")
logger.info(f"Debug: {os.environ.get('DEBUG')}")

# Now import and run the app
try:
    import uvicorn
    
    logger.info("Starting FastAPI application...")
    
    uvicorn.run(
        "src.adapters.web.fastapi_app:app",
        host="0.0.0.0",
        port=int(os.environ.get('PORT', 8080)),
        log_level="info"
    )
except Exception as e:
    logger.error(f"Failed to start application: {str(e)}", exc_info=True)
    sys.exit(1)

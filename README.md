"""
#  MarketSenseAI: MarketSenseAI is a Multi-Asset.  

Advanced multi-agent AI system for comprehensive Forex and Cryptocurrency market analysis using RAG and specialized AI agents.

## 🌟 Features

- **Multi-Agent Architecture**: Coordinated specialist agents (Macro, Technical, Sentiment, Synthesis)
- **RAG-Powered**: Context-aware analysis using ChromaDB vector store
- **Real-time Data**: Integration with Binance, CoinGecko, FRED, and NewsAPI
- **Clean Architecture**: Domain-Driven Design with proper separation of concerns
- **Production-Ready**: Docker, Redis caching, PostgreSQL, comprehensive error handling
- **Interactive Frontend**: Beautiful web interface with real-time charts

## 📋 Prerequisites

- Python 3.10+
- Docker & Docker Compose
- PostgreSQL 15+
- Redis 7+
- OpenAI, Groq, claude, gemini API Keys

## 🚀 Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd multi-asset-ai
```

### 2. Install Backend Dependencies (venv + uv)

Create a project-local virtual environment and install Python dependencies with uv:

```powershell
# create venv (Windows PowerShell)
python -m venv .venv

# activate (PowerShell)
source .\.venv\Scripts\Activate

# or (Command Prompt)
# .venv\Scripts\activate.bat

# Install / sync dependencies from requirements.txt using uv (recommended)
uv pip sync requirements.txt

# Alternative: install without removing extras
# uv pip install -r requirements.txt
```

> Note: uv keeps the environment in sync with the requirements file. Make sure `.venv` is activated before running uv commands.

### 3. Start the Backend (development)

With the virtual environment activated run:

```bash
python -m src.entry_scripts.start_api
```

This starts the FastAPI server (default: http://localhost:8000). Use CTRL+C to stop.

### 4. Run the Frontend (Next.js)

The frontend lives in the `frontend/` directory and is a Next.js app.

```powershell
# from project root
cd frontend

# install dependencies (use pnpm, npm or yarn depending on your setup)
pnpm install
# or
npm install

# set local env (example)
# create a .env.local file in frontend/ or set environment variables in your shell:
# NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1

# run dev server (Windows)
npm run dev
# or with pnpm
pnpm dev
```

Open: http://localhost:3000

### 5. Access the Application

- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Frontend: http://localhost:3000

## 📁 Project Structure

```
multi-asset-ai/
├── src/
│   ├── adapters/              # External integrations & web
│   │   ├── external/          # API clients (Binance, CoinGecko, etc.)
│   │   └── web/               # FastAPI routes
│   ├── application/           # Business logic
│   │   ├── agents/            # AI agents
│   │   └── services/          # Application services
│   ├── config/                # Configuration
│   ├── domain/                # Domain entities & value objects
│   │   ├── entities/          # Business entities
│   │   └── value_objects/     # Immutable value objects
│   ├── infrastructure/        # Database & cache
│   ├── services/              # Background services
│   ├── utilities/             # Helper functions
│   └── entry_scripts/         # Entry points
├── frontend/                  # Web interface
├── tests/                     # Unit tests
└── docs/                      # Documentation
```

## 🔑 API Endpoints

### Health Check
```bash
GET /api/v1/health
```

### Analyze Market
```bash
POST /api/v1/analyze
Content-Type: application/json

{
  "query": "Should I buy Bitcoin now?",
  "asset": "BTC",
  "timeframe": "medium"
}
```

### Quick Analysis
```bash
GET /api/v1/analyze/BTC?timeframe=medium
```

### Get Market Data
```bash
GET /api/v1/market/BTC
```

### Get Trending Assets
```bash
GET /api/v1/trending
```

## The Multi AI Agents

### 1. Macro Analyst
- Analyzes macroeconomic conditions
- Monitors central bank policies
- Tracks inflation, employment, GDP
- Sources: FRED Economic Data

### 2. Technical Analyst
- Price action and chart patterns
- Technical indicators (RSI, MACD, MAs)
- Support/resistance levels
- Sources: Binance, market data APIs

### 3. Sentiment Analyst
- News sentiment analysis
- Market narratives
- Social media trends
- Sources: NewsAPI, financial news

### 4. Synthesis Agent
- Coordinates all specialist agents
- Identifies agreements/contradictions
- Provides investment thesis
- Actionable recommendations

##  Data Sources(Via their APIs)

- **Binance**: Real-time crypto prices and market data
- **CoinGecko**: Comprehensive crypto information
- **FRED**: Federal Reserve economic data
- **NewsAPI**: Financial news and sentiment

## Testing

Run tests:
```bash
poetry run pytest
```

With coverage:
```bash
poetry run pytest --cov=src tests/
```

## Example Usage

### Python SDK

```python
from src.application.services.analysis_service import AnalysisService
from src.domain.value_objects.timeframe import TimeframeVO

async def analyze():
    service = AnalysisService()
    
    result = await service.analyze(
        query="Should I buy Ethereum?",
        asset_symbol="ETH",
        timeframe=TimeframeVO.medium()
    )
    
    print(f"Outlook: {result.outlook}")
    print(f"Confidence: {result.overall_confidence}")
    print(f"Action: {result.trading_action}")

asyncio.run(analyze())
```

### cURL

```bash
curl -X POST http://localhost:8000/api/v1/analyze \\
  -H "Content-Type: application/json" \\
  -d '{
    "query": "Analyze Bitcoin market conditions",
    "asset": "BTC",
    "timeframe": "medium"
  }'
```

## 🔧 Configuration

Key settings in `.env`:

```env
# API Settings
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True

# Agent Settings
MAX_AGENT_ITERATIONS=5
AGENT_TEMPERATURE=0.7
LLM_MODEL=gpt-4

# Data Collection
DATA_UPDATE_INTERVAL=3600
CACHE_TTL=1800

# Logging
LOG_LEVEL=INFO
LOG_FILE=./src/logs/app.log
```

## 🐳 Docker Deployment

### Production Build

```bash
# Build image
docker build -t multi-asset-ai:latest .

# Run with docker-compose
docker-compose -f docker-compose.prod.yml up -d
```

### Environment Variables

Set in docker-compose or .env file:
- Database credentials
- API keys
- Service ports

## Performance

- **Caching**: Redis caches analysis results for 30 minutes
- **Parallel Processing**: All agents run concurrently
- **Rate Limiting**: Built-in protection for external APIs
- **Database**: Indexed queries for fast retrieval

## Security

- API key validation
- Rate limiting on endpoints
- Input validation with Pydantic
- SQL injection protection (SQLAlchemy)
- CORS configuration

## Development

### Code Style

```bash
# Format code
black src/

# Lint
flake8 src/

# Type checking
mypy src/
```

### Adding New Agents

1. Create new agent in `src/application/agents/`
2. Inherit from `BaseAgent`
3. Implement `analyze()` and `get_system_prompt()`
4. Register in `SynthesisAgent`

### Adding New Data Sources

1. Create client in `src/adapters/external/`
2. Implement async methods
3. Add to `DataService`
4. Update `DataCollector` for background collection

## Troubleshooting

### Database Connection Issues

```bash
# Check PostgreSQL
docker exec -it multiasset-postgres psql -U user -d multiasset

# Test connection
python -c "from src.infrastructure.database import get_db; db = get_db(); print(db.health_check())"
```

### Redis Connection Issues

```bash
# Check Redis
docker exec -it multiasset-redis redis-cli ping

# Test connection
python -c "from src.infrastructure.cache import get_cache; cache = get_cache(); print(cache.health_check())"
```

### API Key Issues

Verify your API keys are valid:
```bash
# Test OpenAI
curl https://api.openai.com/v1/models -H "Authorization: Bearer $OPENAI_API_KEY"

# Test FRED
curl "https://api.stlouisfed.org/fred/series?series_id=GNPCA&api_key=$FRED_API_KEY&file_type=json"
```

##  Documentation

- [Architecture Guide](docs/architecture.md)
- [API Reference](docs/api.md)
- [Agent Development](docs/agents.md)
- [Deployment Guide](docs/deployment.md)

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see LICENSE file.

## ⚠️ Disclaimer

This system is for informational purposes only. It does not constitute financial advice. Always do your own research and consult with qualified financial advisors before making investment decisions.

##  Acknowledgments

- OpenAI, claude, groq, gemini for GPT models
- LangChain community
- ChromaDB for vector storage
- FastAPI framework
- All open-source contributors

##  Support

- Issues: [GitHub Issues](https://github.com/yourusername/multi-asset-ai/issues)
- Email: odelolasolomon5@gmail.com
- Documentation: [Wiki](https://github.com/yourusername/multi-asset-ai/wiki)

---

**Built with Love by MarketSense Team**
"""

# MarketSenseAI: Multi-Asset Financial Intelligence System

Advanced multi-agent AI system for comprehensive cryptocurrency market analysis using specialized AI agents, RAG (Retrieval-Augmented Generation), and real-time data integration.

## 🌟 Key Features

- **Multi-Agent Architecture**: Coordinated specialist agents (Macro, Technical, Sentiment, Synthesis) working together
- **RAG-Powered Analysis**: Context-aware insights using ChromaDB vector store
- **Real-time Market Data**: Integration with Binance, CoinGecko, FRED, Reddit, and news APIs
- **Conversational Memory**: Maintains context across the last 5 conversations per user
- **Interactive Frontend**: Next.js web interface with conversation history sidebar
- **Clean Architecture**: Domain-Driven Design with proper separation of concerns
- **Production-Ready**: PostgreSQL database, Redis caching, comprehensive error handling

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.10+** (Python 3.11 recommended)
- **Node.js 18+** and npm/pnpm
- **PostgreSQL 15+** (or SQLite for development)
- **Redis 7+** (optional, for caching)
- **API Keys**:
  - Groq API (for AI agents)
  - Google Generative AI (for frontend chat)
  - CoinGecko API (for crypto data)
  - FRED API (for economic data)
  - NewsAPI/Serper (for news sentiment)

## 🚀 Quick Start Guide

### 1. Clone the Repository

```bash
git clone <repository-url>
cd multi-asset-ai
```

### 2. Backend Setup

#### Install Python Dependencies

We use `uv` for fast dependency management. First, create and activate a virtual environment:

**Windows (PowerShell):**
```powershell
# Create virtual environment
python -m venv uv

# Activate
.\uv\Scripts\Activate
```

**macOS/Linux:**
```bash
# Create virtual environment
python -m venv uv

# Activate
source uv/bin/activate
```

#### Install Dependencies with uv

```bash
# Install uv if you haven't already
pip install uv

# Sync dependencies (recommended - keeps environment clean)
uv pip sync requirements.txt

# Alternative: install without removing extras
# uv pip install -r requirements.txt
```

#### Configure Environment Variables

Create a `.env` file in the project root:

```env
# API Keys
GROQ_API_KEY=your_groq_api_key_here
FRED_API_KEY=your_fred_api_key_here
COINGECKO_API_KEY=your_coingecko_api_key_here
NEWSAPI_KEY=your_newsapi_key_here
SERPER_API_KEY=your_serper_api_key_here

# Database (SQLite for development)
DATABASE_URL=sqlite:///./multiasset.db

# Redis (optional)
REDIS_URL=redis://localhost:6379/0

# API Settings
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True

# Agent Settings
LLM_MODEL=llama-3.3-70b-versatile
AGENT_TEMPERATURE= None
MAX_AGENT_ITERATIONS=None

# Logging
LOG_LEVEL=INFO
```

#### Start the Backend Server

```bash
python -m src.entry_scripts.start_api
```

The API will be available at:
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/

### 3. Frontend Setup

Navigate to the frontend directory and install dependencies:

```bash
cd frontend

# Install dependencies (choose one)
npm install
# or
pnpm install
```

#### Configure Frontend Environment

Create `frontend/.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_BASE_API_URL=http://localhost:8000
GOOGLE_GENERATIVE_AI_API_KEY=your_google_ai_key_here
```

> **Important**: Enable the Google Generative Language API for your project at:
> https://console.developers.google.com/apis/api/generativelanguage.googleapis.com

#### Start the Frontend Development Server

```bash
npm run dev
# or
pnpm dev
```

The frontend will be available at: **http://localhost:3000**

### 4. Access the Application

Open your browser and navigate to:
- **Frontend UI**: http://localhost:3000/chat
- **API Documentation**: http://localhost:8000/docs

## 📁 Project Structure

```
multi-asset-ai/
├── src/                           # Backend source code
│   ├── adapters/                  # External integrations & web layer
│   │   ├── external/              # API clients (Binance, CoinGecko, NewsAPI, etc.)
│   │   └── web/                   # FastAPI routes and application
│   ├── application/               # Business logic layer
│   │   ├── agents/                # AI agents (Macro, Technical, Sentiment, Synthesis)
│   │   └── services/              # Application services (Analysis, RAG, Memory, etc.)
│   ├── config/                    # Configuration and constants
│   ├── domain/                    # Domain layer (entities & value objects)
│   │   ├── entities/              # Business entities (Analysis, Conversation, etc.)
│   │   └── value_objects/         # Immutable value objects (Timeframe, etc.)
│   ├── infrastructure/            # Infrastructure layer
│   │   ├── database.py            # Database manager (PostgreSQL/SQLite)
│   │   ├── cache.py               # Redis cache manager
│   │   └── orm.py                 # SQLAlchemy ORM mappings
│   ├── utilities/                 # Helper functions and utilities
│   └── entry_scripts/             # Application entry points
│       └── start_api.py           # FastAPI server startup
├── frontend/                      # Next.js web interface
│   ├── app/                       # Next.js app directory
│   │   ├── api/chat/              # Chat API route
│   │   └── chat/                  # Chat page
│   ├── components/                # React components
│   │   ├── ai-elements/           # AI chat UI components
│   │   ├── ui/                    # shadcn/ui components
│   │   └── sidebar.tsx            # Conversation history sidebar
│   └── lib/                       # Utility functions
├── tests/                         # Unit and integration tests
├── docs/                          # Documentation
├── requirements.txt               # Python dependencies
└── README.md                      # This file
```

## 🔑 API Endpoints

### Core Analysis Endpoints

#### Health Check
```bash
GET /
GET /api/v1/health
```

#### Analyze Market (Primary Endpoint)
```bash
POST /api/v1/analyze
Content-Type: application/json

{
  "query": "Should I invest in buying Bitcoin now?",
  "asset": "BTC",
  "timeframe": "medium",
  "session_id": "optional-session-uuid",
  "conversation_id": "optional-conversation-uuid"
}
```

**Response:**
```json
{
  "query": "Should I invest in buying Bitcoin now?",
  "asset_symbol": "BTC",
  "analysis": {
    "executive_summary": "...",
    "investment_thesis": "...",
    "outlook": "bullish",
    "overall_confidence": 0.75,
    "trading_action": "buy",
    "position_sizing": "medium",
    "macro_analysis": {...},
    "technical_analysis": {...},
    "sentiment_analysis": {...}
  },
  "confidence": 0.75,
  "timestamp": "2025-12-07T16:00:00"
}
```

#### Quick Analysis
```bash
GET /api/v1/analyze/BTC?timeframe=medium
```

### Conversation Management Endpoints

#### Get User Conversations
```bash
GET /api/v1/conversations/user/{user_id}
```

#### Get Conversation History
```bash
GET /api/v1/conversations/sessions/{session_id}/conversations/{conversation_id}
```

#### Create Session
```bash
POST /api/v1/conversations/sessions
{
  "user_id": "user-uuid"
}
```

### Market Data Endpoints

#### Get Market Data
```bash
GET /api/v1/market/{symbol}
```

#### Get Trending Assets
```bash
GET /api/v1/trending
```

## 🤖 The Multi-Agent System

### Agent Architecture

The system uses four specialized AI agents that work together to provide comprehensive market analysis:

#### 1. **Macro Analyst** (`MacroAnalyst`)
- **Purpose**: Analyzes macroeconomic conditions affecting crypto markets
- **Data Sources**: 
  - FRED Economic Data (interest rates, inflation, GDP)
  - Crypto-specific news (regulatory changes, institutional adoption)
- **Output**: Macroeconomic context, policy impacts, institutional trends

#### 2. **Technical Analyst** (`TechnicalAnalyst`)
- **Purpose**: Analyzes price action and technical indicators
- **Data Sources**:
  - CoinGecko API (price, volume, market cap)
  - Historical price data
- **Analysis**:
  - Multi-timeframe trends (1h, 24h, 7d, 14d, 30d)
  - Technical indicators (RSI, MACD, Moving Averages)
  - Support/resistance levels
  - Liquidity metrics and orderbook depth

#### 3. **Sentiment Analyst** (`SentimentAnalyst`)
- **Purpose**: Gauges market sentiment from news and social media
- **Data Sources**:
  - Reddit (r/Bitcoin, r/Cryptocurrency, etc.)
  - News APIs (Serper, NewsAPI)
  - Financial news websites
- **Analysis**:
  - News sentiment scoring
  - Social media trends
  - Market narratives
  - Fear & Greed indicators

#### 4. **Synthesis Agent** (`SynthesisAgent`)
- **Purpose**: Coordinates all agents and synthesizes final recommendations
- **Process**:
  1. Distributes query to all specialist agents (parallel execution)
  2. Collects and analyzes agent outputs
  3. Identifies agreements and contradictions
  4. Generates unified investment thesis
  5. Provides actionable recommendations with confidence scores
- **Output**: Executive summary, trading action, position sizing, risk assessment

### RAG (Retrieval-Augmented Generation)(Was Optional)

The system uses ChromaDB for vector storage and retrieval:

- **Collections**:
  - `macro_data`: Economic indicators and policy data
  - `crypto_data`: Cryptocurrency market data
  - `news_sentiment`: News articles and sentiment analysis
- **Embedding Model**: `all-MiniLM-L6-v2` (SentenceTransformers)
- **Purpose**: Provides context-aware analysis by retrieving relevant historical data

### Conversational Memory

- **Implementation**: LangChain `ConversationBufferWindowMemory`
- **Window Size**: Last 5 conversations per user
- **Storage**: In-memory with Redis caching
- **Purpose**: Maintains context across multiple queries in a session

## 🎯 Usage Examples

### Python SDK Example

```python
import asyncio
from src.application.services.analysis_service import AnalysisService
from src.domain.value_objects.timeframe import TimeframeVO

async def analyze_bitcoin():
    service = AnalysisService()
    
    result = await service.analyze(
        query="Should I buy Bitcoin now?",
        asset_symbol="BTC",
        timeframe=TimeframeVO.from_string("medium"),
        context={
            "session_id": "my-session-id",
            "conversation_id": "my-conversation-id"
        }
    )
    
    print(f"Outlook: {result.outlook}")
    print(f"Confidence: {result.overall_confidence}")
    print(f"Action: {result.trading_action}")
    print(f"Position Size: {result.position_sizing}")
    print(f"\nExecutive Summary:\n{result.executive_summary}")

# Run the analysis
asyncio.run(analyze_bitcoin())
```

### cURL Example

```bash
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Analyze Bitcoin market conditions",
    "asset": "BTC",
    "timeframe": "medium"
  }'
```

### Frontend Usage

1. Navigate to http://localhost:3000/chat
2. Type your investment question (e.g., "Should I buy Bitcoin?")
3. Select the asset and timeframe
4. Click send or press Enter
5. View the comprehensive analysis from all agents


## 🔧 Configuration

### Environment Variables Reference

#### Required API Keys

```env
# AI Model (Groq)
GROQ_API_KEY=gsk_...

# Frontend AI (Google Gemini)
GOOGLE_GENERATIVE_AI_API_KEY=AIza...

# Data Sources
COINGECKO_API_KEY=CG-...
FRED_API_KEY=...
NEWSAPI_KEY=...
SERPER_API_KEY=...
```

#### Database Configuration

```env
# PostgreSQL (Production)
DATABASE_URL=postgresql://user:password@localhost:5432/multiasset

# SQLite (Development)
DATABASE_URL=sqlite:///./multiasset.db
```

#### Redis Configuration

```env
REDIS_URL=redis://localhost:6379/0
CACHE_TTL=1800  # 30 minutes
```

#### Agent Configuration

```env
LLM_MODEL=llama-3.3-70b-versatile
AGENT_TEMPERATURE=0.7
MAX_AGENT_ITERATIONS=5
```



## 🐳 Docker Deployment (Optional)

### Using Docker Compose

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Services

- **API**: FastAPI backend (port 8000)
- **Frontend**: Next.js app (port 3000)
- **PostgreSQL**: Database (port 5432)
- **Redis**: Cache (port 6379)

## 🔍 Troubleshooting

### Common Issues

#### 1. Database Connection Error

**Error**: `sqlite3.OperationalError: no such table: analysis`

**Solution**: The database tables are created automatically on first run. If you see this error, restart the backend:

```bash
# Stop the server (Ctrl+C)
# Start again
python -m src.entry_scripts.start_api
```

#### 2. Frontend API Connection Error

**Error**: `Failed to fetch` or `Network Error`

**Solution**: Ensure backend is running and environment variables are correct:

```bash
# Check backend is running
curl http://localhost:8000/

# Verify frontend .env.local
cat frontend/.env.local
```

#### 3. Google AI API Error

**Error**: `Generative Language API has not been used in project...`

**Solution**: Enable the API at:
https://console.developers.google.com/apis/api/generativelanguage.googleapis.com

#### 4. Missing Dependencies

**Error**: `ModuleNotFoundError: No module named '...'`

**Solution**: Reinstall dependencies:

```bash
# Activate virtual environment
source uv/Scripts/Activate  # Windows
source uv/bin/activate      # macOS/Linux

# Reinstall
uv pip sync requirements.txt
```

#### 5. Port Already in Use

**Error**: `Address already in use`

**Solution**: Kill the process using the port:

```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# macOS/Linux
lsof -ti:8000 | xargs kill -9
```

## 📊 Performance Optimization

- **Caching**: Redis caches analysis results for 30 minutes
- **Parallel Processing**: All agents run concurrently using `asyncio.gather()`
- **Database Indexing**: Indexed queries on `asset_symbol`, `created_at`
- **Rate Limiting**: Built-in protection for external API calls
- **Connection Pooling**: SQLAlchemy connection pool for database efficiency

## 🔒 Security Features

- **API Key Validation**: All external API calls use secure key management
- **Input Validation**: Pydantic models validate all API inputs
- **SQL Injection Protection**: SQLAlchemy ORM prevents SQL injection
- **CORS Configuration**: Configurable CORS for frontend-backend communication
- **Environment Variables**: Sensitive data stored in `.env` (not committed to git)

## 🛠️ Development

### Code Style

```bash
# Format code
black src/

# Lint
flake8 src/

# Type checking
mypy src/
```

### Adding a New Agent

1. Create new agent file in `src/application/agents/`
2. Inherit from `BaseAgent`
3. Implement required methods:
   ```python
   class MyNewAgent(BaseAgent):
       async def analyze(self, query: str, context: dict) -> dict:
           # Your analysis logic
           pass
       
       def get_system_prompt(self) -> str:
           # Your agent's system prompt
           pass
   ```
4. Register in `SynthesisAgent.analyze()`

### Adding a New Data Source

1. Create client in `src/adapters/external/`
2. Implement async methods for data fetching
3. Add to `DataService` or relevant service
4. Update agent to use new data source

## 📚 Additional Documentation

- **Architecture Guide**: See `docs/architecture.md` (coming soon)
- **API Reference**: http://localhost:8000/docs (when running)
- **Agent Development**: See agent source files for examples

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes and commit: `git commit -m 'Add amazing feature'`
4. Push to your branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

### Contribution Guidelines

- Follow existing code style (use `black` for formatting)
- Add tests for new features
- Update documentation as needed
- Ensure all tests pass before submitting PR

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ Disclaimer

**Important**: This system is for informational and educational purposes only. It does NOT give financial advice. 

- Always conduct your own research (DYOR)
- Consult with qualified financial advisors before making investment decisions
- Cryptocurrency investments carry significant risk
- Past performance does not guarantee future results

## 🙏 Acknowledgments

- **AI Providers**: OpenAI, Anthropic (Claude), Groq, Google (Gemini)
- **Frameworks**: LangChain, FastAPI, Next.js, React
- **Data Sources**: CoinGecko, Binance, FRED, NewsAPI, Reddit
- **Storage**: ChromaDB, PostgreSQL, Redis
- **UI Components**: shadcn/ui, Radix UI
- **Community**: All open-source contributors

## 📞 Support & Contact

- **Issues**: [GitHub Issues](https://github.com/yourusername/multi-asset-ai/issues)
- **Email**: odelolasolomon5@gmail.com
- **Documentation**: See `/docs` directory

---

**Built with ❤️ by the MarketSense Team**

*Empowering informed investment decisions through AI-powered multi-agent analysis*

import asyncio
from src.application.services.news_aggregator import NewsAggregator

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))


async def quick_test():
    async with NewsAggregator() as agg:
        articles = await agg.fetch_from_source('cryptofaxreport')
        print(f"✅ Got {len(articles)} articles!")
        if articles:
            print(f"First article: {articles[0].title}")
        return articles

# Run it
asyncio.run(quick_test())
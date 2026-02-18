import asyncio
import logging
import feedparser
import urllib.parse
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

class ContextRetrievalService:
    """
    Retrieves Real-Time News via Google News RSS.
    Uses 'feedparser' for parsing XML, which is significantly more stable
    than scraping HTML (yfinance).
    """
    
    def __init__(self):
        # ThreadPool to keep the Event Loop non-blocking during network I/O
        self.executor = ThreadPoolExecutor(max_workers=5)
        self.base_url = "https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"

    def _fetch_rss_news(self, symbol: str) -> str:
        """
        Worker function to fetch and parse RSS feed.
        """
        try:
            # Construct Query: "MSFT stock news" or "BTC-USD crypto"
            query_str = f"{symbol} stock news"
            if symbol.upper() in ["BTC", "ETH", "SOL"]:
                query_str = f"{symbol} crypto news"
                
            encoded_query = urllib.parse.quote(query_str)
            feed_url = self.base_url.format(query=encoded_query)
            
            # Parse XML
            feed = feedparser.parse(feed_url)
            
            if not feed.entries:
                return "CONTEXT: No recent specific news found via RSS."

            # Extract Top 3 Headlines + Summary
            headlines = []
            for entry in feed.entries[:3]:
                title = entry.title
                source = entry.source.get('title', 'Unknown Source')
                # Google News RSS titles are usually "Headline - Source"
                headlines.append(f"[{source}] {title}")
            
            return " | ".join(headlines)
            
        except Exception as e:
            logger.error(f"RSS Fetch Failed for {symbol}: {e}")
            return "CONTEXT: News data temporarily unavailable."

    async def retrieve_context(self, symbol: str) -> str:
        """
        Async wrapper for the blocking feedparser call.
        """
        loop = asyncio.get_running_loop()
        try:
            context_str = await loop.run_in_executor(
                self.executor, 
                self._fetch_rss_news, 
                symbol
            )
            logger.info(f"Retrieved RSS Context for {symbol}: {context_str[:50]}...")
            return f"LATEST_NEWS: {context_str}"
            
        except Exception as e:
            logger.error(f"Context Service Error: {e}")
            return "LATEST_NEWS: Unavailable"
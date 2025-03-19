import duckdb
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Cache:
    def __init__(self):
        try:
            self.conn = duckdb.connect('cache.db')
            self.setup_database()
        except Exception as e:
            logger.error(f"Failed to initialize database: {str(e)}")
            raise

    def setup_database(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS article_cache (
                url VARCHAR PRIMARY KEY,
                text_content TEXT,
                summary TEXT,
                og_metadata JSON,
                created_at TIMESTAMP
            )
        """)

    def get_cached_article(self, url: str):
        try:
            result = self.conn.execute("""
                SELECT text_content, summary, og_metadata
                FROM article_cache
                WHERE url = ?
            """, [url]).fetchone()
            
            if result:
                logger.info(f"Cache hit for URL: {url}")
                return {
                    "text_content": result[0],
                    "summary": result[1],
                    "og_metadata": json.loads(result[2])
                }
            logger.info(f"Cache miss for URL: {url}")
            return None
        except Exception as e:
            logger.error(f"Error retrieving from cache: {str(e)}")
            return None

    def cache_article(self, url: str, text_content: str, summary: str, og_metadata: dict):
        try:
            self.conn.execute("""
                INSERT INTO article_cache (url, text_content, summary, og_metadata, created_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT (url) DO UPDATE SET
                    text_content = excluded.text_content,
                    summary = excluded.summary,
                    og_metadata = excluded.og_metadata,
                    created_at = excluded.created_at
            """, [url, text_content, summary, json.dumps(og_metadata), datetime.now()])
            logger.info(f"Successfully cached article: {url}")
        except Exception as e:
            logger.error(f"Error caching article: {str(e)}")
            raise
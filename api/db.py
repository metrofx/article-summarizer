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
                    "og_metadata": json.loads(result[2]) if result[2] else {}
                }
            logger.info(f"Cache miss for URL: {url}")
            return None
        except Exception as e:
            logger.error(f"Error retrieving from cache: {str(e)}")
            return None

    def cache_article(self, url: str, text_content: str = None, summary: str = None, og_metadata: dict = None):
        try:
            # First check if we have existing data to preserve any fields not being updated
            existing = self.get_cached_article(url)

            if existing:
                # Use existing values for any parameters that are None
                text_content = text_content if text_content is not None else existing.get("text_content")
                summary = summary if summary is not None else existing.get("summary")
                og_metadata = og_metadata if og_metadata is not None else existing.get("og_metadata")

            # Ensure we have valid values (empty string/dict instead of None)
            text_content = text_content or ""
            summary = summary or ""
            og_metadata = og_metadata or {}

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
            return True
        except Exception as e:
            logger.error(f"Error caching article: {str(e)}")
            return False

    def get_latest_articles(self, limit: int = 5):
        try:
            result = self.conn.execute("""
                SELECT url, og_metadata, created_at
                FROM article_cache
                WHERE og_metadata IS NOT NULL
                ORDER BY created_at DESC
                LIMIT ?
            """, [limit]).fetchall()

            articles = []
            for row in result:
                url, og_metadata, created_at = row
                metadata = json.loads(og_metadata) if og_metadata else {}
                articles.append({
                    "url": url,
                    "metadata": metadata,
                    "created_at": created_at.isoformat() if created_at else None
                })
            return articles
        except Exception as e:
            logger.error(f"Error getting latest articles: {str(e)}")
            return []
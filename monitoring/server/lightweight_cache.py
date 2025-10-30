"""
Lightweight SQLite-based cache system to replace Redis
"""
import sqlite3
import json
import time
import threading
from typing import Any, Optional, Dict
import logging

logger = logging.getLogger(__name__)

class LightweightCache:
    """SQLite-based cache system to replace Redis functionality"""
    
    def __init__(self, db_path: str = "cache.db"):
        self.db_path = db_path
        self.lock = threading.RLock()
        self._init_db()
    
    def _init_db(self):
        """Initialize the SQLite database"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create cache table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    expires_at REAL,
                    created_at REAL
                )
            ''')
            
            # Create index for expiration cleanup
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_expires_at ON cache(expires_at)
            ''')
            
            conn.commit()
            conn.close()
    
    def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """Set a key-value pair with optional expiration"""
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # Serialize value
                if isinstance(value, (dict, list)):
                    value_str = json.dumps(value)
                else:
                    value_str = str(value)
                
                # Calculate expiration time
                expires_at = None
                if expire:
                    expires_at = time.time() + expire
                
                # Insert or update
                cursor.execute('''
                    INSERT OR REPLACE INTO cache (key, value, expires_at, created_at)
                    VALUES (?, ?, ?, ?)
                ''', (key, value_str, expires_at, time.time()))
                
                conn.commit()
                conn.close()
                return True
        except Exception as e:
            logger.error(f"Error setting cache key {key}: {e}")
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """Get a value by key"""
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT value, expires_at FROM cache 
                    WHERE key = ? AND (expires_at IS NULL OR expires_at > ?)
                ''', (key, time.time()))
                
                result = cursor.fetchone()
                conn.close()
                
                if result:
                    value_str, expires_at = result
                    # Try to deserialize JSON, fallback to string
                    try:
                        return json.loads(value_str)
                    except (json.JSONDecodeError, TypeError):
                        return value_str
                return None
        except Exception as e:
            logger.error(f"Error getting cache key {key}: {e}")
            return None
    
    def delete(self, key: str) -> bool:
        """Delete a key"""
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('DELETE FROM cache WHERE key = ?', (key,))
                deleted = cursor.rowcount > 0
                
                conn.commit()
                conn.close()
                return deleted
        except Exception as e:
            logger.error(f"Error deleting cache key {key}: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists and is not expired"""
        return self.get(key) is not None
    
    def clear_expired(self) -> int:
        """Clear expired entries and return count of deleted items"""
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('DELETE FROM cache WHERE expires_at IS NOT NULL AND expires_at <= ?', (time.time(),))
                deleted = cursor.rowcount
                
                conn.commit()
                conn.close()
                return deleted
        except Exception as e:
            logger.error(f"Error clearing expired cache: {e}")
            return 0
    
    def get_all_keys(self) -> list:
        """Get all non-expired keys"""
        try:
            with self.lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT key FROM cache 
                    WHERE expires_at IS NULL OR expires_at > ?
                ''', (time.time(),))
                
                keys = [row[0] for row in cursor.fetchall()]
                conn.close()
                return keys
        except Exception as e:
            logger.error(f"Error getting cache keys: {e}")
            return []
    
    def cleanup(self):
        """Clean up expired entries"""
        deleted = self.clear_expired()
        if deleted > 0:
            logger.info(f"Cleaned up {deleted} expired cache entries")

# Global cache instance
cache = LightweightCache()

# Convenience functions to match Redis-like interface
def set_cache(key: str, value: Any, expire: Optional[int] = None) -> bool:
    """Set a cache value"""
    return cache.set(key, value, expire)

def get_cache(key: str) -> Optional[Any]:
    """Get a cache value"""
    return cache.get(key)

def delete_cache(key: str) -> bool:
    """Delete a cache value"""
    return cache.delete(key)

def cache_exists(key: str) -> bool:
    """Check if cache key exists"""
    return cache.exists(key)

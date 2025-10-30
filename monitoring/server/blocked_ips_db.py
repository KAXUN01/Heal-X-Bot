"""
Blocked IPs Database Manager
Handles persistence of blocked IP addresses with metadata
"""

import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class BlockedIPsDatabase:
    """Manages blocked IP addresses in SQLite database"""
    
    def __init__(self, db_path: str = "data/blocked_ips.db"):
        """Initialize database connection"""
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()
    
    def _init_database(self):
        """Initialize database schema"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Create blocked_ips table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS blocked_ips (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ip_address TEXT UNIQUE NOT NULL,
                    attack_count INTEGER DEFAULT 1,
                    threat_level TEXT DEFAULT 'Medium',
                    attack_type TEXT,
                    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    blocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    blocked_by TEXT DEFAULT 'system',
                    reason TEXT,
                    is_blocked BOOLEAN DEFAULT 1,
                    unblocked_at TIMESTAMP,
                    unblocked_by TEXT,
                    notes TEXT
                )
            """)
            
            # Create index for faster lookups
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_ip_address 
                ON blocked_ips(ip_address)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_is_blocked 
                ON blocked_ips(is_blocked)
            """)
            
            # Create blocked_ips_history table for audit trail
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS blocked_ips_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ip_address TEXT NOT NULL,
                    action TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    performed_by TEXT,
                    reason TEXT
                )
            """)
            
            logger.info(f"Database initialized at {self.db_path}")
    
    def block_ip(self, ip_address: str, attack_count: int = 1, 
                 threat_level: str = "Medium", attack_type: str = None,
                 reason: str = None, blocked_by: str = "system") -> bool:
        """Block an IP address"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if IP already exists
                cursor.execute(
                    "SELECT id, is_blocked FROM blocked_ips WHERE ip_address = ?",
                    (ip_address,)
                )
                existing = cursor.fetchone()
                
                if existing:
                    # Update existing record
                    cursor.execute("""
                        UPDATE blocked_ips 
                        SET attack_count = attack_count + ?,
                            threat_level = ?,
                            attack_type = ?,
                            last_seen = CURRENT_TIMESTAMP,
                            is_blocked = 1,
                            blocked_at = CURRENT_TIMESTAMP,
                            blocked_by = ?,
                            reason = ?
                        WHERE ip_address = ?
                    """, (attack_count, threat_level, attack_type, blocked_by, reason, ip_address))
                    
                    action = "re-blocked" if existing['is_blocked'] == 0 else "updated"
                else:
                    # Insert new record
                    cursor.execute("""
                        INSERT INTO blocked_ips 
                        (ip_address, attack_count, threat_level, attack_type, reason, blocked_by)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (ip_address, attack_count, threat_level, attack_type, reason, blocked_by))
                    
                    action = "blocked"
                
                # Add to history
                cursor.execute("""
                    INSERT INTO blocked_ips_history 
                    (ip_address, action, performed_by, reason)
                    VALUES (?, ?, ?, ?)
                """, (ip_address, action, blocked_by, reason))
                
                logger.info(f"IP {ip_address} {action}")
                return True
                
        except Exception as e:
            logger.error(f"Error blocking IP {ip_address}: {e}")
            return False
    
    def unblock_ip(self, ip_address: str, unblocked_by: str = "admin", 
                   reason: str = None) -> bool:
        """Unblock an IP address"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if IP exists and is blocked
                cursor.execute(
                    "SELECT id FROM blocked_ips WHERE ip_address = ? AND is_blocked = 1",
                    (ip_address,)
                )
                
                if not cursor.fetchone():
                    logger.warning(f"IP {ip_address} not found or already unblocked")
                    return False
                
                # Update record
                cursor.execute("""
                    UPDATE blocked_ips 
                    SET is_blocked = 0,
                        unblocked_at = CURRENT_TIMESTAMP,
                        unblocked_by = ?
                    WHERE ip_address = ?
                """, (unblocked_by, ip_address))
                
                # Add to history
                cursor.execute("""
                    INSERT INTO blocked_ips_history 
                    (ip_address, action, performed_by, reason)
                    VALUES (?, 'unblocked', ?, ?)
                """, (ip_address, unblocked_by, reason))
                
                logger.info(f"IP {ip_address} unblocked by {unblocked_by}")
                return True
                
        except Exception as e:
            logger.error(f"Error unblocking IP {ip_address}: {e}")
            return False
    
    def is_blocked(self, ip_address: str) -> bool:
        """Check if an IP is currently blocked"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT is_blocked FROM blocked_ips WHERE ip_address = ?",
                    (ip_address,)
                )
                result = cursor.fetchone()
                return result['is_blocked'] == 1 if result else False
        except Exception as e:
            logger.error(f"Error checking if IP {ip_address} is blocked: {e}")
            return False
    
    def get_blocked_ips(self, include_unblocked: bool = False) -> List[Dict[str, Any]]:
        """Get all blocked IPs"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if include_unblocked:
                    query = "SELECT * FROM blocked_ips ORDER BY blocked_at DESC"
                else:
                    query = "SELECT * FROM blocked_ips WHERE is_blocked = 1 ORDER BY blocked_at DESC"
                
                cursor.execute(query)
                rows = cursor.fetchall()
                
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Error getting blocked IPs: {e}")
            return []
    
    def get_ip_info(self, ip_address: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about an IP"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM blocked_ips WHERE ip_address = ?",
                    (ip_address,)
                )
                result = cursor.fetchone()
                return dict(result) if result else None
        except Exception as e:
            logger.error(f"Error getting info for IP {ip_address}: {e}")
            return None
    
    def get_ip_history(self, ip_address: str) -> List[Dict[str, Any]]:
        """Get history of actions for an IP"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """SELECT * FROM blocked_ips_history 
                       WHERE ip_address = ? 
                       ORDER BY timestamp DESC""",
                    (ip_address,)
                )
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting history for IP {ip_address}: {e}")
            return []
    
    def update_attack_count(self, ip_address: str, increment: int = 1) -> bool:
        """Update attack count for an IP"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE blocked_ips 
                    SET attack_count = attack_count + ?,
                        last_seen = CURRENT_TIMESTAMP
                    WHERE ip_address = ?
                """, (increment, ip_address))
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error updating attack count for IP {ip_address}: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about blocked IPs"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Total blocked IPs
                cursor.execute("SELECT COUNT(*) as count FROM blocked_ips WHERE is_blocked = 1")
                total_blocked = cursor.fetchone()['count']
                
                # Total unblocked IPs
                cursor.execute("SELECT COUNT(*) as count FROM blocked_ips WHERE is_blocked = 0")
                total_unblocked = cursor.fetchone()['count']
                
                # Total attacks
                cursor.execute("SELECT SUM(attack_count) as total FROM blocked_ips WHERE is_blocked = 1")
                total_attacks = cursor.fetchone()['total'] or 0
                
                # By threat level
                cursor.execute("""
                    SELECT threat_level, COUNT(*) as count 
                    FROM blocked_ips 
                    WHERE is_blocked = 1 
                    GROUP BY threat_level
                """)
                by_threat_level = {row['threat_level']: row['count'] for row in cursor.fetchall()}
                
                return {
                    "total_blocked": total_blocked,
                    "total_unblocked": total_unblocked,
                    "total_attacks": total_attacks,
                    "by_threat_level": by_threat_level
                }
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}
    
    def cleanup_old_records(self, days: int = 90) -> int:
        """Delete unblocked records older than specified days"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    DELETE FROM blocked_ips 
                    WHERE is_blocked = 0 
                    AND unblocked_at < datetime('now', '-' || ? || ' days')
                """, (days,))
                deleted = cursor.rowcount
                logger.info(f"Cleaned up {deleted} old records")
                return deleted
        except Exception as e:
            logger.error(f"Error cleaning up old records: {e}")
            return 0
    
    def export_to_csv(self, filepath: str, include_unblocked: bool = True) -> bool:
        """Export blocked IPs to CSV file"""
        try:
            import csv
            
            ips = self.get_blocked_ips(include_unblocked=include_unblocked)
            
            with open(filepath, 'w', newline='') as csvfile:
                if ips:
                    fieldnames = ips[0].keys()
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(ips)
                
                logger.info(f"Exported {len(ips)} records to {filepath}")
                return True
                
        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}")
            return False


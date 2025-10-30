"""
IP Blocking System
Handles automatic IP blocking when threat level is high and manages blocked IP statistics
"""
import time
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import sqlite3
import os

# Configure logging
logger = logging.getLogger(__name__)

class IPBlocker:
    """Manages IP blocking functionality and statistics"""
    
    def __init__(self, db_path: str = "blocked_ips.db"):
        self.db_path = db_path
        self.blocked_ips: Dict[str, Dict] = {}
        self.blocking_stats = {
            'total_blocked': 0,
            'auto_blocked': 0,
            'manual_blocked': 0,
            'unblocked': 0,
            'blocked_by_threat_level': defaultdict(int),
            'blocked_by_attack_type': defaultdict(int)
        }
        self.init_database()
        self.load_blocked_ips()
    
    def init_database(self):
        """Initialize SQLite database for blocked IPs"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create blocked_ips table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS blocked_ips (
                    ip TEXT PRIMARY KEY,
                    blocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    reason TEXT,
                    threat_level REAL,
                    attack_type TEXT,
                    auto_blocked BOOLEAN DEFAULT 1,
                    unblocked_at TIMESTAMP NULL,
                    is_active BOOLEAN DEFAULT 1
                )
            ''')
            
            # Create blocking_stats table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS blocking_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    total_blocked INTEGER,
                    auto_blocked INTEGER,
                    manual_blocked INTEGER,
                    unblocked INTEGER
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("IP blocking database initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
    
    def load_blocked_ips(self):
        """Load blocked IPs from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT ip, blocked_at, reason, threat_level, attack_type, 
                       auto_blocked, unblocked_at, is_active
                FROM blocked_ips 
                WHERE is_active = 1
            ''')
            
            for row in cursor.fetchall():
                ip, blocked_at, reason, threat_level, attack_type, auto_blocked, unblocked_at, is_active = row
                self.blocked_ips[ip] = {
                    'blocked_at': blocked_at,
                    'reason': reason,
                    'threat_level': threat_level,
                    'attack_type': attack_type,
                    'auto_blocked': bool(auto_blocked),
                    'unblocked_at': unblocked_at,
                    'is_active': bool(is_active)
                }
            
            conn.close()
            logger.info(f"Loaded {len(self.blocked_ips)} blocked IPs from database")
            
        except Exception as e:
            logger.error(f"Error loading blocked IPs: {e}")
    
    def is_ip_blocked(self, ip: str) -> bool:
        """Check if an IP is currently blocked"""
        return ip in self.blocked_ips and self.blocked_ips[ip]['is_active']
    
    def block_ip(self, ip: str, reason: str, threat_level: float = 0.0, 
                 attack_type: str = "Unknown", auto_blocked: bool = True) -> bool:
        """Block an IP address"""
        try:
            if self.is_ip_blocked(ip):
                logger.warning(f"IP {ip} is already blocked")
                return False
            
            # Add to memory
            self.blocked_ips[ip] = {
                'blocked_at': datetime.now().isoformat(),
                'reason': reason,
                'threat_level': threat_level,
                'attack_type': attack_type,
                'auto_blocked': auto_blocked,
                'unblocked_at': None,
                'is_active': True
            }
            
            # Save to database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO blocked_ips 
                (ip, blocked_at, reason, threat_level, attack_type, auto_blocked, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (ip, datetime.now().isoformat(), reason, threat_level, attack_type, auto_blocked, 1))
            
            conn.commit()
            conn.close()
            
            # Update statistics
            self.blocking_stats['total_blocked'] += 1
            if auto_blocked:
                self.blocking_stats['auto_blocked'] += 1
            else:
                self.blocking_stats['manual_blocked'] += 1
            
            self.blocking_stats['blocked_by_threat_level'][f"{threat_level:.1f}"] += 1
            self.blocking_stats['blocked_by_attack_type'][attack_type] += 1
            
            logger.info(f"Blocked IP {ip} - Reason: {reason}, Threat Level: {threat_level}")
            return True
            
        except Exception as e:
            logger.error(f"Error blocking IP {ip}: {e}")
            return False
    
    def unblock_ip(self, ip: str) -> bool:
        """Unblock an IP address"""
        try:
            if not self.is_ip_blocked(ip):
                logger.warning(f"IP {ip} is not currently blocked")
                return False
            
            # Update in memory
            if ip in self.blocked_ips:
                self.blocked_ips[ip]['is_active'] = False
                self.blocked_ips[ip]['unblocked_at'] = datetime.now().isoformat()
            
            # Update in database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE blocked_ips 
                SET is_active = 0, unblocked_at = ?
                WHERE ip = ?
            ''', (datetime.now().isoformat(), ip))
            
            conn.commit()
            conn.close()
            
            # Update statistics
            self.blocking_stats['unblocked'] += 1
            
            logger.info(f"Unblocked IP {ip}")
            return True
            
        except Exception as e:
            logger.error(f"Error unblocking IP {ip}: {e}")
            return False
    
    def get_blocked_ips(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """Get list of blocked IPs"""
        try:
            blocked_list = []
            for ip, data in self.blocked_ips.items():
                if not active_only or data['is_active']:
                    blocked_list.append({
                        'ip': ip,
                        'blocked_at': data['blocked_at'],
                        'reason': data['reason'],
                        'threat_level': data['threat_level'],
                        'attack_type': data['attack_type'],
                        'auto_blocked': data['auto_blocked'],
                        'unblocked_at': data['unblocked_at'],
                        'is_active': data['is_active']
                    })
            
            # Sort by blocked_at timestamp (newest first)
            blocked_list.sort(key=lambda x: x['blocked_at'], reverse=True)
            return blocked_list
            
        except Exception as e:
            logger.error(f"Error getting blocked IPs: {e}")
            return []
    
    def get_blocking_statistics(self) -> Dict[str, Any]:
        """Get blocking statistics"""
        try:
            # Get counts from database for more accurate stats
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Total blocked (all time)
            cursor.execute('SELECT COUNT(*) FROM blocked_ips')
            total_blocked = cursor.fetchone()[0]
            
            # Currently active
            cursor.execute('SELECT COUNT(*) FROM blocked_ips WHERE is_active = 1')
            currently_blocked = cursor.fetchone()[0]
            
            # Auto vs manual
            cursor.execute('SELECT COUNT(*) FROM blocked_ips WHERE auto_blocked = 1')
            auto_blocked = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM blocked_ips WHERE auto_blocked = 0')
            manual_blocked = cursor.fetchone()[0]
            
            # Unblocked
            cursor.execute('SELECT COUNT(*) FROM blocked_ips WHERE is_active = 0')
            unblocked = cursor.fetchone()[0]
            
            # Attack types distribution
            cursor.execute('''
                SELECT attack_type, COUNT(*) 
                FROM blocked_ips 
                WHERE is_active = 1 
                GROUP BY attack_type
            ''')
            attack_types = dict(cursor.fetchall())
            
            # Threat levels distribution
            cursor.execute('''
                SELECT 
                    CASE 
                        WHEN threat_level >= 0.8 THEN 'Critical (0.8+)'
                        WHEN threat_level >= 0.6 THEN 'High (0.6-0.8)'
                        WHEN threat_level >= 0.4 THEN 'Medium (0.4-0.6)'
                        ELSE 'Low (0.0-0.4)'
                    END as level_range,
                    COUNT(*) 
                FROM blocked_ips 
                WHERE is_active = 1 
                GROUP BY level_range
            ''')
            threat_levels = dict(cursor.fetchall())
            
            # Recent activity (last 24 hours)
            yesterday = (datetime.now() - timedelta(days=1)).isoformat()
            cursor.execute('''
                SELECT COUNT(*) FROM blocked_ips 
                WHERE blocked_at >= ?
            ''', (yesterday,))
            recent_blocks = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'total_blocked': total_blocked,
                'currently_blocked': currently_blocked,
                'auto_blocked': auto_blocked,
                'manual_blocked': manual_blocked,
                'unblocked': unblocked,
                'recent_blocks_24h': recent_blocks,
                'attack_types': attack_types,
                'threat_levels': threat_levels,
                'blocking_rate': (auto_blocked / max(1, total_blocked)) * 100
            }
            
        except Exception as e:
            logger.error(f"Error getting blocking statistics: {e}")
            return {}
    
    def should_auto_block(self, ip: str, threat_level: float, attack_type: str = "Unknown") -> bool:
        """Determine if an IP should be automatically blocked based on threat level"""
        # Auto-block if threat level is high (>= 0.8) or if it's a known attack pattern
        high_threat_threshold = 0.8
        critical_attack_types = ['HTTP Flood', 'SYN Flood', 'UDP Flood', 'Volumetric Attack']
        
        if threat_level >= high_threat_threshold:
            return True
        
        if attack_type in critical_attack_types and threat_level >= 0.6:
            return True
        
        # Check if IP has been blocked before (repeat offender)
        if ip in self.blocked_ips and not self.blocked_ips[ip]['is_active']:
            # If previously blocked and threat level is medium or higher, block again
            if threat_level >= 0.5:
                return True
        
        return False
    
    def cleanup_old_blocks(self, days: int = 30):
        """Remove old blocked IP records from database"""
        try:
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Remove old inactive blocks
            cursor.execute('''
                DELETE FROM blocked_ips 
                WHERE is_active = 0 AND unblocked_at < ?
            ''', (cutoff_date,))
            
            deleted_count = cursor.rowcount
            conn.commit()
            conn.close()
            
            logger.info(f"Cleaned up {deleted_count} old blocked IP records")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up old blocks: {e}")
            return 0

# Global instance
ip_blocker = IPBlocker()

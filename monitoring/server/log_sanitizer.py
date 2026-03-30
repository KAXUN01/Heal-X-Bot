"""
Log Sanitizer - Privacy Protection for AI Log Analysis
Replaces sensitive data (file paths, usernames, IPs, emails, hostnames)
with generic placeholders before sending logs to external LLMs.
Provides de-sanitization to restore placeholders in AI responses.
"""

import re
import os
import socket
import logging
from typing import Dict, Tuple

logger = logging.getLogger(__name__)


class LogSanitizer:
    """
    Sanitizes log text by replacing sensitive information with placeholders.
    Maintains a reversible mapping so AI responses can be de-sanitized for display.
    """

    def __init__(self):
        # Detect current system hostname for replacement
        try:
            self._hostname = socket.gethostname()
        except Exception:
            self._hostname = None

        # Detect current OS username
        try:
            self._os_user = os.getenv("USER") or os.getenv("USERNAME") or ""
        except Exception:
            self._os_user = ""

    def sanitize(self, text: str) -> Tuple[str, Dict[str, str]]:
        """
        Sanitize sensitive data in text, returning (sanitized_text, mapping).
        The mapping can be passed to desanitize() to restore original values.
        """
        if not text:
            return text, {}

        # mapping: placeholder -> original value
        mapping = {}
        # reverse lookup to reuse placeholders for repeated values
        seen = {}

        counters = {
            "USER": 0,
            "PATH": 0,
            "IP": 0,
            "EMAIL": 0,
            "HOST": 0,
        }

        def _get_placeholder(category: str, original: str) -> str:
            """Get or create a placeholder for an original value."""
            if original in seen:
                return seen[original]
            counters[category] += 1
            placeholder = f"[{category}_{counters[category]}]"
            mapping[placeholder] = original
            seen[original] = placeholder
            return placeholder

        sanitized = text

        # --- 1. Replace hostname (before path replacement so paths containing hostname are caught) ---
        if self._hostname and len(self._hostname) > 2:
            pattern = re.compile(re.escape(self._hostname), re.IGNORECASE)
            matches = pattern.findall(sanitized)
            for match in set(matches):
                placeholder = _get_placeholder("HOST", match)
                sanitized = sanitized.replace(match, placeholder)

        # --- 2. Replace email addresses ---
        email_pattern = re.compile(
            r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}'
        )
        for match in set(email_pattern.findall(sanitized)):
            placeholder = _get_placeholder("EMAIL", match)
            sanitized = sanitized.replace(match, placeholder)

        # --- 3. Replace Windows-style paths (C:\Users\..., D:\Projects\...) ---
        # Handles paths with spaces in directory names (e.g. C:\Users\KASUN MADHUSHAN\...)
        win_path_pattern = re.compile(
            r'[A-Za-z]:\\(?:[^\n:*?"<>|\\]+\\)*[^\n:*?"<>|\\]*'
        )
        for match in sorted(set(win_path_pattern.findall(sanitized)), key=len, reverse=True):
            # Extract username from Windows user path if present
            user_match = re.match(r'[A-Za-z]:\\Users\\([^\\]+)', match, re.IGNORECASE)
            if user_match:
                username = user_match.group(1)
                if username.lower() not in ("public", "default", "all users"):
                    _get_placeholder("USER", username)
                    # Replace the username within the path first
                    sanitized_path = match.replace(username, seen[username])
                    placeholder = _get_placeholder("PATH", match)
                    sanitized = sanitized.replace(match, placeholder)
                    continue
            placeholder = _get_placeholder("PATH", match)
            sanitized = sanitized.replace(match, placeholder)

        # --- 4. Replace Linux/Unix-style paths ---
        unix_path_pattern = re.compile(
            r'(?:/(?:home|root|opt|var|etc|tmp|usr|srv|mnt|media)/[^\s:,;\'\")\]}>]+)'
        )
        for match in sorted(set(unix_path_pattern.findall(sanitized)), key=len, reverse=True):
            # Extract username from /home/<user>/... paths
            user_match = re.match(r'/home/([^/]+)', match)
            if user_match:
                username = user_match.group(1)
                _get_placeholder("USER", username)
            placeholder = _get_placeholder("PATH", match)
            sanitized = sanitized.replace(match, placeholder)

        # --- 5. Replace OS username occurrences that weren't caught by paths ---
        if self._os_user and len(self._os_user) > 2:
            # Only replace if it looks like a standalone word (not part of a generic word)
            user_pattern = re.compile(r'\b' + re.escape(self._os_user) + r'\b', re.IGNORECASE)
            for match in set(user_pattern.findall(sanitized)):
                placeholder = _get_placeholder("USER", match)
                sanitized = sanitized.replace(match, placeholder)

        # --- 6. Replace IPv4 addresses (but not 0.0.0.0 or 127.0.0.1 or localhost) ---
        ipv4_pattern = re.compile(
            r'\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b'
        )
        for match in set(ipv4_pattern.findall(sanitized)):
            # Keep common safe IPs
            if match in ("0.0.0.0", "127.0.0.1", "255.255.255.0", "255.255.255.255"):
                continue
            placeholder = _get_placeholder("IP", match)
            sanitized = sanitized.replace(match, placeholder)

        logger.debug(f"Sanitized {len(mapping)} sensitive items from log text")
        return sanitized, mapping

    def desanitize(self, text: str, mapping: Dict[str, str]) -> str:
        """
        Restore placeholders in text back to their original values.
        Used to make AI responses human-readable again.
        """
        if not text or not mapping:
            return text

        result = text
        # Replace longest placeholders first to avoid partial matches
        for placeholder in sorted(mapping.keys(), key=len, reverse=True):
            result = result.replace(placeholder, mapping[placeholder])

        return result


# Singleton instance for convenience
log_sanitizer = LogSanitizer()

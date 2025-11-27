"""
Custom exceptions for Heal-X-Bot
"""


class HealXError(Exception):
    """Base exception for Heal-X-Bot"""
    pass


class ConfigurationError(HealXError):
    """Configuration-related errors"""
    pass


class ServiceError(HealXError):
    """Service-related errors"""
    pass


class HealingError(HealXError):
    """Healing action errors"""
    pass


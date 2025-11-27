"""
AI-Powered Auto-Healing System (Backward Compatibility Shim)
This file provides backward compatibility for existing code.
The actual implementation has been moved to monitoring/server/healing/
"""
# Re-export from new location for backward compatibility
try:
    from .healing import AutoHealer, initialize_auto_healer, get_auto_healer
except ImportError:
    # If running as standalone script, try absolute import
    try:
        from monitoring.server.healing import AutoHealer, initialize_auto_healer, get_auto_healer
    except ImportError:
        # Last resort: try importing from healing subdirectory
        import sys
        from pathlib import Path
        healing_path = Path(__file__).parent / 'healing'
        if healing_path.exists():
            sys.path.insert(0, str(Path(__file__).parent))
            from healing import AutoHealer, initialize_auto_healer, get_auto_healer

# Re-export all public symbols
__all__ = ['AutoHealer', 'initialize_auto_healer', 'get_auto_healer']

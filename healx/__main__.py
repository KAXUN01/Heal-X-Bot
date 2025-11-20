"""
Heal-X-Bot CLI Entry Point
Allows running as: python3 -m healx
"""
from .cli import main
import sys

if __name__ == '__main__':
    sys.exit(main())


"""
BrightData API Service
Web scraping and proxy services
"""

from .api import BrightDataAPI
from .query_helpers import (
    ScrapeBuilder,
    BatchScraper,
    DataExtractor,
    ProxyRotator,
    SearchAggregator,
    CacheManager
)

__all__ = [
    'BrightDataAPI',
    'ScrapeBuilder',
    'BatchScraper',
    'DataExtractor',
    'ProxyRotator',
    'SearchAggregator',
    'CacheManager'
]

__version__ = '2.0.0'
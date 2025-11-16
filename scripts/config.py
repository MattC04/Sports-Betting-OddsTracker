"""
Configuration management for Odds API scraper.
Supports environment variables and configuration files.
"""

import os
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from enum import Enum


class ScrapingMethod(Enum):
    """Enumeration of available scraping methods."""
    ODDS_API = "odds_api"


@dataclass
class ScrapingConfig:
    """Configuration class for Odds API scraping parameters."""
    api_key: str = ""
    sport: str = "basketball_nba"
    method: ScrapingMethod = ScrapingMethod.ODDS_API
    output_file: str = "data/odds_data.csv"
    output_format: str = "csv"
    regions: str = "us"
    markets: str = "h2h,spreads"
    odds_format: str = "decimal"
    date_format: str = "iso"
    retries: int = 3
    backoff_factor: float = 0.5
    save_raw: Optional[str] = None
    request_timeout: int = 30
    
    @classmethod
    def from_env(cls) -> 'ScrapingConfig':
        """Create configuration from environment variables."""
        api_key = os.getenv('ODDS_API_KEY', '')
        if not api_key:
            raise ValueError("ODDS_API_KEY environment variable is required. Please set it before running the scraper.")
        
        return cls(
            api_key=api_key,
            sport=os.getenv('ODDS_API_SPORT', 'basketball_nba'),
            method=ScrapingMethod.ODDS_API,
            output_file=os.getenv('ODDS_API_OUTPUT', 'data/odds_data.csv'),
            output_format=os.getenv('ODDS_API_FORMAT', 'csv'),
            regions=os.getenv('ODDS_API_REGIONS', 'us'),
            markets=os.getenv('ODDS_API_MARKETS', 'h2h,spreads'),
            odds_format=os.getenv('ODDS_API_ODDS_FORMAT', 'decimal'),
            date_format=os.getenv('ODDS_API_DATE_FORMAT', 'iso'),
            retries=int(os.getenv('ODDS_API_RETRIES', '3')),
            backoff_factor=float(os.getenv('ODDS_API_BACKOFF_FACTOR', '0.5')),
            save_raw=os.getenv('ODDS_API_SAVE_RAW'),
            request_timeout=int(os.getenv('ODDS_API_TIMEOUT', '30'))
        )
    
    @classmethod
    def from_args(cls, args) -> 'ScrapingConfig':
        """Create configuration from command line arguments."""
        api_key = getattr(args, 'api_key', None) or os.getenv('ODDS_API_KEY', '')
        if not api_key:
            raise ValueError("API key is required. Set ODDS_API_KEY environment variable or use --api-key argument.")
        
        return cls(
            api_key=api_key,
            sport=getattr(args, 'sport', 'basketball_nba'),
            method=ScrapingMethod.ODDS_API,
            output_file=getattr(args, 'out', 'data/odds_data.csv'),
            output_format=getattr(args, 'format', 'csv'),
            regions=getattr(args, 'regions', 'us'),
            markets=getattr(args, 'markets', 'h2h,spreads,totals'),
            odds_format=getattr(args, 'odds_format', 'american'),
            date_format=getattr(args, 'date_format', 'iso'),
            retries=getattr(args, 'retries', 3),
            backoff_factor=getattr(args, 'backoff', 0.5),
            save_raw=getattr(args, 'save_raw', None)
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            'sport': self.sport,
            'method': self.method.value,
            'output_file': self.output_file,
            'output_format': self.output_format,
            'regions': self.regions,
            'markets': self.markets,
            'odds_format': self.odds_format,
            'date_format': self.date_format,
            'retries': self.retries,
            'backoff_factor': self.backoff_factor,
            'save_raw': self.save_raw,
            'request_timeout': self.request_timeout
        }


@dataclass
class ScrapingMetrics:
    """Class to track scraping performance metrics."""
    start_time: float = field(default_factory=lambda: __import__('time').time())
    end_time: Optional[float] = None
    total_props: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    verification_required: bool = False
    sports_processed: list = field(default_factory=list)
    
    @property
    def duration(self) -> float:
        """Calculate total scraping duration."""
        end = self.end_time or __import__('time').time()
        return end - self.start_time
    
    @property
    def props_per_second(self) -> float:
        """Calculate props scraped per second."""
        duration = self.duration
        return self.total_props / duration if duration > 0 else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            'start_time': self.start_time,
            'end_time': self.end_time,
            'total_props': self.total_props,
            'successful_requests': self.successful_requests,
            'failed_requests': self.failed_requests,
            'verification_required': self.verification_required,
            'sports_processed': self.sports_processed,
            'duration': self.duration,
            'props_per_second': self.props_per_second
        }

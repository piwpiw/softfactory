"""Review Scrapers Package - Multi-platform listing aggregator"""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict

from .base_scraper import BaseScraper
from .revu_scraper import RevuScraper
from .reviewplace_scraper import ReviewPlaceScraper
from .wible_scraper import WibleScraper
from .mibl_scraper import MiblScraper
from .seoulouba_scraper import SeouloubaScraper
from .naver_scraper import NaverScraper
from .moaview_scraper import MoaviewScraper
from .inflexer_scraper import InflexerScraper

logger = logging.getLogger('review.scrapers')

# Registry of all scrapers
SCRAPERS = [
    MoaviewScraper(),
    InflexerScraper(),
    ReviewPlaceScraper(),
    WibleScraper(),
    MiblScraper(),
    SeouloubaScraper(),
    NaverScraper(),
]

# Revu scraper intentionally not included as it's a template/example


def get_scraper(platform: str) -> BaseScraper:
    """
    Get a specific scraper by platform name.

    Args:
        platform: Platform identifier (e.g., 'moaview', 'inflexer')

    Returns:
        Scraper instance or None if not found
    """
    for scraper in SCRAPERS:
        if scraper.platform == platform:
            return scraper
    return None


def aggregate_all_listings(max_workers: int = 3) -> Dict[str, int]:
    """
    Scrape listings from all platforms concurrently.

    Uses ThreadPoolExecutor to parallelize scraping across multiple platforms
    while respecting rate limiting within each scraper.

    Args:
        max_workers: Maximum number of concurrent scraper threads (default: 3)

    Returns:
        Dictionary with platform names as keys and count of saved listings as values
    """
    logger.info(f"Starting aggregation of review listings from {len(SCRAPERS)} platforms")
    results = {}

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all scraper tasks
        future_to_platform = {
            executor.submit(scraper.parse_listings): scraper.platform
            for scraper in SCRAPERS
        }

        # Process completed futures as they finish
        for future in as_completed(future_to_platform):
            platform = future_to_platform[future]
            try:
                count = len(future.result())
                results[platform] = count
                logger.info(f"[{platform}] Completed - {count} listings processed")
            except Exception as e:
                logger.error(f"[{platform}] Failed with error: {e}")
                results[platform] = 0

    logger.info(f"Aggregation completed. Total: {sum(results.values())} listings processed")
    return results


def aggregate_specific_platforms(platforms: List[str], max_workers: int = 3) -> Dict[str, int]:
    """
    Scrape listings from specific platforms.

    Args:
        platforms: List of platform identifiers to scrape
        max_workers: Maximum number of concurrent scraper threads

    Returns:
        Dictionary with platform names as keys and count of saved listings as values
    """
    logger.info(f"Starting aggregation for platforms: {platforms}")
    results = {}

    # Filter scrapers to only requested platforms
    selected_scrapers = [s for s in SCRAPERS if s.platform in platforms]

    if not selected_scrapers:
        logger.warning(f"No valid scrapers found for platforms: {platforms}")
        return results

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_platform = {
            executor.submit(scraper.parse_listings): scraper.platform
            for scraper in selected_scrapers
        }

        for future in as_completed(future_to_platform):
            platform = future_to_platform[future]
            try:
                count = len(future.result())
                results[platform] = count
                logger.info(f"[{platform}] Completed - {count} listings processed")
            except Exception as e:
                logger.error(f"[{platform}] Failed with error: {e}")
                results[platform] = 0

    logger.info(f"Aggregation completed. Total: {sum(results.values())} listings processed")
    return results


def list_available_platforms() -> List[str]:
    """
    Get list of available scraper platforms.

    Returns:
        List of platform identifiers
    """
    return [scraper.platform for scraper in SCRAPERS]


__all__ = [
    'BaseScraper',
    'MoaviewScraper',
    'InflexerScraper',
    'ReviewPlaceScraper',
    'WibleScraper',
    'MiblScraper',
    'SeouloubaScraper',
    'NaverScraper',
    'get_scraper',
    'aggregate_all_listings',
    'aggregate_specific_platforms',
    'list_available_platforms',
    'SCRAPERS',
]

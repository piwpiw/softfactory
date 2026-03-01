"""Review Scrapers Package - Multi-platform listing aggregator

Aggregates experience/review campaign listings from Korean platforms:
  - revu.net          — Korea's largest 체험단 platform (SPA, uses Naver index)
  - reviewplace.co.kr — Product review campaigns (direct scraping)
  - seoulouba.co.kr   — Creator collaboration platform (direct scraping)
  - naver             — Naver blog campaign posts (blog section search)
  - wible.co.kr       — Influencer campaigns (currently unreachable, Naver fallback)
  - mibl.kr           — Micro influencer platform
  - moaview.co.kr     — Review aggregator
  - inflexer.net      — Influencer marketplace

Each scraper extends BaseScraper and implements parse_listings().
Error isolation ensures one failing scraper does not affect others.
"""

import logging
import traceback
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


def _create_scrapers() -> List[BaseScraper]:
    """
    Create fresh scraper instances.

    Returns new instances each time to avoid stale session state
    between aggregation runs.

    Returns:
        List of scraper instances
    """
    return [
        RevuScraper(),           # revu.net (via Naver index)
        ReviewPlaceScraper(),    # reviewplace.co.kr (direct)
        SeouloubaScraper(),      # seoulouba.co.kr (direct)
        NaverScraper(),          # Naver blog search
        WibleScraper(),          # wible.co.kr (Naver fallback)
        MiblScraper(),           # mibl.kr
        MoaviewScraper(),        # moaview.co.kr
        InflexerScraper(),       # inflexer.net
    ]


# Registry of all scrapers (8 platforms)
SCRAPERS = _create_scrapers()


def get_scraper(platform: str) -> BaseScraper:
    """
    Get a specific scraper by platform name.

    Args:
        platform: Platform identifier (e.g., 'revu', 'reviewplace', 'seoulouba')

    Returns:
        Scraper instance or None if not found
    """
    for scraper in SCRAPERS:
        if scraper.platform == platform:
            return scraper
    return None


def aggregate_all_listings(max_workers: int = 3) -> Dict[str, Dict]:
    """
    Scrape listings from all platforms concurrently with error isolation.

    Uses ThreadPoolExecutor to parallelize scraping across multiple platforms
    while respecting rate limiting within each scraper. Each scraper runs
    in isolation — a failure in one does not affect others.

    Args:
        max_workers: Maximum number of concurrent scraper threads (default: 3)

    Returns:
        Dictionary with platform names as keys and result info as values:
        {
            'platform_name': {
                'count': int,       # Number of listings found
                'saved': int,       # Number saved to DB (new only)
                'status': str,      # 'success' | 'error'
                'error': str|None,  # Error message if failed
            }
        }
    """
    scrapers = _create_scrapers()
    logger.info(f"Starting aggregation of review listings from {len(scrapers)} platforms")
    logger.info(f"Platforms: {[s.platform for s in scrapers]}")

    results = {}

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all scraper tasks
        future_to_scraper = {
            executor.submit(_safe_scrape, scraper): scraper
            for scraper in scrapers
        }

        # Process completed futures as they finish
        for future in as_completed(future_to_scraper):
            scraper = future_to_scraper[future]
            platform = scraper.platform
            try:
                result = future.result()
                results[platform] = result
                status_icon = '✓' if result['status'] == 'success' else '✗'
                logger.info(
                    f"[{platform}] {status_icon} {result['status'].upper()} — "
                    f"{result['count']} found, {result.get('saved', 0)} saved"
                )
            except Exception as e:
                error_msg = f"{type(e).__name__}: {str(e)}"
                results[platform] = {
                    'count': 0,
                    'saved': 0,
                    'status': 'error',
                    'error': error_msg,
                }
                logger.error(f"[{platform}] ✗ FAILED — {error_msg}")

    # Summary
    total_found = sum(r.get('count', 0) for r in results.values())
    total_saved = sum(r.get('saved', 0) for r in results.values())
    successes = sum(1 for r in results.values() if r['status'] == 'success')
    failures = len(results) - successes

    logger.info(
        f"Aggregation completed: {total_found} listings found, {total_saved} saved | "
        f"{successes} succeeded, {failures} failed"
    )

    return results


def aggregate_specific_platforms(platforms: List[str], max_workers: int = 3) -> Dict[str, Dict]:
    """
    Scrape listings from specific platforms with error isolation.

    Args:
        platforms: List of platform identifiers to scrape
        max_workers: Maximum number of concurrent scraper threads

    Returns:
        Dictionary with platform results (same format as aggregate_all_listings)
    """
    logger.info(f"Starting aggregation for platforms: {platforms}")
    results = {}

    # Create fresh scrapers and filter
    all_scrapers = _create_scrapers()
    selected_scrapers = [s for s in all_scrapers if s.platform in platforms]

    if not selected_scrapers:
        logger.warning(f"No valid scrapers found for platforms: {platforms}")
        logger.info(f"Available platforms: {[s.platform for s in all_scrapers]}")
        return results

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_scraper = {
            executor.submit(_safe_scrape, scraper): scraper
            for scraper in selected_scrapers
        }

        for future in as_completed(future_to_scraper):
            scraper = future_to_scraper[future]
            platform = scraper.platform
            try:
                result = future.result()
                results[platform] = result
                logger.info(
                    f"[{platform}] {result['status'].upper()} — "
                    f"{result['count']} found"
                )
            except Exception as e:
                results[platform] = {
                    'count': 0,
                    'saved': 0,
                    'status': 'error',
                    'error': str(e),
                }
                logger.error(f"[{platform}] FAILED — {e}")

    total_found = sum(r.get('count', 0) for r in results.values())
    logger.info(f"Aggregation completed. Total: {total_found} listings processed")
    return results


def _safe_scrape(scraper: BaseScraper) -> Dict:
    """
    Run a scraper with full error isolation.

    Catches all exceptions to ensure one scraper failure
    never propagates to other scrapers.

    Args:
        scraper: Scraper instance to run

    Returns:
        Result dictionary with count, status, and optional error
    """
    try:
        listings = scraper.parse_listings()
        return {
            'count': len(listings),
            'saved': len(listings),  # parse_listings() calls save_listings() internally
            'status': 'success',
            'error': None,
        }
    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}"
        logger.error(
            f"[{scraper.platform}] Scraper crashed:\n"
            f"  Error: {error_msg}\n"
            f"  Traceback: {traceback.format_exc()}"
        )
        return {
            'count': 0,
            'saved': 0,
            'status': 'error',
            'error': error_msg,
        }


def list_available_platforms() -> List[str]:
    """
    Get list of available scraper platforms.

    Returns:
        List of platform identifiers
    """
    return [scraper.platform for scraper in SCRAPERS]


def get_platform_info() -> List[Dict]:
    """
    Get detailed info about all available scraper platforms.

    Returns:
        List of dictionaries with platform details
    """
    return [
        {
            'platform': s.platform,
            'base_url': s.base_url,
            'class': type(s).__name__,
        }
        for s in SCRAPERS
    ]


__all__ = [
    'BaseScraper',
    'RevuScraper',
    'ReviewPlaceScraper',
    'SeouloubaScraper',
    'NaverScraper',
    'WibleScraper',
    'MiblScraper',
    'MoaviewScraper',
    'InflexerScraper',
    'get_scraper',
    'aggregate_all_listings',
    'aggregate_specific_platforms',
    'list_available_platforms',
    'get_platform_info',
    'SCRAPERS',
]

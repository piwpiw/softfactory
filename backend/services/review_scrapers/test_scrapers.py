"""
Test script for review scrapers.

Run this to test individual scrapers or all scrapers at once.

Usage:
    # Test all scrapers
    python -m backend.services.review_scrapers.test_scrapers

    # Test specific scraper
    python -m backend.services.review_scrapers.test_scrapers moaview

    # Test with Flask app context
    python -c "from backend.app import app; app.app_context().push(); from backend.services.review_scrapers.test_scrapers import test_all; test_all()"
"""

import logging
import sys
from datetime import datetime
from typing import List, Dict

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('review.scrapers.test')


def test_scraper(scraper_name: str) -> Dict:
    """Test a single scraper"""
    try:
        from . import get_scraper

        logger.info(f"Testing scraper: {scraper_name}")
        scraper = get_scraper(scraper_name)

        if not scraper:
            logger.error(f"Scraper not found: {scraper_name}")
            return {'success': False, 'error': 'Scraper not found'}

        # Test parse_listings
        listings = scraper.parse_listings()

        logger.info(f"Scraper '{scraper_name}' completed successfully")
        logger.info(f"  - Listings collected: {len(listings)}")

        if listings:
            logger.info(f"  - Sample listing: {listings[0]}")

        return {
            'success': True,
            'scraper': scraper_name,
            'listings_count': len(listings),
            'listings': listings
        }

    except Exception as e:
        logger.error(f"Test failed for {scraper_name}: {e}", exc_info=True)
        return {'success': False, 'scraper': scraper_name, 'error': str(e)}


def test_all() -> Dict:
    """Test all scrapers"""
    try:
        from . import list_available_platforms

        logger.info("Starting tests for all scrapers")
        platforms = list_available_platforms()

        logger.info(f"Found {len(platforms)} scrapers: {platforms}")

        results = {}
        for platform in platforms:
            results[platform] = test_scraper(platform)

        logger.info("All scraper tests completed")
        return results

    except Exception as e:
        logger.error(f"Error testing all scrapers: {e}", exc_info=True)
        return {'success': False, 'error': str(e)}


def test_aggregation() -> Dict:
    """Test aggregation function"""
    try:
        from . import aggregate_all_listings

        logger.info("Testing aggregation function")
        start_time = datetime.utcnow()

        results = aggregate_all_listings(max_workers=2)

        elapsed = (datetime.utcnow() - start_time).total_seconds()

        logger.info(f"Aggregation completed in {elapsed:.1f}s")
        logger.info(f"Results: {results}")

        return {
            'success': True,
            'results': results,
            'elapsed_seconds': elapsed,
            'total_listings': sum(results.values())
        }

    except Exception as e:
        logger.error(f"Error during aggregation test: {e}", exc_info=True)
        return {'success': False, 'error': str(e)}


def validate_listing(listing: Dict) -> tuple:
    """Validate listing structure"""
    required_fields = ['external_id', 'title', 'brand', 'reward_type', 'deadline', 'url']
    errors = []

    for field in required_fields:
        if field not in listing or not listing[field]:
            errors.append(f"Missing or empty field: {field}")

    return (len(errors) == 0, errors)


def test_listing_validation(listings: List[Dict]) -> Dict:
    """Test listing validation"""
    logger.info(f"Validating {len(listings)} listings")

    valid_count = 0
    invalid_listings = []

    for i, listing in enumerate(listings):
        is_valid, errors = validate_listing(listing)
        if is_valid:
            valid_count += 1
        else:
            invalid_listings.append({
                'index': i,
                'listing': listing,
                'errors': errors
            })

    logger.info(f"Valid listings: {valid_count}/{len(listings)}")

    if invalid_listings:
        logger.warning(f"Found {len(invalid_listings)} invalid listings")
        for invalid in invalid_listings[:5]:  # Show first 5
            logger.warning(f"  - {invalid['errors']}")

    return {
        'total': len(listings),
        'valid': valid_count,
        'invalid': len(invalid_listings),
        'invalid_listings': invalid_listings
    }


if __name__ == '__main__':
    if len(sys.argv) > 1:
        scraper_name = sys.argv[1]
        logger.info(f"Testing specific scraper: {scraper_name}")
        result = test_scraper(scraper_name)
        print(f"\nResult: {result}")
    else:
        logger.info("Testing all scrapers")
        results = test_all()
        print(f"\nResults: {results}")

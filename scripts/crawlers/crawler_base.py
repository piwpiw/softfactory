"""
Experience Platform Crawler Base
Base class for all experience listing crawlers
"""
from abc import ABC, abstractmethod
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ExperienceCrawler(ABC):
    """Base class for experience platform crawlers"""

    def __init__(self, site_name: str, timeout: int = 10):
        self.site_name = site_name
        self.timeout = timeout
        self.listings = []
        self.error = None

    @abstractmethod
    def crawl(self) -> list:
        """
        Crawl listings from the platform
        Returns list of listing dicts with keys:
        - title: str
        - url: str
        - deadline: datetime or None
        - category: str
        - reward: str
        - description: str
        - image_url: str or None
        """
        pass

    def validate_listing(self, listing: dict) -> bool:
        """Validate listing format"""
        required_keys = ['title', 'url']
        return all(key in listing for key in required_keys)

    def format_listings(self) -> list:
        """Format and validate all listings"""
        valid_listings = []
        for listing in self.listings:
            if self.validate_listing(listing):
                valid_listings.append({
                    'site': self.site_name,
                    'title': listing.get('title', ''),
                    'url': listing.get('url', ''),
                    'deadline': listing.get('deadline'),
                    'category': listing.get('category', '미분류'),
                    'reward': listing.get('reward', '미정'),
                    'description': listing.get('description', ''),
                    'image_url': listing.get('image_url'),
                    'crawled_at': datetime.utcnow().isoformat()
                })
        return valid_listings

    def save_to_db(self, db):
        """Save listings to database"""
        from backend.models import ExperienceListing, CrawlerLog

        if self.error:
            log = CrawlerLog(
                site=self.site_name,
                listing_count=0,
                status='error',
                error_message=str(self.error)
            )
            db.session.add(log)
            db.session.commit()
            logger.error(f"Crawler {self.site_name} failed: {self.error}")
            return False

        # Clear old listings for this site
        ExperienceListing.query.filter_by(site=self.site_name).delete()

        # Add new listings
        valid_listings = self.format_listings()
        for listing_data in valid_listings:
            listing = ExperienceListing(**listing_data)
            db.session.add(listing)

        # Log crawler execution
        log = CrawlerLog(
            site=self.site_name,
            listing_count=len(valid_listings),
            status='success'
        )
        db.session.add(log)
        db.session.commit()

        logger.info(f"Crawler {self.site_name} completed: {len(valid_listings)} listings saved")
        return True

    def run(self, db=None) -> dict:
        """Run crawler and save to database"""
        try:
            self.listings = self.crawl()
            if db:
                self.save_to_db(db)

            return {
                'success': True,
                'site': self.site_name,
                'listings_found': len(self.listings),
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            self.error = str(e)
            logger.exception(f"Error running crawler {self.site_name}")
            if db:
                self.save_to_db(db)

            return {
                'success': False,
                'site': self.site_name,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }


class DummyCrawler(ExperienceCrawler):
    """Dummy crawler for MVP - returns sample data"""

    DUMMY_DATA = {
        'coupang_eats': [
            {
                'title': '[쿠팡이츠] 맛집 배달 리뷰 체험단',
                'url': 'https://www.coupangeats.com',
                'deadline': '2026-03-02',
                'category': '음식',
                'reward': '무료 음식 + 현금 2만원',
                'description': '신규 맛집의 배달 음식을 먹고 솔직한 리뷰를 남겨주세요',
                'image_url': 'https://via.placeholder.com/300x200?text=Coupang'
            }
        ]
    }

    def crawl(self) -> list:
        """Return dummy data for testing"""
        site_data = self.DUMMY_DATA.get(self.site_name, [])
        return site_data


if __name__ == '__main__':
    # Test with dummy data
    crawler = DummyCrawler('coupang_eats')
    result = crawler.run()
    print(f"Test result: {result}")

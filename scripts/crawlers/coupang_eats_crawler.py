"""
Coupang Eats Experience Crawler
Crawls experience listings from Coupang Eats
"""
from crawler_base import ExperienceCrawler
from datetime import datetime, timedelta


class CoupangEatsCrawler(ExperienceCrawler):
    """Crawl experience listings from Coupang Eats"""

    def __init__(self):
        super().__init__(site_name='coupang_eats')

    def crawl(self) -> list:
        """
        Crawl Coupang Eats experience listings
        Phase 5: Implement with BeautifulSoup/Selenium
        """
        # MVP: Return sample data
        listings = [
            {
                'title': '[쿠팡이츠] 맛집 배달 리뷰 체험단',
                'url': 'https://www.coupangeats.com/experience',
                'deadline': datetime.utcnow() + timedelta(days=5),
                'category': '음식',
                'reward': '무료 음식 + 현금 2만원',
                'description': '신규 맛집의 배달 음식을 먹고 솔직한 리뷰를 남겨주세요',
                'image_url': 'https://via.placeholder.com/300x200?text=Coupang+Eats'
            },
            {
                'title': '[쿠팡이츠] 프리미엄 식재료 체험단 모집',
                'url': 'https://www.coupangeats.com/experience',
                'deadline': datetime.utcnow() + timedelta(days=7),
                'category': '음식',
                'reward': '식재료 패키지 50만원 상당',
                'description': '프리미엄 식재료를 직접 요리하고 평가해주세요',
                'image_url': 'https://via.placeholder.com/300x200?text=Premium+Food'
            }
        ]
        return listings


if __name__ == '__main__':
    crawler = CoupangEatsCrawler()
    result = crawler.run()
    print(f"Result: {result}")

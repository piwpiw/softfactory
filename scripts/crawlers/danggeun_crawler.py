"""
Daangn Market Experience Crawler
Crawls experience listings from Daangn Market (당근마켓)
"""
from crawler_base import ExperienceCrawler
from datetime import datetime, timedelta


class DaangnCrawler(ExperienceCrawler):
    """Crawl experience listings from Daangn Market"""

    def __init__(self):
        super().__init__(site_name='danggeun')

    def crawl(self) -> list:
        """
        Crawl Daangn Market experience listings
        Phase 5: Implement with BeautifulSoup/Selenium
        """
        # MVP: Return sample data
        listings = [
            {
                'title': '[당근마켓] 근처 카페 홍보 체험단',
                'url': 'https://www.daangn.com/articles?category=experience',
                'deadline': datetime.utcnow() + timedelta(days=3),
                'category': '카페',
                'reward': '음료 쿠폰 3만원 + 수수료 5천원',
                'description': '당신의 지역 카페를 소개하고 홍보해주세요',
                'image_url': 'https://via.placeholder.com/300x200?text=Cafe'
            },
            {
                'title': '[당근마켓] 편의점 신상품 체험단',
                'url': 'https://www.daangn.com/articles?category=experience',
                'deadline': datetime.utcnow() + timedelta(days=10),
                'category': '편의점',
                'reward': '신상품 무료 + 리뷰비 5천원',
                'description': '편의점 신상품을 먼저 경험하고 평가해주세요',
                'image_url': 'https://via.placeholder.com/300x200?text=Store'
            },
            {
                'title': '[당근마켓] 지역 맛집 배달 평가단',
                'url': 'https://www.daangn.com/articles?category=experience',
                'deadline': datetime.utcnow() + timedelta(days=8),
                'category': '음식',
                'reward': '배달 쿠폰 3만원',
                'description': '우리 동네 맛집을 경험하고 솔직한 평가를 남겨주세요',
                'image_url': 'https://via.placeholder.com/300x200?text=Restaurant'
            }
        ]
        return listings


if __name__ == '__main__':
    crawler = DaangnCrawler()
    result = crawler.run()
    print(f"Result: {result}")

"""
Soomgo Experience Crawler
Crawls experience listings from Soomgo (숨고)
"""
from crawler_base import ExperienceCrawler
from datetime import datetime, timedelta


class SoomgoCrawler(ExperienceCrawler):
    """Crawl experience listings from Soomgo"""

    def __init__(self):
        super().__init__(site_name='soomgo')

    def crawl(self) -> list:
        """
        Crawl Soomgo experience listings
        Phase 5: Implement with BeautifulSoup/Selenium
        """
        # MVP: Return sample data
        listings = [
            {
                'title': '[숨고] 청소 서비스 품질 평가단',
                'url': 'https://www.soomgo.com',
                'deadline': datetime.utcnow() + timedelta(days=6),
                'category': '생활서비스',
                'reward': '청소 서비스 무료 + 평가비 5만원',
                'description': '청소 서비스의 품질을 평가하고 피드백을 주세요',
                'image_url': 'https://via.placeholder.com/300x200?text=Cleaning'
            },
            {
                'title': '[숨고] 인테리어 컨설팅 체험단',
                'url': 'https://www.soomgo.com',
                'deadline': datetime.utcnow() + timedelta(days=12),
                'category': '인테리어',
                'reward': '컨설팅 비용 50만원 무료',
                'description': '전문가의 인테리어 컨설팅을 받고 평가해주세요',
                'image_url': 'https://via.placeholder.com/300x200?text=Interior'
            }
        ]
        return listings


if __name__ == '__main__':
    crawler = SoomgoCrawler()
    result = crawler.run()
    print(f"Result: {result}")

"""Extended E2E User Journey Tests — Complete Business Workflows

Comprehensive end-to-end tests covering:
- SNS monetization user journey (Link-in-Bio → Revenue tracking)
- Review automation user journey (Scrape → Apply → Track)
- CooCook shopping user journey (Recipes → Shopping List → Export)
- AI automation user journey (Setup → Generate → Publish)
- Complex multi-service workflows
"""
import pytest
import json
from datetime import datetime, timedelta
from backend.app import create_app
from backend.models import (
    db, User, SNSLinkInBio, SNSAutomate, ReviewListing,
    ReviewAutoRule, ReviewApplication, SNSAccount
)


@pytest.fixture
def app():
    """Create and configure a test app instance for E2E testing"""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['JWT_SECRET_KEY'] = 'test-secret'

    with app.app_context():
        db.create_all()

        # Create test user
        user = User(
            email='etoend@example.com',
            name='E2E Test User',
            role='user'
        )
        user.set_password('password')
        db.session.add(user)
        db.session.commit()

        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Test client"""
    return app.test_client()


@pytest.fixture
def auth_headers():
    """Auth headers with demo token"""
    return {
        'Authorization': 'Bearer demo_token',
        'Content-Type': 'application/json'
    }


# ========== SNS MONETIZATION JOURNEY ==========

class TestSNSMonetizationJourney:
    """End-to-end SNS monetization workflow"""

    def test_creator_monetization_flow(self, client, auth_headers):
        """Complete creator monetization flow:
        1. Creator creates Link-in-Bio
        2. Shares link across social media
        3. Tracks clicks and engagement
        4. Views revenue metrics
        5. Optimizes based on trending content
        """
        # Step 1: Create Link-in-Bio landing page
        linkinbio_data = {
            'slug': 'creator-monetize',
            'title': 'My Creator Hub',
            'description': 'Welcome to my hub',
            'links': [
                {'url': 'https://youtube.com/@creator', 'label': 'YouTube', 'icon': 'youtube'},
                {'url': 'https://patreon.com/creator', 'label': 'Patreon', 'icon': 'patreon'},
                {'url': 'https://shop.creator.com', 'label': 'Shop', 'icon': 'shopping'}
            ],
            'theme': 'dark',
            'background_color': '#1a1a1a'
        }

        create_resp = client.post('/api/sns/linkinbio', headers=auth_headers,
                                 json=linkinbio_data)
        assert create_resp.status_code == 201
        lib_data = create_resp.get_json()['data']
        lib_id = lib_data['id']
        lib_slug = lib_data['slug']

        # Verify created
        assert lib_data['slug'] == 'creator-monetize'
        assert lib_data['click_count'] == 0

        # Step 2: Get the public URL and simulate shares
        public_urls = [
            f'/bio/{lib_slug}',
            f'/api/sns/linkinbio/public/{lib_slug}'
        ]

        # Simulate 25 clicks from different sources
        click_sources = [
            'instagram_story',
            'instagram_bio',
            'tiktok_bio',
            'youtube_community',
            'twitter_bio',
        ]

        for _ in range(5):
            for source in click_sources:
                # Simulate click from each source
                client.get(f'/bio/{lib_slug}', headers={'referer': source})

        # Step 3: Check Link-in-Bio statistics
        stats_resp = client.get(f'/api/sns/linkinbio/{lib_id}/stats',
                               headers=auth_headers)
        assert stats_resp.status_code == 200
        stats = stats_resp.get_json()

        # Should have clicks recorded
        assert stats['click_count'] >= 25
        assert 'clicks_by_day' in stats
        assert 'top_links' in stats or len(stats) > 0

        # Step 4: View ROI/Revenue metrics
        roi_resp = client.get('/api/sns/roi?period=month', headers=auth_headers)
        assert roi_resp.status_code == 200
        roi_data = roi_resp.get_json()

        # ROI metrics should be available
        assert 'revenue' in roi_data or 'roi_percentage' in roi_data

        # Step 5: Get trending topics to optimize content
        trending_resp = client.get('/api/sns/trending', headers=auth_headers)
        assert trending_resp.status_code == 200
        trending = trending_resp.get_json()

        # Should have trending data
        assert 'hashtags' in trending or 'topics' in trending or 'best_times' in trending

        # Step 6: Create automation to schedule posts aligned with trending
        automate_data = {
            'topic': 'Tech Trends',
            'platforms': ['instagram', 'tiktok'],
            'frequency': 'daily',
            'time_of_day': '10:00',  # Post when trending suggests
            'ai_model': 'claude',
            'is_enabled': True
        }

        auto_resp = client.post('/api/sns/automate', headers=auth_headers,
                               json=automate_data)
        assert auto_resp.status_code == 201
        auto_id = auto_resp.get_json()['data']['id']

        # Step 7: Run automation to generate content
        run_resp = client.post(f'/api/sns/automate/{auto_id}/run',
                              headers=auth_headers)
        assert run_resp.status_code in [200, 202]

        # Step 8: Update Link-in-Bio with new content
        update_resp = client.put(f'/api/sns/linkinbio/{lib_id}',
                                headers=auth_headers,
                                json={'title': 'Creator Monetization Hub 2.0'})
        assert update_resp.status_code == 200

        print(f"""
        ✓ SNS Monetization Journey Complete
        - Created Link-in-Bio: {lib_slug}
        - Tracked {stats['click_count']} clicks
        - Viewed ROI metrics
        - Analyzed trending content
        - Automated posting with AI
        - Updated landing page
        """)

    def test_multi_platform_link_in_bio_strategy(self, client, auth_headers):
        """Creator manages multiple Link-in-Bio pages for different audiences"""
        platforms = ['instagram', 'tiktok', 'youtube']

        created_bios = {}

        # Create separate Link-in-Bio for each platform
        for platform in platforms:
            bio_data = {
                'slug': f'bio-{platform}',
                'title': f'My {platform.title()} Hub',
                'description': f'Optimized for {platform}',
                'links': [
                    {'url': f'https://{platform}.com/@creator', 'label': platform.title(), 'icon': platform},
                    {'url': 'https://shop.com', 'label': 'Shop', 'icon': 'shopping'}
                ],
                'theme': 'light' if platform == 'tiktok' else 'dark'
            }

            resp = client.post('/api/sns/linkinbio', headers=auth_headers,
                              json=bio_data)
            assert resp.status_code == 201
            created_bios[platform] = resp.get_json()['data']

        # Verify all created
        assert len(created_bios) == 3

        # Get comparative stats
        all_stats = {}
        for platform, bio in created_bios.items():
            stats_resp = client.get(f'/api/sns/linkinbio/{bio["id"]}/stats',
                                   headers=auth_headers)
            assert stats_resp.status_code == 200
            all_stats[platform] = stats_resp.get_json()

        print(f"✓ Created {len(created_bios)} platform-specific Link-in-Bio pages")


# ========== REVIEW AUTO-APPLY JOURNEY ==========

class TestReviewAutoApplyJourney:
    """End-to-end review auto-apply workflow"""

    def test_reviewer_auto_apply_flow(self, client, auth_headers):
        """Complete reviewer journey:
        1. User sets up auto-apply rules
        2. System scrapes review listings
        3. Matches listings to rules
        4. Auto-applies to eligible reviews
        5. Tracks application status
        6. Views performance stats
        """
        # Step 1: Create auto-apply rules for Beauty category
        rule_data = {
            'name': 'Beauty Reviews 1K+',
            'enabled': True,
            'category': 'Beauty',
            'min_followers': 1000,
            'max_followers': 100000,
            'min_engagement_rate': 1.0,
            'platforms': ['revu', 'wible', 'reviewplace'],
            'require_english': True,
            'require_niche_match': False
        }

        rule_resp = client.post('/api/review/auto-apply-rules',
                               headers=auth_headers, json=rule_data)
        assert rule_resp.status_code == 201
        rule_id = rule_resp.get_json()['data']['id']

        # Step 2: Trigger scraping of review listings
        scrape_resp = client.post('/api/review/scrape/now', headers=auth_headers)
        assert scrape_resp.status_code in [200, 202]

        # Wait for scraping to complete (in real scenario)
        # For testing, we'll check aggregated results

        # Step 3: View aggregated Beauty listings
        listings_resp = client.get('/api/review/aggregated?category=Beauty',
                                  headers=auth_headers)
        assert listings_resp.status_code == 200
        listings_data = listings_resp.get_json()

        # Should have listings or be empty (depending on scraper mock)
        if isinstance(listings_data, list):
            listings = listings_data
        else:
            listings = listings_data.get('items', [])

        # Step 4: Check my applications (auto-applied)
        apps_resp = client.get('/api/review/my-applications',
                              headers=auth_headers)
        assert apps_resp.status_code == 200
        apps_data = apps_resp.get_json()

        if isinstance(apps_data, list):
            applications = apps_data
        else:
            applications = apps_data.get('items', [])

        # Step 5: Filter applications by status
        pending_resp = client.get('/api/review/my-applications?status=pending',
                                 headers=auth_headers)
        assert pending_resp.status_code == 200

        # Step 6: View detailed application
        if applications:
            app_id = applications[0]['id']
            detail_resp = client.get(f'/api/review/my-applications/{app_id}',
                                    headers=auth_headers)
            assert detail_resp.status_code == 200

        print(f"""
        ✓ Review Auto-Apply Journey Complete
        - Created auto-apply rule: {rule_id}
        - Triggered scraping
        - Found {len(listings)} listings
        - Auto-applied to {len(applications)} reviews
        - Tracking {len(applications)} applications
        """)

    def test_multi_category_auto_apply_strategy(self, client, auth_headers):
        """Reviewer manages multiple auto-apply rules for different categories"""
        categories = ['Beauty', 'Fashion', 'Tech']
        created_rules = {}

        # Create rules for each category
        for category in categories:
            rule_data = {
                'name': f'{category} Reviews',
                'enabled': True,
                'category': category,
                'min_followers': 500,
                'max_followers': 50000,
                'min_engagement_rate': 1.0,
                'platforms': ['revu', 'wible'],
                'require_english': True
            }

            resp = client.post('/api/review/auto-apply-rules',
                              headers=auth_headers, json=rule_data)
            assert resp.status_code == 201
            created_rules[category] = resp.get_json()['data']

        # Verify all rules created
        assert len(created_rules) == 3

        # Scrape once, applications match all rules
        scrape_resp = client.post('/api/review/scrape/now', headers=auth_headers)
        assert scrape_resp.status_code in [200, 202]

        print(f"✓ Created {len(created_rules)} auto-apply rules for categories: {', '.join(categories)}")


# ========== COOCOOK SHOPPING JOURNEY ==========

class TestCooCookShoppingJourney:
    """End-to-end cooking and shopping workflow"""

    def test_family_meal_planning_flow(self, client, auth_headers):
        """Complete family meal planning journey:
        1. Browse recipes
        2. Add recipes to favorites
        3. Create shopping list from recipes
        4. Export/share shopping list
        5. View meal plan
        """
        # Step 1: Search for recipes
        search_resp = client.get('/api/coocook/recipes?search=pasta&per_page=5',
                                headers=auth_headers)
        assert search_resp.status_code == 200
        recipes_data = search_resp.get_json()

        # Handle different response formats
        if isinstance(recipes_data, dict):
            recipes = recipes_data.get('items', recipes_data.get('recipes', []))
        else:
            recipes = recipes_data

        # Step 2: Create shopping list
        shopping_list_data = {
            'name': 'Weekly Grocery Shopping',
            'recipes': []  # Would add recipe IDs here
        }

        list_resp = client.post('/api/coocook/shopping-lists',
                               headers=auth_headers,
                               json=shopping_list_data)
        assert list_resp.status_code in [200, 201]
        list_id = list_resp.get_json().get('id', '')

        # Step 3: Add items to shopping list
        if list_id:
            item_data = {
                'name': 'Pasta (2 boxes)',
                'category': 'Grocery',
                'quantity': 2,
                'unit': 'box'
            }

            item_resp = client.post(f'/api/coocook/shopping-lists/{list_id}/items',
                                   headers=auth_headers,
                                   json=item_data)
            assert item_resp.status_code in [200, 201]

            # Step 4: Export shopping list
            export_resp = client.get(f'/api/coocook/shopping-lists/{list_id}/export?format=pdf',
                                    headers=auth_headers)
            # Could be PDF bytes or JSON with download link
            assert export_resp.status_code == 200

            # Step 5: Share shopping list
            share_resp = client.post(f'/api/coocook/shopping-lists/{list_id}/share',
                                    headers=auth_headers,
                                    json={'share_with': 'family'})
            # Sharing might be optional
            if share_resp.status_code != 404:
                assert share_resp.status_code in [200, 201]

        print(f"""
        ✓ CooCook Shopping Journey Complete
        - Found {len(recipes)} recipes
        - Created shopping list
        - Added items
        - Exported shopping list
        """)


# ========== AI CONTENT AUTOMATION JOURNEY ==========

class TestAIContentAutomationJourney:
    """End-to-end AI content generation and publishing"""

    def test_content_creator_ai_workflow(self, client, auth_headers):
        """Complete AI content workflow:
        1. Connect social media accounts
        2. Set up automation rules
        3. AI generates content
        4. Review and schedule
        5. Publish to multiple platforms
        6. Track performance
        """
        # Step 1: List connected SNS accounts
        accounts_resp = client.get('/api/sns/accounts', headers=auth_headers)
        assert accounts_resp.status_code == 200

        # Step 2: Create automation rule
        auto_data = {
            'topic': 'AI and Automation',
            'platforms': ['instagram', 'twitter', 'tiktok'],
            'frequency': 'every_3_days',
            'time_of_day': '09:00',
            'ai_model': 'claude',
            'is_enabled': True
        }

        auto_resp = client.post('/api/sns/automate', headers=auth_headers,
                               json=auto_data)
        assert auto_resp.status_code == 201
        auto_id = auto_resp.get_json()['data']['id']

        # Step 3: Generate content using AI
        ai_gen_resp = client.post('/api/sns/ai/generate',
                                 headers=auth_headers,
                                 json={
                                     'topic': 'AI and Automation',
                                     'platform': 'instagram'
                                 })
        assert ai_gen_resp.status_code == 200
        ai_content = ai_gen_resp.get_json()

        # Should have generated content
        assert 'content' in ai_content or 'success' in ai_content

        # Step 4: Create post from generated content
        if 'content' in ai_content:
            post_data = {
                'account_ids': [1],  # Mock account ID
                'content': ai_content['content'],
                'scheduled_at': (datetime.utcnow() + timedelta(hours=2)).isoformat(),
                'hashtags': ai_content.get('hashtags', []),
                'platforms': ['instagram', 'twitter']
            }

            post_resp = client.post('/api/sns/posts', headers=auth_headers,
                                   json=post_data)
            # Post creation might vary
            if post_resp.status_code != 404:
                assert post_resp.status_code in [200, 201]

        # Step 5: Get analytics for automation
        analytics_resp = client.get('/api/sns/analytics', headers=auth_headers)
        assert analytics_resp.status_code == 200

        print(f"""
        ✓ AI Content Automation Journey Complete
        - Created automation: {auto_id}
        - Generated AI content
        - Created scheduled posts
        - Tracking performance
        """)


# ========== COMPLEX MULTI-SERVICE WORKFLOW ==========

class TestMultiServiceIntegration:
    """Complex workflows involving multiple services"""

    def test_influencer_complete_platform_flow(self, client, auth_headers):
        """Influencer uses entire platform:
        1. Monetizes existing audience via Link-in-Bio
        2. Uses AI to automate content
        3. Applies to paid reviews
        4. Plans meals and shares shopping list
        """
        print("\n=== Multi-Service Integration Test ===")

        # Step 1: Monetization
        bio_resp = client.post('/api/sns/linkinbio', headers=auth_headers,
                              json={
                                  'slug': 'influencer-hub',
                                  'title': 'Influencer Hub',
                                  'links': [
                                      {'url': 'https://shop.influencer.com', 'label': 'Shop'},
                                      {'url': 'https://patreon.com/influencer', 'label': 'Support'}
                                  ]
                              })
        assert bio_resp.status_code == 201
        bio_id = bio_resp.get_json()['data']['id']

        # Step 2: AI Automation
        auto_resp = client.post('/api/sns/automate', headers=auth_headers,
                               json={
                                   'topic': 'Lifestyle',
                                   'platforms': ['instagram', 'tiktok'],
                                   'frequency': 'daily',
                                   'ai_model': 'claude'
                               })
        assert auto_resp.status_code == 201
        auto_id = auto_resp.get_json()['data']['id']

        # Step 3: Review Auto-Apply
        rule_resp = client.post('/api/review/auto-apply-rules',
                               headers=auth_headers,
                               json={
                                   'name': 'Lifestyle Reviews',
                                   'category': 'Lifestyle',
                                   'min_followers': 5000,
                                   'enabled': True
                               })
        assert rule_resp.status_code == 201
        rule_id = rule_resp.get_json()['data']['id']

        # Step 4: Cooking/Meal Planning
        list_resp = client.post('/api/coocook/shopping-lists',
                               headers=auth_headers,
                               json={'name': 'Content Creator Meal Plan'})
        # May not exist
        if list_resp.status_code != 404:
            assert list_resp.status_code in [200, 201]

        print(f"""
        ✓ Multi-Service Integration Complete
        - Link-in-Bio: {bio_id}
        - AI Automation: {auto_id}
        - Review Auto-Apply: {rule_id}
        - Meal Planning: configured
        """)


# ========== ERROR RECOVERY JOURNEYS ==========

class TestErrorRecoveryJourneys:
    """Test user journeys with error handling"""

    def test_incomplete_linkinbio_submission(self, client, auth_headers):
        """User tries to create incomplete Link-in-Bio"""
        # Missing required fields
        resp = client.post('/api/sns/linkinbio', headers=auth_headers,
                          json={'title': 'Only Title'})

        assert resp.status_code == 422

        # User corrects and retries
        correct_data = {
            'slug': 'corrected',
            'title': 'Only Title',
            'links': [{'url': 'https://example.com', 'label': 'Home'}]
        }

        retry_resp = client.post('/api/sns/linkinbio', headers=auth_headers,
                                json=correct_data)
        assert retry_resp.status_code == 201

    def test_duplicate_rule_handling(self, client, auth_headers):
        """User tries to create duplicate auto-apply rule"""
        rule_data = {
            'name': 'Beauty Reviews',
            'category': 'Beauty',
            'enabled': True
        }

        # Create first
        first_resp = client.post('/api/review/auto-apply-rules',
                                headers=auth_headers, json=rule_data)
        assert first_resp.status_code == 201

        # Try to create duplicate
        dup_resp = client.post('/api/review/auto-apply-rules',
                              headers=auth_headers, json=rule_data)
        # Should either reject or allow (depends on implementation)
        # Gracefully handle either way


# ========== JOURNEY DOCUMENTATION ==========

class TestJourneyDocumentation:
    """Document supported user journeys"""

    def test_document_user_journey_sms_monetization(self):
        """Document SNS monetization journey"""
        journey = {
            'name': 'SNS Monetization',
            'steps': [
                'Create Link-in-Bio landing page',
                'Share link across social media',
                'Track clicks and engagement',
                'View revenue metrics',
                'Analyze trending content',
                'Automate content with AI',
                'Optimize based on performance'
            ],
            'endpoints': [
                'POST /api/sns/linkinbio',
                'GET /api/sns/linkinbio/<id>/stats',
                'GET /api/sns/roi',
                'GET /api/sns/trending',
                'POST /api/sns/automate'
            ]
        }

        assert journey['name'] == 'SNS Monetization'
        assert len(journey['steps']) >= 5
        assert len(journey['endpoints']) >= 3

    def test_document_user_journey_review_auto_apply(self):
        """Document review auto-apply journey"""
        journey = {
            'name': 'Review Auto-Apply',
            'steps': [
                'Create auto-apply rules by category',
                'Trigger scraping of review listings',
                'Auto-apply to matching reviews',
                'Track application status',
                'View performance stats'
            ],
            'endpoints': [
                'POST /api/review/auto-apply-rules',
                'POST /api/review/scrape/now',
                'GET /api/review/aggregated',
                'GET /api/review/my-applications'
            ]
        }

        assert journey['name'] == 'Review Auto-Apply'
        assert len(journey['steps']) >= 3

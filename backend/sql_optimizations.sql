-- Database Optimization Script for SoftFactory
-- SQLite Version
-- Generated: 2026-02-25
-- Execute after backing up platform.db

-- ============= STEP 1: CREATE INDEXES =============

-- Campaign Applications - High traffic query
CREATE INDEX IF NOT EXISTS idx_campaign_applications_campaign_id
ON campaign_applications(campaign_id);

-- SNS Posts - Account lookup
CREATE INDEX IF NOT EXISTS idx_sns_posts_account_id
ON sns_posts(account_id);

-- Booking Reviews - Chef detail page
CREATE INDEX IF NOT EXISTS idx_booking_reviews_chef_id
ON booking_reviews(chef_id);

-- Bookings - User's bookings by date (composite)
CREATE INDEX IF NOT EXISTS idx_bookings_user_date
ON bookings(user_id, booking_date DESC);

-- SNS Posts - Status filter (optional, partial index)
-- Note: SQLite has limited partial index support
CREATE INDEX IF NOT EXISTS idx_sns_posts_status
ON sns_posts(status, created_at DESC);

-- Campaign - Status and deadline (common filter)
CREATE INDEX IF NOT EXISTS idx_campaigns_status_deadline
ON campaigns(status, deadline);

-- Subscriptions - User lookup
CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id
ON subscriptions(user_id);

-- Payments - User lookup
CREATE INDEX IF NOT EXISTS idx_payments_user_id
ON payments(user_id);

-- SNS Accounts - User lookup
CREATE INDEX IF NOT EXISTS idx_sns_accounts_user_id
ON sns_accounts(user_id);

-- ============= STEP 2: ANALYZE (Update Statistics) =============

-- SQLite ANALYZE - updates query planner statistics
ANALYZE;

-- ============= STEP 3: VERIFY INDEXES =============

-- Query to verify indexes are being used
-- Use EXPLAIN QUERY PLAN before and after

-- Example checks:
-- EXPLAIN QUERY PLAN SELECT * FROM campaign_applications WHERE campaign_id = 5;
-- Should show: SEARCH campaign_applications USING idx_campaign_applications_campaign_id

-- ============= STEP 4: OPTIONAL - VACUUM & OPTIMIZE =============

-- Clean up database file (reorder pages for efficiency)
-- Note: This locks the database, run during maintenance window
-- VACUUM;

-- Optimize query execution (analyze and reindex)
-- PRAGMA optimize;

-- ============= MIGRATION NOTES FOR POSTGRESQL =============

/*
For PostgreSQL migration, use these statements instead:

-- Create schema
CREATE SCHEMA IF NOT EXISTS public;

-- Create indexes CONCURRENTLY (non-blocking)
CREATE INDEX CONCURRENTLY idx_campaign_applications_campaign_id
ON campaign_applications(campaign_id);

CREATE INDEX CONCURRENTLY idx_sns_posts_account_id
ON sns_posts(account_id);

CREATE INDEX CONCURRENTLY idx_booking_reviews_chef_id
ON booking_reviews(chef_id);

CREATE INDEX CONCURRENTLY idx_bookings_user_date
ON bookings(user_id, booking_date DESC);

-- Partial index (PostgreSQL supports better)
CREATE INDEX CONCURRENTLY idx_sns_posts_status_active
ON sns_posts(created_at DESC) WHERE status IN ('draft', 'scheduled', 'published');

-- ANALYZE statistics
ANALYZE;

-- Show index bloat
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;
*/

-- ============= PERFORMANCE BASELINES =============

/*
After running these optimizations, use these queries to measure improvements:

-- Test 1: Campaign list (was 42ms with N+1)
SELECT c.id, c.title, COUNT(ca.id) as app_count
FROM campaigns c
LEFT JOIN campaign_applications ca ON c.id = ca.campaign_id
WHERE c.status = 'active' AND c.deadline > datetime('now')
GROUP BY c.id
ORDER BY c.created_at DESC
LIMIT 12;

-- Expected time: <10ms (was 42ms)
-- Uses: idx_campaigns_status_deadline, idx_campaign_applications_campaign_id

-- Test 2: SNS accounts with post counts (was 25ms with N+1)
SELECT a.id, a.platform, COUNT(p.id) as post_count
FROM sns_accounts a
LEFT JOIN sns_posts p ON a.id = p.account_id
WHERE a.user_id = 1
GROUP BY a.id;

-- Expected time: <5ms (was 25ms)
-- Uses: idx_sns_accounts_user_id, idx_sns_posts_account_id

-- Test 3: User bookings with chef (was 18ms with N+1)
SELECT b.id, b.user_id, c.name, b.booking_date, b.status
FROM bookings b
JOIN chefs c ON b.chef_id = c.id
WHERE b.user_id = 1
ORDER BY b.booking_date DESC;

-- Expected time: <3ms (was 18ms)
-- Uses: idx_bookings_user_date (user_id + date)

-- Test 4: Dashboard stats (was 58ms with 6 separate queries)
SELECT
    (SELECT COUNT(*) FROM users) as users,
    (SELECT COUNT(*) FROM payments) as payments,
    (SELECT COUNT(*) FROM bookings) as bookings,
    (SELECT COUNT(*) FROM sns_posts) as sns_posts,
    (SELECT COUNT(*) FROM campaigns) as campaigns,
    (SELECT COUNT(*) FROM ai_employees) as ai_employees;

-- Alternative using UNION
SELECT 'users' as metric, COUNT(*) as count FROM users
UNION ALL
SELECT 'payments', COUNT(*) FROM payments
UNION ALL
SELECT 'bookings', COUNT(*) FROM bookings
UNION ALL
SELECT 'sns_posts', COUNT(*) FROM sns_posts
UNION ALL
SELECT 'campaigns', COUNT(*) FROM campaigns
UNION ALL
SELECT 'ai_employees', COUNT(*) FROM ai_employees;

-- Expected time: <5ms (was 58ms)
-- Note: Multiple subqueries still better than 6 separate round trips
*/

-- ============= SCHEMA VALIDATION =============

/*
Run this to verify all indexes exist:

SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%';

Expected results should include:
- idx_campaign_applications_campaign_id
- idx_sns_posts_account_id
- idx_booking_reviews_chef_id
- idx_bookings_user_date
- idx_sns_posts_status
- idx_campaigns_status_deadline
- idx_subscriptions_user_id
- idx_payments_user_id
- idx_sns_accounts_user_id
*/

-- ============= MAINTENANCE QUERIES =============

/*
Run periodically to maintain performance:

-- Check largest tables (identify bloat)
SELECT name, sum(pgsize) as size_bytes
FROM (
    SELECT name, pgsize FROM dbstat
) GROUP BY name ORDER BY size_bytes DESC LIMIT 10;

-- Alternative for SQLite (without dbstat extension)
PRAGMA database_list;
SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size();

-- Defragment database (SQLite)
VACUUM;

-- Recompute index statistics (SQLite)
ANALYZE;
*/

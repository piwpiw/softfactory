/**
 * SoftFactory API Client Module v2.0
 * Comprehensive API integration for all SoftFactory services
 *
 * FEATURES:
 * - Authentication: login, register, OAuth (Google, Facebook, Kakao)
 * - SNS Automation: 25+ endpoints for multi-platform social media management
 * - Review Campaigns: 15+ endpoints for review management and auto-apply
 * - Payment & Billing: subscription, invoice, and billing management
 * - Demo Mode: Full simulation without backend (passkey: "demo2026")
 *
 * DEMO MODE: Use passkey "demo2026" to bypass authentication
 *
 * @module api
 * @version 2.0
 * @since 2026-02-26
 *
 * FUNCTION CATEGORIES:
 * - Auth Management: register, login, logout, refresh tokens
 * - OAuth & Social Login: loginWithGoogle, loginWithFacebook, loginWithKakao, handleOAuthCallback
 * - SNS Accounts: getSNSAccounts, createSNSAccount, deleteSNSAccount, reconnectSNSAccount
 * - SNS Posts: getSNSPosts, createSNSPost, updateSNSPost, deleteSNSPost, publishSNSPost, getSNSPostMetrics
 * - SNS Analytics: getSNSAnalytics, getSNSAnalyticsLegacy
 * - SNS Inbox: getSNSInboxMessages, replySNSInboxMessage, markSNSInboxRead
 * - SNS Calendar: getSNSCalendar
 * - SNS Campaigns: getSNSCampaigns, createSNSCampaign, updateSNSCampaign, deleteSNSCampaign
 * - SNS Link in Bio: createLinkInBio, updateLinkInBio, getLinkInBio, getLinkInBioStats
 * - SNS Automation: createAutomate, getAutomate, updateAutomate, deleteAutomate
 * - SNS Intelligence: getTrending, getCompetitor
 * - SNS AI: generateSNSContent, generateSNSHashtags, optimizeSNSContent
 * - Review Listings: getReviewListings, getReviewListing
 * - Review Applications: applyToReview, getMyApplications
 * - Review Accounts: getReviewAccounts, createReviewAccount, updateReviewAccount, deleteReviewAccount
 * - Review Auto-Apply: getAutoApplyRules, createAutoApplyRule, updateAutoApplyRule, deleteAutoApplyRule, runAutoApply
 * - Review Stats: getReviewStats, getReviewAnalytics, bookmarkReview, unbookmarkReview, getBookmarkedReviews
 * - Payment: getBillingInfo, getPaymentHistory, getPlans, createCheckout, getSubscriptions, cancelSubscription
 * - UI Helpers: formatKRW, formatDate, statusBadge, showToast, showError, showSuccess, etc.
 * - Token Management: getAuthToken, setAuthToken, clearAuthToken, isAuthenticated, getAuthUser
 *
 * ERROR HANDLING:
 * - All async functions include try/catch with user-friendly error messages
 * - showError() displays errors as toast notifications
 * - showSuccess() displays success confirmations
 * - confirmModal() requests user confirmation for destructive actions
 *
 * DEMO DATA:
 * - isDemoMode() checks localStorage for demo mode flag
 * - enableDemoMode() loads mock data without API calls
 * - generateMockData() provides realistic test data for all endpoints
 *
 * JSDOC STANDARDS:
 * - All functions include @param, @returns, @throws documentation
 * - Parameter types specified with examples
 * - Return types and structures documented
 * - Error conditions documented
 */

const API_BASE = window.__SF_API_BASE
    || (typeof window !== 'undefined' && window.location && window.location.origin !== 'null'
        ? window.location.origin
        : 'http://localhost:9000');
const isLocalHost = typeof window !== 'undefined' && (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1');
const API_BASE_FALLBACKS = isLocalHost
    ? [
        'http://localhost:9000',
        'http://localhost:8000',
        'http://127.0.0.1:9000',
        'http://127.0.0.1:8000'
    ]
    : [''];
const DEMO_PASSKEY = 'demo2026';
const DEMO_USER = {
    id: 999,
    email: 'demo@softfactory.com',
    name: 'Demo User',
    role: 'admin',
    is_admin: true,
    is_superuser: true
};

// ============ SMART API MODE DETECTION ============

/**
 * Detects whether the live backend is available.
 * Sets window.__API_MODE to 'live' or 'demo'.
 * Tries primary API_BASE first, then fallback port.
 * @returns {Promise<boolean>} true if live backend is available
 */
async function detectApiMode() {
    const endpoints = [API_BASE, ...API_BASE_FALLBACKS].filter((value, index, arr) => {
        if (!value) return false;
        return arr.indexOf(value) === index;
    });
    for (const base of endpoints) {
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 3000);
            const resp = await fetch(base + '/health', {
                signal: controller.signal,
                headers: { 'Accept': 'application/json' }
            });
            clearTimeout(timeoutId);
            if (resp.ok || resp.status === 404) {
                // 404 is acceptable — server is alive but may not have /health
                window.__API_MODE = 'live';
                window.__SF_API_BASE_RESOLVED = base;
                console.log('[API] Connected to live backend at ' + base);
                _sfRenderApiModeIndicator();
                return true;
            }
        } catch (e) {
            // Try next endpoint
        }
    }
    window.__API_MODE = 'demo';
    window.__SF_API_BASE_RESOLVED = null;
    console.log('[API] Demo mode (backend not available)');
    if (!isDemoMode()) {
        enableDemoMode();
    }
    _sfRenderApiModeIndicator();
    return false;
}

/**
 * Get the resolved API base URL (after detection)
 * @returns {string} Resolved API base URL
 */
function getResolvedApiBase() {
    return window.__SF_API_BASE_RESOLVED || API_BASE;
}

/**
 * Returns current API mode: 'live', 'demo', or 'detecting'
 */
function getApiMode() {
    return window.__API_MODE || 'detecting';
}

/**
 * Render visual API mode indicator in the page
 * Shows a small badge in the bottom-left corner
 */
function _sfRenderApiModeIndicator() {
    let indicator = document.getElementById('sf-api-mode-indicator');
    if (!indicator) {
        indicator = document.createElement('div');
        indicator.id = 'sf-api-mode-indicator';
        indicator.style.cssText = 'position:fixed;top:12px;right:12px;z-index:9997;padding:4px 12px;border-radius:20px;font-size:11px;font-weight:600;cursor:pointer;transition:all 0.3s ease;font-family:Inter,sans-serif;display:flex;align-items:center;gap:6px;box-shadow:0 2px 8px rgba(0,0,0,0.3);';
        indicator.onclick = () => {
            const mode = getApiMode();
            if (mode === 'demo') {
                showToast('Demo mode - Backend unavailable. Using simulated data.', 'warning');
            } else {
                showToast('Live mode - Connected to backend at ' + getResolvedApiBase(), 'success');
            }
        };
        document.body.appendChild(indicator);
    }

    const mode = getApiMode();
    if (mode === 'live') {
        indicator.style.background = 'linear-gradient(135deg, #059669, #047857)';
        indicator.style.border = '1px solid #10b981';
        indicator.style.color = '#fff';
        indicator.innerHTML = '<span style="width:6px;height:6px;border-radius:50%;background:#4ade80;display:inline-block;animation:sf-pulse-dot 2s infinite;"></span> LIVE';
    } else {
        indicator.style.background = 'linear-gradient(135deg, #d97706, #b45309)';
        indicator.style.border = '1px solid #f59e0b';
        indicator.style.color = '#fff';
        indicator.innerHTML = '<span style="width:6px;height:6px;border-radius:50%;background:#fcd34d;display:inline-block;"></span> DEMO';
    }

    // Inject pulse animation if not present
    if (!document.getElementById('sf-pulse-dot-style')) {
        const style = document.createElement('style');
        style.id = 'sf-pulse-dot-style';
        style.textContent = '@keyframes sf-pulse-dot{0%,100%{opacity:1}50%{opacity:0.4}}';
        document.head.appendChild(style);
    }
}

// Auto-detect API mode on page load
if (typeof document !== 'undefined') {
    document.addEventListener('DOMContentLoaded', () => {
        detectApiMode();
    });
}

// ============ GLOBAL LOADING OVERLAY ============

/**
 * Show a full-screen loading overlay with optional message
 * @param {string} message - Loading message to display
 */
function showLoading(message = '로딩 중...') {
    let overlay = document.getElementById('sf-loading-overlay');
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.id = 'sf-loading-overlay';
        overlay.innerHTML = `
            <div style="position:fixed;inset:0;background:rgba(15,23,42,0.75);backdrop-filter:blur(4px);display:flex;align-items:center;justify-content:center;z-index:9999;transition:opacity 0.3s ease;">
                <div style="text-align:center;">
                    <div style="width:48px;height:48px;border:4px solid rgba(139,92,246,0.3);border-top-color:#8b5cf6;border-radius:50%;animation:sf-spin 0.7s linear infinite;margin:0 auto 16px;"></div>
                    <p id="sf-loading-message" style="color:#e2e8f0;font-size:14px;font-weight:500;">${message}</p>
                </div>
            </div>
        `;
        if (!document.getElementById('sf-loading-styles')) {
            const style = document.createElement('style');
            style.id = 'sf-loading-styles';
            style.textContent = '@keyframes sf-spin{to{transform:rotate(360deg)}}';
            document.head.appendChild(style);
        }
        document.body.appendChild(overlay);
    } else {
        const msgEl = document.getElementById('sf-loading-message');
        if (msgEl) msgEl.textContent = message;
        overlay.style.display = 'block';
        overlay.firstElementChild.style.opacity = '1';
    }
}

/**
 * Hide the global loading overlay
 */
function hideLoading() {
    const overlay = document.getElementById('sf-loading-overlay');
    if (overlay) {
        overlay.firstElementChild.style.opacity = '0';
        setTimeout(() => { overlay.style.display = 'none'; }, 300);
    }
}

// ============ OFFLINE DETECTION & NOTIFICATION ============

let _sfIsOffline = !navigator.onLine;
let _sfOfflineBanner = null;

function _sfCreateOfflineBanner() {
    if (_sfOfflineBanner) return;
    _sfOfflineBanner = document.createElement('div');
    _sfOfflineBanner.id = 'sf-offline-banner';
    _sfOfflineBanner.style.cssText = 'position:fixed;top:0;left:0;right:0;padding:10px 16px;background:linear-gradient(135deg,#dc2626,#b91c1c);color:#fff;text-align:center;font-size:13px;font-weight:600;z-index:10000;transform:translateY(-100%);transition:transform 0.4s cubic-bezier(0.16,1,0.3,1);box-shadow:0 4px 12px rgba(0,0,0,0.3);';
    _sfOfflineBanner.innerHTML = '<span style="margin-right:8px;">&#x26A0;</span>  &#xC778;&#xD130;&#xB137; &#xC5F0;&#xACB0;&#xC774; &#xB04A;&#xC5B4;&#xC84C;&#xC2B5;&#xB2C8;&#xB2E4;. &#xC77C;&#xBD80; &#xAE30;&#xB2A5;&#xC774; &#xC81C;&#xD55C;&#xB420; &#xC218; &#xC788;&#xC2B5;&#xB2C8;&#xB2E4;.';
    document.body.appendChild(_sfOfflineBanner);
}

function _sfShowOfflineBanner() {
    _sfCreateOfflineBanner();
    requestAnimationFrame(() => {
        requestAnimationFrame(() => {
            _sfOfflineBanner.style.transform = 'translateY(0)';
        });
    });
}

function _sfHideOfflineBanner() {
    if (_sfOfflineBanner) {
        _sfOfflineBanner.style.transform = 'translateY(-100%)';
    }
}

window.addEventListener('offline', () => {
    _sfIsOffline = true;
    _sfShowOfflineBanner();
});

window.addEventListener('online', () => {
    _sfIsOffline = false;
    _sfHideOfflineBanner();
    showToast('인터넷 연결이 복구되었습니다', 'success');
});

// Show banner on load if already offline
if (typeof document !== 'undefined') {
    document.addEventListener('DOMContentLoaded', () => {
        if (!navigator.onLine) {
            _sfShowOfflineBanner();
        }
    });
}

// ============ NETWORK RETRY WITH EXPONENTIAL BACKOFF ============

/**
 * Fetch with automatic retry and exponential backoff
 * @param {string} url - URL to fetch
 * @param {object} options - Fetch options
 * @param {number} maxRetries - Maximum number of retries (default: 3)
 * @param {number} baseDelay - Base delay in ms (default: 1000)
 * @returns {Promise<Response>}
 */
async function fetchWithRetry(url, options = {}, maxRetries = 3, baseDelay = 1000) {
    let lastError;
    for (let attempt = 0; attempt <= maxRetries; attempt++) {
        try {
            const response = await fetch(url, options);
            // Retry on 5xx server errors, not on 4xx client errors
            if (response.status >= 500 && attempt < maxRetries) {
                throw new Error(`Server error: ${response.status}`);
            }
            return response;
        } catch (error) {
            lastError = error;
            if (attempt < maxRetries) {
                const delay = baseDelay * Math.pow(2, attempt) + Math.random() * 500;
                console.warn(`[API] Retry ${attempt + 1}/${maxRetries} after ${Math.round(delay)}ms:`, error.message);
                await new Promise(resolve => setTimeout(resolve, delay));
            }
        }
    }
    throw lastError;
}

// ============ DEMO MODE ============

function isDemoMode() {
    return localStorage.getItem('demo_mode') === 'true';
}

function enableDemoMode() {
    localStorage.setItem('demo_mode', 'true');
    localStorage.setItem('user', JSON.stringify(DEMO_USER));
    localStorage.setItem('access_token', 'demo_token');
    localStorage.setItem('refresh_token', 'demo_token');
}

function disableDemoMode() {
    localStorage.removeItem('demo_mode');
    localStorage.clear();
}

// ============ AUTH MANAGEMENT ============

async function apiFetch(path, options = {}) {
    // Block requests when offline
    if (_sfIsOffline) {
        // Fall back to demo mode when offline
        if (isDemoMode()) {
            return mockApiFetch(path, options);
        }
        showToast('오프라인 상태입니다. 인터넷 연결을 확인하세요.', 'warning');
        throw new Error('Network offline');
    }

    // If explicitly in demo mode and we haven't detected a live backend, use mock
    if (isDemoMode() && getApiMode() !== 'live') {
        return mockApiFetch(path, options);
    }

    // Always try real API first
    const apiBase = getResolvedApiBase();
    const url = `${apiBase}${path}`;
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers
    };

    // Add auth token if available
    const token = localStorage.getItem('access_token');
    if (token && token !== 'demo_token') {
        headers['Authorization'] = `Bearer ${token}`;
    } else if (token === 'demo_token') {
        headers['Authorization'] = 'Bearer demo_token';
    }

    try {
        let response = await fetchWithRetry(url, {
            ...options,
            headers
        }, 2, 800);

        // If 401, try to refresh token
        if (response.status === 401) {
            const refreshToken = localStorage.getItem('refresh_token');
            if (refreshToken && refreshToken !== 'demo_token') {
                const refreshResp = await fetchWithRetry(`${apiBase}/api/auth/refresh`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ refresh_token: refreshToken })
                }, 1);

                if (refreshResp.ok) {
                    const refreshData = await refreshResp.json();
                    localStorage.setItem('access_token', refreshData.access_token);
                    localStorage.setItem('refresh_token', refreshData.refresh_token);

                    // Retry original request
                    headers['Authorization'] = `Bearer ${refreshData.access_token}`;
                    response = await fetchWithRetry(url, {
                        ...options,
                        headers
                    }, 1);
                } else {
                    // Refresh failed - redirect to login
                    localStorage.clear();
                    window.location.href = '/web/platform/login.html';
                }
            }
        }

        return response;
    } catch (error) {
        // Connection failed — fall back to demo mode gracefully
        console.warn('[API] Real API failed, falling back to demo mode:', error.message);
        if (window.__API_MODE !== 'demo') {
            window.__API_MODE = 'demo';
            _sfRenderApiModeIndicator();
        }
        return mockApiFetch(path, options);
    }
}

// Mock API responses for demo mode
async function mockApiFetch(path, options = {}) {
    await new Promise(resolve => setTimeout(resolve, 300)); // Simulate network delay

    const response = new Response(JSON.stringify(generateMockData(path, options)), {
        status: 200,
        headers: { 'Content-Type': 'application/json' }
    });

    response.ok = true;
    return response;
}

function generateMockData(path, options) {
    // Platform
    if (path === '/api/platform/products') {
        return {
            'coocook': { slug: 'coocook', name: 'CooCook', description: 'Local food experiences', icon: '🍳', monthly_price: 39000 },
            'sns-auto': { slug: 'sns-auto', name: 'SNS Auto', description: 'Social media automation', icon: '📱', monthly_price: 49000 },
            'review': { slug: 'review', name: 'Review Campaign', description: 'Brand reviews', icon: '⭐', monthly_price: 99000 },
            'ai-automation': { slug: 'ai-automation', name: 'AI Automation', description: '24/7 AI employees', icon: '🤖', monthly_price: 89000 },
            'webapp-builder': { slug: 'webapp-builder', name: 'WebApp Builder', description: '8-week bootcamp', icon: '💻', monthly_price: 590000 }
        };
    }
    if (path === '/api/platform/dashboard') {
        return {
            active_services: 5,
            total_spent: 195000,
            monthly_mrr: 276000,
            email: DEMO_USER.email,
            products: [
                { slug: 'coocook', name: 'CooCook', status: 'active', next_billing: '2026-03-24' },
                { slug: 'sns-auto', name: 'SNS Auto', status: 'active', next_billing: '2026-03-24' },
                { slug: 'review', name: 'Review Campaign', status: 'active', next_billing: '2026-03-24' },
                { slug: 'ai-automation', name: 'AI Automation', status: 'active', next_billing: '2026-03-24' },
                { slug: 'webapp-builder', name: 'WebApp Builder', status: 'completed', progress: 25 }
            ]
        };
    }

    // CooCook
    if (path.startsWith('/api/coocook/chefs') && !path.includes('/')) {
        const chefs = [
            { id: 1, name: 'Chef Park', cuisine_type: 'Korean', location: 'Seoul', price_per_session: 150000, rating: 4.9, rating_count: 28, bio: 'Traditional Korean cuisine expert with 15 years experience', image: '🇰🇷', specialties: ['Hansik', 'Bibimbap', 'Kimchi'] },
            { id: 2, name: 'Chef Marco', cuisine_type: 'Italian', location: 'Seoul', price_per_session: 180000, rating: 4.8, rating_count: 35, bio: 'Authentic Italian pasta and risotto specialist', image: '🇮🇹', specialties: ['Pasta', 'Risotto', 'Tiramisu'] },
            { id: 3, name: 'Chef Tanaka', cuisine_type: 'Japanese', location: 'Seoul', price_per_session: 200000, rating: 4.9, rating_count: 42, bio: 'Master sushi chef trained in Tokyo', image: '🇯🇵', specialties: ['Sushi', 'Tempura', 'Kaiseki'] },
            { id: 4, name: 'Chef Dubois', cuisine_type: 'French', location: 'Seoul', price_per_session: 180000, rating: 4.7, rating_count: 22, bio: 'Trained in French culinary techniques', image: '🇫🇷', specialties: ['Cuisine Classique', 'Coq au Vin', 'Beef Bourguignon'] },
            { id: 5, name: 'Chef Garcia', cuisine_type: 'Mexican', location: 'Seoul', price_per_session: 140000, rating: 4.8, rating_count: 31, bio: 'Authentic Mexican street food master', image: '🇲🇽', specialties: ['Tacos', 'Mole', 'Ceviche'] }
        ];
        return { chefs: chefs, pages: 1, page: 1 };
    }
    if (path.match(/\/api\/coocook\/chefs\/\d+$/)) {
        const chefId = parseInt(path.match(/\/(\d+)$/)[1]);
        const chefs = {
            1: { id: 1, name: 'Chef Park', cuisine_type: 'Korean', location: 'Seoul', price_per_session: 150000, rating: 4.9, rating_count: 28, bio: 'Traditional Korean cuisine expert with 15 years experience', image: '🇰🇷', specialties: ['Hansik', 'Bibimbap', 'Kimchi'], reviews: [{ author: 'User A', rating: 5, comment: 'Amazing experience!' }, { author: 'User B', rating: 5, comment: 'Very professional' }] },
            2: { id: 2, name: 'Chef Marco', cuisine_type: 'Italian', location: 'Seoul', price_per_session: 180000, rating: 4.8, rating_count: 35, bio: 'Authentic Italian pasta and risotto specialist', image: '🇮🇹', specialties: ['Pasta', 'Risotto', 'Tiramisu'], reviews: [{ author: 'User C', rating: 5, comment: 'Delicious!' }] },
            3: { id: 3, name: 'Chef Tanaka', cuisine_type: 'Japanese', location: 'Seoul', price_per_session: 200000, rating: 4.9, rating_count: 42, bio: 'Master sushi chef trained in Tokyo', image: '🇯🇵', specialties: ['Sushi', 'Tempura', 'Kaiseki'], reviews: [{ author: 'User D', rating: 5, comment: 'Exceptional skills' }] },
            4: { id: 4, name: 'Chef Dubois', cuisine_type: 'French', location: 'Seoul', price_per_session: 180000, rating: 4.7, rating_count: 22, bio: 'Trained in French culinary techniques', image: '🇫🇷', specialties: ['Cuisine Classique', 'Coq au Vin', 'Beef Bourguignon'], reviews: [{ author: 'User E', rating: 5, comment: 'Classic French' }] },
            5: { id: 5, name: 'Chef Garcia', cuisine_type: 'Mexican', location: 'Seoul', price_per_session: 140000, rating: 4.8, rating_count: 31, bio: 'Authentic Mexican street food master', image: '🇲🇽', specialties: ['Tacos', 'Mole', 'Ceviche'], reviews: [{ author: 'User F', rating: 5, comment: 'Street food perfection' }] }
        };
        return chefs[chefId] || chefs[1];
    }
    if (path.startsWith('/api/coocook/bookings') && options.method === 'POST') {
        return { id: 1, status: 'confirmed', total_price: 300000, message: 'Booking confirmed!' };
    }
    if (path === '/api/coocook/bookings') {
        return [
            { id: 1, chef_id: 1, chef_name: 'Chef Park', booking_date: '2026-03-01', duration_hours: 2, status: 'confirmed', total_price: 300000 },
            { id: 2, chef_id: 2, chef_name: 'Chef Marco', booking_date: '2026-02-28', duration_hours: 3, status: 'completed', total_price: 540000 }
        ];
    }

    // CooCook Search
    if (path.startsWith('/api/coocook/search')) {
        const chefs = [
            { id: 1, name: 'Chef Park', cuisine_type: 'Korean', location: 'Seoul', price_per_session: 150000, rating: 4.9, rating_count: 28, bio: 'Traditional Korean cuisine expert', menus: [{ id: 1, name: 'Traditional Bibimbap Set', category: 'main', cuisine: 'Korean', price: 45000 }] },
            { id: 3, name: 'Chef Tanaka', cuisine_type: 'Japanese', location: 'Seoul', price_per_session: 200000, rating: 4.9, rating_count: 42, bio: 'Master sushi chef', menus: [{ id: 5, name: 'Premium Sushi Omakase', category: 'main', cuisine: 'Japanese', price: 95000 }] },
            { id: 2, name: 'Chef Marco', cuisine_type: 'Italian', location: 'Seoul', price_per_session: 180000, rating: 4.8, rating_count: 35, bio: 'Italian pasta specialist', menus: [{ id: 3, name: 'Truffle Pasta Carbonara', category: 'main', cuisine: 'Italian', price: 55000 }] },
        ];
        return { results: chefs, total: 3, pages: 1, current_page: 1, query: '', filters: {} };
    }
    if (path === '/api/coocook/categories') {
        return {
            categories: [
                { slug: 'main', name: 'main', display_name: 'Main Course', count: 7 },
                { slug: 'soup', name: 'soup', display_name: 'Soup & Stew', count: 1 },
                { slug: 'noodle', name: 'noodle', display_name: 'Noodle', count: 1 },
                { slug: 'appetizer', name: 'appetizer', display_name: 'Appetizer', count: 1 }
            ]
        };
    }
    if (path === '/api/coocook/cuisines') {
        return {
            cuisines: [
                { name: 'Korean', chef_count: 1, avg_rating: 4.9, avg_price: 150000 },
                { name: 'Italian', chef_count: 1, avg_rating: 4.8, avg_price: 180000 },
                { name: 'Japanese', chef_count: 1, avg_rating: 4.9, avg_price: 200000 },
                { name: 'French', chef_count: 1, avg_rating: 4.7, avg_price: 180000 },
                { name: 'Mexican', chef_count: 1, avg_rating: 4.8, avg_price: 140000 }
            ]
        };
    }
    if (path.startsWith('/api/coocook/popular')) {
        return {
            popular_chefs: [
                { rank: 1, id: 3, name: 'Chef Tanaka', cuisine_type: 'Japanese', rating: 4.9, rating_count: 42, price_per_session: 200000, total_bookings: 15, popularity_score: 205.8 },
                { rank: 2, id: 2, name: 'Chef Marco', cuisine_type: 'Italian', rating: 4.8, rating_count: 35, price_per_session: 180000, total_bookings: 12, popularity_score: 168.0 },
                { rank: 3, id: 5, name: 'Chef Garcia', cuisine_type: 'Mexican', rating: 4.8, rating_count: 31, price_per_session: 140000, total_bookings: 10, popularity_score: 148.8 },
                { rank: 4, id: 1, name: 'Chef Park', cuisine_type: 'Korean', rating: 4.9, rating_count: 28, price_per_session: 150000, total_bookings: 8, popularity_score: 137.2 },
                { rank: 5, id: 4, name: 'Chef Dubois', cuisine_type: 'French', rating: 4.7, rating_count: 22, price_per_session: 180000, total_bookings: 6, popularity_score: 103.4 }
            ], updated_at: new Date().toISOString()
        };
    }

    // CooCook Nutrition
    if (path.match(/\/api\/coocook\/nutrition\/\d+$/)) {
        return {
            menu_id: 1, menu_name: 'Traditional Bibimbap Set', servings: 2,
            total_nutrition: { calories: 1245.5, protein: 82.3, carbs: 95.1, fat: 45.8, fiber: 10.2, sodium: 892.0 },
            per_serving: { calories: 622.8, protein: 41.2, carbs: 47.6, fat: 22.9, fiber: 5.1, sodium: 446.0 },
            daily_value_percent: { calories: 31.1, protein: 82.3, carbs: 15.9, fat: 35.2, fiber: 20.4, sodium: 19.4 },
            ingredient_breakdown: [
                { name: 'rice', portion_grams: 150, nutrition: { calories: 195.0, protein: 4.1, carbs: 42.3, fat: 0.5, fiber: 0.6, sodium: 1.5 } },
                { name: 'beef', portion_grams: 150, nutrition: { calories: 375.0, protein: 39.0, carbs: 0.0, fat: 22.5, fiber: 0.0, sodium: 108.0 } }
            ],
            disclaimer: 'Nutritional values are estimates based on standard portions.'
        };
    }
    if (path === '/api/coocook/nutrition/calculate' && options.method === 'POST') {
        return {
            servings: 1,
            total_nutrition: { calories: 295.0, protein: 33.7, carbs: 28.2, fat: 3.9, fiber: 0.4, sodium: 75.0 },
            per_serving: { calories: 295.0, protein: 33.7, carbs: 28.2, fat: 3.9, fiber: 0.4, sodium: 75.0 },
            daily_value_percent: { calories: 14.8, protein: 67.4, carbs: 9.4, fat: 6.0, fiber: 1.6, sodium: 3.3 },
            ingredient_breakdown: [],
            unknown_ingredients: [],
            available_ingredients: ['beef', 'broccoli', 'butter', 'carrot', 'cheese', 'chicken breast', 'egg', 'garlic', 'kimchi', 'mushroom', 'olive oil', 'onion', 'pasta', 'potato', 'rice', 'salmon', 'shrimp', 'soy sauce', 'spinach', 'tofu']
        };
    }

    // CooCook Shopping List
    if (path === '/api/coocook/shopping-list' && options.method === 'POST') {
        return {
            id: 1, message: 'Shopping list created',
            shopping_list: {
                id: 1, user_id: 1, name: 'Shopping for Bibimbap Set', items: [
                    { name: 'rice', quantity: 1, unit: 'pack', checked: false, category: 'grain' },
                    { name: 'beef', quantity: 1, unit: 'pack', checked: false, category: 'protein' },
                    { name: 'egg', quantity: 1, unit: 'pack', checked: false, category: 'protein' },
                    { name: 'spinach', quantity: 1, unit: 'pack', checked: false, category: 'produce' },
                ], created_at: new Date().toISOString(), updated_at: new Date().toISOString()
            }
        };
    }
    if (path === '/api/coocook/shopping-list' && (!options.method || options.method === 'GET')) {
        return {
            shopping_lists: [
                {
                    id: 1, user_id: 1, name: 'Shopping for Bibimbap Set', items: [
                        { name: 'rice', quantity: 1, unit: 'pack', checked: true, category: 'grain' },
                        { name: 'beef', quantity: 1, unit: 'pack', checked: false, category: 'protein' },
                        { name: 'egg', quantity: 6, unit: 'pc', checked: false, category: 'protein' },
                        { name: 'spinach', quantity: 1, unit: 'bunch', checked: true, category: 'produce' }
                    ], created_at: '2026-02-25T10:00:00', updated_at: '2026-02-25T12:00:00'
                },
                {
                    id: 2, user_id: 1, name: 'Shopping for Sushi Omakase', items: [
                        { name: 'salmon', quantity: 300, unit: 'g', checked: false, category: 'protein' },
                        { name: 'rice', quantity: 2, unit: 'pack', checked: false, category: 'grain' },
                        { name: 'soy sauce', quantity: 1, unit: 'bottle', checked: false, category: 'condiment' }
                    ], created_at: '2026-02-26T08:00:00', updated_at: '2026-02-26T08:00:00'
                }
            ],
            total: 2
        };
    }
    if (path.match(/\/api\/coocook\/shopping-list\/\d+$/) && options.method === 'PUT') {
        return { message: 'Shopping list updated', shopping_list: { id: 1, user_id: 1, name: 'Updated List', items: [], created_at: '2026-02-25T10:00:00', updated_at: new Date().toISOString() } };
    }
    if (path.match(/\/api\/coocook\/shopping-list\/\d+$/) && options.method === 'DELETE') {
        return { message: 'Shopping list deleted' };
    }

    // CooCook Feed & Recommendations
    if (path === '/api/coocook/feed') {
        return {
            feed: [
                { type: 'recent_booking', title: 'Your booking with Chef Park', subtitle: 'Korean - 2026-03-01', status: 'confirmed', chef_id: 1, booking_id: 1, timestamp: '2026-02-25T10:00:00' },
                { type: 'popular_chef', title: 'Chef Tanaka - Trending!', subtitle: 'Japanese | 4.9 rating (42 reviews)', chef_id: 3, price_per_session: 200000, timestamp: new Date().toISOString() },
                { type: 'new_menu', title: 'Truffle Pasta Carbonara', subtitle: 'Italian - main', menu_id: 3, chef_id: 2, price: 55000, timestamp: new Date().toISOString() },
                { type: 'new_menu', title: 'Ceviche de Camaron', subtitle: 'Mexican - appetizer', menu_id: 10, chef_id: 5, price: 42000, timestamp: new Date().toISOString() },
                { type: 'popular_chef', title: 'Chef Marco - Trending!', subtitle: 'Italian | 4.8 rating (35 reviews)', chef_id: 2, price_per_session: 180000, timestamp: new Date().toISOString() }
            ], total: 5
        };
    }
    if (path.startsWith('/api/coocook/recommendations')) {
        return {
            chef_recommendations: [
                { type: 'chef', chef: { id: 3, name: 'Chef Tanaka', cuisine_type: 'Japanese', rating: 4.9, rating_count: 42, price_per_session: 200000 }, menus: [{ id: 5, name: 'Premium Sushi Omakase', price: 95000 }], reason: 'Highly rated chef', confidence: 0.94 },
                { type: 'chef', chef: { id: 5, name: 'Chef Garcia', cuisine_type: 'Mexican', rating: 4.8, rating_count: 31, price_per_session: 140000 }, menus: [{ id: 9, name: 'Tacos al Pastor', price: 35000 }], reason: 'Based on your Korean preference', confidence: 0.87 },
                { type: 'chef', chef: { id: 4, name: 'Chef Dubois', cuisine_type: 'French', rating: 4.7, rating_count: 22, price_per_session: 180000 }, menus: [{ id: 7, name: 'Coq au Vin', price: 65000 }], reason: 'Highly rated chef', confidence: 0.82 }
            ],
            menu_recommendations: [
                { type: 'menu', menu: { id: 8, name: 'Beef Bourguignon', cuisine: 'French', price: 72000, category: 'main' }, reason: 'Popular French dish', confidence: 0.88 },
                { type: 'menu', menu: { id: 6, name: 'Tempura Udon Set', cuisine: 'Japanese', price: 38000, category: 'noodle' }, reason: 'Popular Japanese dish', confidence: 0.85 }
            ],
            preferred_cuisines: ['Korean', 'Italian'],
            total_bookings_analyzed: 2
        };
    }

    // CooCook Menus
    if (path.startsWith('/api/coocook/menus')) {
        return {
            menus: [
                { id: 1, chef_id: 1, name: 'Traditional Bibimbap Set', category: 'main', cuisine: 'Korean', price: 45000, description: 'Classic Korean mixed rice bowl', servings: 2, prep_time: 45 },
                { id: 3, chef_id: 2, name: 'Truffle Pasta Carbonara', category: 'main', cuisine: 'Italian', price: 55000, description: 'Creamy carbonara with truffle oil', servings: 2, prep_time: 35 },
                { id: 5, chef_id: 3, name: 'Premium Sushi Omakase', category: 'main', cuisine: 'Japanese', price: 95000, description: '12-piece chef selection', servings: 1, prep_time: 60 },
                { id: 7, chef_id: 4, name: 'Coq au Vin', category: 'main', cuisine: 'French', price: 65000, description: 'Classic French braised chicken', servings: 2, prep_time: 90 },
                { id: 9, chef_id: 5, name: 'Tacos al Pastor', category: 'main', cuisine: 'Mexican', price: 35000, description: 'Authentic marinated pork tacos', servings: 3, prep_time: 40 }
            ], total: 5
        };
    }

    // SNS Auto
    if (path === '/api/sns/accounts') {
        return {
            accounts: [
                { id: 1, platform: 'instagram', account_name: '@demo_user', is_active: true, created_at: '2026-02-20', followers: 2540, engagement_rate: 4.2 },
                { id: 2, platform: 'blog', account_name: 'demo-blog', is_active: true, created_at: '2026-02-21', followers: 850, engagement_rate: 2.8 },
                { id: 3, platform: 'tiktok', account_name: '@demo_tiktok', is_active: false, created_at: '2026-02-22', followers: 0, engagement_rate: 0 }
            ]
        };
    }
    if (path === '/api/sns/analytics') {
        return {
            total_posts: 24,
            total_engagement: 8450,
            average_engagement: 352,
            top_performing: { title: 'Product Launch', views: 2340, likes: 320 },
            platform_breakdown: [
                { platform: 'Instagram', posts: 16, engagement: 5200 },
                { platform: 'Blog', posts: 8, engagement: 3250 }
            ],
            trend_30days: [
                { day: 'Feb 24', posts: 3, engagement: 420 },
                { day: 'Feb 23', posts: 2, engagement: 280 },
                { day: 'Feb 22', posts: 1, engagement: 140 }
            ]
        };
    }
    if (path === '/api/sns/posts' || path.startsWith('/api/sns/posts?')) {
        return {
            posts: [
                { id: 1, account_id: 1, content: 'Hello World!', status: 'published', template_type: 'card_news', scheduled_at: '2026-02-24', created_at: '2026-02-24' }
            ]
        };
    }
    if (path === '/api/sns/templates') {
        return [
            { id: 1, name: 'Card News', type: 'card_news', description: 'Instagram card format' },
            { id: 2, name: 'Blog Post', type: 'blog_post', description: 'Blog article' },
            { id: 3, name: 'Reel', type: 'reel', description: 'Instagram Reel' },
            { id: 4, name: 'Shorts', type: 'shorts', description: 'YouTube Shorts' }
        ];
    }
    if (path.startsWith('/api/sns/accounts') && options.method === 'POST') {
        return { id: 3, platform: 'tiktok', account_name: '@demo_tiktok', is_active: true };
    }
    if (path.startsWith('/api/sns/posts') && options.method === 'POST') {
        return { id: 2, account_id: 1, content: 'New post', status: 'scheduled', template_type: 'card_news' };
    }
    if (path.match(/\/api\/sns\/posts\/\d+\/publish/)) {
        return { id: 1, status: 'published', message: 'Post published successfully!' };
    }

    // Review Campaigns
    if (path.startsWith('/api/review/campaigns') && !path.includes('/')) {
        return {
            campaigns: [
                { id: 1, title: 'Skincare Product Launch', brand: 'GlowSkin Pro', category: 'beauty', platform: 'revu', reward_value: '₩150,000 키트', max_reviewers: 20, current_reviewers: 5, deadline: '2026-03-24', status: 'active', applications: 5, image: '💄', profit_score: 94 },
                { id: 2, title: 'Coffee Brand Review', brand: 'BeanBliss', category: 'food', platform: 'reviewnote', reward_value: '₩50,000 카드', max_reviewers: 15, current_reviewers: 3, deadline: '2026-03-19', status: 'active', applications: 3, image: '☕', profit_score: 82 },
                { id: 3, title: 'Tech Gadget Review', brand: 'SmartHub X3', category: 'tech', platform: 'gangnam', reward_value: '₩75,000 보너스', max_reviewers: 10, current_reviewers: 8, deadline: '2026-03-14', status: 'active', applications: 8, image: '⌚', profit_score: 89 }
            ]
        };
    }
    if (path.match(/\/api\/review\/campaigns\/\d+$/) || path.match(/\/api\/review\/campaign_detail\/\d+$/)) {
        const campaignId = parseInt(path.match(/\/(\d+)$/)[1]);
        const campaigns = {
            1: { id: 1, title: 'Skincare Product Launch', brand: 'GlowSkin Pro', category: 'beauty', platform: 'revu', reward_value: '₩150,000 키트', description: 'Review our new skincare line with active vitamin C. High conversion potential for beauty bloggers.', deadline: '2026-03-24', status: 'active', image_url: 'https://images.unsplash.com/photo-1556228720-195a672e8a03?auto=format&fit=crop&q=80&w=800' },
            2: { id: 2, title: 'Coffee Brand Review', brand: 'BeanBliss', category: 'food', platform: 'reviewnote', reward_value: '₩50,000 카드', description: 'Try our premium arabica coffee beans and write a sensory review.', deadline: '2026-03-19', status: 'active', image_url: 'https://images.unsplash.com/photo-1509042239860-f550ce710b93?auto=format&fit=crop&q=80&w=800' },
            3: { id: 3, title: 'Tech Gadget Review', brand: 'SmartHub X3', category: 'tech', platform: 'gangnam', reward_value: '₩75,000 보너스', description: 'Review our newest smart home hub. High competition, expert tech reviews required.', deadline: '2026-03-14', status: 'active', image_url: 'https://images.unsplash.com/photo-1558346489-19413928158b?auto=format&fit=crop&q=80&w=800' }
        };
        return campaigns[campaignId] || campaigns[1];
    }
    if (path.match(/\/api\/review\/campaigns\/\d+\/apply/)) {
        return { id: 1, status: 'pending', message: 'Application submitted successfully!' };
    }
    if (path === '/api/review/my-applications') {
        return [
            { id: 1, campaign_id: 1, status: 'approved', message: 'Great influencer!' }
        ];
    }

    // AI Automation
    if (path === '/api/ai-automation/plans') {
        return {
            'starter': { name: 'Starter', price: 89000, hours_saved: '15/month', features: ['1 AI Employee', 'Email automation', 'Basic support'] },
            'ambassador': { name: 'Ambassador', price: 189000, hours_saved: '40/month', features: ['3 AI Employees', 'All automations', '24/7 support'] },
            'enterprise': { name: 'Enterprise', price: 490000, hours_saved: '100+/month', features: ['Unlimited AI Employees', 'Custom workflows', 'Dedicated support'] }
        };
    }
    if (path === '/api/ai-automation/scenarios') {
        return [
            { id: 1, name: 'Email Response', category: 'email', complexity: 'easy', estimated_savings: 15, icon: '📧' },
            { id: 2, name: 'Social Media Posting', category: 'social', complexity: 'medium', estimated_savings: 20, icon: '📱' },
            { id: 3, name: 'Customer Support Bot', category: 'customer_service', complexity: 'advanced', estimated_savings: 30, icon: '💬' },
            { id: 4, name: 'Data Entry Automation', category: 'data', complexity: 'medium', estimated_savings: 25, icon: '📊' },
            { id: 5, name: 'Schedule Management', category: 'calendar', complexity: 'easy', estimated_savings: 10, icon: '📅' }
        ];
    }
    if (path === '/api/ai-automation/analytics') {
        return {
            total_hours_saved: 150,
            total_cost_saved: 1500000,
            efficiency_increase: 35,
            trend_data: [
                { month: 'Jan', hours: 30, cost: 300000 },
                { month: 'Feb', hours: 60, cost: 600000 },
                { month: 'Mar', hours: 60, cost: 600000 }
            ]
        };
    }
    if (path === '/api/ai-automation/employees' && options.method !== 'POST') {
        return [
            { id: 1, name: 'Email Bot', scenario: 'Email Response', status: 'active', savings_hours: 15, description: 'Automated email responses' }
        ];
    }
    if (path === '/api/ai-automation/employees' && options.method === 'POST') {
        return { id: 2, name: 'Social Bot', scenario: 'Social Media', status: 'training', message: 'AI employee created and training started' };
    }
    if (path === '/api/ai-automation/dashboard') {
        return { active_employees: 1, total_monthly_savings_hours: 15, estimated_annual_savings: '₩1,800,000' };
    }

    // WebApp Builder
    if (path === '/api/webapp-builder/plans') {
        return {
            'weekday': { name: 'Weekday', schedule: 'Mon-Fri 7-9pm', duration: '8 weeks', price: 590000, seats: 3, available: 3 },
            'weekend': { name: 'Weekend', schedule: 'Sat-Sun 10am-2pm', duration: '8 weeks', price: 590000, seats: 3, available: 3 }
        };
    }
    if (path === '/api/payment/billing-info') {
        return {
            current_plan: 'Multi-Service Bundle',
            monthly_charge: 276000,
            next_billing_date: '2026-03-24',
            services: [
                { name: 'CooCook', price: 39000, next_billing: '2026-03-24' },
                { name: 'SNS Auto', price: 49000, next_billing: '2026-03-24' },
                { name: 'Review Campaign', price: 99000, next_billing: '2026-03-24' },
                { name: 'AI Automation', price: 89000, next_billing: '2026-03-24' }
            ]
        };
    }
    if (path === '/api/payment/history') {
        return [
            { id: 1, date: '2026-02-24', service: 'Multi-Service Bundle', amount: 276000, status: 'paid' },
            { id: 2, date: '2026-01-24', service: 'Multi-Service Bundle', amount: 276000, status: 'paid' },
            { id: 3, date: '2026-01-01', service: 'CooCook + SNS Auto', amount: 88000, status: 'paid' }
        ];
    }
    if (path === '/api/payment/plans') {
        return {
            coocook: {
                starter: { name: 'Starter', price: 39000, features: ['Up to 5 bookings/month', 'Basic profile', 'Standard support'] },
                pro: { name: 'Pro', price: 99000, features: ['Unlimited bookings', 'Premium profile', 'Priority support', 'Analytics'] }
            },
            sns_auto: {
                starter: { name: 'Starter', price: 49000, features: ['1 account', '10 posts/month', 'Basic scheduling'] },
                pro: { name: 'Pro', price: 99000, features: ['5 accounts', 'Unlimited posts', 'Advanced analytics', 'Team access'] }
            },
            review: {
                starter: { name: 'Starter', price: 99000, features: ['1 campaign', 'Up to 20 reviewers', 'Basic reward'] },
                pro: { name: 'Pro', price: 299000, features: ['5 campaigns', 'Unlimited reviewers', 'Custom rewards'] }
            },
            ai_automation: {
                starter: { name: 'Starter', price: 89000, features: ['1 AI employee', 'Email automation', 'Basic support'] },
                pro: { name: 'Pro', price: 189000, features: ['3 AI employees', 'All automations', '24/7 support'] }
            }
        };
    }
    if (path === '/api/payment/subscriptions') {
        return [
            { id: 1, product: 'CooCook', status: 'active', current_period_end: '2026-03-24', price: 39000 },
            { id: 2, product: 'SNS Auto', status: 'active', current_period_end: '2026-03-24', price: 49000 },
            { id: 3, product: 'Review Campaign', status: 'active', current_period_end: '2026-03-24', price: 99000 },
            { id: 4, product: 'AI Automation', status: 'active', current_period_end: '2026-03-24', price: 89000 }
        ];
    }
    if (path === '/api/webapp-builder/courses') {
        return {
            'automation_1': { name: 'Automation 1: Email + Data Entry', duration_weeks: 2, difficulty: 'beginner', description: 'Repeat task automation' },
            'automation_2': { name: 'Automation 2: CRM System', duration_weeks: 2, difficulty: 'intermediate', description: 'Customer data automation' },
            'automation_3': { name: 'Automation 3: Reporting', duration_weeks: 2, difficulty: 'intermediate', description: 'Report generation' },
            'webapp': { name: 'WebApp Building', duration_weeks: 2, difficulty: 'advanced', description: 'Full-stack web development' }
        };
    }
    if (path === '/api/webapp-builder/enrollments') {
        return [
            { id: 1, plan: 'weekday', status: 'in_progress', progress: 25, start: '2026-02-24', end: '2026-04-21', days_remaining: 56 }
        ];
    }
    if (path.startsWith('/api/webapp-builder/enroll')) {
        return { id: 1, status: 'in_progress', message: 'Enrollment successful!' };
    }
    if (path === '/api/webapp-builder/webapps') {
        return [
            { id: 1, name: 'Customer Portal', description: 'CRM system for managing customers', status: 'building', url: null, repo: null, created: '2026-02-24' }
        ];
    }
    if (path.match(/\/api\/webapp-builder\/webapps\/\d+$/) && options.method !== 'POST') {
        return { id: 1, name: 'Customer Portal', description: 'CRM system', status: 'building', url: null, repo: null };
    }
    if (path === '/api/webapp-builder/webapps' && options.method === 'POST') {
        return { id: 2, name: 'New App', description: 'My new application', status: 'draft', message: 'WebApp created successfully!' };
    }
    if (path.match(/\/api\/webapp-builder\/webapps\/\d+\/deploy/)) {
        return { id: 1, status: 'deployed', url: 'https://demo.example.com', message: 'WebApp deployed!' };
    }
    if (path === '/api/webapp-builder/dashboard') {
        return { active_enrollment: { status: 'in_progress', progress: 25 }, webapps_created: 1, webapps_deployed: 0 };
    }

    // Review Aggregated
    if (path.startsWith('/api/review/aggregated')) {
        return {
            success: true,
            data: {
                listings: [
                    { id: 101, title: '프리미엄 스킨케어 세트 체험단', brand: 'GlowSkin', category: 'beauty', reward_value: 150000, source_platform: '레뷰', deadline: new Date(Date.now() + 5 * 86400000).toISOString(), url: '#', image_url: null, applicants: 45 },
                    { id: 102, title: '유기농 커피 원두 체험단', brand: 'BeanBliss', category: 'food', reward_value: 50000, source_platform: '미블', deadline: new Date(Date.now() + 12 * 86400000).toISOString(), url: '#', image_url: null, applicants: 22 },
                    { id: 103, title: '스마트워치 X3 리뷰어 모집', brand: 'SmartHub', category: 'tech', reward_value: 200000, source_platform: '체험단닷컴', deadline: new Date(Date.now() + 3 * 86400000).toISOString(), url: '#', image_url: null, applicants: 78 },
                    { id: 104, title: '여행용 캐리어 체험단', brand: 'TravelPro', category: 'travel', reward_value: 100000, source_platform: '레뷰', deadline: new Date(Date.now() + 8 * 86400000).toISOString(), url: '#', image_url: null, applicants: 33 },
                    { id: 105, title: '프리미엄 요가매트 리뷰', brand: 'FlexFit', category: 'home', reward_value: 75000, source_platform: '미블', deadline: new Date(Date.now() + 15 * 86400000).toISOString(), url: '#', image_url: null, applicants: 18 },
                    { id: 106, title: '수제 초콜릿 세트 체험', brand: 'ChocoLux', category: 'food', reward_value: 60000, source_platform: '체험단닷컴', deadline: new Date(Date.now() + 2 * 86400000).toISOString(), url: '#', image_url: null, applicants: 55 }
                ],
                pages: 3,
                total: 36,
                last_scraped: new Date().toISOString()
            }
        };
    }

    // Review Scraper Status
    if (path === '/api/review/scraper/status') {
        return {
            success: true,
            data: {
                status: 'idle',
                last_run: new Date(Date.now() - 3600000).toISOString(),
                total_scraped: 142,
                sources: ['레뷰', '미블', '체험단닷컴', '인플루언서'],
                next_scheduled: new Date(Date.now() + 3600000).toISOString()
            }
        };
    }

    // SNS AI Generate Content
    if (path === '/api/sns/ai/generate' && options.method === 'POST') {
        const body = JSON.parse(options.body || '{}');
        const topic = body.topic || '일반 포스트';
        const tone = body.tone || 'professional';
        const platform = body.platform || 'instagram';

        const toneMap = {
            professional: '전문적이고 신뢰감 있는',
            casual: '친근하고 편안한',
            humorous: '재미있고 유머러스한',
            inspiring: '영감을 주는'
        };

        return {
            content: `[AI Generated] ${toneMap[tone]} ${topic} 콘텐츠입니다.\n\n오늘은 ${topic}에 대해 이야기해볼까요? 최근 트렌드를 분석해보면, 이 분야에서 가장 중요한 포인트는 바로 진정성과 일관성입니다.\n\n핵심 포인트 3가지:\n1. 타겟 오디언스를 명확히 정의하세요\n2. 가치를 먼저 제공하세요\n3. 꾸준한 소통이 성장의 열쇠입니다`,
            hashtags: '#마케팅 #소셜미디어 #' + topic.replace(/\s/g, '') + ' #트렌드 #비즈니스성장',
            suggestions: [
                '이미지나 영상을 추가하면 참여율이 2-3배 올라갑니다',
                platform + '에서는 ' + (platform === 'instagram' ? '캐러셀 포스트' : '짧은 형식') + '이 효과적입니다',
                '오후 6-8시 발행이 최적입니다'
            ],
            estimated_engagement: { likes: '120-180', comments: '15-25', shares: '8-12' }
        };
    }

    // SNS AI Hashtags
    if (path === '/api/sns/ai/hashtags' && options.method === 'POST') {
        return {
            hashtags: ['#마케팅', '#소셜미디어', '#브랜딩', '#콘텐츠전략', '#디지털마케팅', '#트렌드', '#성장', '#비즈니스'],
            trending: ['#AI활용', '#숏폼콘텐츠', '#바이럴마케팅'],
            platform_specific: ['#인스타그램', '#릴스', '#좋아요']
        };
    }

    // SNS AI Optimize
    if (path === '/api/sns/ai/optimize' && options.method === 'POST') {
        return {
            optimized_content: 'Optimized version of your content...',
            improvements: [
                { type: 'length', suggestion: '글자수를 150자 이내로 줄이면 참여율이 높아집니다' },
                { type: 'hashtags', suggestion: '해시태그를 5-8개로 조절하세요' },
                { type: 'cta', suggestion: '행동 유도 문구를 추가하세요' }
            ],
            score: { before: 65, after: 88 }
        };
    }

    // SNS Link in Bio
    if (path === '/api/sns/linkinbio' && options.method === 'POST') {
        return { success: true, id: 1, slug: 'demo-user', url: 'https://link.softfactory.com/demo-user', message: 'Link in bio saved!' };
    }
    if (path.startsWith('/api/sns/link-in-bio') && !path.includes('/stats')) {
        return {
            success: true,
            data: {
                id: 1, title: 'My Links', description: 'Check out my content', theme: 'pink', slug: 'demo-user',
                url: 'https://link.softfactory.com/demo-user',
                links: [
                    { title: 'My Blog', url: 'https://blog.example.com', clicks: 342 },
                    { title: 'YouTube Channel', url: 'https://youtube.com/@demo', clicks: 567 },
                    { title: 'Online Store', url: 'https://store.example.com', clicks: 189 }
                ],
                total_clicks: 1098,
                total_views: 4521
            }
        };
    }
    if (path.includes('/stats')) {
        return {
            success: true,
            data: {
                total_clicks: 1098, total_views: 4521,
                daily_clicks: [45, 52, 38, 61, 73, 55, 48],
                top_links: [
                    { title: 'YouTube Channel', clicks: 567 },
                    { title: 'My Blog', clicks: 342 },
                    { title: 'Online Store', clicks: 189 }
                ],
                referrers: ['instagram.com', 'twitter.com', 'direct'],
                devices: { mobile: 72, desktop: 23, tablet: 5 }
            }
        };
    }

    // Dashboard KPIs endpoint
    if (path === '/api/dashboard/kpis') {
        return {
            success: true,
            data: {
                mrr: 2400000,
                active_users: 8342,
                growth_rate: 23.5,
                roi: 342,
                churn_rate: 2.3,
                ltv: 2800000
            }
        };
    }

    // Dashboard Charts endpoint
    if (path === '/api/dashboard/charts') {
        return {
            success: true,
            data: {
                revenue_trends: [1200000, 1420000, 1650000, 1890000, 2100000, 2400000],
                service_distribution: [
                    { name: 'CooCook', users: 2450, revenue: 98000 },
                    { name: 'SNS Auto', users: 1850, revenue: 90500 },
                    { name: 'Review', users: 2042, revenue: 202000 },
                    { name: 'AI Auto', users: 1600, revenue: 142400 },
                    { name: 'WebApp', users: 1400, revenue: 826000 }
                ]
            }
        };
    }

    // Default
    return { success: true, data: [] };
}

function getUser() {
    const user = localStorage.getItem('user');
    return user ? JSON.parse(user) : null;
}

function getToken() {
    return localStorage.getItem('access_token');
}

function requireAuth() {
    if (!getToken() && !isDemoMode()) {
        window.location.href = '/web/platform/login.html';
    }
}

function logout() {
    if (isDemoMode()) {
        disableDemoMode();
    } else {
        localStorage.clear();
    }
    window.location.href = '/web/platform/login.html';
}

// ============ UI HELPERS ============

/**
 * Format amount as Korean Won (₩)
 * @param {number} amount - Amount to format
 * @returns {string} Formatted string like "₩99,000"
 */
function formatKRW(amount) {
    if (amount >= 1000000) {
        return '₩' + (amount / 1000000).toFixed(1) + 'M';
    }
    return '₩' + amount.toLocaleString('ko-KR');
}

/**
 * Format date for display
 * @param {string|Date} date - ISO date or Date object
 * @param {string} format - 'short' (Feb 24), 'long' (February 24, 2026), 'relative' (2 days ago)
 * @returns {string} Formatted date
 */
function formatDate(date, format = 'short') {
    const d = typeof date === 'string' ? new Date(date) : date;
    const options = {
        short: { month: 'short', day: 'numeric' },
        long: { year: 'numeric', month: 'long', day: 'numeric' },
        relative: {}
    };

    if (format === 'relative') {
        const now = new Date();
        const diff = Math.floor((now - d) / 1000);
        if (diff < 60) return 'Just now';
        if (diff < 3600) return Math.floor(diff / 60) + ' minutes ago';
        if (diff < 86400) return Math.floor(diff / 3600) + ' hours ago';
        if (diff < 604800) return Math.floor(diff / 86400) + ' days ago';
        if (diff < 2592000) return Math.floor(diff / 604800) + ' weeks ago';
        return Math.floor(diff / 2592000) + ' months ago';
    }

    return d.toLocaleDateString('en-US', options[format] || options.short);
}

/**
 * Get status badge HTML
 * @param {string} status - Status key (e.g., 'active', 'pending', 'completed', 'draft')
 * @returns {string} HTML badge
 */
function statusBadge(status) {
    const badges = {
        active: '<span class="inline-flex items-center px-2 py-1 text-xs font-medium rounded-full bg-green-900 text-green-200">🟢 Active</span>',
        pending: '<span class="inline-flex items-center px-2 py-1 text-xs font-medium rounded-full bg-yellow-900 text-yellow-200">⏳ Pending</span>',
        completed: '<span class="inline-flex items-center px-2 py-1 text-xs font-medium rounded-full bg-blue-900 text-blue-200">✅ Completed</span>',
        approved: '<span class="inline-flex items-center px-2 py-1 text-xs font-medium rounded-full bg-green-900 text-green-200">✅ Approved</span>',
        rejected: '<span class="inline-flex items-center px-2 py-1 text-xs font-medium rounded-full bg-red-900 text-red-200">❌ Rejected</span>',
        draft: '<span class="inline-flex items-center px-2 py-1 text-xs font-medium rounded-full bg-slate-700 text-slate-200">📝 Draft</span>',
        published: '<span class="inline-flex items-center px-2 py-1 text-xs font-medium rounded-full bg-indigo-900 text-indigo-200">📤 Published</span>',
        scheduled: '<span class="inline-flex items-center px-2 py-1 text-xs font-medium rounded-full bg-purple-900 text-purple-200">📅 Scheduled</span>',
        training: '<span class="inline-flex items-center px-2 py-1 text-xs font-medium rounded-full bg-cyan-900 text-cyan-200">🔧 Training</span>',
        deployed: '<span class="inline-flex items-center px-2 py-1 text-xs font-medium rounded-full bg-emerald-900 text-emerald-200">🚀 Deployed</span>',
        building: '<span class="inline-flex items-center px-2 py-1 text-xs font-medium rounded-full bg-orange-900 text-orange-200">🏗️ Building</span>',
        in_progress: '<span class="inline-flex items-center px-2 py-1 text-xs font-medium rounded-full bg-blue-900 text-blue-200">▶️ In Progress</span>'
    };
    return badges[status] || `<span class="inline-flex items-center px-2 py-1 text-xs font-medium rounded-full bg-slate-700 text-slate-200">${status}</span>`;
}

/**
 * Generate skeleton loading card
 * @returns {string} HTML skeleton
 */
function skeletonCard() {
    return `<div class="bg-slate-800 rounded-lg p-6 animate-pulse">
        <div class="h-4 bg-slate-700 rounded mb-4 w-3/4"></div>
        <div class="space-y-3">
            <div class="h-3 bg-slate-700 rounded"></div>
            <div class="h-3 bg-slate-700 rounded w-5/6"></div>
        </div>
    </div>`;
}

/**
 * Generate empty state HTML
 * @param {string} icon - Emoji icon
 * @param {string} title - Title text
 * @param {string} desc - Description text
 * @param {string} actionLabel - CTA button label (optional)
 * @param {string} actionHref - CTA link (optional)
 * @returns {string} HTML empty state
 */
function emptyState(icon, title, desc, actionLabel = null, actionHref = null) {
    const action = actionLabel && actionHref
        ? `<a href="${actionHref}" class="inline-block mt-4 px-6 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-medium transition">${actionLabel}</a>`
        : '';
    return `<div class="text-center py-12">
        <div class="text-6xl mb-4">${icon}</div>
        <h3 class="text-xl font-semibold text-slate-100 mb-2">${title}</h3>
        <p class="text-slate-400 mb-6">${desc}</p>
        ${action}
    </div>`;
}

/**
 * Get Chart.js dark theme defaults
 * @returns {object} Chart.js options
 */
function getChartDefaults() {
    return {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                labels: { color: '#cbd5e1', font: { family: "'Inter', sans-serif" } }
            },
            tooltip: {
                backgroundColor: '#1e293b',
                borderColor: '#475569',
                titleColor: '#f1f5f9',
                bodyColor: '#cbd5e1',
                padding: 12
            }
        },
        scales: {
            x: {
                ticks: { color: '#94a3b8' },
                grid: { color: '#334155' }
            },
            y: {
                ticks: { color: '#94a3b8' },
                grid: { color: '#334155' }
            }
        }
    };
}

/**
 * Show confirm modal (returns Promise)
 * @param {string} message - Confirmation message
 * @returns {Promise<boolean>} User's choice
 */
function confirmModal(message) {
    return new Promise(resolve => {
        const modal = document.createElement('div');
        modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
        modal.innerHTML = `<div class="bg-slate-800 border border-slate-700 rounded-lg p-6 max-w-sm">
            <p class="text-slate-100 mb-6">${message}</p>
            <div class="flex gap-3">
                <button class="flex-1 px-4 py-2 bg-slate-700 hover:bg-slate-600 text-slate-100 rounded-lg transition" onclick="this.closest('.fixed').remove(); window.confirmResult = false;">Cancel</button>
                <button class="flex-1 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg transition" onclick="this.closest('.fixed').remove(); window.confirmResult = true;">Confirm</button>
            </div>
        </div>`;
        document.body.appendChild(modal);

        // Simple polling approach
        const checkInterval = setInterval(() => {
            if (window.confirmResult !== undefined) {
                clearInterval(checkInterval);
                const result = window.confirmResult;
                delete window.confirmResult;
                resolve(result);
            }
        }, 100);
    });
}

/** Toast notification container and stacking system */
let _sfToastContainer = null;
const _sfMaxToasts = 5;

function _sfGetToastContainer() {
    if (!_sfToastContainer || !document.body.contains(_sfToastContainer)) {
        _sfToastContainer = document.createElement('div');
        _sfToastContainer.id = 'sf-toast-container';
        _sfToastContainer.style.cssText = 'position:fixed;bottom:16px;right:16px;z-index:9998;display:flex;flex-direction:column-reverse;gap:8px;max-width:400px;pointer-events:none;';
        document.body.appendChild(_sfToastContainer);

        // Inject toast animation styles once
        if (!document.getElementById('sf-toast-styles')) {
            const style = document.createElement('style');
            style.id = 'sf-toast-styles';
            style.textContent = `
                @keyframes sf-toast-in{from{opacity:0;transform:translateX(100%) scale(0.95)}to{opacity:1;transform:translateX(0) scale(1)}}
                @keyframes sf-toast-out{from{opacity:1;transform:translateX(0) scale(1);max-height:100px}to{opacity:0;transform:translateX(100%) scale(0.95);max-height:0;margin:0;padding:0}}
                .sf-toast{animation:sf-toast-in 0.35s cubic-bezier(0.16,1,0.3,1) forwards;pointer-events:auto;}
                .sf-toast.sf-toast-exit{animation:sf-toast-out 0.3s ease forwards;}
                .sf-toast-progress{position:absolute;bottom:0;left:0;height:3px;border-radius:0 0 8px 8px;transition:width linear;}
            `;
            document.head.appendChild(style);
        }
    }
    return _sfToastContainer;
}

/**
 * Show a toast notification with icon, message, type, and auto-dismiss progress bar
 * @param {string} message - Toast message
 * @param {string} type - 'success' | 'error' | 'warning' | 'info'
 * @param {number} duration - Duration in ms (default: 4000)
 */
function showToast(message, type = 'success', duration = 4000) {
    const container = _sfGetToastContainer();

    const icons = { success: '&#x2705;', error: '&#x274C;', warning: '&#x26A0;', info: '&#x2139;' };
    const bgColors = {
        success: 'background:linear-gradient(135deg,#059669,#047857);border-color:#10b981;',
        error: 'background:linear-gradient(135deg,#dc2626,#b91c1c);border-color:#ef4444;',
        warning: 'background:linear-gradient(135deg,#d97706,#b45309);border-color:#f59e0b;',
        info: 'background:linear-gradient(135deg,#2563eb,#1d4ed8);border-color:#3b82f6;'
    };
    const progressColors = { success: '#34d399', error: '#fca5a5', warning: '#fcd34d', info: '#93c5fd' };

    // Limit toast count
    const existing = container.querySelectorAll('.sf-toast:not(.sf-toast-exit)');
    if (existing.length >= _sfMaxToasts) {
        _sfDismissToast(existing[existing.length - 1]);
    }

    const toast = document.createElement('div');
    toast.className = 'sf-toast';
    toast.style.cssText = `${bgColors[type] || bgColors.success}position:relative;padding:12px 40px 12px 16px;border-radius:8px;border:1px solid;color:#fff;display:flex;align-items:center;gap:10px;font-size:13px;font-weight:500;box-shadow:0 8px 24px rgba(0,0,0,0.3);overflow:hidden;`;
    toast.innerHTML = `
        <span style="font-size:16px;flex-shrink:0;">${icons[type] || icons.success}</span>
        <span style="flex:1;line-height:1.4;">${message}</span>
        <button style="position:absolute;top:8px;right:10px;background:none;border:none;color:rgba(255,255,255,0.7);font-size:18px;cursor:pointer;line-height:1;padding:0;" aria-label="Close">&times;</button>
        <div class="sf-toast-progress" style="background:${progressColors[type] || progressColors.success};width:100%;"></div>
    `;

    const closeBtn = toast.querySelector('button');
    closeBtn.onclick = () => _sfDismissToast(toast);

    container.appendChild(toast);

    // Animate progress bar
    const progressBar = toast.querySelector('.sf-toast-progress');
    progressBar.style.transitionDuration = duration + 'ms';
    requestAnimationFrame(() => {
        requestAnimationFrame(() => {
            progressBar.style.width = '0%';
        });
    });

    // Auto dismiss
    const timer = setTimeout(() => _sfDismissToast(toast), duration);
    toast._sfTimer = timer;

    // Pause on hover
    toast.addEventListener('mouseenter', () => {
        clearTimeout(toast._sfTimer);
        progressBar.style.transitionDuration = '0ms';
        progressBar.style.width = progressBar.getBoundingClientRect().width / toast.getBoundingClientRect().width * 100 + '%';
    });
    toast.addEventListener('mouseleave', () => {
        const remaining = parseFloat(progressBar.style.width) / 100 * duration;
        progressBar.style.transitionDuration = remaining + 'ms';
        requestAnimationFrame(() => { progressBar.style.width = '0%'; });
        toast._sfTimer = setTimeout(() => _sfDismissToast(toast), remaining);
    });
}

function _sfDismissToast(toast) {
    if (!toast || toast.classList.contains('sf-toast-exit')) return;
    clearTimeout(toast._sfTimer);
    toast.classList.add('sf-toast-exit');
    setTimeout(() => toast.remove(), 300);
}

function showError(message) {
    showToast(message, 'error');
}

function showSuccess(message) {
    showToast(message, 'success');
}

function showWarning(message) {
    showToast(message, 'warning');
}

function showInfo(message) {
    showToast(message, 'info');
}

/**
 * Validate email format
 */
function isValidEmail(email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

/**
 * Validate password strength
 */
function validatePassword(password) {
    return password && password.length >= 6;
}

/**
 * Global error handler for API calls
 */
window.addEventListener('error', (event) => {
    if (event.error && event.error.message) {
        showError('오류 발생: ' + event.error.message);
    }
});

// ============ API CALLS ============

// Auth
async function register(email, password, name) {
    const response = await apiFetch('/api/auth/register', {
        method: 'POST',
        body: JSON.stringify({ email, password, name })
    });
    return response.json();
}

async function login(email, password) {
    const response = await apiFetch('/api/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password })
    });
    return response.json();
}

async function getMe() {
    const response = await apiFetch('/api/auth/me');
    return response.json();
}

// Platform
async function getProducts() {
    const response = await apiFetch('/api/platform/products');
    return response.json();
}

async function getDashboard() {
    const response = await apiFetch('/api/platform/dashboard');
    return response.json();
}

async function getAdminUsers(page = 1) {
    const response = await apiFetch(`/api/platform/admin/users?page=${page}`);
    return response.json();
}

async function getAdminRevenue() {
    const response = await apiFetch('/api/platform/admin/revenue');
    return response.json();
}

// Payment
async function getPlans() {
    const response = await apiFetch('/api/payment/plans');
    return response.json();
}

async function createCheckout(productId, planType = 'monthly') {
    const response = await apiFetch('/api/payment/checkout', {
        method: 'POST',
        body: JSON.stringify({ product_id: productId, plan_type: planType })
    });
    return response.json();
}

async function getSubscriptions() {
    const response = await apiFetch('/api/payment/subscriptions');
    return response.json();
}

async function cancelSubscription(subscriptionId) {
    const response = await apiFetch(`/api/payment/subscriptions/${subscriptionId}`, {
        method: 'DELETE'
    });
    return response.json();
}

// CooCook
async function getChefs(page = 1, cuisine = '', location = '') {
    let query = `?page=${page}`;
    if (cuisine) query += `&cuisine=${cuisine}`;
    if (location) query += `&location=${location}`;
    const response = await apiFetch(`/api/coocook/chefs${query}`);
    return response.json();
}

async function getChefDetail(chefId) {
    const response = await apiFetch(`/api/coocook/chefs/${chefId}`);
    return response.json();
}

async function createBooking(chefId, bookingDate, durationHours, specialRequests = '') {
    const response = await apiFetch('/api/coocook/bookings', {
        method: 'POST',
        body: JSON.stringify({
            chef_id: chefId,
            booking_date: bookingDate,
            duration_hours: durationHours,
            special_requests: specialRequests
        })
    });
    return response.json();
}

async function getMyBookings() {
    const response = await apiFetch('/api/coocook/bookings');
    return response.json();
}

// CooCook Phase 2-3: Search, Nutrition, Shopping List, Feed, Recommendations

async function searchCooCook(q = '', category = '', cuisine = '', priceMin = null, priceMax = null, ratingMin = null, page = 1) {
    let query = `?page=${page}`;
    if (q) query += `&q=${encodeURIComponent(q)}`;
    if (category) query += `&category=${encodeURIComponent(category)}`;
    if (cuisine) query += `&cuisine=${encodeURIComponent(cuisine)}`;
    if (priceMin !== null) query += `&price_min=${priceMin}`;
    if (priceMax !== null) query += `&price_max=${priceMax}`;
    if (ratingMin !== null) query += `&rating_min=${ratingMin}`;
    const response = await apiFetch(`/api/coocook/search${query}`);
    return response.json();
}

async function getCooCookCategories() {
    const response = await apiFetch('/api/coocook/categories');
    return response.json();
}

async function getCooCookCuisines() {
    const response = await apiFetch('/api/coocook/cuisines');
    return response.json();
}

async function getPopularChefs(limit = 10) {
    const response = await apiFetch(`/api/coocook/popular?limit=${limit}`);
    return response.json();
}

async function getMenuNutrition(menuId) {
    const response = await apiFetch(`/api/coocook/nutrition/${menuId}`);
    return response.json();
}

async function calculateNutrition(ingredients, servings = 1) {
    const response = await apiFetch('/api/coocook/nutrition/calculate', {
        method: 'POST',
        body: JSON.stringify({ ingredients, servings })
    });
    return response.json();
}

async function createShoppingList(name, menuId = null, items = []) {
    const body = { name };
    if (menuId) body.menu_id = menuId;
    if (items.length > 0) body.items = items;
    const response = await apiFetch('/api/coocook/shopping-list', {
        method: 'POST',
        body: JSON.stringify(body)
    });
    return response.json();
}

async function getShoppingLists() {
    const response = await apiFetch('/api/coocook/shopping-list');
    return response.json();
}

async function updateShoppingList(listId, data) {
    const response = await apiFetch(`/api/coocook/shopping-list/${listId}`, {
        method: 'PUT',
        body: JSON.stringify(data)
    });
    return response.json();
}

async function deleteShoppingList(listId) {
    const response = await apiFetch(`/api/coocook/shopping-list/${listId}`, {
        method: 'DELETE'
    });
    return response.json();
}

async function getCooCookFeed() {
    const response = await apiFetch('/api/coocook/feed');
    return response.json();
}

async function getCooCookRecommendations(limit = 6) {
    const response = await apiFetch(`/api/coocook/recommendations?limit=${limit}`);
    return response.json();
}

async function getCooCookMenus(chefId = null, category = '', cuisine = '') {
    let query = '?';
    if (chefId) query += `chef_id=${chefId}&`;
    if (category) query += `category=${encodeURIComponent(category)}&`;
    if (cuisine) query += `cuisine=${encodeURIComponent(cuisine)}&`;
    const response = await apiFetch(`/api/coocook/menus${query}`);
    return response.json();
}

// SNS Auto
async function getSNSAccounts() {
    const response = await apiFetch('/api/sns/accounts');
    return response.json();
}

async function createSNSAccount(platform, accountName) {
    const response = await apiFetch('/api/sns/accounts', {
        method: 'POST',
        body: JSON.stringify({ platform, account_name: accountName })
    });
    return response.json();
}

async function deleteSNSAccount(accountId) {
    const response = await apiFetch(`/api/sns/accounts/${accountId}`, {
        method: 'DELETE'
    });
    return response.json();
}

async function getSNSPosts(accountId = null, status = null, page = 1) {
    let query = `?page=${page}`;
    if (accountId) query += `&account_id=${accountId}`;
    if (status) query += `&status=${status}`;
    const response = await apiFetch(`/api/sns/posts${query}`);
    return response.json();
}

async function createSNSPost(accountId, content, templateType) {
    const response = await apiFetch('/api/sns/posts', {
        method: 'POST',
        body: JSON.stringify({
            account_id: accountId,
            content,
            template_type: templateType
        })
    });
    return response.json();
}

async function publishSNSPost(postId, scheduledAt = null) {
    const response = await apiFetch(`/api/sns/posts/${postId}/publish`, {
        method: 'POST',
        body: JSON.stringify({ scheduled_at: scheduledAt })
    });
    return response.json();
}

async function getSNSTemplates() {
    const response = await apiFetch('/api/sns/templates');
    return response.json();
}

// Review
async function getCampaigns(page = 1, category = '') {
    let query = `?page=${page}`;
    if (category) query += `&category=${category}`;
    const response = await apiFetch(`/api/review/campaigns${query}`);
    return response.json();
}

async function getCampaignDetail(campaignId) {
    const response = await apiFetch(`/api/review/campaigns/${campaignId}`);
    return response.json();
}

async function applyCampaign(campaignId, message, snsLink = '', followerCount = 0) {
    const response = await apiFetch(`/api/review/campaigns/${campaignId}/apply`, {
        method: 'POST',
        body: JSON.stringify({
            message,
            sns_link: snsLink,
            follower_count: followerCount
        })
    });
    return response.json();
}

async function getMyApplications() {
    const response = await apiFetch('/api/review/my-applications');
    return response.json();
}

// AI Automation
async function getAIPlans() {
    const response = await apiFetch('/api/ai-automation/plans');
    return response.json();
}

async function getAIScenarios(category = '') {
    let query = '';
    if (category) query = `?category=${category}`;
    const response = await apiFetch(`/api/ai-automation/scenarios${query}`);
    return response.json();
}

async function getAIEmployees() {
    const response = await apiFetch('/api/ai-automation/employees');
    return response.json();
}

async function createAIEmployee(name, scenario, instructions) {
    const response = await apiFetch('/api/ai-automation/employees', {
        method: 'POST',
        body: JSON.stringify({ name, scenario, instructions })
    });
    return response.json();
}

async function getAIEmployeeDetail(employeeId) {
    const response = await apiFetch(`/api/ai-automation/employees/${employeeId}`);
    return response.json();
}

async function deleteAIEmployee(employeeId) {
    const response = await apiFetch(`/api/ai-automation/employees/${employeeId}`, {
        method: 'DELETE'
    });
    return response.json();
}

async function getAIAutomationDashboard() {
    const response = await apiFetch('/api/ai-automation/dashboard');
    return response.json();
}

async function getAIAnalytics() {
    const response = await apiFetch('/api/ai-automation/analytics');
    return response.json();
}

// WebApp Builder
async function getWebAppPlans() {
    const response = await apiFetch('/api/webapp-builder/plans');
    return response.json();
}

async function getWebAppCourses() {
    const response = await apiFetch('/api/webapp-builder/courses');
    return response.json();
}

async function getWebAppEnrollments() {
    const response = await apiFetch('/api/webapp-builder/enrollments');
    return response.json();
}

async function enrollWebApp(planSlug) {
    const response = await apiFetch('/api/webapp-builder/enroll', {
        method: 'POST',
        body: JSON.stringify({ plan_slug: planSlug })
    });
    return response.json();
}

async function getWebApps() {
    const response = await apiFetch('/api/webapp-builder/webapps');
    return response.json();
}

async function getWebAppDetail(appId) {
    const response = await apiFetch(`/api/webapp-builder/webapps/${appId}`);
    return response.json();
}

async function createWebApp(name, description, templateId) {
    const response = await apiFetch('/api/webapp-builder/webapps', {
        method: 'POST',
        body: JSON.stringify({ name, description, template_id: templateId })
    });
    return response.json();
}

async function deployWebApp(appId) {
    const response = await apiFetch(`/api/webapp-builder/webapps/${appId}/deploy`, {
        method: 'POST'
    });
    return response.json();
}

async function getWebAppDashboard() {
    const response = await apiFetch('/api/webapp-builder/dashboard');
    return response.json();
}

// ============ REVIEW AGGREGATOR ============

async function getReviewAggregated(filters = {}) {
    const params = new URLSearchParams(filters);
    const response = await apiFetch(`/api/review/aggregated?${params}`, {
        method: 'GET'
    });
    return response.json();
}

async function triggerReviewScrape() {
    const response = await apiFetch('/api/review/scrape/now', {
        method: 'POST'
    });
    return response.json();
}

async function addReviewBookmark(listingId) {
    const response = await apiFetch(`/api/review/listings/${listingId}/bookmark`, {
        method: 'POST'
    });
    return response.json();
}

async function getReviewAccounts() {
    const response = await apiFetch('/api/review/accounts', {
        method: 'GET'
    });
    return response.json();
}

async function createReviewAccount(accountData) {
    const response = await apiFetch('/api/review/accounts', {
        method: 'POST',
        body: JSON.stringify(accountData)
    });
    return response.json();
}

async function getReviewApplications() {
    const response = await apiFetch('/api/review/applications', {
        method: 'GET'
    });
    return response.json();
}

async function getReviewAutoApplyRules() {
    const response = await apiFetch('/api/review/auto-apply/rules', {
        method: 'GET'
    });
    return response.json();
}

async function createReviewAutoApplyRule(ruleData) {
    const response = await apiFetch('/api/review/auto-apply/rules', {
        method: 'POST',
        body: JSON.stringify(ruleData)
    });
    return response.json();
}

// ============ OAUTH & SOCIAL LOGIN ============

// ============ SOCIAL LOGIN (OAuth) ============

/**
 * Get authorization URL for Google OAuth
 * @returns {Promise<string>} Google OAuth authorization URL
 * @throws {Error} If API call fails
 */
async function loginWithGoogle() {
    try {
        const response = await apiFetch('/api/auth/oauth/google/url', {
            method: 'GET'
        });
        if (!response.ok) throw new Error('Failed to get Google OAuth URL');
        const data = await response.json();
        return data.auth_url;
    } catch (error) {
        showError('Google login failed: ' + error.message);
        throw error;
    }
}

/**
 * Get authorization URL for Facebook OAuth
 * @returns {Promise<string>} Facebook OAuth authorization URL
 * @throws {Error} If API call fails
 */
async function loginWithFacebook() {
    try {
        const response = await apiFetch('/api/auth/oauth/facebook/url', {
            method: 'GET'
        });
        if (!response.ok) throw new Error('Failed to get Facebook OAuth URL');
        const data = await response.json();
        return data.auth_url;
    } catch (error) {
        showError('Facebook login failed: ' + error.message);
        throw error;
    }
}

/**
 * Get authorization URL for Kakao OAuth
 * @returns {Promise<string>} Kakao OAuth authorization URL
 * @throws {Error} If API call fails
 */
async function loginWithKakao() {
    try {
        const response = await apiFetch('/api/auth/oauth/kakao/url', {
            method: 'GET'
        });
        if (!response.ok) throw new Error('Failed to get Kakao OAuth URL');
        const data = await response.json();
        return data.auth_url;
    } catch (error) {
        showError('Kakao login failed: ' + error.message);
        throw error;
    }
}

/**
 * Get OAuth authorization URL for any provider
 * @param {string} provider - Provider name (google, facebook, kakao, etc.)
 * @returns {Promise<string>} OAuth authorization URL
 * @throws {Error} If provider is unsupported or API call fails
 */
async function getOAuthUrl(provider) {
    const validProviders = ['google', 'facebook', 'kakao'];
    if (!validProviders.includes(provider)) {
        throw new Error(`Unsupported OAuth provider: ${provider}`);
    }

    try {
        const response = await apiFetch(`/api/auth/oauth/${provider}/url`, {
            method: 'GET'
        });
        if (!response.ok) throw new Error(`Failed to get ${provider} OAuth URL`);
        const data = await response.json();
        return data.auth_url;
    } catch (error) {
        showError(`${provider} OAuth failed: ${error.message}`);
        throw error;
    }
}

/**
 * Helper to handle OAuth callback for any provider
 * @param {string} provider - Provider name (google, facebook, kakao)
 * @param {string} code - Authorization code from provider
 * @param {string} state - State parameter for CSRF protection
 * @returns {Promise<Object>} User data and tokens {access_token, refresh_token, user}
 * @throws {Error} If callback handling fails
 */
async function handleOAuthCallback(provider, code, state) {
    const validProviders = ['google', 'facebook', 'kakao'];
    if (!validProviders.includes(provider)) {
        throw new Error(`Unsupported OAuth provider: ${provider}`);
    }

    try {
        const response = await apiFetch(`/api/auth/oauth/${provider}/callback`, {
            method: 'POST',
            body: JSON.stringify({ code, state })
        });
        if (!response.ok) throw new Error(`OAuth callback failed for ${provider}`);

        const data = await response.json();
        if (data.access_token) {
            localStorage.setItem('access_token', data.access_token);
            localStorage.setItem('refresh_token', data.refresh_token || data.access_token);
            localStorage.setItem('user', JSON.stringify(data.user));
            showSuccess(`Successfully logged in with ${provider}`);
        }
        return data;
    } catch (error) {
        showError(`${provider} callback error: ${error.message}`);
        throw error;
    }
}

/**
 * Handle Google OAuth callback
 * @param {string} code - Authorization code from Google
 * @param {string} state - State parameter for CSRF protection
 * @returns {Promise<Object>} User data and tokens
 */
async function handleGoogleCallback(code, state) {
    return handleOAuthCallback('google', code, state);
}

/**
 * Handle Facebook OAuth callback
 * @param {string} code - Authorization code from Facebook
 * @param {string} state - State parameter for CSRF protection
 * @returns {Promise<Object>} User data and tokens
 */
async function handleFacebookCallback(code, state) {
    return handleOAuthCallback('facebook', code, state);
}

/**
 * Handle Kakao OAuth callback
 * @param {string} code - Authorization code from Kakao
 * @param {string} state - State parameter for CSRF protection
 * @returns {Promise<Object>} User data and tokens
 */
async function handleKakaoCallback(code, state) {
    return handleOAuthCallback('kakao', code, state);
}

/**
 * Get Google OAuth authorization URL
 * @returns {Promise<string>} Google OAuth authorization URL
 * @throws {Error} If API call fails
 */
async function getGoogleAuthUrl() {
    return getOAuthUrl('google');
}

/**
 * Get Facebook OAuth authorization URL
 * @returns {Promise<string>} Facebook OAuth authorization URL
 * @throws {Error} If API call fails
 */
async function getFacebookAuthUrl() {
    return getOAuthUrl('facebook');
}

/**
 * Get Kakao OAuth authorization URL
 * @returns {Promise<string>} Kakao OAuth authorization URL
 * @throws {Error} If API call fails
 */
async function getKakaoAuthUrl() {
    return getOAuthUrl('kakao');
}

// ============ SNS AUTOMATION API ============

/**
 * Create or update a Link in Bio (Linktree-style)
 * @param {Object} data - Link in bio configuration
 * @param {string} data.title - Title of the link
 * @param {string} data.url - Target URL
 * @param {string} data.description - Optional description
 * @param {string} data.platform - SNS platform (instagram, tiktok, etc.)
 * @returns {Promise<Object>} Created link in bio object
 */
async function createLinkInBio(data) {
    try {
        const response = await apiFetch('/api/sns/link-in-bio', {
            method: 'POST',
            body: JSON.stringify(data)
        });
        if (!response.ok) throw new Error('Failed to create link in bio');
        const result = await response.json();
        showSuccess('Link in bio created successfully');
        return result;
    } catch (error) {
        showError('Link in bio creation failed: ' + error.message);
        throw error;
    }
}

/**
 * Update an existing Link in Bio
 * @param {number} id - Link in bio ID
 * @param {Object} data - Updated link data
 * @returns {Promise<Object>} Updated link in bio object
 */
async function updateLinkInBio(id, data) {
    try {
        const response = await apiFetch(`/api/sns/link-in-bio/${id}`, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
        if (!response.ok) throw new Error('Failed to update link in bio');
        const result = await response.json();
        showSuccess('Link in bio updated successfully');
        return result;
    } catch (error) {
        showError('Link in bio update failed: ' + error.message);
        throw error;
    }
}

/**
 * Get Link in Bio by ID
 * @param {number} id - Link in bio ID
 * @returns {Promise<Object>} Link in bio object with analytics
 */
async function getLinkInBio(id) {
    try {
        const response = await apiFetch(`/api/sns/link-in-bio/${id}`);
        if (!response.ok) throw new Error('Failed to fetch link in bio');
        return await response.json();
    } catch (error) {
        showError('Failed to load link in bio: ' + error.message);
        throw error;
    }
}

/**
 * Get analytics for a Link in Bio
 * @param {number} id - Link in bio ID
 * @param {string} startDate - Start date (ISO format)
 * @param {string} endDate - End date (ISO format)
 * @returns {Promise<Object>} Analytics data {clicks, impressions, ctr, etc.}
 */
async function getLinkInBioStats(id, startDate = null, endDate = null) {
    try {
        let query = '';
        if (startDate && endDate) {
            query = `?start_date=${startDate}&end_date=${endDate}`;
        }
        const response = await apiFetch(`/api/sns/link-in-bio/${id}/stats${query}`);
        if (!response.ok) throw new Error('Failed to fetch link in bio stats');
        return await response.json();
    } catch (error) {
        showError('Failed to load link in bio stats: ' + error.message);
        throw error;
    }
}

/**
 * Create SNS automation workflow
 * @param {Object} data - Automation configuration
 * @param {string} data.name - Workflow name
 * @param {string} data.trigger - Trigger type (schedule, event, keyword)
 * @param {string} data.action - Action to perform
 * @param {Object} data.config - Workflow configuration
 * @returns {Promise<Object>} Created automation object
 */
async function createAutomate(data) {
    try {
        const response = await apiFetch('/api/sns/automate', {
            method: 'POST',
            body: JSON.stringify(data)
        });
        if (!response.ok) throw new Error('Failed to create automation');
        const result = await response.json();
        showSuccess('Automation created successfully');
        return result;
    } catch (error) {
        showError('Automation creation failed: ' + error.message);
        throw error;
    }
}

/**
 * Get all automations for current user
 * @returns {Promise<Array>} Array of automation objects
 */
async function getAutomate() {
    try {
        const response = await apiFetch('/api/sns/automate');
        if (!response.ok) throw new Error('Failed to fetch automations');
        return await response.json();
    } catch (error) {
        showError('Failed to load automations: ' + error.message);
        throw error;
    }
}

/**
 * Update an automation workflow
 * @param {number} id - Automation ID
 * @param {Object} data - Updated configuration
 * @returns {Promise<Object>} Updated automation object
 */
async function updateAutomate(id, data) {
    try {
        const response = await apiFetch(`/api/sns/automate/${id}`, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
        if (!response.ok) throw new Error('Failed to update automation');
        const result = await response.json();
        showSuccess('Automation updated successfully');
        return result;
    } catch (error) {
        showError('Automation update failed: ' + error.message);
        throw error;
    }
}

/**
 * Delete an automation workflow
 * @param {number} id - Automation ID
 * @returns {Promise<Object>} Deletion confirmation
 */
async function deleteAutomate(id) {
    try {
        const result = await confirmModal('Are you sure you want to delete this automation?');
        if (!result) return;

        const response = await apiFetch(`/api/sns/automate/${id}`, {
            method: 'DELETE'
        });
        if (!response.ok) throw new Error('Failed to delete automation');
        const data = await response.json();
        showSuccess('Automation deleted successfully');
        return data;
    } catch (error) {
        showError('Automation deletion failed: ' + error.message);
        throw error;
    }
}

/**
 * Get trending posts/hashtags for a platform
 * @param {string} platform - SNS platform (instagram, tiktok, twitter, etc.)
 * @param {string} category - Optional category filter
 * @returns {Promise<Array>} Array of trending items
 */
async function getTrending(platform, category = null) {
    try {
        let query = `?platform=${platform}`;
        if (category) query += `&category=${category}`;
        const response = await apiFetch(`/api/sns/trending${query}`);
        if (!response.ok) throw new Error('Failed to fetch trending');
        return await response.json();
    } catch (error) {
        showError('Failed to load trending: ' + error.message);
        throw error;
    }
}

/**
 * Get competitor analysis
 * @param {number} id - Competitor/Account ID
 * @returns {Promise<Object>} Competitor analysis data {followers, engagement, posts, etc.}
 */
async function getCompetitor(id) {
    try {
        const response = await apiFetch(`/api/sns/competitor/${id}`);
        if (!response.ok) throw new Error('Failed to fetch competitor data');
        return await response.json();
    } catch (error) {
        showError('Failed to load competitor data: ' + error.message);
        throw error;
    }
}

/**
 * Get SNS analytics with date range
 * @param {string} startDate - Start date (ISO format)
 * @param {string} endDate - End date (ISO format)
 * @param {string} platform - Optional platform filter
 * @returns {Promise<Object>} Aggregated analytics
 */
async function getSNSAnalytics(startDate, endDate, platform = null) {
    try {
        let query = `?start_date=${startDate}&end_date=${endDate}`;
        if (platform) query += `&platform=${platform}`;
        const response = await apiFetch(`/api/sns/analytics${query}`);
        if (!response.ok) throw new Error('Failed to fetch analytics');
        return await response.json();
    } catch (error) {
        showError('Failed to load analytics: ' + error.message);
        throw error;
    }
}

/**
 * Get SNS analytics (legacy, for compatibility)
 * @returns {Promise<Object>} Current period analytics
 */
async function getSNSAnalyticsLegacy() {
    const today = new Date();
    const thirtyDaysAgo = new Date(today.getTime() - 30 * 24 * 60 * 60 * 1000);
    return getSNSAnalytics(thirtyDaysAgo.toISOString().split('T')[0], today.toISOString().split('T')[0]);
}

/**
 * Get SNS inbox messages
 * @param {Object} filters - Filter options {status, platform, account_id, page}
 * @returns {Promise<Object>} Messages and pagination
 */
async function getSNSInboxMessages(filters = {}) {
    try {
        const params = new URLSearchParams(filters);
        const response = await apiFetch(`/api/sns/inbox?${params}`);
        if (!response.ok) throw new Error('Failed to fetch inbox messages');
        return await response.json();
    } catch (error) {
        showError('Failed to load messages: ' + error.message);
        throw error;
    }
}

/**
 * Reply to an SNS inbox message
 * @param {number} messageId - Message ID
 * @param {string} content - Reply content
 * @returns {Promise<Object>} Reply confirmation
 */
async function replySNSInboxMessage(messageId, content) {
    try {
        const response = await apiFetch(`/api/sns/inbox/${messageId}/reply`, {
            method: 'POST',
            body: JSON.stringify({ content })
        });
        if (!response.ok) throw new Error('Failed to send reply');
        const result = await response.json();
        showSuccess('Reply sent successfully');
        return result;
    } catch (error) {
        showError('Failed to send reply: ' + error.message);
        throw error;
    }
}

/**
 * Mark SNS inbox message as read
 * @param {number} messageId - Message ID
 * @returns {Promise<Object>} Update confirmation
 */
async function markSNSInboxRead(messageId) {
    try {
        const response = await apiFetch(`/api/sns/inbox/${messageId}/read`, {
            method: 'POST'
        });
        if (!response.ok) throw new Error('Failed to mark as read');
        return await response.json();
    } catch (error) {
        showError('Failed to mark message: ' + error.message);
        throw error;
    }
}

/**
 * Get SNS calendar view of scheduled posts
 * @param {number} year - Year (e.g., 2026)
 * @param {number} month - Month (1-12)
 * @returns {Promise<Object>} Calendar data with posts by day
 */
async function getSNSCalendar(year, month) {
    try {
        const response = await apiFetch(`/api/sns/calendar?year=${year}&month=${month}`);
        if (!response.ok) throw new Error('Failed to fetch calendar');
        return await response.json();
    } catch (error) {
        showError('Failed to load calendar: ' + error.message);
        throw error;
    }
}

/**
 * Get SNS campaigns list
 * @param {Object} filters - Filter options {status, platform, page}
 * @returns {Promise<Object>} Campaigns and pagination
 */
async function getSNSCampaigns(filters = {}) {
    try {
        const params = new URLSearchParams(filters);
        const response = await apiFetch(`/api/sns/campaigns?${params}`);
        if (!response.ok) throw new Error('Failed to fetch campaigns');
        return await response.json();
    } catch (error) {
        showError('Failed to load campaigns: ' + error.message);
        throw error;
    }
}

/**
 * Fetch detailed information for a single campaign
 * @param {number|string} id - Campaign ID
 * @returns {Promise<Object>}
 */
async function getCampaignDetail(id) {
    try {
        const response = await apiFetch(`/api/review/campaign_detail/${id}`);
        return await response.json();
    } catch (error) {
        console.error('[API] getCampaignDetail failed:', error);
        throw error;
    }
}

/**
 * Fetch all curated campaigns
 * @returns {Promise<Object>}
 */
async function getCampaigns() {
    try {
        const response = await apiFetch('/api/review/campaigns');
        return await response.json();
    } catch (error) {
        console.error('[API] getCampaigns failed:', error);
        throw error;
    }
}

/**
 * Create new SNS campaign
 * @param {Object} data - Campaign data {name, description, start_date, end_date, platforms}
 * @returns {Promise<Object>} Created campaign
 */
async function createSNSCampaign(data) {
    try {
        const response = await apiFetch('/api/sns/campaigns', {
            method: 'POST',
            body: JSON.stringify(data)
        });
        if (!response.ok) throw new Error('Failed to create campaign');
        const result = await response.json();
        showSuccess('Campaign created successfully');
        return result;
    } catch (error) {
        showError('Campaign creation failed: ' + error.message);
        throw error;
    }
}

/**
 * Update SNS campaign
 * @param {number} id - Campaign ID
 * @param {Object} data - Updated campaign data
 * @returns {Promise<Object>} Updated campaign
 */
async function updateSNSCampaign(id, data) {
    try {
        const response = await apiFetch(`/api/sns/campaigns/${id}`, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
        if (!response.ok) throw new Error('Failed to update campaign');
        const result = await response.json();
        showSuccess('Campaign updated successfully');
        return result;
    } catch (error) {
        showError('Campaign update failed: ' + error.message);
        throw error;
    }
}

/**
 * Delete SNS campaign
 * @param {number} id - Campaign ID
 * @returns {Promise<Object>} Deletion confirmation
 */
async function deleteSNSCampaign(id) {
    try {
        const result = await confirmModal('Are you sure you want to delete this campaign?');
        if (!result) return;

        const response = await apiFetch(`/api/sns/campaigns/${id}`, {
            method: 'DELETE'
        });
        if (!response.ok) throw new Error('Failed to delete campaign');
        const data = await response.json();
        showSuccess('Campaign deleted successfully');
        return data;
    } catch (error) {
        showError('Campaign deletion failed: ' + error.message);
        throw error;
    }
}

/**
 * Update SNS post with new content
 * @param {number} id - Post ID
 * @param {Object} data - Updated post data
 * @returns {Promise<Object>} Updated post
 */
async function updateSNSPost(id, data) {
    try {
        const response = await apiFetch(`/api/sns/posts/${id}`, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
        if (!response.ok) throw new Error('Failed to update post');
        const result = await response.json();
        showSuccess('Post updated successfully');
        return result;
    } catch (error) {
        showError('Post update failed: ' + error.message);
        throw error;
    }
}

/**
 * Delete SNS post
 * @param {number} id - Post ID
 * @returns {Promise<Object>} Deletion confirmation
 */
async function deleteSNSPost(id) {
    try {
        const result = await confirmModal('Are you sure you want to delete this post?');
        if (!result) return;

        const response = await apiFetch(`/api/sns/posts/${id}`, {
            method: 'DELETE'
        });
        if (!response.ok) throw new Error('Failed to delete post');
        const data = await response.json();
        showSuccess('Post deleted successfully');
        return data;
    } catch (error) {
        showError('Post deletion failed: ' + error.message);
        throw error;
    }
}

/**
 * AI-generated content for SNS
 * @param {Object} data - Generation parameters {topic, platform, tone, length}
 * @returns {Promise<Object>} Generated content with variations
 */
async function generateSNSContent(data) {
    try {
        const response = await apiFetch('/api/sns/ai/generate', {
            method: 'POST',
            body: JSON.stringify(data)
        });
        if (!response.ok) throw new Error('Failed to generate content');
        return await response.json();
    } catch (error) {
        showError('Content generation failed: ' + error.message);
        throw error;
    }
}

/**
 * Generate hashtags via AI
 * @param {string} content - Content text
 * @param {string} platform - Platform name
 * @returns {Promise<Object>} Generated hashtags
 */
async function generateSNSHashtags(content, platform) {
    try {
        const response = await apiFetch('/api/sns/ai/hashtags', {
            method: 'POST',
            body: JSON.stringify({ content, platform })
        });
        if (!response.ok) throw new Error('Failed to generate hashtags');
        return await response.json();
    } catch (error) {
        showError('Hashtag generation failed: ' + error.message);
        throw error;
    }
}

/**
 * Optimize SNS post content
 * @param {string} content - Content text
 * @param {string} platform - Platform name
 * @returns {Promise<Object>} Optimization suggestions
 */
async function optimizeSNSContent(content, platform) {
    try {
        const response = await apiFetch('/api/sns/ai/optimize', {
            method: 'POST',
            body: JSON.stringify({ content, platform })
        });
        if (!response.ok) throw new Error('Failed to optimize content');
        return await response.json();
    } catch (error) {
        showError('Optimization failed: ' + error.message);
        throw error;
    }
}

/**
 * Reconnect SNS account (re-authenticate)
 * @param {number} id - Account ID
 * @returns {Promise<Object>} OAuth URL for reconnection
 */
async function reconnectSNSAccount(id) {
    try {
        const response = await apiFetch(`/api/sns/accounts/${id}/reconnect`, {
            method: 'POST'
        });
        if (!response.ok) throw new Error('Failed to reconnect account');
        return await response.json();
    } catch (error) {
        showError('Account reconnection failed: ' + error.message);
        throw error;
    }
}

/**
 * Get SNS post metrics
 * @param {number} id - Post ID
 * @returns {Promise<Object>} Post metrics {views, likes, comments, shares, engagement_rate}
 */
async function getSNSPostMetrics(id) {
    try {
        const response = await apiFetch(`/api/sns/posts/${id}/metrics`);
        if (!response.ok) throw new Error('Failed to fetch post metrics');
        return await response.json();
    } catch (error) {
        showError('Failed to load post metrics: ' + error.message);
        throw error;
    }
}

// ============ REVIEW CAMPAIGN API ============

/**
 * Get review listings with filters
 * @param {Object} filters - Filter options {category, status, reward_min, reward_max, page}
 * @returns {Promise<Object>} Listings and pagination
 */
async function getReviewListings(filters = {}) {
    try {
        const params = new URLSearchParams(filters);
        const response = await apiFetch(`/api/review/listings?${params}`);
        if (!response.ok) throw new Error('Failed to fetch review listings');
        return await response.json();
    } catch (error) {
        showError('Failed to load review listings: ' + error.message);
        throw error;
    }
}

/**
 * Get review listing detail
 * @param {number} id - Listing ID
 * @returns {Promise<Object>} Complete listing details
 */
async function getReviewListing(id) {
    try {
        const response = await apiFetch(`/api/review/listings/${id}`);
        if (!response.ok) throw new Error('Failed to fetch review listing');
        return await response.json();
    } catch (error) {
        showError('Failed to load review listing: ' + error.message);
        throw error;
    }
}

/**
 * Apply to a review campaign
 * @param {number} listingId - Listing/Campaign ID
 * @param {number} accountId - SNS Account ID to use
 * @param {Object} data - Application data {message, sns_link, follower_count}
 * @returns {Promise<Object>} Application confirmation
 */
async function applyToReview(listingId, accountId, data = {}) {
    try {
        const payload = { account_id: accountId, ...data };
        const response = await apiFetch(`/api/review/listings/${listingId}/apply`, {
            method: 'POST',
            body: JSON.stringify(payload)
        });
        if (!response.ok) throw new Error('Failed to apply to review');
        const result = await response.json();
        showSuccess('Application submitted successfully');
        return result;
    } catch (error) {
        showError('Application failed: ' + error.message);
        throw error;
    }
}

/**
 * Get user's review applications
 * @param {string} status - Filter by status (pending, approved, rejected, completed)
 * @returns {Promise<Array>} User's applications
 */
async function getMyApplications(status = null) {
    try {
        let query = '';
        if (status) query = `?status=${status}`;
        const response = await apiFetch(`/api/review/applications${query}`);
        if (!response.ok) throw new Error('Failed to fetch applications');
        return await response.json();
    } catch (error) {
        showError('Failed to load applications: ' + error.message);
        throw error;
    }
}

/**
 * Get review accounts (SNS accounts used for reviews)
 * @returns {Promise<Array>} User's review accounts
 */
async function getReviewAccounts() {
    try {
        const response = await apiFetch('/api/review/accounts');
        if (!response.ok) throw new Error('Failed to fetch review accounts');
        return await response.json();
    } catch (error) {
        showError('Failed to load review accounts: ' + error.message);
        throw error;
    }
}

/**
 * Create new review account
 * @param {Object} data - Account data {platform, account_name, follower_count, niche}
 * @returns {Promise<Object>} Created account
 */
async function createReviewAccount(data) {
    try {
        const response = await apiFetch('/api/review/accounts', {
            method: 'POST',
            body: JSON.stringify(data)
        });
        if (!response.ok) throw new Error('Failed to create review account');
        const result = await response.json();
        showSuccess('Review account created successfully');
        return result;
    } catch (error) {
        showError('Account creation failed: ' + error.message);
        throw error;
    }
}

/**
 * Update review account
 * @param {number} id - Account ID
 * @param {Object} data - Updated account data
 * @returns {Promise<Object>} Updated account
 */
async function updateReviewAccount(id, data) {
    try {
        const response = await apiFetch(`/api/review/accounts/${id}`, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
        if (!response.ok) throw new Error('Failed to update review account');
        const result = await response.json();
        showSuccess('Review account updated successfully');
        return result;
    } catch (error) {
        showError('Account update failed: ' + error.message);
        throw error;
    }
}

/**
 * Delete review account
 * @param {number} id - Account ID
 * @returns {Promise<Object>} Deletion confirmation
 */
async function deleteReviewAccount(id) {
    try {
        const result = await confirmModal('Are you sure you want to delete this review account?');
        if (!result) return;

        const response = await apiFetch(`/api/review/accounts/${id}`, {
            method: 'DELETE'
        });
        if (!response.ok) throw new Error('Failed to delete review account');
        const data = await response.json();
        showSuccess('Review account deleted successfully');
        return data;
    } catch (error) {
        showError('Account deletion failed: ' + error.message);
        throw error;
    }
}

/**
 * Get auto-apply rules
 * @returns {Promise<Array>} Array of auto-apply rules
 */
async function getAutoApplyRules() {
    try {
        const response = await apiFetch('/api/review/auto-apply/rules');
        if (!response.ok) throw new Error('Failed to fetch auto-apply rules');
        return await response.json();
    } catch (error) {
        showError('Failed to load auto-apply rules: ' + error.message);
        throw error;
    }
}

/**
 * Create auto-apply rule
 * @param {Object} data - Rule data {name, category, min_reward, min_followers, auto_message}
 * @returns {Promise<Object>} Created rule
 */
async function createAutoApplyRule(data) {
    try {
        const response = await apiFetch('/api/review/auto-apply/rules', {
            method: 'POST',
            body: JSON.stringify(data)
        });
        if (!response.ok) throw new Error('Failed to create auto-apply rule');
        const result = await response.json();
        showSuccess('Auto-apply rule created successfully');
        return result;
    } catch (error) {
        showError('Rule creation failed: ' + error.message);
        throw error;
    }
}

/**
 * Update auto-apply rule
 * @param {number} id - Rule ID
 * @param {Object} data - Updated rule data
 * @returns {Promise<Object>} Updated rule
 */
async function updateAutoApplyRule(id, data) {
    try {
        const response = await apiFetch(`/api/review/auto-apply/rules/${id}`, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
        if (!response.ok) throw new Error('Failed to update auto-apply rule');
        const result = await response.json();
        showSuccess('Auto-apply rule updated successfully');
        return result;
    } catch (error) {
        showError('Rule update failed: ' + error.message);
        throw error;
    }
}

/**
 * Delete auto-apply rule
 * @param {number} id - Rule ID
 * @returns {Promise<Object>} Deletion confirmation
 */
async function deleteAutoApplyRule(id) {
    try {
        const result = await confirmModal('Are you sure you want to delete this rule?');
        if (!result) return;

        const response = await apiFetch(`/api/review/auto-apply/rules/${id}`, {
            method: 'DELETE'
        });
        if (!response.ok) throw new Error('Failed to delete auto-apply rule');
        const data = await response.json();
        showSuccess('Rule deleted successfully');
        return data;
    } catch (error) {
        showError('Rule deletion failed: ' + error.message);
        throw error;
    }
}

/**
 * Manually trigger auto-apply process
 * @returns {Promise<Object>} Process result {applied_count, skipped_count, errors}
 */
async function runAutoApply() {
    try {
        const response = await apiFetch('/api/review/auto-apply/run', {
            method: 'POST'
        });
        if (!response.ok) throw new Error('Failed to run auto-apply');
        const result = await response.json();
        showSuccess(`Auto-apply completed: ${result.applied_count} applications`);
        return result;
    } catch (error) {
        showError('Auto-apply failed: ' + error.message);
        throw error;
    }
}

/**
 * Get review statistics
 * @returns {Promise<Object>} Stats {total_applications, approved_count, pending_count, completion_rate}
 */
async function getReviewStats() {
    try {
        const response = await apiFetch('/api/review/stats');
        if (!response.ok) throw new Error('Failed to fetch review stats');
        return await response.json();
    } catch (error) {
        showError('Failed to load review stats: ' + error.message);
        throw error;
    }
}

/**
 * Get review analytics with date range
 * @param {string} startDate - Start date (ISO format)
 * @param {string} endDate - End date (ISO format)
 * @returns {Promise<Object>} Analytics data {applications_by_day, earnings, category_breakdown}
 */
async function getReviewAnalytics(startDate = null, endDate = null) {
    try {
        let query = '';
        if (startDate && endDate) {
            query = `?start_date=${startDate}&end_date=${endDate}`;
        }
        const response = await apiFetch(`/api/review/analytics${query}`);
        if (!response.ok) throw new Error('Failed to fetch review analytics');
        return await response.json();
    } catch (error) {
        showError('Failed to load review analytics: ' + error.message);
        throw error;
    }
}

/**
 * Bookmark a review campaign
 * @param {number} id - Campaign/Listing ID
 * @returns {Promise<Object>} Bookmark confirmation
 */
async function bookmarkReview(id) {
    try {
        const response = await apiFetch(`/api/review/listings/${id}/bookmark`, {
            method: 'POST'
        });
        if (!response.ok) throw new Error('Failed to bookmark');
        const result = await response.json();
        showSuccess('Campaign bookmarked successfully');
        return result;
    } catch (error) {
        showError('Bookmark failed: ' + error.message);
        throw error;
    }
}

/**
 * Remove review campaign bookmark
 * @param {number} id - Campaign/Listing ID
 * @returns {Promise<Object>} Removal confirmation
 */
async function unbookmarkReview(id) {
    try {
        const response = await apiFetch(`/api/review/listings/${id}/bookmark`, {
            method: 'DELETE'
        });
        if (!response.ok) throw new Error('Failed to remove bookmark');
        const result = await response.json();
        showSuccess('Bookmark removed successfully');
        return result;
    } catch (error) {
        showError('Bookmark removal failed: ' + error.message);
        throw error;
    }
}

/**
 * Get user's bookmarked reviews
 * @returns {Promise<Array>} Bookmarked campaigns
 */
async function getBookmarkedReviews() {
    try {
        const response = await apiFetch('/api/review/bookmarks');
        if (!response.ok) throw new Error('Failed to fetch bookmarks');
        return await response.json();
    } catch (error) {
        showError('Failed to load bookmarks: ' + error.message);
        throw error;
    }
}

// ============ PAYMENT & BILLING ============

/**
 * Get billing information
 * @returns {Promise<Object>} Billing data {current_plan, monthly_charge, services, next_billing_date}
 */
async function getBillingInfo() {
    try {
        const response = await apiFetch('/api/payment/billing-info');
        if (!response.ok) throw new Error('Failed to fetch billing info');
        return await response.json();
    } catch (error) {
        showError('Failed to load billing info: ' + error.message);
        throw error;
    }
}

/**
 * Get payment history
 * @param {number} page - Page number
 * @returns {Promise<Object>} Payment history with pagination
 */
async function getPaymentHistory(page = 1) {
    try {
        const response = await apiFetch(`/api/payment/history?page=${page}`);
        if (!response.ok) throw new Error('Failed to fetch payment history');
        return await response.json();
    } catch (error) {
        showError('Failed to load payment history: ' + error.message);
        throw error;
    }
}

// ============ TOKEN MANAGEMENT HELPERS ============

/**
 * Get stored authentication token
 * @returns {string|null} Authentication token or null if not set
 */
function getAuthToken() {
    return localStorage.getItem('access_token') || null;
}

/**
 * Set authentication token in local storage
 * @param {string} token - Access token
 * @param {string|null} refreshToken - Optional refresh token
 */
function setAuthToken(token, refreshToken = null) {
    localStorage.setItem('access_token', token);
    if (refreshToken) {
        localStorage.setItem('refresh_token', refreshToken);
    } else {
        localStorage.setItem('refresh_token', token);
    }
}

/**
 * Clear all authentication tokens and user data
 */
function clearAuthToken() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    localStorage.removeItem('demo_mode');
}

/**
 * Check if user is currently authenticated
 * @returns {boolean} True if user has valid token
 */
function isAuthenticated() {
    const token = getAuthToken();
    return token !== null && token !== undefined && token !== '';
}

/**
 * Get authenticated user object from local storage
 * @returns {Object|null} User object or null if not authenticated
 */
function getAuthUser() {
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
}

// ============ AI STATUS WIDGET (Task 5) ============

/**
 * Global AI Status Widget — shows on every page.
 * Displays: API connection status, AI availability, last sync time.
 * Can be toggled open/closed by clicking.
 */
let _sfAiWidgetOpen = false;
let _sfLastSyncTime = null;

function _sfRenderAiStatusWidget() {
    let widget = document.getElementById('ai-status-widget');
    if (widget) widget.remove();

    widget = document.createElement('div');
    widget.id = 'ai-status-widget';
    widget.style.cssText = 'position:fixed;bottom:20px;right:20px;z-index:1000;font-family:Inter,sans-serif;';

    const mode = getApiMode();
    const isLive = mode === 'live';
    const lastSync = _sfLastSyncTime ? formatDate(_sfLastSyncTime, 'relative') : 'Never';
    const baseUrl = getResolvedApiBase();

    if (_sfAiWidgetOpen) {
        widget.innerHTML = `
            <div style="background:linear-gradient(135deg,rgba(30,41,59,0.95),rgba(15,23,42,0.98));border:1px solid ${isLive ? 'rgba(16,185,129,0.4)' : 'rgba(245,158,11,0.4)'};border-radius:16px;padding:16px;width:280px;box-shadow:0 20px 50px rgba(0,0,0,0.5);backdrop-filter:blur(12px);">
                <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;">
                    <span style="font-size:13px;font-weight:700;color:#f1f5f9;">System Status</span>
                    <button onclick="_sfAiWidgetOpen=false;_sfRenderAiStatusWidget();" style="background:none;border:none;color:#94a3b8;cursor:pointer;font-size:16px;padding:0 4px;">&times;</button>
                </div>
                <div style="display:flex;flex-direction:column;gap:8px;">
                    <div style="display:flex;align-items:center;justify-content:space-between;padding:8px 10px;background:rgba(${isLive ? '16,185,129' : '245,158,11'},0.1);border-radius:8px;">
                        <span style="font-size:11px;color:#94a3b8;">API Status</span>
                        <span style="font-size:11px;font-weight:600;color:${isLive ? '#4ade80' : '#fbbf24'};">${isLive ? 'Connected' : 'Demo Mode'}</span>
                    </div>
                    <div style="display:flex;align-items:center;justify-content:space-between;padding:8px 10px;background:rgba(139,92,246,0.1);border-radius:8px;">
                        <span style="font-size:11px;color:#94a3b8;">AI Engine</span>
                        <span style="font-size:11px;font-weight:600;color:${isLive ? '#a78bfa' : '#94a3b8'};">${isLive ? 'Available' : 'Simulated'}</span>
                    </div>
                    <div style="display:flex;align-items:center;justify-content:space-between;padding:8px 10px;background:rgba(30,41,59,0.5);border-radius:8px;">
                        <span style="font-size:11px;color:#94a3b8;">Last Sync</span>
                        <span style="font-size:11px;font-weight:600;color:#cbd5e1;">${lastSync}</span>
                    </div>
                    ${isLive ? `<div style="display:flex;align-items:center;justify-content:space-between;padding:8px 10px;background:rgba(30,41,59,0.5);border-radius:8px;">
                        <span style="font-size:11px;color:#94a3b8;">Backend</span>
                        <span style="font-size:11px;font-weight:500;color:#64748b;">${baseUrl}</span>
                    </div>` : ''}
                    <button onclick="_sfRefreshApiStatus()" style="margin-top:4px;width:100%;padding:6px;background:linear-gradient(135deg,${isLive ? '#059669,#047857' : '#d97706,#b45309'});border:none;border-radius:8px;color:#fff;font-size:11px;font-weight:600;cursor:pointer;">Refresh Status</button>
                </div>
            </div>
        `;
    } else {
        // Collapsed: just show a small circle button
        widget.innerHTML = `
            <button onclick="_sfAiWidgetOpen=true;_sfRenderAiStatusWidget();" style="width:40px;height:40px;border-radius:50%;border:2px solid ${isLive ? '#10b981' : '#f59e0b'};background:linear-gradient(135deg,rgba(30,41,59,0.95),rgba(15,23,42,0.98));color:${isLive ? '#4ade80' : '#fbbf24'};cursor:pointer;display:flex;align-items:center;justify-content:center;font-size:16px;box-shadow:0 4px 16px rgba(0,0,0,0.4);backdrop-filter:blur(8px);transition:all 0.3s ease;" onmouseover="this.style.transform='scale(1.1)'" onmouseout="this.style.transform='scale(1)'">
                ${isLive ? '<span style="animation:sf-pulse-dot 2s infinite;">&#x26A1;</span>' : '&#x1F4E1;'}
            </button>
        `;
    }

    document.body.appendChild(widget);
}

async function _sfRefreshApiStatus() {
    const wasLive = getApiMode() === 'live';
    const isLiveNow = await detectApiMode();
    _sfLastSyncTime = new Date();
    _sfRenderAiStatusWidget();
    if (isLiveNow && !wasLive) {
        showToast('Backend connection restored!', 'success');
    } else if (!isLiveNow && wasLive) {
        showToast('Backend disconnected. Switched to demo mode.', 'warning');
    } else {
        showToast('Status refreshed. Mode: ' + getApiMode(), 'info');
    }
}

// Auto-render widget on page load
if (typeof document !== 'undefined') {
    document.addEventListener('DOMContentLoaded', () => {
        // Small delay to let detectApiMode finish
        setTimeout(() => {
            _sfLastSyncTime = new Date();
            _sfRenderAiStatusWidget();
        }, 1500);
    });
}

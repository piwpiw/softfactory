/**
 * SoftFactory API Client Module v2.0
 * Comprehensive API integration for all SoftFactory services
 *
 * FEATURES:
 * - Authentication: login, register, OAuth (Google, Facebook, Kakao)
 * - SNS Automation: 25+ endpoints for multi-platform social media management
 * - Review Campaigns: 15+ endpoints for review management and auto-apply
 * - Payment & Billing: subscription, invoice, and billing management
 * - 데모 모드: Full simulation without backend (passkey: "demo2026")
 *
 * DEMO MODE: Use passkey "demo2026" to bypass authentication
 *
 * @module api
 * @version 2.0
 * @since 2026-02-26
 *
 * FUNCTION CATEGORIES:
 * - Auth 관리: register, login, logout, refresh tokens
 * - OAuth & Social 로그인: loginWithGoogle, loginWithFacebook, loginWithKakao, handleOAuthCallback
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
 * - 리뷰 Listings: getReviewListings, getReviewListing
 * - Review Applications: applyToReview, getMyApplications
 * - 리뷰 Accounts: getReviewAccounts, createReviewAccount, updateReviewAccount, deleteReviewAccount
 * - 리뷰 Auto-Apply: getAutoApplyRules, createAutoApplyRule, updateAutoApplyRule, deleteAutoApplyRule, runAutoApply
 * - 리뷰 Stats: getReviewStats, getReviewAnalytics, bookmarkReview, unbookmarkReview, getBookmarkedReviews
 * - Payment: getBillingInfo, getPaymentHistory, getPlans, createCheckout, getSubscriptions, cancelSubscription
 * - UI Helpers: formatKRW, formatDate, statusBadge, showToast, showError, showSuccess, etc.
 * - Token 관리: getAuthToken, setAuthToken, clearAuthToken, isAuthenticated, getAuthUser
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
const ADMIN_FIXTURE_KEY = 'sf_admin_fixture_mode';
const ADMIN_FIXTURE_SEEDED_KEY = 'sf_admin_fixture_seeded';
const API_GET_CACHE_TTL_MS = 45 * 1000;
const API_GET_CACHE_PREFIX = 'sf_api_cache:';
const API_MODE_CACHE_TTL_MS = 20 * 1000;
const _sfInflightRequests = new Map();
const _sfPrefetchedPages = new Set();
let _sfActiveRequests = 0;
let _sfDetectApiModePromise = null;
let _sfApiModeCheckedAt = 0;
const _sfPendingButtons = new Set();

function _sfCanUseStorage() {
    try {
        return typeof window !== 'undefined' && !!window.localStorage;
    } catch (e) {
        return false;
    }
}

function _sfGetRequestProgress() {
    let bar = document.getElementById('sf-api-progress');
    if (bar) return bar;
    bar = document.createElement('div');
    bar.id = 'sf-api-progress';
    bar.setAttribute('aria-hidden', 'true');
    bar.style.cssText = 'position:fixed;top:0;left:0;height:3px;width:0%;z-index:10001;pointer-events:none;background:linear-gradient(90deg,#22c55e,#38bdf8,#f59e0b);box-shadow:0 0 18px rgba(56,189,248,0.4);opacity:0;transition:width 0.2s ease,opacity 0.18s ease;';
    document.body.appendChild(bar);
    return bar;
}

function _sfStartRequestProgress() {
    _sfActiveRequests += 1;
    const bar = _sfGetRequestProgress();
    bar.style.opacity = '1';
    bar.style.width = _sfActiveRequests > 1 ? '76%' : '42%';
}

function _sfFinishRequestProgress() {
    _sfActiveRequests = Math.max(0, _sfActiveRequests - 1);
    const bar = _sfGetRequestProgress();
    if (_sfActiveRequests > 0) {
        bar.style.width = '84%';
        return;
    }
    bar.style.width = '100%';
    setTimeout(() => {
        bar.style.opacity = '0';
        bar.style.width = '0%';
    }, 160);
    if (_sfActiveRequests === 0) {
        _sfClearPendingButtons();
    }
}

function _sfMarkPendingButton(button) {
    if (!button || button.dataset.sfPending === 'true') return;
    button.dataset.sfPending = 'true';
    button.dataset.sfOriginalLabel = button.innerHTML;
    button.disabled = true;
    button.style.opacity = '0.72';
    button.style.cursor = 'wait';
    button.innerHTML = '<span style="display:inline-flex;align-items:center;gap:8px;"><span style="width:12px;height:12px;border:2px solid rgba(255,255,255,0.35);border-top-color:currentColor;border-radius:999px;display:inline-block;animation:sf-pulse-dot 0.9s linear infinite;"></span><span>처리 중...</span></span>';
    _sfPendingButtons.add(button);
}

function _sfClearPendingButtons() {
    _sfPendingButtons.forEach((button) => {
        if (!button || !button.isConnected) return;
        button.disabled = false;
        button.style.opacity = '';
        button.style.cursor = '';
        if (button.dataset.sfOriginalLabel) {
            button.innerHTML = button.dataset.sfOriginalLabel;
        }
        delete button.dataset.sfOriginalLabel;
        delete button.dataset.sfPending;
    });
    _sfPendingButtons.clear();
}

function _sfBindPendingFormState() {
    if (document.body.dataset.sfPendingFormBound === 'true') return;
    document.body.dataset.sfPendingFormBound = 'true';

    document.addEventListener('submit', (event) => {
        const form = event.target;
        if (!(form instanceof HTMLFormElement)) return;
        const submitter = event.submitter || form.querySelector('button[type="submit"],input[type="submit"]');
        if (submitter) {
            _sfMarkPendingButton(submitter);
            setTimeout(() => {
                if (_sfActiveRequests === 0) {
                    _sfClearPendingButtons();
                }
            }, 12000);
        }
    }, true);

    window.addEventListener('pageshow', () => {
        _sfClearPendingButtons();
    });
}

function _sfCacheKey(url) {
    return `${API_GET_CACHE_PREFIX}${url}`;
}

function _sfReadCachedResponse(url) {
    if (!_sfCanUseStorage()) return null;
    try {
        const raw = localStorage.getItem(_sfCacheKey(url));
        if (!raw) return null;
        const parsed = JSON.parse(raw);
        if (!parsed || (Date.now() - parsed.savedAt) > API_GET_CACHE_TTL_MS) return null;
        return new Response(parsed.body, {
            status: parsed.status || 200,
            headers: parsed.headers || { 'Content-Type': 'application/json' }
        });
    } catch (e) {
        return null;
    }
}

async function _sfWriteCachedResponse(url, response) {
    if (!_sfCanUseStorage() || !(response instanceof Response) || !response.ok) return;
    const contentType = response.headers.get('content-type') || '';
    if (!/application\/json|text\//i.test(contentType)) return;
    try {
        const body = await response.clone().text();
        localStorage.setItem(_sfCacheKey(url), JSON.stringify({
            savedAt: Date.now(),
            status: response.status,
            headers: { 'Content-Type': contentType || 'application/json' },
            body
        }));
    } catch (e) {}
}

function _sfNormalizePrefetchHref(href) {
    if (!href || href.startsWith('javascript:') || href.startsWith('#')) return null;
    try {
        const target = new URL(href, window.location.href);
        if (target.origin !== window.location.origin) return null;
        if (!/\.html($|\?)/i.test(target.pathname) && !/\/(platform|review|sns-auto|coocook|ai-automation|webapp-builder|instagram-cardnews)\//i.test(target.pathname)) {
            return null;
        }
        return target.href;
    } catch (e) {
        return null;
    }
}

function _sfPrefetchPage(href) {
    const connection = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
    if (document.hidden) return;
    if (connection && (connection.saveData || /(^slow-2g$|^2g$)/i.test(String(connection.effectiveType || '')))) return;
    const normalized = _sfNormalizePrefetchHref(href);
    if (!normalized || _sfPrefetchedPages.has(normalized)) return;
    _sfPrefetchedPages.add(normalized);

    try {
        const link = document.createElement('link');
        link.rel = 'prefetch';
        link.as = 'document';
        link.href = normalized;
        document.head.appendChild(link);
    } catch (e) {}

    fetch(normalized, { method: 'GET', credentials: 'same-origin' }).catch(() => null);
}

function _sfBindNavigationPrefetch() {
    if (document.body.dataset.sfPrefetchBound === 'true') return;
    document.body.dataset.sfPrefetchBound = 'true';

    const trigger = (event) => {
        const link = event.target && event.target.closest ? event.target.closest('a[href]') : null;
        if (!link) return;
        _sfPrefetchPage(link.getAttribute('href'));
    };

    document.addEventListener('mouseover', trigger, { passive: true });
    document.addEventListener('focusin', trigger);
}

function _sfEnsureQuickOpen() {
    if (document.getElementById('sf-quick-open')) return;
    const links = Array.from(document.querySelectorAll('a[href]'))
        .map((link) => ({
            href: link.getAttribute('href') || '',
            label: (link.textContent || '').replace(/\s+/g, ' ').trim()
        }))
        .filter((item, index, arr) => item.href && item.label && !item.href.startsWith('#') && arr.findIndex((candidate) => candidate.href === item.href) === index)
        .slice(0, 32);
    if (!links.length) return;

    const root = document.createElement('div');
    root.id = 'sf-quick-open';
    root.style.cssText = 'display:none;position:fixed;inset:0;z-index:10030;';
    root.innerHTML = `
        <div data-quick-close="true" style="position:absolute;inset:0;background:rgba(2,6,23,0.7);backdrop-filter:blur(8px);"></div>
        <div style="position:relative;width:min(680px,calc(100vw - 24px));margin:8vh auto 0;background:linear-gradient(180deg,rgba(15,23,42,0.98),rgba(17,27,43,0.98));border:1px solid rgba(148,163,184,0.2);border-radius:22px;box-shadow:0 32px 80px rgba(2,6,23,0.45);overflow:hidden;">
            <div style="display:flex;align-items:center;justify-content:space-between;padding:16px 16px 10px;color:#dbeafe;">
                <strong style="font-size:15px;">빠른 이동</strong>
                <span style="font-size:12px;color:#94a3b8;">Ctrl+K</span>
            </div>
            <input id="sf-quick-open-input" type="text" autocomplete="off" placeholder="화면 이름이나 경로를 입력하세요" style="width:calc(100% - 32px);margin:0 16px 14px;padding:14px 16px;border-radius:14px;border:1px solid rgba(96,165,250,0.22);background:rgba(15,23,42,0.88);color:#f8fafc;outline:none;">
            <div id="sf-quick-open-list" style="display:grid;gap:6px;max-height:min(56vh,520px);overflow:auto;padding:0 12px 14px;"></div>
        </div>
    `;
    document.body.appendChild(root);

    const list = root.querySelector('#sf-quick-open-list');
    const input = root.querySelector('#sf-quick-open-input');
    const render = (query = '') => {
        const normalized = String(query).toLowerCase().trim();
        const filtered = links.filter((item) => !normalized || item.label.toLowerCase().includes(normalized) || item.href.toLowerCase().includes(normalized));
        list.innerHTML = filtered.length
            ? filtered.map((item) => `<a href="${item.href}" style="display:flex;justify-content:space-between;gap:16px;padding:13px 14px;border-radius:14px;border:1px solid rgba(148,163,184,0.12);background:rgba(15,23,42,0.54);color:#e2e8f0;text-decoration:none;"><span>${item.label}</span><span style="font-size:12px;color:#94a3b8;">${item.href}</span></a>`).join('')
            : '<div style="padding:14px;border-radius:14px;border:1px solid rgba(148,163,184,0.12);background:rgba(15,23,42,0.54);color:#94a3b8;">일치하는 화면이 없습니다.</div>';
    };

    const open = () => {
        root.style.display = 'block';
        input.value = '';
        render('');
        input.focus();
    };
    const close = () => {
        root.style.display = 'none';
    };

    root.addEventListener('click', (event) => {
        if (event.target && event.target.getAttribute('data-quick-close') === 'true') {
            close();
        }
    });
    input.addEventListener('input', (event) => render(event.target.value));

    document.addEventListener('keydown', (event) => {
        const key = String(event.key || '').toLowerCase();
        const target = event.target;
        const typing = target && (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable);
        if (key === 'escape' && root.style.display === 'block') {
            close();
            return;
        }
        if (typing) return;
        if ((event.ctrlKey || event.metaKey) && key === 'k') {
            event.preventDefault();
            open();
        }
    });
}

function isAdminUser(user) {
    if (!user || typeof user !== 'object') return false;
    return user.role === 'admin' || user.is_admin === true || user.is_superuser === true;
}

// ============ SMART API MODE DETECTION ============

/**
 * Detects whether the live backend is available.
 * Sets window.__API_MODE to 'live' or 'demo'.
 * Tries primary API_BASE first, then fallback port.
 * @returns {Promise<boolean>} true if live backend is available
 */
async function detectApiMode(options = {}) {
    const force = !!options.force;
    if (!force && _sfDetectApiModePromise) {
        return _sfDetectApiModePromise;
    }
    if (!force && window.__API_MODE && (Date.now() - _sfApiModeCheckedAt) < API_MODE_CACHE_TTL_MS) {
        return window.__API_MODE === 'live';
    }

    const endpoints = [API_BASE, ...API_BASE_FALLBACKS].filter((value, index, arr) => {
        if (!value) return false;
        return arr.indexOf(value) === index;
    });
    _sfDetectApiModePromise = (async () => {
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
        // 404는 /health 엔드포인트가 없어도 서버가 살아 있는 신호로 간주
                    window.__API_MODE = 'live';
                    window.__SF_API_BASE_RESOLVED = base;
                    _sfApiModeCheckedAt = Date.now();
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
        _sfApiModeCheckedAt = Date.now();
        console.log('[API] Demo mode (backend not available)');
        if (!isDemoMode()) {
            enableDemoMode();
        }
        _sfRenderApiModeIndicator();
        return false;
    })();

    try {
        return await _sfDetectApiModePromise;
    } finally {
        _sfDetectApiModePromise = null;
    }
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
            if (isAdminFixtureMode()) {
                showToast('관리자 테스트 모드입니다. 전체 기능은 더미 데이터로 안전하게 동작합니다.', 'info');
            } else if (mode === 'demo') {
                showToast('데모 모드입니다. 백엔드가 오프라인이어서 샘플 데이터로 동작합니다.', 'warning');
            } else {
                showToast('실시간 모드입니다. 백엔드에 연결됨: ' + getResolvedApiBase(), 'success');
            }
        };
        document.body.appendChild(indicator);
    }

    const mode = getApiMode();
    const fixtureMode = isAdminFixtureMode();
    if (fixtureMode) {
        indicator.style.background = 'linear-gradient(135deg, #7c3aed, #5b21b6)';
        indicator.style.border = '1px solid #a78bfa';
        indicator.style.color = '#fff';
        indicator.innerHTML = '<span style="width:6px;height:6px;border-radius:50%;background:#ddd6fe;display:inline-block;animation:sf-pulse-dot 2s infinite;"></span> 관리자 테스트';
    } else if (mode === 'live') {
        indicator.style.background = 'linear-gradient(135deg, #059669, #047857)';
        indicator.style.border = '1px solid #10b981';
        indicator.style.color = '#fff';
        indicator.innerHTML = '<span style="width:6px;height:6px;border-radius:50%;background:#4ade80;display:inline-block;animation:sf-pulse-dot 2s infinite;"></span> 실시간';
    } else {
        indicator.style.background = 'linear-gradient(135deg, #d97706, #b45309)';
        indicator.style.border = '1px solid #f59e0b';
        indicator.style.color = '#fff';
        indicator.innerHTML = '<span style="width:6px;height:6px;border-radius:50%;background:#fcd34d;display:inline-block;"></span> 데모';
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
    showToast('네트워크 복구됨. 백엔드 동기화를 재시작합니다.', 'success');
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

function isAdminFixtureMode() {
    return localStorage.getItem(ADMIN_FIXTURE_KEY) === 'true';
}

function seedAdminDummyData(user = DEMO_USER) {
    if (localStorage.getItem(ADMIN_FIXTURE_SEEDED_KEY) === 'true') return;

    const now = new Date().toISOString();
    const templates = [
        {
            id: 'fixture_template_performance',
            name: '성과 리포트형',
            tone: 'professional',
            slides: 8,
            created_at: now
        },
        {
            id: 'fixture_template_story',
            name: '스토리텔링형',
            tone: 'friendly',
            slides: 10,
            created_at: now
        }
    ];
    const projects = [
        {
            id: 'fixture_project_1',
            title: '신규 런칭 캠페인 테스트',
            status: 'draft',
            created_at: now,
            updated_at: now,
            owner: user.email || DEMO_USER.email
        },
        {
            id: 'fixture_project_2',
            title: '리텐션 캠페인 테스트',
            status: 'published',
            created_at: now,
            updated_at: now,
            owner: user.email || DEMO_USER.email
        }
    ];

    localStorage.setItem('sf_cardnews_templates', JSON.stringify(templates));
    localStorage.setItem('sf_cardnews_projects', JSON.stringify(projects));
    localStorage.setItem('onboarding_complete', 'true');
    localStorage.setItem(ADMIN_FIXTURE_SEEDED_KEY, 'true');
}

function enableAdminFixtureMode(user = DEMO_USER) {
    localStorage.setItem(ADMIN_FIXTURE_KEY, 'true');
    if (user && typeof user === 'object') {
        localStorage.setItem('user', JSON.stringify(user));
    }
    seedAdminDummyData(user || DEMO_USER);
    _sfRenderApiModeIndicator();
}

function disableAdminFixtureMode() {
    localStorage.removeItem(ADMIN_FIXTURE_KEY);
    localStorage.removeItem(ADMIN_FIXTURE_SEEDED_KEY);
    _sfRenderApiModeIndicator();
}

function enableDemoMode() {
    localStorage.setItem('demo_mode', 'true');
    localStorage.setItem('user', JSON.stringify(DEMO_USER));
    localStorage.setItem('access_token', 'demo_token');
    localStorage.setItem('refresh_token', 'demo_token');
    enableAdminFixtureMode(DEMO_USER);
}

function disableDemoMode() {
    disableAdminFixtureMode();
    localStorage.removeItem('demo_mode');
    localStorage.clear();
}

function requiresStrictRealApi(path, options = {}) {
    if (options && options.strictRealApi) return true;
    const strictPrefixes = [
        '/api/instagram-cardnews',
    ];
    return strictPrefixes.some((prefix) => path.startsWith(prefix));
}

// ============ AUTH MANAGEMENT ============

async function apiFetch(path, options = {}) {
    const strictRealApi = requiresStrictRealApi(path, options);
    const method = String(options.method || 'GET').toUpperCase();

    // Admin fixture mode: force all API paths to deterministic mock data.
    if (isAdminFixtureMode() && path.startsWith('/api/')) {
        if (strictRealApi) {
            throw new Error(`Strict real API required for ${path}`);
        }
        return mockApiFetch(path, options);
    }

    // Block requests when offline
    if (_sfIsOffline) {
        // Fall back to demo mode when offline
        if (isDemoMode()) {
            if (strictRealApi) {
                throw new Error(`Offline: strict real API required for ${path}`);
            }
            return mockApiFetch(path, options);
        }
        showToast('오프라인 상태입니다. 일부 기능은 샘플 데이터 모드로 전환됩니다.', 'warning');
        throw new Error('Network offline');
    }

    // If explicitly in demo mode and we haven't detected a live backend, use mock
    if (isDemoMode() && getApiMode() !== 'live') {
        if (strictRealApi) {
            throw new Error(`Demo fallback disabled for ${path}`);
        }
        return mockApiFetch(path, options);
    }

    // Always try real API first
    const apiBase = getResolvedApiBase();
    const url = `${apiBase}${path}`;
    const canUseCache = method === 'GET' && !strictRealApi && options.cache !== 'no-store' && options.disableCache !== true;
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

    if (canUseCache) {
        const cached = _sfReadCachedResponse(url);
        if (cached) {
            if (!options.silentRefresh) {
                apiFetch(path, { ...options, disableCache: true, silentRefresh: true }).catch(() => null);
            }
            return cached;
        }
    }

    const inflightKey = canUseCache ? `${method}:${url}:${headers.Authorization || ''}` : null;
    if (inflightKey && _sfInflightRequests.has(inflightKey)) {
        return _sfInflightRequests.get(inflightKey).then((response) => response.clone());
    }

    try {
        const requestTask = (async () => {
            _sfStartRequestProgress();
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
                        window.location.href = getLoginPageUrl();
                    }
                }
            }

            if (canUseCache) {
                await _sfWriteCachedResponse(url, response);
            }
            return response;
        })();

        if (inflightKey) {
            _sfInflightRequests.set(inflightKey, requestTask);
        }

        try {
            return await requestTask;
        } finally {
            if (inflightKey) _sfInflightRequests.delete(inflightKey);
            _sfFinishRequestProgress();
        }
    } catch (error) {
        if (strictRealApi) {
            console.error('[API] Strict real API request failed:', path, error);
            throw error;
        }
        // 연결 실패: 데모 모드로 안전 전환
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
    const safeGetStorage = (key, fallback = []) => {
        try {
            if (typeof localStorage === 'undefined') return fallback;
            const raw = localStorage.getItem(key);
            if (!raw) return fallback;
            const parsed = JSON.parse(raw);
            if (!Array.isArray(parsed) && key.endsWith('_templates') === false && key.endsWith('_projects') === false) return fallback;
            return parsed;
        } catch (_) {
            return fallback;
        }
    };
    const safeGetJson = (key, fallback = null) => {
        try {
            if (typeof localStorage === 'undefined') return fallback;
            const raw = localStorage.getItem(key);
            if (!raw) return fallback;
            return JSON.parse(raw);
        } catch (_) {
            return fallback;
        }
    };
    const safeSetStorage = (key, value) => {
        try {
            if (typeof localStorage !== 'undefined') {
                localStorage.setItem(key, JSON.stringify(value || []));
            }
        } catch (_) {}
    };
    const clone = (value) => JSON.parse(JSON.stringify(value || []));
    const now = new Date().toISOString();
    const method = (options.method || 'GET').toUpperCase();
    const body = (() => {
        try {
            return typeof options.body === 'string' ? JSON.parse(options.body || '{}') : {};
        } catch (_) {
            return {};
        }
    })();
    const basePath = path.split('?')[0];
    const linkInBioStorageKey = 'sf_demo_link_in_bio';
    const campaignStorageKey = 'sf_demo_sns_campaigns';
    const trendingStorageKey = 'sf_demo_sns_trending';
    const competitorStorageKey = 'sf_demo_sns_competitors';

    const ensureLinkInBioStore = () => {
        const existing = safeGetJson(linkInBioStorageKey, null);
        if (Array.isArray(existing) && existing.length > 0) {
            return existing;
        }
        const seed = [
            {
                id: 1,
                slug: 'creator-jin',
                title: 'Jin님의 링크 바이오',
                description: '브랜드 스토리와 콘텐츠로 연결합니다',
                theme: 'pink',
                links: [
                    { title: 'YouTube', url: 'https://youtube.com/@softfactory', icon: '🎬', clicks: 342 },
                    { title: 'Instagram', url: 'https://instagram.com/softfactory', icon: '📸', clicks: 128 },
                    { title: 'Store', url: 'https://shop.softfactory.com', icon: '🛍️', clicks: 95 }
                ],
                created_at: now
            },
            {
                id: 2,
                slug: 'daily-insight',
                title: 'Daily Insight',
                description: '일상 루틴과 노하우를 한 번에',
                theme: 'blue',
                links: [
                    { title: 'X', url: 'https://x.com/demo', icon: '🐦', clicks: 210 },
                    { title: 'Blog', url: 'https://blog.softfactory.com', icon: '✍️', clicks: 66 }
                ],
                created_at: now
            }
        ];
        safeSetStorage(linkInBioStorageKey, seed);
        return seed;
    };
    const getLinkInBioStatsSeed = (bioId) => ({
        total_clicks: 1000 + bioId * 57,
        total_views: 2200 + bioId * 143,
        daily_clicks: [45, 52, 38, 61, 73, 55, 48],
        top_links: [
            { title: 'YouTube', clicks: 260 + bioId * 11 },
            { title: 'Instagram', clicks: 140 + bioId * 7 },
            { title: 'Store', clicks: 88 + bioId * 5 }
        ],
        referrers: ['instagram.com', 'x.com', 'direct'],
        devices: { mobile: 72, desktop: 23, tablet: 5 }
    });
    const linkInBioMatch = basePath.match(/^\/api\/sns\/link(?:-|)inbio(\/([^/]+))?(\/stats)?$/);
    if (linkInBioMatch) {
        const list = ensureLinkInBioStore();
        const targetId = linkInBioMatch[2] ? Number(linkInBioMatch[2]) : null;
        const isStats = linkInBioMatch[3] === '/stats';

        if (!targetId && isStats) {
            const params = new URLSearchParams(path.split('?')[1] || '');
            const id = Number(params.get('lib_id') || 0);
            return { success: true, data: getLinkInBioStatsSeed(id || 1) };
        }

        if (basePath === '/api/sns/linkinbio' || basePath === '/api/sns/link-in-bio') {
            if (method === 'GET') {
                return { success: true, data: clone(list) };
            }
            if (method === 'POST') {
                const nextId = list.reduce((m, b) => Math.max(m, b.id), 0) + 1;
                const slug = String(body.slug || `bio-${nextId}`).trim();
                const created = {
                    id: nextId,
                    title: String(body.title || 'Untitled'),
                    description: String(body.description || ''),
                    theme: body.theme || 'light',
                    slug,
                    links: clone(body.links || []),
                    created_at: now
                };
                list.push(created);
                safeSetStorage(linkInBioStorageKey, list);
                return { success: true, data: created, message: 'Link in bio saved!' };
            }
        }

        if (targetId) {
            const index = list.findIndex((item) => item.id === targetId);
            if (index === -1) {
                return { success: false, error: 'Not found' };
            }
            if (isStats) {
                return { success: true, data: getLinkInBioStatsSeed(targetId) };
            }
            if (method === 'GET') {
                return { success: true, data: list[index], message: 'Link in bio loaded' };
            }
            if (method === 'PUT') {
                list[index] = {
                    ...list[index],
                    ...body,
                    id: targetId,
                    slug: body.slug || list[index].slug || `bio-${targetId}`,
                    updated_at: now
                };
                safeSetStorage(linkInBioStorageKey, list);
                return { success: true, data: list[index], message: 'Updated' };
            }
            if (method === 'DELETE') {
                const removed = list.splice(index, 1)[0];
                safeSetStorage(linkInBioStorageKey, list);
                return { success: true, data: removed, message: 'Deleted' };
            }
        }
    }

    if (basePath === '/api/sns/linkinbio') {
        // alias path compatibility (no hyphen)
        if (method === 'POST') {
            const fallback = ensureLinkInBioStore();
            const nextId = fallback.reduce((m, b) => Math.max(m, b.id), 0) + 1;
            const slug = String(body.slug || `bio-${nextId}`).trim();
            const created = {
                id: nextId,
                title: String(body.title || 'Untitled'),
                description: String(body.description || ''),
                theme: body.theme || 'light',
                slug,
                links: clone(body.links || []),
                created_at: now
            };
            fallback.push(created);
            safeSetStorage(linkInBioStorageKey, fallback);
            return { success: true, data: created, message: 'Link in bio saved!' };
        }
        if (method === 'GET') {
            return { success: true, data: clone(ensureLinkInBioStore()) };
        }
    }

    const ensureCampaignStore = () => {
        const existing = safeGetJson(campaignStorageKey, null);
        if (Array.isArray(existing) && existing.length > 0) {
            return existing;
        }
        const seed = [
            {
                id: 1,
                name: '봄 런칭 캠페인',
                description: '신상품 티저 콘텐츠 번들',
                target_platforms: ['instagram', 'tiktok'],
                start_date: '2026-03-01',
                end_date: '2026-03-31',
                status: 'active',
                post_count: 12,
                created_at: now
            },
            {
                id: 2,
                name: '리뷰 확장',
                description: '블로그/숏폼 동시 배포',
                target_platforms: ['youtube', 'instagram', 'blog'],
                start_date: '2026-02-10',
                end_date: '2026-02-28',
                status: 'completed',
                post_count: 6,
                created_at: now
            }
        ];
        safeSetStorage(campaignStorageKey, seed);
        return seed;
    };
    const campaignMatch = basePath.match(/^\/api\/sns\/campaigns\/(\d+)$/);
    if (basePath === '/api/sns/campaigns' || campaignMatch) {
        const list = ensureCampaignStore();
        if (basePath === '/api/sns/campaigns') {
            if (method === 'POST') {
                const nextId = list.reduce((m, item) => Math.max(m, item.id), 0) + 1;
                const created = {
                    id: nextId,
                    name: body.name || 'New Campaign',
                    description: body.description || '',
                    target_platforms: body.target_platforms || [],
                    start_date: body.start_date || now.slice(0, 10),
                    end_date: body.end_date || now.slice(0, 10),
                    status: body.status || 'active',
                    post_count: 0,
                    created_at: now
                };
                list.push(created);
                safeSetStorage(campaignStorageKey, list);
                return { success: true, campaign: created };
            }
            return { success: true, campaigns: clone(list), total: list.length };
        }
        if (campaignMatch) {
            const id = Number(campaignMatch[1]);
            const index = list.findIndex((item) => item.id === id);
            if (index === -1) {
                return { success: false, error: 'Campaign not found' };
            }
            if (method === 'GET') {
                return { success: true, campaign: list[index] };
            }
            if (method === 'PUT') {
                list[index] = { ...list[index], ...body, id };
                safeSetStorage(campaignStorageKey, list);
                return { success: true, campaign: list[index] };
            }
            if (method === 'DELETE') {
                const removed = list.splice(index, 1)[0];
                safeSetStorage(campaignStorageKey, list);
                return { success: true, campaign: removed };
            }
        }
    }

    if (basePath.startsWith('/api/sns/competitor/')) {
        const existing = safeGetJson(competitorStorageKey, null) || [];
        const username = decodeURIComponent(basePath.split('/').pop());
        const competitorIndex = existing.findIndex((item) => item.username === username);
        const competitorSeed = {
            username,
            platform: 'Instagram',
            followers: 120000 + (Math.floor(Math.random() * 280000)),
            follower_growth: 3.2,
            engagement_rate: 6.8,
            weekly_posts: 9,
            top_post_likes: 25000,
            tags: ['콘텐츠', '브랜딩', '릴스']
        };
        if (competitorIndex < 0) {
            existing.push(competitorSeed);
            safeSetStorage(competitorStorageKey, existing);
        }
        return { success: true, data: (competitorIndex >= 0 ? existing[competitorIndex] : competitorSeed) };
    }

    if (basePath.startsWith('/api/sns/trending')) {
        const params = new URLSearchParams(path.split('?')[1] || '');
        const platform = params.get('platform') || 'Instagram';
        const category = params.get('category') || '';
        const region = (params.get('region') || '').toUpperCase();
        const trendSeed = safeGetJson(trendingStorageKey, null) || [
            { tag: '#트렌드', growth: 45, posts: '1.2M', platform: 'Instagram' },
            { tag: '#콘텐츠', growth: 32, posts: '850K', platform: 'TikTok' },
            { tag: '#브랜딩', growth: 28, posts: '720K', platform: 'YouTube' }
        ];
        safeSetStorage(trendingStorageKey, trendSeed);
        const merged = trendSeed.map((item, index) => ({
            tag: item.tag,
            growth: item.growth,
            posts: item.posts,
            platform: item.platform || 'Instagram',
            category: item.category || category,
            country: item.country || region || 'GLOBAL',
            emoji: index === 0 ? '🔥' : index === 1 ? '🎬' : '📈'
        })).filter((item) => !platform || item.platform === platform || item.platform.toLowerCase() === platform.toLowerCase());

        if (merged.length === 0) {
            return {
                platform,
                category,
                trends: trendSeed
            };
        }
        return { platform, category, trends: merged };
    }

    const defaultTemplates = [
        {
            id: 'template_corporate',
            name: '브랜드 신뢰형',
            tone: 'professional',
            description: '명확한 메시지 구조와 깔끔한 타이포그래피 중심',
            slides: 8,
            structure: ['문제 제시', '인사이트', '핵심 제안', '실행 CTA'],
            design: {
                fontFamily: 'Inter',
                titleSize: 18,
                bodySize: 13,
                titleAlign: 'left',
                bodyAlign: 'left',
                titlePosition: 'top',
                textColor: '#f8fafc',
                accentColor: '#6366f1',
                backgroundColor: '#0f172a'
            },
            format: 'instagram-carousel-4-5',
            tags: ['신뢰', '브랜드', '정형']
        },
        {
            id: 'template_dynamic',
            name: '트렌드 반응형',
            tone: 'dynamic',
            description: '첫 장면 훅에 강한 문구와 반응형 컬러 배치',
            slides: 10,
            structure: ['임팩트 훅', '근거 제시', '숫자로 설득', '구매/문의 유도'],
            design: {
                fontFamily: 'Pretendard',
                titleSize: 20,
                bodySize: 13,
                titleAlign: 'center',
                bodyAlign: 'center',
                titlePosition: 'middle',
                textColor: '#ffffff',
                accentColor: '#f59e0b',
                backgroundColor: '#312e81'
            },
            format: 'instagram-feed-1-1',
            tags: ['트렌드', '반응형', '강한 훅']
        },
        {
            id: 'template_story',
            name: '브랜딩 스토리형',
            tone: 'narrative',
            description: '브랜드 이야기형 전개 + 감성 기반 전환',
            slides: 6,
            structure: ['챕터 1', '경험 제시', '혜택 요약', '행동 촉진'],
            design: {
                fontFamily: 'Noto Sans KR',
                titleSize: 19,
                bodySize: 12,
                titleAlign: 'left',
                bodyAlign: 'left',
                titlePosition: 'top',
                textColor: '#e2e8f0',
                accentColor: '#ec4899',
                backgroundColor: '#1e293b'
            },
            format: 'instagram-carousel-4-5',
            tags: ['브랜딩', '스토리', '감성']
        }
    ];
    const loadTemplates = () => {
        const stored = safeGetStorage('sf_cardnews_templates', null);
        const source = Array.isArray(stored) && stored.length ? stored : defaultTemplates;
        if (!stored || !stored.length) {
            safeSetStorage('sf_cardnews_templates', source);
        }
        return clone(source);
    };
    const loadProjects = () => safeGetStorage('sf_cardnews_projects', [
        {
            id: 101,
            title: '봄 시즌 브랜드 카드뉴스',
            accountIds: ['ig_account_01'],
            topic: '브랜드 리런칭 공지',
            tone: 'professional',
            slide_count: 8,
            status: 'scheduled',
            scheduled_at: '2026-03-06T09:30:00',
            created_at: '2026-03-03T01:20:00',
            last_post_url: '',
            templates: { used_template_id: 'template_corporate', score: 93 },
            channels: [{ platform: 'instagram', format: 'instagram-carousel-4-5', status: 'ready' }],
            preview: ['신규 서비스', '핵심 메시지', '고객 신뢰 지표', '참여 CTA']
        },
        {
            id: 102,
            title: '가맹점 이벤트 카드뉴스',
            accountIds: ['ig_account_02'],
            topic: '오픈 이벤트',
            tone: 'dynamic',
            slide_count: 10,
            status: 'published',
            scheduled_at: '2026-03-05T18:00:00',
            created_at: '2026-03-02T16:30:00',
            last_post_url: 'https://www.instagram.com/reel/placeholder',
            templates: { used_template_id: 'template_dynamic', score: 88 },
            channels: [{ platform: 'instagram', format: 'instagram-feed-1-1', status: 'done' }],
            preview: ['오픈 안내', '혜택', '혜택 조건', '바로가기']
        }
    ]);
    const saveProjects = (projects) => safeSetStorage('sf_cardnews_projects', projects);
    const parseJson = (raw, fallback = {}) => {
        try {
            return JSON.parse(raw || '{}') || fallback;
        } catch (_) {
            return fallback;
        }
    };
    const findById = (list, id) => list.find((item) => String(item.id) === String(id));

    // Platform
    if (path === '/api/platform/products') {
        return {
            'coocook': { slug: 'coocook', name: '쿠쿠크', description: 'Local food experiences', icon: '🍳', monthly_price: 39000 },
            'sns-auto': { slug: 'sns-auto', name: 'SNS 자동화', description: 'Social media automation', icon: '📱', monthly_price: 49000 },
            'review': { slug: 'review', name: '리뷰 캠페인', description: 'Brand reviews', icon: '⭐', monthly_price: 99000 },
            'ai-automation': { slug: 'ai-automation', name: 'AI 자동화', description: '24/7 AI employees', icon: '🤖', monthly_price: 89000 },
            'webapp-builder': { slug: 'webapp-builder', name: '웹앱 빌더', description: '8-week bootcamp', icon: '💻', monthly_price: 590000 },
            'instagram-cardnews': { slug: 'instagram-cardnews', name: '인스타그램 카드뉴스 자동화', description: 'AI 카드뉴스 생성과 다중 계정 자동 발행', icon: '📸', monthly_price: 79000 }

        };
    }
    if (path === '/api/platform/dashboard') {
        return {
            active_services: 6,
            total_spent: 195000,
            monthly_mrr: 276000,
            email: DEMO_USER.email,
            products: [
                { slug: 'coocook', name: '쿠쿠크', status: 'active', next_billing: '2026-03-24' },
                { slug: 'sns-auto', name: 'SNS 자동화', status: 'active', next_billing: '2026-03-24' },
                { slug: 'review', name: '리뷰 캠페인', status: 'active', next_billing: '2026-03-24' },
                { slug: 'ai-automation', name: 'AI 자동화', status: 'active', next_billing: '2026-03-24' },
                { slug: 'webapp-builder', name: '웹앱 빌더', status: 'completed', progress: 25 },
                { slug: 'instagram-cardnews', name: '인스타그램 카드뉴스 자동화', status: 'active', next_billing: '2026-03-24' }
            ]
        };
    }

    if (path === '/api/instagram-cardnews/accounts') {
        return [
            {
                id: 'ig_account_01',
                name: '메인 브랜드 계정',
                platform: 'Instagram',
                handle: '@softfactory_main',
                status: 'connected',
                followers: 18420,
                profileTone: 'trustworthy',
                businessType: 'B2B SaaS',
                audience: '브랜드 운영자, 마케팅 리더, 소상공인',
                contentPillars: ['브랜드 전략', '운영 자동화', '성장 사례'],
                preferredTemplateTags: ['브랜딩', '전략', '신뢰'],
                bestPostingWindow: '화-목 09:00~11:00',
                region: 'KR'
            },
            {
                id: 'ig_account_02',
                name: '로컬 매장 운영 계정',
                platform: 'Instagram',
                handle: '@softfactory_store',
                status: 'connected',
                followers: 7340,
                profileTone: 'friendly',
                businessType: 'Local Commerce',
                audience: '방문 고객, 동네 상권 고객, 재방문 유저',
                contentPillars: ['신메뉴/신상품', '매장 분위기', '방문 혜택'],
                preferredTemplateTags: ['이벤트', '매장운영', '친근함'],
                bestPostingWindow: '수-일 17:00~20:00',
                region: 'KR'
            },
            {
                id: 'ig_account_03',
                name: '광고 캠페인 계정',
                platform: 'Instagram',
                handle: '@softfactory_ad',
                status: 'pending',
                followers: 1020,
                profileTone: 'bold',
                businessType: 'Performance Marketing',
                audience: '신규 리드, 캠페인 유입 사용자',
                contentPillars: ['한정 혜택', '성과 지표', '캠페인 CTA'],
                preferredTemplateTags: ['캠페인', '전환', '광고'],
                bestPostingWindow: '월-금 12:00~14:00',
                region: 'KR'
            }
        ];
    }

    if (path === '/api/instagram-cardnews/templates' && options && options.method === 'POST') {
        const payload = parseJson(options.body, {});
        const templates = loadTemplates();
        const next = {
            id: payload.id || `template_${Date.now()}`,
            name: payload.name || '새 템플릿',
            tone: payload.tone || 'balanced',
            description: payload.description || '',
            slides: Number(payload.slides || payload.slide_count || 6),
            structure: Array.isArray(payload.structure) ? payload.structure : (typeof payload.structure === 'string' ? payload.structure.split('\n').map((line) => line.trim()).filter(Boolean) : ['슬라이드']),
            design: payload.design || {
                fontFamily: 'Inter',
                titleSize: 18,
                bodySize: 13,
                titleAlign: 'left',
                bodyAlign: 'left',
                titlePosition: 'top',
                textColor: '#f8fafc',
                accentColor: '#6366f1',
                backgroundColor: '#0f172a'
            },
            format: payload.format || 'instagram-carousel-4-5',
            tags: Array.isArray(payload.tags) ? payload.tags : []
        };
        templates.unshift(next);
        safeSetStorage('sf_cardnews_templates', templates);
        return next;
    }
    if (path.startsWith('/api/instagram-cardnews/templates/') && options && /^\/api\/instagram-cardnews\/templates\/[^/]+$/.test(path) && options.method === 'PUT') {
        const templateId = path.split('/').pop();
        const payload = parseJson(options.body, {});
        const templates = loadTemplates();
        const idx = templates.findIndex((template) => String(template.id) === String(templateId));
        if (idx === -1) return { ok: false, message: '템플릿을 찾을 수 없습니다.' };
        const target = templates[idx];
        const updated = Object.assign({}, target, payload, {
            id: target.id,
            structure: Array.isArray(payload.structure)
                ? payload.structure
                : (typeof payload.structure === 'string'
                    ? payload.structure.split('\n').map((line) => line.trim()).filter(Boolean)
                    : target.structure)
        });
        templates[idx] = updated;
        safeSetStorage('sf_cardnews_templates', templates);
        return updated;
    }
    if (path.startsWith('/api/instagram-cardnews/templates/') && options && /^\/api\/instagram-cardnews\/templates\/[^/]+$/.test(path) && options.method === 'DELETE') {
        const templateId = path.split('/').pop();
        const templates = loadTemplates().filter((template) => String(template.id) !== String(templateId));
        safeSetStorage('sf_cardnews_templates', templates);
        return { ok: true, removed: templateId };
    }
    if (path.match(/^\/api\/instagram-cardnews\/templates\/[^/]+$/)) {
        const templateId = path.split('/').pop();
        return findById(loadTemplates(), templateId) || null;
    }
    if (path === '/api/instagram-cardnews/templates') {
        return loadTemplates();
    }

    if (path === '/api/instagram-cardnews/dm-rules' && options && options.method === 'POST') {
        let payload = {};
        try {
            payload = options && options.body ? JSON.parse(options.body) : {};
        } catch (_) {
            payload = {};
        }
        return {
            id: Date.now(),
            keyword: payload.keyword || '키워드',
            reply: payload.reply || '안내 메시지',
            action: payload.action || 'notify',
            created_at: new Date().toISOString()
        };
    }
    if (path === '/api/instagram-cardnews/dm-rules') {
        return [
            { id: 1, keyword: '가격', reply: '안녕하세요! 현재 가격 정책은 DM 또는 링크드 바우처에서 확인 가능합니다. 원하시면 세부 견적서를 보내드릴게요.', action: 'approve' },
            { id: 2, keyword: '예약', reply: '예약은 DM로 날짜/시간 알려주시면 바로 확인 후 가용 시간을 공유해드리겠습니다.', action: 'approve' },
            { id: 3, keyword: '배송', reply: '안전한 배송을 위해 현재 운영 정책으로 즉시 확인 중입니다. 재문의 주시면 영업시간 내에 업데이트해드릴게요.', action: 'notify' }
        ];
    }

    if (path === '/api/instagram-cardnews/projects' && options && options.method === 'POST') {
        const payload = parseJson(options.body, {});
        const projects = loadProjects();
        const created = {
            id: payload.id || Date.now(),
            title: payload.title || `${payload.topic || '카드뉴스'} 프로젝트`,
            accountIds: Array.isArray(payload.accountIds) ? payload.accountIds : [],
            topic: payload.topic || '일반 주제',
            tone: payload.tone || 'balanced',
            slide_count: Number(payload.slide_count || 6),
            status: payload.scheduled_at ? 'scheduled' : 'ready',
            scheduled_at: payload.scheduled_at || null,
            created_at: now,
            last_post_url: '',
            templates: payload.templates || { used_template_id: payload.template_id || null },
            channels: Array.isArray(payload.channels) ? payload.channels : [],
            preview: Array.isArray(payload.preview) ? payload.preview : [],
            automation: payload.automation || null
        };
        projects.unshift(created);
        saveProjects(projects);
        return created;
    }
    if (path === '/api/instagram-cardnews/projects') {
        return loadProjects();
    }

    if (/^\/api\/instagram-cardnews\/projects\/(\d+)$/.test(path)) {
        const projects = generateMockData('/api/instagram-cardnews/projects');
        const projectId = Number(path.split('/').pop());
        return (projects || []).find((project) => Number(project.id) === projectId) || null;
    }

    if (/^\/api\/instagram-cardnews\/projects\/(\d+)\/publish$/.test(path) && options.method === 'POST') {
        const projectId = Number(path.split('/').slice(-2, -1)[0]);
        const projects = loadProjects();
        const target = projects.find((item) => Number(item.id) === projectId);
        if (target) {
            target.status = 'published';
            target.last_post_url = `https://softfactory.local/post/${projectId}`;
            saveProjects(projects);
        }
        return {
            id: projectId,
            status: 'publishing',
            channels: (target && target.channels) || [],
            published_at: new Date().toISOString(),
            message: '채널 발행 요청이 접수되었습니다.'
        };
    }

    if (path === '/api/instagram-cardnews/generate' && options.method === 'POST') {
        const payload = parseJson(options.body, {});
        const topic = payload.topic || '일반 주제';
        const slideCount = Number(payload.slide_count || 6);
        const channels = Array.isArray(payload.channels) ? payload.channels : [];
        const design = payload.design || {};
        const hasAiKey = !!(payload.ai && payload.ai.apiKey && payload.ai.apiKey.trim());
        if (!hasAiKey) {
            return {
                id: Date.now(),
                status: 'blocked',
                message: 'AI 키가 없어 생성이 제한됩니다. API 키를 등록해 주세요.',
                topic,
                slide_count: slideCount,
                account_ids: Array.isArray(payload.account_ids) ? payload.account_ids : []
            };
        }
        const slides = Array.from({ length: slideCount }).map((_, idx) => ({
            index: idx + 1,
            title: `${topic} - 핵심 ${idx + 1}`,
            body: `${topic}를 쉽고 간결하게 전달하는 문장 ${idx + 1}`,
            imagePrompt: `social media card slide ${idx + 1}, platform ${channels[0]?.platform || 'instagram'}, format ${channels[0]?.format || 'instagram-carousel-4-5'}, 색상 ${design.accentColor || '#6366f1'}, 폰트 ${design.fontFamily || 'Inter'}, 톤 ${payload.tone || 'balanced'}`
        }));
        const accountIds = Array.isArray(payload.account_ids) ? payload.account_ids : [];
        return {
            id: Date.now(),
            status: 'ready',
            title: `${topic} 카드뉴스`,
            topic,
            slide_count: slideCount,
            tone: payload.tone || 'balanced',
            account_ids: accountIds,
            channels,
            design,
            preview_text: `${topic} 주제에 맞춘 카드뉴스 초안이 준비되었습니다.`,
            slides,
            automation: payload.automation || null
        };
    }

    if (path === '/api/instagram-cardnews/simulate-dm' && options.method === 'POST') {
        let payload = {};
        try {
            payload = options && options.body ? JSON.parse(options.body) : {};
        } catch (_) {
            payload = {};
        }
        const incoming = (payload.message || '').toLowerCase();
        const rules = path === '/api/instagram-cardnews/dm-rules' ? [] : [
            { id: 1, keyword: '가격', reply: '안녕하세요! 최신 가격은 DM로 바로 안내드릴게요.', action: 'approve' },
            { id: 2, keyword: '예약', reply: '원하시는 날짜를 알려주시면 우선순위 예약 가능 시간을 안내드립니다.', action: 'approve' },
            { id: 3, keyword: '문의', reply: '문의 감사합니다. 영업시간 내로 상세 답변을 드리겠습니다.', action: 'notify' }
        ];
        const matched = rules.filter((rule) => incoming.includes(rule.keyword.toLowerCase()));
        return {
            message: payload.message || '',
            matched_count: matched.length,
            triggered: matched.map((rule) => ({ keyword: rule.keyword, suggestion: rule.reply, action: rule.action })),
            confidence: matched.length ? 0.89 : 0.32,
            recommended_action: matched.length ? 'auto_reply' : 'human_review'
        };
    }

    // 쿠쿠크
    if (path.startsWith('/api/coocook/chefs') && !path.includes('/')) {
        const chefs = [
            { id: 1, name: 'Chef Park', cuisine_type: 'Korean', location: 'Seoul', price_per_session: 150000, rating: 4.9, rating_count: 28, bio: 'Traditional Korean cuisine expert with 15 years experience', image: '?눖?눟', specialties: ['Hansik', 'Bibimbap', 'Kimchi'] },
            { id: 2, name: 'Chef Marco', cuisine_type: 'Italian', location: 'Seoul', price_per_session: 180000, rating: 4.8, rating_count: 35, bio: 'Authentic Italian pasta and risotto specialist', image: '?눒?눢', specialties: ['Pasta', 'Risotto', 'Tiramisu'] },
            { id: 3, name: 'Chef Tanaka', cuisine_type: 'Japanese', location: 'Seoul', price_per_session: 200000, rating: 4.9, rating_count: 42, bio: 'Master sushi chef trained in Tokyo', image: '?눓?눝', specialties: ['Sushi', 'Tempura', 'Kaiseki'] },
            { id: 4, name: 'Chef Dubois', cuisine_type: 'French', location: 'Seoul', price_per_session: 180000, rating: 4.7, rating_count: 22, bio: 'Trained in French culinary techniques', image: '?눏?눟', specialties: ['Cuisine Classique', 'Coq au Vin', 'Beef Bourguignon'] },
            { id: 5, name: 'Chef Garcia', cuisine_type: 'Mexican', location: 'Seoul', price_per_session: 140000, rating: 4.8, rating_count: 31, bio: 'Authentic Mexican street food master', image: '?눚?눦', specialties: ['Tacos', 'Mole', 'Ceviche'] }
        ];
        return { chefs: chefs, pages: 1, page: 1 };
    }
    if (path.match(/\/api\/coocook\/chefs\/\d+$/)) {
        const chefId = parseInt(path.match(/\/(\d+)$/)[1]);
        const chefs = {
            1: { id: 1, name: 'Chef Park', cuisine_type: 'Korean', location: 'Seoul', price_per_session: 150000, rating: 4.9, rating_count: 28, bio: 'Traditional Korean cuisine expert with 15 years experience', image: '?눖?눟', specialties: ['Hansik', 'Bibimbap', 'Kimchi'], reviews: [{ author: 'User A', rating: 5, comment: 'Amazing experience!' }, { author: 'User B', rating: 5, comment: 'Very professional' }] },
            2: { id: 2, name: 'Chef Marco', cuisine_type: 'Italian', location: 'Seoul', price_per_session: 180000, rating: 4.8, rating_count: 35, bio: 'Authentic Italian pasta and risotto specialist', image: '?눒?눢', specialties: ['Pasta', 'Risotto', 'Tiramisu'], reviews: [{ author: 'User C', rating: 5, comment: 'Delicious!' }] },
            3: { id: 3, name: 'Chef Tanaka', cuisine_type: 'Japanese', location: 'Seoul', price_per_session: 200000, rating: 4.9, rating_count: 42, bio: 'Master sushi chef trained in Tokyo', image: '?눓?눝', specialties: ['Sushi', 'Tempura', 'Kaiseki'], reviews: [{ author: 'User D', rating: 5, comment: 'Exceptional skills' }] },
            4: { id: 4, name: 'Chef Dubois', cuisine_type: 'French', location: 'Seoul', price_per_session: 180000, rating: 4.7, rating_count: 22, bio: 'Trained in French culinary techniques', image: '?눏?눟', specialties: ['Cuisine Classique', 'Coq au Vin', 'Beef Bourguignon'], reviews: [{ author: 'User E', rating: 5, comment: 'Classic French' }] },
            5: { id: 5, name: 'Chef Garcia', cuisine_type: 'Mexican', location: 'Seoul', price_per_session: 140000, rating: 4.8, rating_count: 31, bio: 'Authentic Mexican street food master', image: '?눚?눦', specialties: ['Tacos', 'Mole', 'Ceviche'], reviews: [{ author: 'User F', rating: 5, comment: 'Street food perfection' }] }
        };
        return chefs[chefId] || chefs[1];
    }
    if (path.startsWith('/api/coocook/bookings') && options.method === 'POST') {
        return { id: 1, status: 'confirmed', total_price: 300000, message: 'Booking confirmed!' };
    }
    if (path.match(/^\/api\/coocook\/bookings\/\d+$/) && options.method === 'PUT') {
        const bookingId = Number(path.match(/\/(\d+)$/)[1]);
        const payload = parseBody(options.body) || {};
        return {
            message: 'Booking updated',
            booking: {
                id: bookingId,
                chef_id: bookingId === 2 ? 2 : 1,
                chef_name: bookingId === 2 ? 'Chef Marco' : 'Chef Park',
                chef_avatar: bookingId === 2 ? '🍝' : '🍳',
                cuisine: bookingId === 2 ? 'Italian' : 'Korean',
                location: 'Seoul',
                booking_date: payload.booking_date ? String(payload.booking_date).split('T')[0] : (bookingId === 2 ? '2026-02-28' : '2026-03-01'),
                duration_hours: Number(payload.duration_hours || (bookingId === 2 ? 3 : 2)),
                status: payload.status || (bookingId === 2 ? 'completed' : 'confirmed'),
                total_price: Number(payload.duration_hours || (bookingId === 2 ? 3 : 2)) * 150000,
                special_requests: payload.special_requests || '',
                payment_status: payload.status === 'cancelled' ? 'pending' : 'paid',
                created_at: '2026-02-24T10:00:00'
            }
        };
    }
    if (path === '/api/coocook/bookings') {
        return [
            { id: 1, chef_id: 1, chef_name: 'Chef Park', booking_date: '2026-03-01', duration_hours: 2, status: 'confirmed', total_price: 300000 },
            { id: 2, chef_id: 2, chef_name: 'Chef Marco', booking_date: '2026-02-28', duration_hours: 3, status: 'completed', total_price: 540000 }
        ];
    }

    // 쿠쿠크 Search
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

    // 쿠쿠크 Nutrition
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

    // 쿠쿠크 Shopping List
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

    // 쿠쿠크 Feed & Recommendations
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

    // 쿠쿠크 Menus
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

    // SNS 자동화
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

    // 리뷰 캠페인
    if (path.startsWith('/api/review/campaigns') && !path.includes('/')) {
        return {
            campaigns: [
                { id: 1, title: 'Skincare Product Launch', brand: 'GlowSkin Pro', category: 'beauty', platform: 'revu', reward_value: '50,000원', max_reviewers: 20, current_reviewers: 5, deadline: '2026-03-24', status: 'active', applications: 5, image: '🍀', profit_score: 94 },
                { id: 2, title: 'Coffee Brand 리뷰', brand: 'BeanBliss', category: 'food', platform: 'reviewnote', reward_value: '30,000원', max_reviewers: 15, current_reviewers: 3, deadline: '2026-03-19', status: 'active', applications: 3, image: '☕', profit_score: 82 },
                { id: 3, title: 'Tech Gadget 리뷰', brand: 'SmartHub X3', category: 'tech', platform: 'gangnam', reward_value: '25,000원', max_reviewers: 10, current_reviewers: 8, deadline: '2026-03-14', status: 'active', applications: 8, image: '🔧', profit_score: 89 }
            ]
        };
    }
    if (path.match(/\/api\/review\/campaigns\/\d+$/) || path.match(/\/api\/review\/campaign_detail\/\d+$/)) {
        const campaignId = parseInt(path.match(/\/(\d+)$/)[1]);
        const campaigns = {
            1: { id: 1, title: 'Skincare Product Launch', brand: 'GlowSkin Pro', category: 'beauty', platform: 'revu', reward_value: '50,000원', description: '리뷰 our new skincare line with active vitamin C. High conversion potential for beauty bloggers.', deadline: '2026-03-24', status: 'active', image_url: 'https://images.unsplash.com/photo-1556228720-195a672e8a03?auto=format&fit=crop&q=80&w=800' },
            2: { id: 2, title: 'Coffee Brand 리뷰', brand: 'BeanBliss', category: 'food', platform: 'reviewnote', reward_value: '30,000원', description: 'Try our premium arabica coffee beans and write a sensory review.', deadline: '2026-03-19', status: 'active', image_url: 'https://images.unsplash.com/photo-1509042239860-f550ce710b93?auto=format&fit=crop&q=80&w=800' },
            3: { id: 3, title: 'Tech Gadget 리뷰', brand: 'SmartHub X3', category: 'tech', platform: 'gangnam', reward_value: '25,000원', description: '리뷰 our newest smart home hub. High competition, expert tech reviews required.', deadline: '2026-03-14', status: 'active', image_url: 'https://images.unsplash.com/photo-1558346489-19413928158b?auto=format&fit=crop&q=80&w=800' }
        };
        return campaigns[campaignId] || campaigns[1];
    }
    if (path === '/api/review/my-applications') {
        return [
            { id: 1, campaign_id: 1, status: 'approved', message: 'Great influencer!' }
        ];
    }

    // AI 자동화
    if (path === '/api/ai-automation/plans') {
        return {
            'starter': { name: 'Starter', price: 89000, hours_saved: '15/month', features: ['1 AI Employee', 'Email automation', 'Basic support'] },
            'ambassador': { name: 'Ambassador', price: 189000, hours_saved: '40/month', features: ['3 AI Employees', 'All automations', '24/7 support'] },
            'enterprise': { name: 'Enterprise', price: 490000, hours_saved: '100+/month', features: ['Unlimited AI Employees', 'Custom workflows', 'Dedicated support'] }
        };
    }
    if (path === '/api/ai-automation/scenarios') {
        return [
            { id: 1, name: 'Email Response', category: 'email', complexity: 'easy', estimated_savings: 15, icon: '?벁' },
            { id: 2, name: 'Social Media Posting', category: 'social', complexity: 'medium', estimated_savings: 20, icon: '?벑' },
            { id: 3, name: 'Customer Support Bot', category: 'customer_service', complexity: 'advanced', estimated_savings: 30, icon: '?뮠' },
            { id: 4, name: 'Data Entry Automation', category: 'data', complexity: 'medium', estimated_savings: 25, icon: '?뱤' },
            { id: 5, name: 'Schedule 관리', category: 'calendar', complexity: 'easy', estimated_savings: 10, icon: '?뱟' }
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
        return { active_employees: 1, total_monthly_savings_hours: 15, estimated_annual_savings: '95,800,000' };
    }

    // 웹앱 빌더
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
                { name: '쿠쿠크', price: 39000, next_billing: '2026-03-24' },
                { name: 'SNS 자동화', price: 49000, next_billing: '2026-03-24' },
                { name: '리뷰 캠페인', price: 99000, next_billing: '2026-03-24' },
                { name: 'AI 자동화', price: 89000, next_billing: '2026-03-24' }
            ]
        };
    }
    if (path === '/api/payment/history') {
        return [
            { id: 1, date: '2026-02-24', service: 'Multi-Service Bundle', amount: 276000, status: 'paid' },
            { id: 2, date: '2026-01-24', service: 'Multi-Service Bundle', amount: 276000, status: 'paid' },
            { id: 3, date: '2026-01-01', service: '쿠쿠크 + SNS 자동화', amount: 88000, status: 'paid' }
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
            { id: 1, product: '쿠쿠크', status: 'active', current_period_end: '2026-03-24', price: 39000 },
            { id: 2, product: 'SNS 자동화', status: 'active', current_period_end: '2026-03-24', price: 49000 },
            { id: 3, product: '리뷰 캠페인', status: 'active', current_period_end: '2026-03-24', price: 99000 },
            { id: 4, product: 'AI 자동화', status: 'active', current_period_end: '2026-03-24', price: 89000 }
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
        const enrollmentEndDate = '2026-04-21';
        const remainingDays = Math.max(
            0,
            Math.ceil((new Date(`${enrollmentEndDate}T23:59:59`).getTime() - Date.now()) / 86400000)
        );
        return [
            { id: 1, plan: 'weekday', status: 'in_progress', progress: 25, start: '2026-02-24', end: enrollmentEndDate, days_remaining: remainingDays }
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

    // 리뷰 Aggregated
    if (path.startsWith('/api/review/aggregated')) {
        return {
            success: true,
            data: {
                listings: [
                    { id: 101, title: '스킨케어 제품 체험단', brand: 'GlowSkin', category: 'beauty', reward_value: 150000, source_platform: '리뷰플랫폼', deadline: new Date(Date.now() + 5 * 86400000).toISOString(), url: '#', image_url: null, applicants: 45 },
                    { id: 102, title: '카페 신메뉴 시식단', brand: 'BeanBliss', category: 'food', reward_value: 50000, source_platform: '블로그존', deadline: new Date(Date.now() + 12 * 86400000).toISOString(), url: '#', image_url: null, applicants: 22 },
                    { id: 103, title: '스마트기기 신제품 리뷰', brand: 'SmartHub', category: 'tech', reward_value: 200000, source_platform: '커뮤니티A', deadline: new Date(Date.now() + 3 * 86400000).toISOString(), url: '#', image_url: null, applicants: 78 },
                    { id: 104, title: '여행 상품 후기 캠페인', brand: 'TravelPro', category: 'travel', reward_value: 100000, source_platform: '리뷰플랫폼', deadline: new Date(Date.now() + 8 * 86400000).toISOString(), url: '#', image_url: null, applicants: 33 },
                    { id: 105, title: '피트니스 굿즈 체험단', brand: 'FlexFit', category: 'home', reward_value: 75000, source_platform: '블로그존', deadline: new Date(Date.now() + 15 * 86400000).toISOString(), url: '#', image_url: null, applicants: 18 },
                    { id: 106, title: '디저트 브랜드 체험단', brand: 'ChocoLux', category: 'food', reward_value: 60000, source_platform: '커뮤니티A', deadline: new Date(Date.now() + 2 * 86400000).toISOString(), url: '#', image_url: null, applicants: 55 }
                ],
                pages: 3,
                total: 36,
                last_scraped: new Date().toISOString()
            }
        };
    }
    // SNS AI Generate Content
    if (path === '/api/sns/ai/generate' && options.method === 'POST') {
        const body = JSON.parse(options.body || '{}');
        const topic = body.topic || '브랜드 콘텐츠 주제';
        const tone = body.tone || 'professional';

        const toneMap = {
            professional: '전문적이고 신뢰감 있는',
            casual: '친근하고 부드러운',
            humorous: '위트 있고 가벼운',
            inspiring: '동기부여 중심'
        };

        return {
            content: `[AI 생성본] ${toneMap[tone]} 톤으로 ${topic} 내용을 작성했습니다.\n\n메시지 초안:\n1. 핵심 메시지를 한 번에 전달합니다.\n2. 고객이 궁금한 포인트를 반영합니다.\n3. CTA를 명확하게 넣어 반응을 유도합니다.`,
            hashtags: '#브랜드 #마케팅 #' + topic.replace(/\s/g, '') + ' #콘텐츠 #성과',
            suggestions: [
                '오류 가능성 있는 표현은 2~3개 정도만 줄여주세요.',
                platform + ' 최적화로 CTA와 해시태그를 교체하면 성과 개선에 유리합니다.',
                '이미지는 6~8장 범위에서 업로드 추천.'
            ],
            estimated_engagement: { likes: '120-180', comments: '15-25', shares: '8-12' }
        };
    }
    // SNS AI Hashtags
    if (path === '/api/sns/ai/hashtags' && options.method === 'POST') {
        return {
            hashtags: ['#브랜드', '#리뷰', '#콘텐츠', '#성과', '#성과분석', '#마케팅', '#SNS', '#트렌드'],
            trending: ['#AI', '#트렌드', '#디지털마케팅'],
            platform_specific: ['#인스타그램', '#유튜브', '#콘텐츠전략']
        };
    }
    // SNS AI Optimize
    if (path === '/api/sns/ai/optimize' && options.method === 'POST') {
        return {
            optimized_content: 'Optimized version of your content...',
            improvements: [
                { type: 'length', suggestion: '분량을 150자 이내로 줄여 가독성을 높입니다.' },
                { type: 'hashtags', suggestion: '해시태그는 5~8개로 제한해 가독성을 확보합니다.' },
                { type: 'cta', suggestion: '마무리에 명확한 행동 유도 문구를 추가하세요.' }
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
                    { name: '쿠쿠크', users: 2450, revenue: 98000 },
                    { name: 'SNS 자동화', users: 1850, revenue: 90500 },
                    { name: '리뷰', users: 2042, revenue: 202000 },
                    { name: 'AI 자동화', users: 1600, revenue: 142400 },
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

function getLoginPageUrl() {
    const next = typeof window !== 'undefined' && window.location
        ? window.location.pathname + (window.location.search || '')
        : '';
    const loginPath = '/web/platform/login.html';
    return next && next !== loginPath
        ? `${loginPath}?next=${encodeURIComponent(next)}`
        : loginPath;
}

function requireAuth() {
    if (!getToken() && !isDemoMode()) {
        window.location.href = getLoginPageUrl();
    }
}

function hasAuthSession() {
    return !!getToken() || isDemoMode();
}

function logout() {
    if (isDemoMode()) {
        disableDemoMode();
    } else {
        localStorage.clear();
    }
    window.location.href = getLoginPageUrl();
}

window.hasAuthSession = hasAuthSession;

function setupSessionActionButton(buttonId = "sessionActionButton") {
    const button = document.getElementById(buttonId);
    if (!button) return;

    if (hasAuthSession()) {
        button.textContent = "로그아웃";
        button.onclick = logout;
    } else {
        button.textContent = "플랫폼 로그인";
        button.onclick = () => {
            window.location.href = getLoginPageUrl();
        };
    }
}

window.setupSessionActionButton = setupSessionActionButton;

// ============ UI HELPERS ============

/**
 * Format amount as Korean Won
 * @param {number} amount - Amount to format
 * @returns {string} Formatted string like "₩9,000"
 */
function formatKRW(amount) {
    if (amount >= 1000000) {
        return `${(amount / 1000000).toFixed(1)}M`;
    }
    return `₩${amount.toLocaleString('ko-KR')}`;
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
        active: '<span class="inline-flex items-center px-2 py-1 text-xs font-medium rounded-full bg-green-900 text-green-200">활성</span>',
        pending: '<span class="inline-flex items-center px-2 py-1 text-xs font-medium rounded-full bg-yellow-900 text-yellow-200">대기</span>',
        completed: '<span class="inline-flex items-center px-2 py-1 text-xs font-medium rounded-full bg-blue-900 text-blue-200">완료</span>',
        approved: '<span class="inline-flex items-center px-2 py-1 text-xs font-medium rounded-full bg-green-900 text-green-200">승인</span>',
        rejected: '<span class="inline-flex items-center px-2 py-1 text-xs font-medium rounded-full bg-red-900 text-red-200">거부</span>',
        draft: '<span class="inline-flex items-center px-2 py-1 text-xs font-medium rounded-full bg-slate-700 text-slate-200">임시저장</span>',
        published: '<span class="inline-flex items-center px-2 py-1 text-xs font-medium rounded-full bg-indigo-900 text-indigo-200">공개됨</span>',
        scheduled: '<span class="inline-flex items-center px-2 py-1 text-xs font-medium rounded-full bg-purple-900 text-purple-200">예약</span>',
        training: '<span class="inline-flex items-center px-2 py-1 text-xs font-medium rounded-full bg-cyan-900 text-cyan-200">학습중</span>',
        deployed: '<span class="inline-flex items-center px-2 py-1 text-xs font-medium rounded-full bg-emerald-900 text-emerald-200">배포됨</span>',
        building: '<span class="inline-flex items-center px-2 py-1 text-xs font-medium rounded-full bg-orange-900 text-orange-200">빌드중</span>',
        in_progress: '<span class="inline-flex items-center px-2 py-1 text-xs font-medium rounded-full bg-blue-900 text-blue-200">진행중</span>'
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
                <button class="flex-1 px-4 py-2 bg-slate-700 hover:bg-slate-600 text-slate-100 rounded-lg transition" onclick="this.closest('.fixed').remove(); window.confirmResult = false;">취소</button>
                <button class="flex-1 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg transition" onclick="this.closest('.fixed').remove(); window.confirmResult = true;">확인</button>
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
        showError('?ㅻ쪟 諛쒖깮: ' + event.error.message);
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
    const data = await response.json();
    if (data?.user && isAdminUser(data.user)) {
        enableAdminFixtureMode(data.user);
    } else {
        disableAdminFixtureMode();
    }
    return data;
}

async function getMe() {
    const response = await apiFetch('/api/auth/me');
    return response.json();
}

async function parseJsonOrThrow(response, endpoint) {
    const data = await response.json();
    if (!response.ok) {
        throw new Error(data?.error || data?.message || `Request failed for ${endpoint}`);
    }
    if (data && typeof data === 'object' && data.status === 'mock') {
        throw new Error(`Mock backend detected for ${endpoint}`);
    }
    if (data && typeof data === 'object' && data.status === 'upstream-required') {
        throw new Error(`Real backend upstream is not configured for ${endpoint}`);
    }
    if (data && typeof data === 'object' && data.status === 'upstream-error') {
        throw new Error(data.message || `Upstream error for ${endpoint}`);
    }
    return data;
}

// Platform
async function getProducts() {
    const response = await apiFetch('/api/platform/products');
    return parseJsonOrThrow(response, '/api/platform/products');
}

async function getDashboard() {
    const response = await apiFetch('/api/platform/dashboard');
    return parseJsonOrThrow(response, '/api/platform/dashboard');
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

// 쿠쿠크
async function getChefs(page = 1, cuisine = '', location = '') {
    let query = `?page=${page}`;
    if (cuisine) query += `&cuisine=${cuisine}`;
    if (location) query += `&location=${location}`;
    const response = await apiFetch(`/api/coocook/chefs${query}`);
    return parseJsonOrThrow(response, '/api/coocook/chefs');
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
    return parseJsonOrThrow(response, '/api/coocook/bookings');
}

async function updateCooCookBooking(bookingId, payload) {
    const response = await apiFetch(`/api/coocook/bookings/${bookingId}`, {
        method: 'PUT',
        body: JSON.stringify(payload)
    });
    return parseJsonOrThrow(response, `/api/coocook/bookings/${bookingId}`);
}

// 쿠쿠크 Phase 2-3: Search, Nutrition, Shopping List, Feed, Recommendations

async function search쿠쿠크(q = '', category = '', cuisine = '', priceMin = null, priceMax = null, ratingMin = null, page = 1) {
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

async function get쿠쿠크Categories() {
    const response = await apiFetch('/api/coocook/categories');
    return response.json();
}

async function get쿠쿠크Cuisines() {
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

async function get쿠쿠크Feed() {
    const response = await apiFetch('/api/coocook/feed');
    return response.json();
}

async function get쿠쿠크Recommendations(limit = 6) {
    const response = await apiFetch(`/api/coocook/recommendations?limit=${limit}`);
    return response.json();
}

async function get쿠쿠크Menus(chefId = null, category = '', cuisine = '') {
    let query = '?';
    if (chefId) query += `chef_id=${chefId}&`;
    if (category) query += `category=${encodeURIComponent(category)}&`;
    if (cuisine) query += `cuisine=${encodeURIComponent(cuisine)}&`;
    const response = await apiFetch(`/api/coocook/menus${query}`);
    return response.json();
}

// SNS 자동화
async function getSNSAccounts() {
    const response = await apiFetch('/api/sns/accounts');
    return parseJsonOrThrow(response, '/api/sns/accounts');
}

async function createSNSAccount(platform, accountName) {
    const response = await apiFetch('/api/sns/accounts', {
        method: 'POST',
        body: JSON.stringify({ platform, account_name: accountName })
    });
    return parseJsonOrThrow(response, '/api/sns/accounts');
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
    return parseJsonOrThrow(response, '/api/sns/posts');
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
    return parseJsonOrThrow(response, '/api/sns/posts');
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
    return parseJsonOrThrow(response, '/api/sns/templates');
}

async function getWordPressSites() {
    const response = await apiFetch('/api/sns/wordpress/sites');
    return parseJsonOrThrow(response, '/api/sns/wordpress/sites');
}

async function saveWordPressSite(payload) {
    const response = await apiFetch('/api/sns/wordpress/sites', {
        method: 'POST',
        body: JSON.stringify(payload)
    });
    return parseJsonOrThrow(response, '/api/sns/wordpress/sites');
}

async function testWordPressSite(siteId) {
    const response = await apiFetch(`/api/sns/wordpress/sites/${siteId}/test`, {
        method: 'POST'
    });
    return parseJsonOrThrow(response, `/api/sns/wordpress/sites/${siteId}/test`);
}

async function getWordPressTemplates() {
    const response = await apiFetch('/api/sns/wordpress/templates');
    return parseJsonOrThrow(response, '/api/sns/wordpress/templates');
}

async function getWordPressRuns(limit = 20) {
    const response = await apiFetch(`/api/sns/wordpress/runs?limit=${limit}`);
    return parseJsonOrThrow(response, '/api/sns/wordpress/runs');
}

async function auditWordPressBrief(brief) {
    const response = await apiFetch('/api/sns/wordpress/content-audit', {
        method: 'POST',
        body: JSON.stringify({ brief })
    });
    return parseJsonOrThrow(response, '/api/sns/wordpress/content-audit');
}

async function createWordPressPost(payload) {
    const response = await apiFetch('/api/sns/wordpress/posts', {
        method: 'POST',
        body: JSON.stringify(payload)
    });
    return parseJsonOrThrow(response, '/api/sns/wordpress/posts');
}

// 리뷰
async function fetchReviewCampaigns(page = 1, category = '') {
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

async function getMyApplicationsLegacy() {
    const response = await apiFetch('/api/review/my-applications');
    return response.json();
}

// AI 자동화
async function getAIPlans() {
    const response = await apiFetch('/api/ai-automation/plans');
    return parseJsonOrThrow(response, '/api/ai-automation/plans');
}

async function getAIScenarios(category = '') {
    let query = '';
    if (category) query = `?category=${category}`;
    const response = await apiFetch(`/api/ai-automation/scenarios${query}`);
    return parseJsonOrThrow(response, '/api/ai-automation/scenarios');
}

async function getAIEmployees() {
    const response = await apiFetch('/api/ai-automation/employees');
    return parseJsonOrThrow(response, '/api/ai-automation/employees');
}

async function createAIEmployee(name, scenario, instructions) {
    const response = await apiFetch('/api/ai-automation/employees', {
        method: 'POST',
        body: JSON.stringify({
            name,
            scenario_type: scenario,
            description: instructions
        })
    });
    return parseJsonOrThrow(response, '/api/ai-automation/employees');
}

async function getAIEmployeeDetail(employeeId) {
    const response = await apiFetch(`/api/ai-automation/employees/${employeeId}`);
    return parseJsonOrThrow(response, `/api/ai-automation/employees/${employeeId}`);
}

async function deleteAIEmployee(employeeId) {
    const response = await apiFetch(`/api/ai-automation/employees/${employeeId}`, {
        method: 'DELETE'
    });
    return parseJsonOrThrow(response, `/api/ai-automation/employees/${employeeId}`);
}

async function deployAIEmployee(employeeId, savingsHours = 10) {
    const response = await apiFetch(`/api/ai-automation/employees/${employeeId}/deploy`, {
        method: 'POST',
        body: JSON.stringify({ savings_hours: savingsHours })
    });
    return parseJsonOrThrow(response, `/api/ai-automation/employees/${employeeId}/deploy`);
}

async function activateAIEmployee(employeeId) {
    const response = await apiFetch(`/api/ai-automation/employees/${employeeId}/activate`, {
        method: 'POST'
    });
    return parseJsonOrThrow(response, `/api/ai-automation/employees/${employeeId}/activate`);
}

async function getAIAutomationDashboard() {
    const response = await apiFetch('/api/ai-automation/dashboard');
    return parseJsonOrThrow(response, '/api/ai-automation/dashboard');
}

async function getAIAnalytics() {
    const response = await apiFetch('/api/ai-automation/analytics');
    return response.json();
}

// 웹앱 빌더
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

function assertRealCardNewsArray(data, endpoint) {
    if (!Array.isArray(data)) {
        if (data && typeof data === 'object' && data.status === 'mock') {
            throw new Error(`Mock backend detected for ${endpoint}`);
        }
        throw new Error(`Unexpected response shape for ${endpoint}`);
    }
    return data;
}

function assertRealCardNewsObject(data, endpoint) {
    if (!data || typeof data !== 'object' || Array.isArray(data)) {
        throw new Error(`Unexpected response shape for ${endpoint}`);
    }
    if (data.status === 'mock') {
        throw new Error(`Mock backend detected for ${endpoint}`);
    }
    return data;
}

// 인스타그램 카드뉴스 자동화
async function getInstagramCardNewsAccounts() {
    const response = await apiFetch('/api/instagram-cardnews/accounts', { strictRealApi: true });
    return assertRealCardNewsArray(await response.json(), '/api/instagram-cardnews/accounts');
}

async function getInstagramCardNewsTemplates() {
    const response = await apiFetch('/api/instagram-cardnews/templates', { strictRealApi: true });
    return assertRealCardNewsArray(await response.json(), '/api/instagram-cardnews/templates');
}

async function createInstagramCardNewsTemplate(templateData) {
    const response = await apiFetch('/api/instagram-cardnews/templates', {
        method: 'POST',
        body: JSON.stringify(templateData),
        strictRealApi: true
    });
    return assertRealCardNewsObject(await response.json(), '/api/instagram-cardnews/templates');
}

async function updateInstagramCardNewsTemplate(templateId, templateData) {
    const response = await apiFetch(`/api/instagram-cardnews/templates/${templateId}`, {
        method: 'PUT',
        body: JSON.stringify(templateData),
        strictRealApi: true
    });
    return assertRealCardNewsObject(await response.json(), `/api/instagram-cardnews/templates/${templateId}`);
}

async function deleteInstagramCardNewsTemplate(templateId) {
    const response = await apiFetch(`/api/instagram-cardnews/templates/${templateId}`, {
        method: 'DELETE',
        strictRealApi: true
    });
    return assertRealCardNewsObject(await response.json(), `/api/instagram-cardnews/templates/${templateId}`);
}

async function getInstagramCardNewsTemplate(templateId) {
    const response = await apiFetch(`/api/instagram-cardnews/templates/${templateId}`, { strictRealApi: true });
    return assertRealCardNewsObject(await response.json(), `/api/instagram-cardnews/templates/${templateId}`);
}

async function createInstagramCardNewsProject(payload) {
    const response = await apiFetch('/api/instagram-cardnews/projects', {
        method: 'POST',
        body: JSON.stringify(payload),
        strictRealApi: true
    });
    return assertRealCardNewsObject(await response.json(), '/api/instagram-cardnews/projects');
}

async function getInstagramCardNewsDmRules() {
    const response = await apiFetch('/api/instagram-cardnews/dm-rules', { strictRealApi: true });
    return assertRealCardNewsArray(await response.json(), '/api/instagram-cardnews/dm-rules');
}

async function createInstagramCardNewsRule(ruleData) {
    const response = await apiFetch('/api/instagram-cardnews/dm-rules', {
        method: 'POST',
        body: JSON.stringify(ruleData),
        strictRealApi: true
    });
    return assertRealCardNewsObject(await response.json(), '/api/instagram-cardnews/dm-rules');
}

async function getInstagramCardNewsProjects() {
    const response = await apiFetch('/api/instagram-cardnews/projects', { strictRealApi: true });
    return assertRealCardNewsArray(await response.json(), '/api/instagram-cardnews/projects');
}

async function getInstagramCardNewsProject(projectId) {
    const response = await apiFetch(`/api/instagram-cardnews/projects/${projectId}`, { strictRealApi: true });
    return assertRealCardNewsObject(await response.json(), `/api/instagram-cardnews/projects/${projectId}`);
}

async function generateInstagramCardNews(payload) {
    const response = await apiFetch('/api/instagram-cardnews/generate', {
        method: 'POST',
        body: JSON.stringify(payload),
        strictRealApi: true
    });
    return assertRealCardNewsObject(await response.json(), '/api/instagram-cardnews/generate');
}

async function publishInstagramCardNewsJob(projectId) {
    const response = await apiFetch(`/api/instagram-cardnews/projects/${projectId}/publish`, {
        method: 'POST',
        strictRealApi: true
    });
    return assertRealCardNewsObject(await response.json(), `/api/instagram-cardnews/projects/${projectId}/publish`);
}

async function simulateInstagramDM(payload) {
    const response = await apiFetch('/api/instagram-cardnews/simulate-dm', {
        method: 'POST',
        body: JSON.stringify(payload),
        strictRealApi: true
    });
    return assertRealCardNewsObject(await response.json(), '/api/instagram-cardnews/simulate-dm');
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
            if (isAdminUser(data.user)) {
                enableAdminFixtureMode(data.user);
            } else {
                disableAdminFixtureMode();
            }
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
async function getTrending(platform, category = null, region = null) {
    try {
        const params = [];
        if (platform) params.push(`platform=${encodeURIComponent(platform)}`);
        if (region) params.push(`region=${encodeURIComponent(region)}`);
        if (category) params.push(`category=${encodeURIComponent(category)}`);
        const query = params.length ? `?${params.join('&')}` : '';
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
async function getCampaigns(page = 1, category = '') {
    try {
        return await fetchReviewCampaigns(page, category);
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
 * @param {Object} data - 지원 data {message, sns_link, follower_count}
 * @returns {Promise<Object>} 지원 confirmation
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
        showSuccess('지원 submitted successfully');
        return result;
    } catch (error) {
        showError('지원 failed: ' + error.message);
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
        showSuccess('리뷰 account created successfully');
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
        showSuccess('리뷰 account updated successfully');
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
        showSuccess('리뷰 account deleted successfully');
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
    localStorage.removeItem(ADMIN_FIXTURE_KEY);
    localStorage.removeItem(ADMIN_FIXTURE_SEEDED_KEY);
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
 * Global AI Status Widget는 모든 페이지에 표시됩니다.
 * API 연결 상태, AI 사용 가능 상태, 마지막 동기화 시각을 표시합니다.
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
    const lastSync = _sfLastSyncTime ? formatDate(_sfLastSyncTime, 'relative') : '없음';
    const baseUrl = getResolvedApiBase();

    if (_sfAiWidgetOpen) {
        widget.innerHTML = `
            <div style="background:linear-gradient(135deg,rgba(30,41,59,0.95),rgba(15,23,42,0.98));border:1px solid ${isLive ? 'rgba(16,185,129,0.4)' : 'rgba(245,158,11,0.4)'};border-radius:16px;padding:16px;width:280px;box-shadow:0 20px 50px rgba(0,0,0,0.5);backdrop-filter:blur(12px);">
                <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;">
                    <span style="font-size:13px;font-weight:700;color:#f1f5f9;">시스템 상태</span>
                    <button onclick="_sfAiWidgetOpen=false;_sfRenderAiStatusWidget();" style="background:none;border:none;color:#94a3b8;cursor:pointer;font-size:16px;padding:0 4px;">&times;</button>
                </div>
                <div style="display:flex;flex-direction:column;gap:8px;">
                    <div style="display:flex;align-items:center;justify-content:space-between;padding:8px 10px;background:rgba(${isLive ? '16,185,129' : '245,158,11'},0.1);border-radius:8px;">
                        <span style="font-size:11px;color:#94a3b8;">API 상태</span>
                        <span style="font-size:11px;font-weight:600;color:${isLive ? '#4ade80' : '#fbbf24'};">${isLive ? '연결됨' : '데모 모드'}</span>
                    </div>
                    <div style="display:flex;align-items:center;justify-content:space-between;padding:8px 10px;background:rgba(139,92,246,0.1);border-radius:8px;">
                        <span style="font-size:11px;color:#94a3b8;">AI 상태</span>
                        <span style="font-size:11px;font-weight:600;color:${isLive ? '#a78bfa' : '#94a3b8'};">${isLive ? '사용 가능' : '시뮬레이션 모드'}</span>
                    </div>
                    <div style="display:flex;align-items:center;justify-content:space-between;padding:8px 10px;background:rgba(30,41,59,0.5);border-radius:8px;">
                        <span style="font-size:11px;color:#94a3b8;">마지막 동기화</span>
                        <span style="font-size:11px;font-weight:600;color:#cbd5e1;">${lastSync}</span>
                    </div>
                    ${isLive ? `<div style="display:flex;align-items:center;justify-content:space-between;padding:8px 10px;background:rgba(30,41,59,0.5);border-radius:8px;">
                        <span style="font-size:11px;color:#94a3b8;">백엔드</span>
                        <span style="font-size:11px;font-weight:500;color:#64748b;">${baseUrl}</span>
                    </div>` : ''}
                    <button onclick="_sfRefreshApiStatus()" style="margin-top:4px;width:100%;padding:6px;background:linear-gradient(135deg,${isLive ? '#059669,#047857' : '#d97706,#b45309'});border:none;border-radius:8px;color:#fff;font-size:11px;font-weight:600;cursor:pointer;">상태 새로고침</button>
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
    const isLiveNow = await detectApiMode({ force: true });
    _sfLastSyncTime = new Date();
    _sfRenderAiStatusWidget();
    if (isLiveNow && !wasLive) {
        showToast('백엔드 연결이 복구되었습니다.', 'success');
    } else if (!isLiveNow && wasLive) {
        showToast('백엔드 연결이 끊어져 데모 모드로 전환되었습니다.', 'warning');
    } else {
        showToast('상태가 갱신되었습니다. 모드: ' + getApiMode(), 'info');
    }
}

const PLATFORM_MENU_LABELS = {
    'dashboard.html': '운영 대시보드',
    'index.html': '플랫폼 홈',
    'performance.html': '성능',
    'analytics.html': '분석',
    'billing.html': '결제',
    'invoices.html': '인보이스',
    'profile.html': '계정',
    'team.html': '팀',
    'security.html': '보안',
    'notifications.html': '알림',
    'api-keys.html': 'API 키',
    'integrations.html': '통합',
    'admin.html': '관리자',
    'admin-monitoring.html': '모니터링',
    'usage.html': '사용량',
    'status.html': '상태',
    'feedback.html': '피드백',
    'help.html': '도움말',
    'contact.html': '문의',
    'settings.html': '설정',
    'usage-export.html': '내보내기',
    'data-export.html': '내보내기',
    'changelog.html': '변경 사항',
    'health.html': '시스템 상태',
    'onboarding.html': '온보딩',
    'forgot-password.html': '비밀번호 찾기',
    'reset-password.html': '비밀번호 재설정',
    'api-reference.html': 'API 참조',
    'verify-email.html': '이메일 인증',
    '2fa-setup.html': '2FA 설정',
    'login.html': '로그인',
    'register.html': '회원가입',
    'demo-login.html': '데모 로그인',
    'auto-apply.html': '자동 신청',
    'create.html': '캠페인 생성',
    'applications.html': '신청 현황',
    'my-campaigns.html': '내 캠페인',
    'aggregator.html': '캠페인 찾기',
    '../sns-auto/index.html': 'SNS 자동화',
    '../review/index.html': '리뷰',
    '../coocook/index.html': '쿠쿠크',
    '../ai-automation/index.html': 'AI 자동화',
    '../bohemian-marketing/index.html': '보헤미안',
    '../webapp-builder/index.html': '웹앱 빌더',
    '../instagram-cardnews/index.html': '카드뉴스'
};

const PLATFORM_TITLE_BY_PATH = {
    'settings.html': '고급 설정 — SoftFactory',
    'data-export.html': '데이터 내보내기 — SoftFactory',
    'privacy.html': '개인정보 처리방침 — SoftFactory',
    'terms.html': '이용약관 — SoftFactory',
    'onboarding.html': '온보딩 — SoftFactory',
    'reset-password.html': '비밀번호 재설정 — SoftFactory'
};

const SF_SERVICE_PREFIXES = [
    'sns-auto',
    'review',
    'coocook',
    'ai-automation',
    'bohemian-marketing',
    'webapp-builder',
    'instagram-cardnews'
];

function _sfGetCurrentServicePrefix() {
    const path = (location.pathname || '').toLowerCase();
    return SF_SERVICE_PREFIXES.find((prefix) => path.includes(`/${prefix}/`)) || '';
}

function _sfGetServicePrefixFromHref(href) {
    const text = (href || '').toLowerCase();
    return SF_SERVICE_PREFIXES.find((prefix) => text.includes(`${prefix}/`) || text.includes(`/${prefix}/`)) || '';
}

function _sfInjectPlatformUiStyle() {
    if (document.getElementById('sf-platform-ui-style')) return;
    const style = document.createElement('style');
    style.id = 'sf-platform-ui-style';
    style.textContent = `
        .sf-nav-shell {
            background: rgba(15, 23, 42, 0.95);
            backdrop-filter: blur(6px);
            border-right-color: rgba(255, 255, 255, 0.08);
            box-shadow: 0 0 0 1px rgba(71, 85, 105, 0.15);
            color: #e2e8f0;
        }
        .sf-nav-shell nav { row-gap: 0.25rem; }
        .sf-nav-shell .nav-item { transition: all 0.2s ease; }
        .sf-nav-shell .sf-menu-section {
            padding: 0 1rem;
            margin: 0.75rem 0 0.4rem;
            color: #64748b;
            font-size: 0.68rem;
            letter-spacing: 0.08em;
            font-weight: 700;
            text-transform: uppercase;
            text-align: left;
        }
        .sf-nav-shell .sf-nav-link,
        .sf-nav-shell .nav-item {
            display: flex !important;
            align-items: center;
            gap: 0.65rem;
            color: #e2e8f0 !important;
            border-radius: 0.75rem;
            min-height: 2.3rem;
            transition: all 0.2s ease;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .sf-nav-shell .sf-nav-link[data-sf-group="service"] {
            opacity: 0.72;
        }
        .sf-nav-shell .sf-nav-link[data-sf-group="current-service"] {
            opacity: 1;
        }
        .sf-nav-shell .sf-nav-link:not(.sf-nav-active):hover,
        .sf-nav-shell .nav-item:hover {
            background: rgba(148, 163, 184, 0.12);
            color: #f8fafc !important;
            opacity: 1;
        }
        .sf-nav-shell .sf-nav-active,
        .sf-nav-shell .nav-item.active {
            background: linear-gradient(90deg, rgba(99, 102, 241, 0.2), transparent);
            color: #ffffff !important;
            border-left: 2px solid #6366f1;
        }
        .sf-nav-shell .sf-nav-child {
            padding-left: 2.75rem !important;
            position: relative;
        }
        .sf-nav-shell .sf-nav-child::before {
            content: '';
            position: absolute;
            left: 1.35rem;
            top: 50%;
            width: 0.55rem;
            height: 1px;
            background: rgba(148, 163, 184, 0.55);
            transform: translateY(-50%);
        }
        .sf-nav-shell .sf-nav-userbar {
            background: rgba(15, 23, 42, 0.7);
            border-top: 1px solid rgba(71, 85, 105, 0.25);
        }
        .sf-nav-shell .soft-topbar h2,
        .sf-nav-shell .soft-topbar h1 {
            font-size: 1.05rem;
            letter-spacing: -0.01em;
            line-height: 1.4;
        }
        .sf-nav-shell .soft-topbar p {
            line-height: 1.5;
        }
    `;
    document.head.appendChild(style);
}

function _sfNormalizeMenuTextByHref(href) {
    if (!href) return '';
    const cleanHref = (href || '').split('?')[0].split('#')[0].trim();
    if (PLATFORM_MENU_LABELS[cleanHref]) return PLATFORM_MENU_LABELS[cleanHref];

    const normalized = cleanHref.replace(/^\.\.\//, '').replace(/^\.\//, '');
    if (PLATFORM_MENU_LABELS[normalized]) return PLATFORM_MENU_LABELS[normalized];

    const fileName = normalized.split('/').pop().toLowerCase();
    return PLATFORM_MENU_LABELS[fileName] || '';
}

function _sfMenuGroupByHref(href) {
    if (!href) return 'platform';
    const text = href.toLowerCase();
    const fileName = (text.split('?')[0].split('#')[0].split('/').pop() || '').toLowerCase();
    const currentService = _sfGetCurrentServicePrefix();
    const targetService = _sfGetServicePrefixFromHref(text);

    if (targetService) {
        return currentService && currentService === targetService ? 'current-service' : 'service';
    }
    if (text.includes('../') || /sns-auto|review|coocook|ai-automation|webapp-builder|bohemian-marketing|instagram-cardnews/.test(text)) {
        return 'service';
    }
    if (fileName === 'admin.html' || fileName === 'admin-monitoring.html' || fileName === 'health.html') {
        return 'platform';
    }
    if (/^team\.html$|^settings\.html$|^security\.html$|^api-keys\.html$|^notifications\.html$|^integrations\.html$|^feedback\.html$|^contact\.html$|^privacy\.html$|^terms\.html$|^help\.html$|2fa|^onboarding\.html$/.test(fileName)) {
        return 'platform';
    }

    return 'platform';
}

function _sfNormalizeNav활성(navLink, href) {
    const current = (location.pathname.split('/').pop() || 'index.html').toLowerCase();
    const target = (href.split('?')[0].split('#')[0].split('/').pop() || '').toLowerCase();
    if (!target) return false;
    if (target === current) return true;
    if (current === 'index.html' && (target === 'dashboard.html' || target === 'platform/index.html')) return true;
    return false;
}

function _sfNormalizePlatformSidebar() {
    const asides = Array.from(document.querySelectorAll('aside')).filter((aside) => aside.querySelector('nav'));
    if (!asides.length) return;

    asides.forEach((aside) => {
        aside.classList.add('sf-nav-shell');
        const nav = aside.querySelector('nav');
        if (!nav) return;
        nav.classList.add('sf-nav-tree');

        const links = Array.from(nav.querySelectorAll('a[href]')).filter((link) => {
            const href = (link.getAttribute('href') || '').trim();
            if (!href) return false;
            if (href.startsWith('#') || href.startsWith('javascript:')) return false;
            return true;
        });
        if (!links.length) return;

        const normalizeLink = (href = '') => {
            const noQuery = (href || '').split('?')[0].split('#')[0].trim().toLowerCase();
            return noQuery.replace(/^\.{1,2}\//, '').replace(/^\/web\//, '').replace(/^\//, '');
        };
        const existingNormalized = new Set(links.map((link) => normalizeLink(link.getAttribute('href') || '')));
        const serviceLinks = [
            { href: '../sns-auto/index.html', icon: '📱', label: 'SNS 자동화' },
            { href: '../review/index.html', icon: '⭐', label: '리뷰' },
            { href: '../coocook/index.html', icon: '🍳', label: '쿠쿠크' },
            { href: '../ai-automation/index.html', icon: '🤖', label: 'AI 자동화' },
            { href: '../bohemian-marketing/index.html', icon: '🚀', label: '보헤미안 마케팅 AI' },
            { href: '../webapp-builder/index.html', icon: '💻', label: '웹앱 빌더' },
            { href: '../instagram-cardnews/index.html', icon: '📸', label: '인스타그램 카드뉴스 자동화' }
        ];
        const missingServiceLinks = serviceLinks.filter((service) => !existingNormalized.has(normalizeLink(service.href)) && ![...existingNormalized].some((key) => key.endsWith(normalizeLink(service.href))));

        const hasSectionTitle = !!nav.querySelector('.section-title, .sf-menu-section');

        links.forEach((link) => {
            const rawHref = (link.getAttribute('href') || '').trim();
            if (!rawHref || rawHref.startsWith('javascript')) return;

            const mappedLabel = _sfNormalizeMenuTextByHref(rawHref);
            const group = _sfMenuGroupByHref(rawHref);
            link.classList.add('soft-nav-link', 'sf-nav-link', 'nav-item');
            link.dataset.sfGroup = group;
            if (group === 'service' || group === 'current-service') link.classList.add('sf-nav-child');

            if (mappedLabel) {
                const icon = link.querySelector('span');
                const hasIcon = icon && icon.tagName === 'SPAN';
                if (hasIcon) {
                    const originalSpan = icon.cloneNode(true);
                    link.textContent = '';
                    link.appendChild(originalSpan);
                    link.append(` ${mappedLabel}`);
                } else {
                    link.textContent = mappedLabel;
                }
            }

            if (_sfNormalizeNav활성(link, rawHref)) {
                link.classList.add('sf-nav-active', 'active');
                link.setAttribute('aria-current', 'page');
            } else {
                link.classList.remove('sf-nav-active');
                link.classList.remove('active');
                link.removeAttribute('aria-current');
            }
        });

        if (missingServiceLinks.length > 0) {
            const serviceWrapper = document.createElement('div');
            serviceWrapper.className = 'sf-nav-service-missing space-y-1';
            const heading = document.createElement('p');
            heading.className = 'sf-menu-section';
            heading.dataset.sfGroup = 'service';
            heading.textContent = '다른 서비스';
            serviceWrapper.appendChild(heading);

            missingServiceLinks.forEach((item) => {
                const a = document.createElement('a');
                a.href = item.href;
                a.className = 'soft-nav-link sf-nav-link nav-item sf-nav-child';
                a.dataset.sfGroup = _sfMenuGroupByHref(item.href);
                a.innerHTML = `<span aria-hidden="true">${item.icon}</span> <span>${item.label}</span>`;
                serviceWrapper.appendChild(a);
            });

            const userBtn = aside.querySelector('button[onclick*=\"logout\"]');
            const userPanel = userBtn ? userBtn.closest('div') : null;
            const navReference = userPanel && userPanel.parentNode === nav ? userPanel : null;
            if (navReference) {
                nav.insertBefore(serviceWrapper, navReference);
            } else {
                nav.appendChild(serviceWrapper);
            }
        }

        if (!hasSectionTitle && links.length > 4) {
            const inserted = new Set();
            const titleByGroup = {
                platform: '플랫폼',
                'current-service': '현재 서비스',
                service: '다른 서비스'
            };

            links.forEach((link) => {
                const group = _sfMenuGroupByHref(link.getAttribute('href') || '');
                if (!inserted.has(group)) {
                    const title = document.createElement('p');
                    title.className = 'sf-menu-section';
                    title.dataset.sfGroup = group;
                    title.textContent = titleByGroup[group] || '메뉴';
                    let insertionTarget = link;
                    while (insertionTarget && insertionTarget.parentNode !== nav) {
                        insertionTarget = insertionTarget.parentNode;
                    }
                    if (insertionTarget && insertionTarget.parentNode === nav) {
                        nav.insertBefore(title, insertionTarget);
                    } else {
                        nav.appendChild(title);
                    }
                    inserted.add(group);
                }
            });
        }

        const userBtn = aside.querySelector('button[onclick*="logout"]');
        if (userBtn) {
            userBtn.classList.add('sf-user-logout');
            const wrapper = userBtn.closest('div');
            if (wrapper) wrapper.classList.add('sf-nav-userbar');
        }
    });
}

function _sfNormalizePlatformTitles() {
    const page = (location.pathname.split('/').pop() || 'index.html').toLowerCase();
    const targetTitle = PLATFORM_TITLE_BY_PATH[page];
    if (!targetTitle) return;
    if (document.title !== targetTitle) {
        document.title = targetTitle;
    }
}

// Auto-render widget and normalize platform UI on page load
if (typeof document !== 'undefined') {
    document.addEventListener('DOMContentLoaded', () => {
        const currentUser = getAuthUser();
        if (isAdminUser(currentUser)) {
            enableAdminFixtureMode(currentUser);
        } else if (isAdminFixtureMode()) {
            disableAdminFixtureMode();
        }

        detectApiMode();
        _sfInjectPlatformUiStyle();
        _sfNormalizePlatformSidebar();
        _sfNormalizePlatformTitles();
        _sfBindNavigationPrefetch();
        _sfEnsureQuickOpen();
        _sfBindPendingFormState();
        // Small delay to let detectApiMode finish
        setTimeout(() => {
            _sfLastSyncTime = new Date();
            _sfRenderAiStatusWidget();
        }, 1500);
    });
}

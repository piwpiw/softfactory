/**
 * Cookie Consent Banner
 * SoftFactory — GDPR + 한국 개인정보보호법 준수
 *
 * 사용법: 모든 HTML 페이지의 </body> 직전에 아래 태그를 추가하세요.
 * <script src="/web/platform/cookie-consent.js" defer></script>
 *
 * 의존성: 없음 (순수 JS, 외부 라이브러리 불필요)
 */
(function () {
    'use strict';

    var STORAGE_KEY = 'sf_cookie_consent';
    var DATE_KEY    = 'sf_cookie_consent_date';
    var BANNER_ID   = 'sf-cookie-banner';

    // ---- 이미 동의한 경우 종료 ----
    try {
        if (localStorage.getItem(STORAGE_KEY)) return;
    } catch (e) {
        // localStorage 비활성화된 경우(시크릿 모드 등) 배너를 표시하지 않음
        return;
    }

    // ---- DOM 준비 후 실행 ----
    function init() {
        if (document.getElementById(BANNER_ID)) return; // 중복 방지

        var banner = document.createElement('div');
        banner.id = BANNER_ID;
        banner.setAttribute('role', 'dialog');
        banner.setAttribute('aria-label', '쿠키 동의 배너');
        banner.setAttribute('aria-live', 'polite');

        banner.innerHTML = [
            '<div style="',
            '  position:fixed;bottom:0;left:0;right:0;',
            '  background:rgba(17,24,39,0.97);',
            '  backdrop-filter:blur(8px);',
            '  border-top:1px solid rgba(124,58,237,0.3);',
            '  color:#e2e8f0;',
            '  padding:14px 20px;',
            '  z-index:99999;',
            '  display:flex;align-items:center;gap:14px;flex-wrap:wrap;',
            '  font-family:Inter,system-ui,-apple-system,sans-serif;',
            '  font-size:13px;line-height:1.5;',
            '  box-shadow:0 -4px 24px rgba(0,0,0,0.4);',
            '">',
            '  <p style="margin:0;flex:1;min-width:200px;">',
            '    SoftFactory는 서비스 품질 개선을 위해 쿠키를 사용합니다.',
            '    <a href="/web/platform/privacy.html"',
            '       style="color:#a78bfa;text-decoration:underline;"',
            '       target="_blank" rel="noopener noreferrer">개인정보처리방침</a>에서 자세한 내용을 확인하세요.',
            '  </p>',
            '  <div style="display:flex;gap:8px;flex-shrink:0;flex-wrap:wrap;">',
            '    <button',
            '      id="sf-cookie-essential"',
            '      style="',
            '        background:transparent;color:#94a3b8;',
            '        border:1px solid #475569;',
            '        padding:7px 14px;border-radius:7px;cursor:pointer;',
            '        font-size:12px;font-weight:500;white-space:nowrap;',
            '        transition:border-color .2s,color .2s;',
            '      "',
            '      onmouseover="this.style.borderColor=\'#7c3aed\';this.style.color=\'#e2e8f0\'"',
            '      onmouseout="this.style.borderColor=\'#475569\';this.style.color=\'#94a3b8\'"',
            '      aria-label="필수 쿠키만 허용">',
            '      필수만 허용',
            '    </button>',
            '    <button',
            '      id="sf-cookie-all"',
            '      style="',
            '        background:#7c3aed;color:#fff;',
            '        border:1px solid transparent;',
            '        padding:7px 16px;border-radius:7px;cursor:pointer;',
            '        font-size:12px;font-weight:600;white-space:nowrap;',
            '        transition:background .2s;',
            '      "',
            '      onmouseover="this.style.background=\'#6d28d9\'"',
            '      onmouseout="this.style.background=\'#7c3aed\'"',
            '      aria-label="모든 쿠키 허용">',
            '      모두 허용',
            '    </button>',
            '  </div>',
            '</div>'
        ].join('');

        document.body.appendChild(banner);

        // ---- 버튼 이벤트 ----
        document.getElementById('sf-cookie-essential').addEventListener('click', function () {
            sfCookieConsent('essential');
        });
        document.getElementById('sf-cookie-all').addEventListener('click', function () {
            sfCookieConsent('all');
        });

        // ---- 키보드 접근성: Escape로 '필수만 허용' 처리 ----
        document.addEventListener('keydown', function onKeydown(evt) {
            if (evt.key === 'Escape') {
                sfCookieConsent('essential');
                document.removeEventListener('keydown', onKeydown);
            }
        });
    }

    // ---- 동의 처리 ----
    window.sfCookieConsent = function (type) {
        try {
            localStorage.setItem(STORAGE_KEY, type);
            localStorage.setItem(DATE_KEY, new Date().toISOString());
        } catch (e) {
            // 저장 실패는 무시 (시크릿 모드 등)
        }

        var banner = document.getElementById(BANNER_ID);
        if (banner) {
            // 부드럽게 사라지는 애니메이션
            banner.style.transition = 'opacity .25s ease';
            banner.style.opacity = '0';
            setTimeout(function () {
                if (banner.parentNode) {
                    banner.parentNode.removeChild(banner);
                }
            }, 280);
        }

        // 'all' 동의 시 분석 스크립트 초기화 (향후 확장)
        if (type === 'all') {
            _initAnalytics();
        }
    };

    // ---- 분석 초기화 (Google Analytics 등 향후 추가) ----
    function _initAnalytics() {
        // 예: window.gtag && gtag('consent', 'update', { analytics_storage: 'granted' });
        // 현재는 자체 분석만 사용 — 추가 스크립트 없음
    }

    // ---- 현재 동의 상태 조회 (다른 스크립트에서 참조 가능) ----
    window.sfGetCookieConsent = function () {
        try {
            return localStorage.getItem(STORAGE_KEY) || null;
        } catch (e) {
            return null;
        }
    };

    // ---- 동의 초기화 (설정 페이지 등에서 호출) ----
    window.sfResetCookieConsent = function () {
        try {
            localStorage.removeItem(STORAGE_KEY);
            localStorage.removeItem(DATE_KEY);
        } catch (e) {
            // 무시
        }
    };

    // ---- DOM 준비 확인 후 실행 ----
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        // DOMContentLoaded가 이미 발생한 경우
        setTimeout(init, 0);
    }
})();

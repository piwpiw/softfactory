/**
 * SoftFactory Mobile Optimization v1.0
 * Handles hamburger menu, sidebar toggle, touch gestures, and mobile-specific behavior
 */

(function() {
    'use strict';

    // ============ Subproject Sidebar Recovery ============
    const SUBPROJECT_LINKS = [
        { href: '/sns-auto/index.html', icon: '\uD83D\uDCF1', label: 'SNS 자동화' },
        { href: '/review/index.html', icon: '\u2B50', label: '리뷰 자동화' },
        { href: '/coocook/index.html', icon: '\uD83E\uDD5A', label: 'CooCook' },
        { href: '/ai-automation/index.html', icon: '\uD83E\uDD16', label: 'AI 자동화' },
        { href: '/growth-automation/index.html', icon: '🚀', label: 'Growth Automation' },
        { href: '/bohemian-marketing/index.html', icon: '\uD83D\uDE80', label: '보헤미안 마케팅 AI' },
        { href: '/webapp-builder/index.html', icon: '\uD83D\uDCBB', label: '웹앱 빌더' },
        { href: '/instagram-cardnews/index.html', icon: '\uD83D\uDCF8', label: '인스타그램 카드뉴스 자동화' }
    ];

    const CORE_SERVICE_LINKS = [
        { href: '/sns-auto/index.html', icon: '\uD83D\uDCF1', label: 'SNS 자동화', section: '운영 서비스' },
        { href: '/review/index.html', icon: '\u2B50', label: '리뷰 자동화', section: '운영 서비스' },
        { href: '/coocook/index.html', icon: '\uD83E\uDD5A', label: 'CooCook', section: '운영 서비스' },
        { href: '/ai-automation/index.html', icon: '\uD83E\uDD16', label: 'AI 자동화', section: '운영 서비스' },
        { href: '/growth-automation/index.html', icon: '🚀', label: 'Growth Automation', section: '운영 서비스' },
        { href: '/bohemian-marketing/index.html', icon: '\uD83D\uDE80', label: '보헤미안 마케팅 AI', section: '운영 서비스' },
        { href: '/webapp-builder/index.html', icon: '\uD83D\uDCBB', label: '웹앱 빌더', section: '운영 서비스' },
        { href: '/instagram-cardnews/index.html', icon: '\uD83D\uDCF8', label: '인스타그램 카드뉴스', section: '운영 서비스' },
        { href: '/platform/index.html', icon: '\uD83C\uDFED', label: '플랫폼 홈', section: '플랫폼' }
    ];

    const SERVICE_LINKS = {
            '/bohemian-marketing/': [
                { href: 'index.html', icon: '🚀', label: '보헤미안 마케팅 AI' },
                { href: 'app.html', icon: '📱', label: '운영 대시보드' },
                { href: 'autopilot.html', icon: '⚡', label: '오토파일럿' },
                { href: 'persona.html', icon: '🎭', label: '페르소나 설정' },
                { href: 'pricing.html', icon: '💳', label: '요금제' }
            ],
            '/instagram-cardnews/': [
                { href: 'index.html', icon: '📸', label: '카드뉴스 자동화' }
            ],
            '/webapp-builder/': [
                { href: 'index.html', icon: '💻', label: '웹앱 빌더' },
                { href: 'dashboard.html', icon: '📊', label: '대시보드' },
                { href: 'curriculum.html', icon: '📚', label: '커리큘럼' },
                { href: 'enroll.html', icon: '📝', label: '등록/신청' },
                { href: 'my-apps.html', icon: '📱', label: '내 앱' },
                { href: 'community.html', icon: '👥', label: '커뮤니티' }
            ],
            '/growth-automation/': [
                { href: 'index.html', icon: '🚀', label: 'Growth Hub' },
                { href: 'journeys.html', icon: '🧭', label: '여정 관리' },
                { href: 'contacts.html', icon: '👥', label: '연락처' },
                { href: 'ops.html', icon: '🛠️', label: '운영 센터' }
            ],
            '/review/': [
                { href: 'index.html', icon: '⭐', label: '리뷰 대시보드' },
                { href: 'my-campaigns.html', icon: '🚀', label: '캠페인 관리' },
                { href: 'accounts.html', icon: '👤', label: '계정 관리' },
                { href: 'aggregator.html', icon: '📥', label: '집계 분석' },
                { href: 'create.html', icon: '✍️', label: '새 캠페인' }
            ],
            '/sns-auto/': [
                { href: 'index.html', icon: '📱', label: 'SNS 자동화' },
                { href: 'create.html', icon: '✍️', label: '캠페인 생성' },
                { href: 'campaigns.html', icon: '🎯', label: '캠페인 목록' },
                { href: 'analytics.html', icon: '📈', label: '분석' },
                { href: 'inbox.html', icon: '📩', label: '인박스' },
                { href: 'accounts.html', icon: '🔗', label: '계정 관리' }
            ],
            '/platform/': [
                { href: 'index.html', icon: '🏭', label: '플랫폼 홈' },
                { href: 'dashboard.html', icon: '📊', label: '플랫폼 대시보드' },
                { href: 'analytics.html', icon: '🧭', label: '플랫폼 분석' },
                { href: 'billing.html', icon: '💳', label: '요금/결제' },
                { href: 'settings.html', icon: '⚙️', label: '설정' },
                { href: 'help.html', icon: '❓', label: '도움말' },
                { href: 'admin.html', icon: '🛠️', label: '운영 관리' }
            ],
            '/ai-automation/': [
                { href: 'index.html', icon: '🤖', label: 'AI 자동화' },
                { href: 'create.html', icon: '🧩', label: '워크플로우 생성' },
                { href: 'scenarios.html', icon: '🧪', label: '시나리오' },
                { href: 'analytics.html', icon: '📈', label: '성과 분석' },
                { href: 'pricing.html', icon: '💳', label: '요금제' }
            ],
            '/coocook/': [
                { href: 'index.html', icon: '🍳', label: 'CooCook' },
                { href: 'explore.html', icon: '🔍', label: '셰프 탐색' },
                { href: 'my-bookings.html', icon: '📅', label: '내 예약' },
                { href: 'recipes.html', icon: '🍛', label: '레시피' },
                { href: 'review.html', icon: '⭐', label: '리뷰' },
                { href: 'payment.html', icon: '💳', label: '결제' }
            ]
        };

    const SERVICE_SEGMENT_LABELS = {
        'coocook': { icon: '🍳', name: 'CooCook' },
        'sns-auto': { icon: '📱', name: 'SNS 자동화' },
        'ai-automation': { icon: '🤖', name: 'AI 자동화' },
        'growth-automation': { icon: '🚀', name: 'Growth Automation' },
        'bohemian-marketing': { icon: '🚀', name: '보헤미안 마케팅 AI' },
        'webapp-builder': { icon: '💻', name: '웹앱 빌더' },
        'instagram-cardnews': { icon: '📸', name: '인스타그램 카드뉴스' },
        'platform': { icon: '🏭', name: '플랫폼' },
        'review': { icon: '⭐', name: '리뷰' }
    };

    const SERVICE_NAV_GROUP_PRIORITY = [
        '플랫폼',
        '현재 서비스',
        '운영 서비스',
        '연동 서비스',
        '관리/지원',
        '일반 기능'
    ];

    const SERVICE_NAV_GROUP_META = {
        '현재 서비스': { icon: '\uD83E\uDDD1', title: '현재 서비스' },
        '운영 서비스': { icon: '\uD83D\uDD17', title: '운영 서비스' },
        '연동 서비스': { icon: '🔗', title: '연동 서비스' },
        '플랫폼': { icon: '\uD83C\uDFED', title: '플랫폼' },
        '관리/지원': { icon: '\u2699\uFE0F', title: '관리/지원' },
        '일반 기능': { icon: '\uD83E\uDDC0', title: '일반 기능' }
    };

    const SERVICE_NAV_GROUP_CANONICAL_MAP = {
        '현재 서비스 메뉴': '현재 서비스',
        'current service menu': '현재 서비스',
        'current service': '현재 서비스',
        '플랫폼 개요': '플랫폼',
        '워크스페이스': '관리/지원',
        '운영 연결': '연동 서비스',
        '운영연결': '연동 서비스',
        '보헤미안 워크스페이스': '관리/지원',
        '소프트팩토리': '플랫폼',
        'softfactory': '플랫폼',
        'SoftFactory': '플랫폼',
        'soft factory': '플랫폼',
        '보헤미안': '관리/지원'
    };

    const SERVICE_NAV_GROUP_HINT_RULES = [
        { pattern: /(현재\s*서비스\s*메뉴|현재서비스|current service)/i, result: '현재 서비스' },
        { pattern: /(플랫폼\s*개요|platform overview|platform home|플랫폼 홈|platform menu)/i, result: '플랫폼' },
        { pattern: /(워크스페이스|workspace)/i, result: '관리/지원' },
        { pattern: /(운영\s*연결|운영연결|연동|integration|integrat|연계)/i, result: '연동 서비스' },
        { pattern: /(보헤미안\s*워크스페이스|bohemian workspace)/i, result: '관리/지원' }
    ];

    const SIDEBAR_EXEMPT_PATH_PATTERNS = [
        /\/platform\/(login|register|forgot-password|reset-password|verify-email|demo-login|login-2fa|2fa-setup|onboarding|roadmap|status|health|search|features|contact|partners|changelog|team|privacy|terms|404|404\\.html)\/?$/,
        /^\/(email-templates|emails?)\//,
        /\/admin\//,
        /\/analytics\//
    ];

    const KEYWORD_NAV_ICON_MAP = [
        [/(대시보드|dashboard|홈)/i, '\uD83D\uDCCA'],
        [/(분석|analytics|성과|리포트|report|통계)/i, '\uD83D\uDCC8'],
        [/(요금|결제|invoice|과금|billing|인보이스)/i, '\uD83D\uDCB3'],
        [/(API|키|키관리|api)/i, '\uD83D\uDD12'],
        [/(알림|notification|notice)/i, '\uD83D\uDD14'],
        [/(프로필|profile|계정|account)/i, '\uD83D\uDC64'],
        [/(설정|setting|보안|security)/i, '\u2699\uFE0F'],
        [/(지원|help|문의|문제|faq|이슈)/i, '\uD83E\uDD19'],
        [/(검색|search)/i, '\uD83D\uDD0E'],
        [/(초대|회원|로그인|로그아웃|회원가입)/i, '\uD83D\uDC4B'],
        [/(데이터|export|import|백업)/i, '\uD83D\uDCC2'],
        [/(연동|integrat|연계|연결)/i, '\uD83D\uDD17']
    ];

    function createFallbackNavSectionHtml(groupName, title, icon, links, isOpen) {
        if (!Array.isArray(links) || !links.length) return '';
        const normalizedLinks = links.map((item) =>
            `<a href="${item.href}" class="soft-nav-link flex items-center gap-3 px-4 py-2.5 rounded-lg hover:bg-slate-800 transition" title="${item.label || ''}">
                <span aria-hidden="true">${item.icon || '🧭'}</span>
                <span>${item.label || '메뉴'}</span>
            </a>`
        ).join('');

        return `
            <details class="soft-nav-group" data-sf-group="${groupName}" ${isOpen ? 'open' : ''}>
                <summary class="soft-nav-summary"><span>${icon} ${title}</span><span class="soft-nav-badge">${normalizedLinks.length}</span></summary>
                <div class="soft-nav-sub">${normalizedLinks}</div>
            </details>
        `;
    }

    function createFallbackSidebarForService(pathPrefix, title) {
        const existingAside = document.querySelector('aside');
        const main = document.querySelector('main')
            || document.querySelector('.container')
            || document.querySelector('#app')
            || (document.body ? document.body.children[0] : null);
        if (existingAside || !main || !document.body || main === document.body) return;

        const aside = document.createElement('aside');
        aside.className = 'w-64 soft-sidebar border-r border-slate-800 flex flex-col shrink-0';
        const titleText = title || 'SoftFactory 허브';
        const links = SERVICE_LINKS[pathPrefix] || SERVICE_LINKS['/platform/'] || CORE_SERVICE_LINKS;
        const platformHomeHref = '/platform/index.html';
        const serviceName = titleText.includes('SoftFactory') ? 'SoftFactory' : titleText;
        const segment = getServiceSegment(pathPrefix || '');
        const serviceIcon = getSegmentIcon(segment || 'platform');

        const serviceSection = createFallbackNavSectionHtml(
            '현재 서비스',
            `${serviceName}`,
            serviceIcon,
            links.map((item) => ({
                href: item.href,
                icon: item.icon || resolveNavIcon(item.label || ''),
                label: item.label || '메뉴'
            })),
            true
        );

        const platformSection = createFallbackNavSectionHtml(
            '플랫폼',
            '플랫폼 홈',
            '🏭',
            [{ href: platformHomeHref, icon: '🏭', label: '플랫폼 홈' }]
        );

        const coreSection = createFallbackNavSectionHtml(
            '운영 서비스',
            '운영 서비스',
            '🧭',
            CORE_SERVICE_LINKS.map((item) => ({
                href: item.href,
                icon: item.icon || resolveNavIcon(item.label || ''),
                label: item.label || '메뉴'
            }))
        );

        const subprojectSection = createFallbackNavSectionHtml(
            '연동 서비스',
            '연동 서비스',
            '🔗',
            SUBPROJECT_LINKS
        );

        aside.innerHTML = `
            <div class="p-6 border-b border-slate-800">
                <a href="${platformHomeHref}" class="flex items-center gap-3">
                    <span class="text-2xl" aria-hidden="true">🏭</span>
                    <div>
                        <h1 class="font-bold text-white">${titleText}</h1>
                        <p class="text-xs text-slate-400">SoftFactory</p>
                    </div>
                </a>
            </div>
            <nav class="soft-nav-tree flex-1 p-6 space-y-2 overflow-y-auto" aria-label="${titleText} 메뉴">
                <button class="hamburger" aria-label="메뉴 열기/닫기"><span></span><span></span><span></span></button>
                ${platformSection}
                ${serviceSection}
                ${coreSection}
                ${subprojectSection}
            </nav>
            <div class="p-6 border-t border-slate-800">
                <button onclick="if (typeof window.logout === 'function') { logout(); } else { window.location.href = '/'; }" class="p-2 hover:bg-slate-800 rounded-lg w-full text-left">🚪 로그아웃</button>
            </div>
        `;

        const shell = document.createElement('div');
        shell.className = 'flex h-screen overflow-hidden';
        const content = document.createElement('div');
        content.className = 'flex-1 flex flex-col overflow-hidden';
        main.parentElement.removeChild(main);
        content.appendChild(main);
        shell.appendChild(aside);
        shell.appendChild(content);
        document.body.innerHTML = '';
        document.body.appendChild(shell);
    }

    function normalizeNavPath(path) {
        const raw = String(path || '').trim().toLowerCase();
        const noQueryHash = raw.replace(/[?#].*$/, '');
        let normalized = noQueryHash;

        if (/^[a-z][a-z0-9+.-]*:/.test(normalized)) {
            try {
                normalized = new URL(normalized, location.href).pathname;
            } catch (err) {
                normalized = noQueryHash;
            }
        }

        normalized = normalized.replace(/^\/+/, '/');
        if (!normalized.startsWith('/')) {
            normalized = '/' + normalized;
        }
        normalized = normalized.replace(/\/{2,}/g, '/');
        normalized = normalized.replace(/^\/web(?=\/|$)/, '');

        if (/\/index\.html?$/i.test(normalized)) {
            normalized = normalized.replace(/index\.html?$/i, '');
        }
        normalized = normalized.replace(/\/+$/, '');
        normalized = normalized || '/';
        return normalized;
    }

    function normalizeNavHref(rawHref) {
        if (!rawHref) return '';
        const trimmed = String(rawHref).trim();
        if (!trimmed || trimmed === '#' || trimmed.startsWith('javascript:') || trimmed.startsWith('mailto:') || trimmed.startsWith('tel:')) {
            return '';
        }
        try {
            const anchor = document.createElement('a');
            anchor.href = trimmed;
            return normalizeNavPath(anchor.pathname);
        } catch (e) {
            return normalizeNavPath(trimmed);
        }
    }

    function getServiceSegment(pathname) {
        const normalized = normalizeNavPath(pathname);
        const match = normalized.match(/^\/([a-z0-9\-]+)\/?/);
        return match && match[1] ? match[1] : '';
    }

    function getServicePrefixFromPath(pathname) {
        const segment = getServiceSegment(pathname);
        if (!segment) {
            const normalized = normalizeNavPath(pathname);
            if (normalized === '/') {
                return '/platform/';
            }
            return '/';
        }
        return `/${segment}/`;
    }

    function getSegmentLabel(segment) {
        const info = SERVICE_SEGMENT_LABELS[segment] || {};
        return info.name || segment;
    }

    function getSegmentIcon(segment) {
        const info = SERVICE_SEGMENT_LABELS[segment];
        return info && info.icon ? info.icon : '🧭';
    }

    function getNormalizedNavHref(rawHref) {
        return normalizeNavHref(rawHref);
    }

    function normalizeNavText(raw) {
        return String(raw || '').trim() || '메뉴';
    }

    function resolveNavGroupFromHint(rawHint) {
        const hint = normalizeNavText(rawHint);
        if (!hint) return '일반 기능';
        const normalized = hint.toLowerCase();
        const canonical = SERVICE_NAV_GROUP_CANONICAL_MAP[hint] || SERVICE_NAV_GROUP_CANONICAL_MAP[normalized];
        if (canonical) return canonical;

        const matchedHint = SERVICE_NAV_GROUP_HINT_RULES.find((rule) => rule.pattern.test(normalized));
        if (matchedHint && matchedHint.result) return matchedHint.result;

        if (normalized.includes('현재')) return '현재 서비스';
        if (normalized.includes('연동') || normalized.includes('sub')) return '연동 서비스';
        if (normalized.includes('운영')) return '운영 서비스';
        if (normalized.includes('platform') || normalized.includes('플랫폼')) return '플랫폼';
        if (normalized.includes('관리') || normalized.includes('지원') || normalized.includes('help') || normalized.includes('faq') || normalized.includes('notice') || normalized.includes('설정') || normalized.includes('보안')) return '관리/지원';
        if (normalized.includes('워크스페이스') || normalized.includes('workspace')) return '관리/지원';
        return '일반 기능';
    }

    function getNavGroupMeta(groupName) {
        const canonical = resolveNavGroupFromHint(groupName || '일반 기능');
        return SERVICE_NAV_GROUP_META[canonical] || {
            icon: '🧭',
            title: canonical || '일반 기능'
        };
    }

    function resolveNavIconForLink(rawText) {
        const text = normalizeNavText(rawText);
        const iconMatch = text.match(/^\s*([\p{Extended_Pictographic}\uFE0F]+)/u);
        return iconMatch && iconMatch[1] ? iconMatch[1] : resolveNavIcon(text);
    }

    function resolveNavIcon(rawText) {
        const text = normalizeNavText(rawText);
        for (let i = 0; i < KEYWORD_NAV_ICON_MAP.length; i++) {
            if (KEYWORD_NAV_ICON_MAP[i][0].test(text)) return KEYWORD_NAV_ICON_MAP[i][1];
        }
        return '🧭';
    }

    function deriveNavGroupName(link, parentGroupHint) {
        const rawHref = link.getAttribute('href') || '';
        const target = getNormalizedNavHref(rawHref);
        const label = normalizeNavText(link.textContent).replace(/^\s*[\p{Extended_Pictographic}\uFE0F]+\s*/gu, '').trim();
        const currentPath = normalizeNavPath(location.pathname || '');
        const currentSegment = getServiceSegment(currentPath);
        if (!target) {
            return resolveNavGroupFromHint(parentGroupHint || '일반 기능');
        }

        const segment = getServiceSegment(target);
        const isCurrentService = segment === currentSegment
            || target === currentPath
            || currentPath === `${target}/`;
        const isPlatformHome = target === '/platform/' || target === '/platform/index/';

        if (isCurrentService || (segment && segment === currentSegment)) return '현재 서비스';
        if (segment === 'platform' || isPlatformHome || target.includes('/platform/') || target.includes('/web/platform/')) return '플랫폼';
        if (segment && SERVICE_SEGMENT_LABELS[segment]) return '운영 서비스';

        if (/^(로그인|회원|로그아웃|도움|help|faq|약관|정책|개인정보|문의|지원|공지|알림|보안|설정|관리)$/.test(label)) {
            return '관리/지원';
        }
        const resolved = '일반 기능';
        const forced = resolveNavGroupFromHint(parentGroupHint || resolved);
        if (parentGroupHint && resolved !== forced) {
            return forced;
        }
        return resolved;
    }

    function collectServiceSeedLinks(servicePrefix) {
        const serviceItems = (SERVICE_LINKS[servicePrefix] || []).map((item) => ({
            href: getNormalizedNavHref(item.href || ''),
            icon: item.icon || resolveNavIcon(item.label || ''),
            text: item.label || '메뉴',
            sourceGroup: '현재 서비스',
            ariaCurrent: '',
            title: item.label || '',
            target: '',
            rel: ''
        }));
        const coreItems = CORE_SERVICE_LINKS.map((item) => ({
            href: getNormalizedNavHref(item.href || ''),
            icon: item.icon || resolveNavIcon(item.label || ''),
            text: item.label || '메뉴',
            sourceGroup: item.section || '운영 서비스',
            ariaCurrent: '',
            title: item.label || '',
            target: '',
            rel: ''
        }));
        return { serviceItems, coreItems };
    }

    function sortByTextThenPath(items) {
        return items.sort((a, b) => {
            const byText = a.text.localeCompare(b.text, 'ko');
            if (byText) return byText;
            return a.href.localeCompare(b.href);
        });
    }

    function collectNavItems(nav, includeSeedLinks) {
        const currentPrefix = getServicePrefixFromPath(normalizeNavPath(location.pathname || ''));
        const grouped = new Map();
        SERVICE_NAV_GROUP_PRIORITY.forEach((name) => grouped.set(name, []));
        const dynamicGroups = new Set();
        const seen = new Set();

            const toPayload = function(link, parentGroupHint) {
            const rawHref = getNormalizedNavHref(link.getAttribute('href') || '');
            if (!rawHref || seen.has(rawHref)) return null;
            const fullText = normalizeNavText(link.textContent);
            const groupName = deriveNavGroupName(link, parentGroupHint);
            const item = {
                href: rawHref,
                icon: resolveNavIconForLink(fullText),
                text: fullText.replace(/^\s*[\p{Extended_Pictographic}\uFE0F]+\s*/u, '').trim() || fullText,
                ariaCurrent: link.getAttribute('aria-current') || '',
                title: link.getAttribute('title') || '',
                target: link.getAttribute('target') || '',
                rel: link.getAttribute('rel') || '',
                sourceGroup: groupName
            };
            seen.add(rawHref);
            return item;
        };

        const directGroupSections = Array.from(nav.children).filter((node) => node instanceof HTMLElement && node.classList && node.classList.contains('soft-nav-group'));
        if (directGroupSections.length) {
            directGroupSections.forEach((groupRoot) => {
                const summary = groupRoot.querySelector('summary');
                const groupHint = normalizeNavText(summary ? summary.textContent : '').replace(/\s*\d+\s*$/, '');
                const groupName = resolveNavGroupFromHint(groupHint);
                if (!grouped.has(groupName)) {
                    grouped.set(groupName, []);
                    dynamicGroups.add(groupName);
                }
                Array.from(groupRoot.querySelectorAll('a[href]')).forEach((link) => {
                    const item = toPayload(link, groupName);
                    if (!item) return;
                    grouped.get(groupName).push(item);
                });
            });
        } else {
            Array.from(nav.querySelectorAll('a[href]')).forEach((link) => {
                const item = toPayload(link);
                if (!item) return;
                const key = item.sourceGroup || '일반 기능';
                if (!grouped.has(key)) {
                    grouped.set(key, []);
                    dynamicGroups.add(key);
                }
                grouped.get(key).push(item);
            });
        }

        if (includeSeedLinks) {
            const seed = collectServiceSeedLinks(currentPrefix);
            seed.serviceItems.concat(seed.coreItems).forEach((item) => {
                if (!item.href || seen.has(item.href)) return;
                seen.add(item.href);
                const group = item.sourceGroup || '운영 서비스';
                if (!grouped.has(group)) grouped.set(group, []);
                grouped.get(group).push(item);
            });
        }

        SERVICE_NAV_GROUP_PRIORITY.forEach((name) => {
            if (grouped.has(name)) {
                grouped.set(name, sortByTextThenPath(grouped.get(name) || []));
            }
        });

        Array.from(grouped.keys()).forEach((name) => {
            if (SERVICE_NAV_GROUP_PRIORITY.indexOf(name) === -1) {
                grouped.set(name, sortByTextThenPath(grouped.get(name) || []));
            }
        });

        Array.from(grouped.keys()).forEach((name) => {
            const existing = grouped.get(name);
            if (!existing || !existing.length) return;
            const compact = [];
            const check = new Set();
            existing.forEach((item) => {
                if (check.has(item.href)) return;
                check.add(item.href);
                compact.push(item);
            });
            grouped.set(name, compact);
        });

        return grouped;
    }

    function ensureSafeText(raw) {
        return String(raw || '').trim() || '메뉴';
    }

    function standardizeSidebarTree() {
        const aside = document.querySelector('aside');
        const nav = aside ? aside.querySelector('nav') : null;
        if (!nav) return;
        if (nav.dataset.sfStructured === '1') return;

        const preservedLeading = [];
        Array.from(nav.children).forEach((node) => {
            if (!(node instanceof HTMLElement)) return;
            if (node.classList.contains('soft-nav-group') || node.tagName === 'A' || node.matches('div.soft-nav-divider')) {
                return;
            }
            if (node.classList.contains('hamburger')) {
                preservedLeading.push(node.outerHTML);
                return;
            }
            if (/^(현재 서비스|운영 서비스|연동 서비스|플랫폼|관리\/지원|일반 기능)/.test(normalizeNavText(node.textContent || ''))) {
                preservedLeading.push(node.outerHTML);
            }
        });

        const hasStructuredSource = nav.querySelector('details.soft-nav-group') || nav.querySelector('[data-sf-group]');
        const hasSeedableLinks = !hasStructuredSource && nav.querySelectorAll('a[href]').length <= 6;
        const grouped = collectNavItems(nav, hasSeedableLinks);
        const extraGroups = [];
        Array.from(grouped.keys()).forEach((groupName) => {
            if (SERVICE_NAV_GROUP_PRIORITY.indexOf(groupName) !== -1) return;
            if ((grouped.get(groupName) || []).length) {
                extraGroups.push(groupName);
            }
        });
        const groups = SERVICE_NAV_GROUP_PRIORITY.filter((group) => (grouped.get(group) || []).length).concat(extraGroups);
        const currentServiceLabel = getSegmentLabel(getServiceSegment(normalizeNavPath(location.pathname || '')));
        const toolbar = `
            <div class="soft-nav-toolbar" role="group" aria-label="사이드바 제어">
                <button type="button" class="soft-nav-control-btn" data-soft-nav="expand-all" aria-label="모든 메뉴 펼치기">전체 펼치기</button>
                <button type="button" class="soft-nav-control-btn" data-soft-nav="collapse-all" aria-label="모든 메뉴 접기">전체 접기</button>
            </div>
        `;
        const groupHtml = groups.map((groupName, groupIndex) => {
            const items = grouped.get(groupName) || [];
            if (!items.length) return '';
            const isActive = items.some((item) => item.ariaCurrent === 'page');
            const meta = getNavGroupMeta(groupName);
            const title = meta.title === '현재 서비스'
                ? `${meta.title || '현재 서비스'} (${ensureSafeText(currentServiceLabel)})`
                : meta.title || groupName;
            const icon = meta.icon || '🧭';
            const open = isActive || groupIndex === 0 || groupName === '현재 서비스' ? 'open' : '';
            const links = items.map((item) => `
                <a href="${item.href}" class="soft-nav-link flex items-center gap-3 px-4 py-2.5 rounded-lg hover:bg-slate-800 transition"${item.target ? ` target="${item.target}"` : ''}${item.rel ? ` rel="${item.rel}"` : ''}${item.ariaCurrent ? ' aria-current="page"' : ''} title="${item.title}">
                    <span aria-hidden="true">${item.icon}</span>${item.text}
                </a>
            `).join('');
            return `
                <details class="soft-nav-group" data-sf-group="${groupName}" ${open}>
                    <summary class="soft-nav-summary"><span>${icon} ${title}</span><span class="soft-nav-badge">${items.length}</span></summary>
                    <div class="soft-nav-sub">
                        ${links}
                    </div>
                </details>
            `;
        }).join('<div class="soft-nav-divider"></div>');

        if (!groupHtml) return;
        nav.dataset.sfStructured = '1';
        nav.innerHTML = `${toolbar}${preservedLeading.join('')}${groupHtml}`;
        const firstDetails = nav.querySelector('details');
        if (firstDetails) firstDetails.setAttribute('open', '');
        nav.querySelectorAll('.soft-nav-group[data-sf-group]').forEach((group) => {
            const menuLinks = group.querySelectorAll('.soft-nav-link');
            if (menuLinks.length > 0) {
                const badge = group.querySelector('.soft-nav-badge');
                if (badge) badge.textContent = `${menuLinks.length}`;
            }
        });
    }

    function syncSubprojectLinks() {
        const aside = document.querySelector('aside');
        if (!aside) return;

        const nav = aside.querySelector('nav');
        if (!nav) return;
        if (nav.querySelector('.soft-nav-group')) return;
        if (nav.dataset.sfSubprojectSynced === '1') return;

        const existingSection = nav.querySelector('[data-soft-subprojects]');
        if (existingSection) {
            const currentSectionLinks = new Set(
                Array.from(existingSection.querySelectorAll('a[href]')).map((link) => normalizeNavHref(link.getAttribute('href')))
            );
            const add = SUBPROJECT_LINKS.filter((item) => !currentSectionLinks.has(normalizeNavPath(item.href)));
            if (!add.length) return;
            existingSection.insertAdjacentHTML(
                'beforeend',
                add.map((item) =>
                    `<a href="${item.href}" class="soft-nav-link flex items-center gap-3 px-4 py-2.5 rounded-lg text-slate-300 hover:bg-slate-800 transition"><span aria-hidden="true">${item.icon}</span> <span>${item.label}</span></a>`
                ).join('')
            );
            return;
        }

        const currentLinks = new Set(
            Array.from(nav.querySelectorAll('a[href]')).map((link) => normalizeNavHref(link.getAttribute('href')))
        );
        const missing = SUBPROJECT_LINKS.filter((item) => !currentLinks.has(normalizeNavPath(item.href)));
        if (!missing.length) return;

        const existingServices = nav.querySelector('[data-soft-core-services]');
        if (existingServices) {
            existingServices.insertAdjacentHTML(
                'beforeend',
                missing.map((item) =>
                    `<a href="${item.href}" class="soft-nav-link flex items-center gap-3 px-4 py-2.5 rounded-lg text-slate-300 hover:bg-slate-800 transition"><span aria-hidden="true">${item.icon}</span> <span>${item.label}</span></a>`
                ).join('')
            );
            return;
        }

        const serviceSection = document.createElement('details');
        serviceSection.className = 'soft-nav-group';
        serviceSection.setAttribute('open', '');
        serviceSection.dataset.softSubprojects = 'true';
        serviceSection.innerHTML = `
            <summary class="soft-nav-summary"><span>운영 서비스</span></summary>
            <div class="soft-nav-sub">${missing.map((item) =>
                `<a href="${item.href}" class="soft-nav-link flex items-center gap-3 px-4 py-2.5 rounded-lg text-slate-300 hover:bg-slate-800 transition"><span aria-hidden="true">${item.icon}</span> <span>${item.label}</span></a>`
            ).join('')}</div>
        `;
        nav.appendChild(document.createElement('div')).className = 'soft-nav-divider';
        nav.appendChild(serviceSection);
        nav.dataset.sfSubprojectSynced = '1';
    }

    function syncCoreServiceLinks() {
        const nav = document.querySelector('aside nav');
        if (!nav) return;
        if (nav.querySelector('.soft-nav-group')) return;
        if (nav.dataset.sfCoreSynced === '1') return;
        const existing = new Map(
            Array.from(nav.querySelectorAll('a[href]')).map((anchor) => [normalizeNavHref(anchor.getAttribute('href')), anchor])
        );
        CORE_SERVICE_LINKS.forEach((item) => {
            const key = normalizeNavPath(item.href);
            if (existing.has(key)) return;
            const target = nav.querySelector('[data-soft-subprojects]');
            if (target) {
                target.insertAdjacentHTML('afterbegin', `<a href="${item.href}" class="soft-nav-link flex items-center gap-3 px-4 py-2.5 rounded-lg text-slate-300 hover:bg-slate-800 transition"><span aria-hidden="true">${item.icon}</span> <span>${item.label}</span></a>`);
            } else {
                const list = nav.querySelector('.soft-nav-sub[data-soft-service-default]') || nav;
                if (list !== nav && list instanceof HTMLElement) {
                    list.insertAdjacentHTML('beforeend', `<a href="${item.href}" class="soft-nav-link flex items-center gap-3 px-4 py-2.5 rounded-lg text-slate-300 hover:bg-slate-800 transition"><span aria-hidden="true">${item.icon}</span> <span>${item.label}</span></a>`);
                }
            }
        });
        nav.dataset.sfCoreSynced = '1';
    }

    function getPrimaryContentContainer() {
        return document.querySelector('main')
            || document.querySelector('.container')
            || document.querySelector('.content')
            || document.querySelector('#app')
            || (document.body ? document.body : null);
    }

    // ============ Sidebar Toggle ============
    let hamburger = document.querySelector('.hamburger');
    let sidebar = document.querySelector('aside');
    let overlay = null;

    function refreshDomRefs() {
        hamburger = document.querySelector('.hamburger');
        sidebar = document.querySelector('aside');
    }

    function createOverlay() {
        if (overlay) return overlay;
        overlay = document.createElement('div');
        overlay.className = 'sidebar-overlay';
        overlay.addEventListener('click', closeSidebar);
        document.body.appendChild(overlay);
        return overlay;
    }

    function openSidebar() {
        refreshDomRefs();
        if (!sidebar) return;
        const ov = createOverlay();
        sidebar.classList.add('sidebar-open');
        if (hamburger) hamburger.classList.add('active');
        // Use rAF for smooth animation
        requestAnimationFrame(() => {
            ov.style.display = 'block';
            requestAnimationFrame(() => {
                ov.classList.add('active');
            });
        });
        document.body.style.overflow = 'hidden';
    }

    function closeSidebar() {
        refreshDomRefs();
        if (!sidebar) return;
        sidebar.classList.remove('sidebar-open');
        if (hamburger) hamburger.classList.remove('active');
        if (overlay) {
            overlay.classList.remove('active');
            setTimeout(() => {
                overlay.style.display = 'none';
            }, 300);
        }
        document.body.style.overflow = '';
    }

    function bindSidebarEvents() {
        refreshDomRefs();
        if (hamburger) {
            hamburger.addEventListener('click', function(e) {
                e.stopPropagation();
                if (sidebar && sidebar.classList.contains('sidebar-open')) {
                    closeSidebar();
                } else {
                    openSidebar();
                }
            });
        }

        if (sidebar) {
            sidebar.querySelectorAll('a').forEach((link) => {
                link.addEventListener('click', () => {
                    if (window.innerWidth <= 768) {
                        closeSidebar();
                    }
                });
            });
        }
    }

    // Close sidebar on window resize to desktop
    let lastWidth = window.innerWidth;
    window.addEventListener('resize', () => {
        const currentWidth = window.innerWidth;
        if (lastWidth <= 768 && currentWidth > 768) {
            closeSidebar();
        }
        lastWidth = currentWidth;
    });

    // ============ Swipe Gesture for Sidebar ============
    let touchStartX = 0;
    let touchStartY = 0;
    let touchCurrentX = 0;
    let isSwiping = false;

    document.addEventListener('touchstart', function(e) {
        touchStartX = e.touches[0].clientX;
        touchStartY = e.touches[0].clientY;
        isSwiping = false;
    }, { passive: true });

    document.addEventListener('touchmove', function(e) {
        touchCurrentX = e.touches[0].clientX;
        const diffX = touchCurrentX - touchStartX;
        const diffY = Math.abs(e.touches[0].clientY - touchStartY);

        // Only trigger if horizontal swipe is dominant
        if (Math.abs(diffX) > diffY && Math.abs(diffX) > 30) {
            isSwiping = true;
        }
    }, { passive: true });

    document.addEventListener('touchend', function() {
        if (!isSwiping) return;
        const diffX = touchCurrentX - touchStartX;

        if (window.innerWidth <= 768) {
            // Swipe right from left edge to open sidebar
            if (diffX > 80 && touchStartX < 50) {
                openSidebar();
            }
            // Swipe left to close sidebar
            if (diffX < -80 && sidebar && sidebar.classList.contains('sidebar-open')) {
                closeSidebar();
            }
        }
        isSwiping = false;
    }, { passive: true });

    function getServicePrefix() {
        const path = normalizeNavPath(location.pathname || '');
        const keys = Object.keys(SERVICE_LINKS);
        return keys.find((key) => path === key || path.startsWith(key)) || '/platform/';
    }

    function shouldCreateFallbackSidebar() {
        const path = normalizeNavPath(location.pathname || '');
        const exempt = SIDEBAR_EXEMPT_PATH_PATTERNS.some((pattern) => pattern.test(path));
        const hasExplicitSidebar = !!document.querySelector('aside');
        return !exempt && !hasExplicitSidebar;
    }

    function isKnownServiceShellPath(pathname) {
        const path = normalizeNavPath(pathname || '');
        const segment = getServiceSegment(path);
        const serviceSegments = Object.keys(SERVICE_LINKS).map((value) => value.replace(/^\/|\/$/g, ''));
        return path === '/' || serviceSegments.includes(segment);
    }

    function syncCurrentPageMenuState() {
        const currentPath = normalizeNavPath(location.pathname || '');
        const nav = document.querySelector('aside nav');
        if (!nav) return;
        const candidates = [];
        Array.from(nav.querySelectorAll('a[href]')).forEach((link) => {
            const target = normalizeNavHref(link.getAttribute('href'));
            const active = currentPath === target
                || currentPath === `${target}/`
                || (target && `${target}/` === currentPath)
                || target.endsWith('/') && currentPath.startsWith(target)
                || currentPath.startsWith(`${target}/`);
            if (active) {
                candidates.push({ link, target });
            } else {
                link.removeAttribute('aria-current');
                link.classList.remove('bg-slate-800/60', 'border-l-2');
            }
        });

        if (!candidates.length) return;
        candidates.sort((a, b) => b.target.length - a.target.length);
        const winner = candidates[0].link;
        winner.setAttribute('aria-current', 'page');
        winner.classList.add('bg-slate-800/60', 'border-l-2', 'border-indigo-500');
        const activeGroup = winner.closest('.soft-nav-group');
        if (activeGroup instanceof HTMLElement) {
            activeGroup.setAttribute('open', '');
        }
    }

    function bindSidebarTreeControls() {
        const nav = document.querySelector('aside nav');
        if (!nav || nav.dataset.sfTreeControls === '1') return;
        const onNavClick = function(event) {
            const target = event.target;
            if (!(target instanceof HTMLElement)) return;
            const btn = target.closest('.soft-nav-control-btn');
            if (!btn || !nav.contains(btn)) return;
            const groups = nav.querySelectorAll('.soft-nav-group');
            if (btn.getAttribute('data-soft-nav') === 'expand-all') {
                groups.forEach((group) => group.setAttribute('open', 'open'));
                return;
            }
            if (btn.getAttribute('data-soft-nav') === 'collapse-all') {
                groups.forEach((group) => group.removeAttribute('open'));
            }
        };
        nav.addEventListener('click', onNavClick);
        nav.dataset.sfTreeControls = '1';
    }

    function applyKoreanTextCleanup() {
        const replacements = [
            ['Activity', '활동'],
            ['Current Service Menu', '현재 서비스 메뉴'],
            ['Tracking your active journey from application to reward settlement', '신규 신청부터 보상 정산까지의 여정을 추적합니다.'],
            ['No active journey found. Start exploring in Hub.', '진행 중인 여정이 없습니다. 허브에서 시작하세요.'],
            ['Reward Value', '보상 가치'],
            ['Portfolio', '캠페인 포트폴리오'],
            ['Dashboard', '대시보드']
        ];
        const walk = Array.from(document.querySelectorAll('nav a, nav p, nav span, h1, h2, h3, h4, p, header p'));
        walk.forEach((el) => {
            if (!el || !el.textContent) return;
            const text = el.textContent;
            replacements.forEach(([from, to]) => {
                if (text.trim() === from) {
                    el.textContent = text.replace(from, to);
                }
            });
        });
    }

    function enhanceContentSegmentation() {
        const main = getPrimaryContentContainer();
        if (!main) return;
        const directSections = Array.from(main.children).filter(
            (child) => child.tagName === 'SECTION' ||
                (child.tagName === 'ARTICLE' && child.querySelector('h2, h3, h4, h5, h6'))
        );
        const fallbackSections = directSections.length
            ? directSections
            : Array.from(main.querySelectorAll('section, .space-y-6 > section, .space-y-6 > article, .grid > section, .grid > article, .panel, .card, .soft-screen-section'));
        const fallbackPanels = Array.from(main.children).filter((child) => {
            if (!(child instanceof HTMLElement)) return false;
            if (!child.tagName) return false;
            if (child.matches('header, nav, aside, footer, script, style')) return false;
            if (child.matches('section, article, .panel, .card, .soft-screen-section')) return true;
            return false;
        });
        const sections = directSections.length ? directSections : Array.from(new Set(fallbackSections.concat(fallbackPanels)));

        sections.forEach((section, index) => {
            section.classList.add('soft-screen-section');
            section.setAttribute('role', 'region');
            const heading = section.querySelector('h2, h3, h4, h5, h6');
            if (heading && !section.hasAttribute('aria-label')) {
                section.setAttribute('aria-label', heading.textContent.trim());
            }
            if (!section.hasAttribute('aria-label')) {
                const navTitle = section.getAttribute('id') || section.className || '화면 영역';
                section.setAttribute('aria-label', navTitle.replace(/soft-+/gi, '').trim());
            }
            if (index > 0) {
                const hasHeading = section.querySelector('h2, h3, h4, h5, h6');
                if (!hasHeading) {
                    section.insertAdjacentHTML('beforebegin', '<hr class="soft-section-divider" aria-hidden="true">');
                }
            }
        });
    }

    function applyShellStyling() {
        const currentAside = document.querySelector('aside');
        if (!currentAside) return;
        document.documentElement.dataset.theme = 'dark';
        currentAside.classList.add('soft-sidebar');
        currentAside.classList.add('sf-nav-shell');
        document.body.classList.add('soft-shell');
        document.documentElement.lang = document.documentElement.lang || 'ko';
        if (!currentAside.classList.contains('soft-nav-tree')) {
            currentAside.classList.add('soft-nav-tree');
        }
        const nav = currentAside.querySelector('nav');
        if (nav && !nav.classList.contains('soft-nav-tree')) {
            nav.classList.add('soft-nav-tree');
        }
        const main = getPrimaryContentContainer();
        if (main) {
            main.classList.add('soft-main');
        }
        const header = document.querySelector('header');
        if (header) {
            header.classList.add('soft-topbar');
        }
    }

    function ensureUnifiedUiAssets() {
        const head = document.head;
        if (!head) return;

        if (!document.querySelector('link[href*="unified-ui.css"]')) {
            const link = document.createElement('link');
            link.rel = 'stylesheet';
            link.href = '/unified-ui.css';
            head.appendChild(link);
        }

        if (!document.querySelector('script[src*="unified-ui.js"]')) {
            const script = document.createElement('script');
            script.src = '/unified-ui.js';
            script.defer = true;
            head.appendChild(script);
        }

        if (!document.querySelector('script[src*="mobile-optimization.js"]')) {
            const script = document.createElement('script');
            script.src = '/mobile-optimization.js';
            script.defer = true;
            head.appendChild(script);
        }
    }

    function bindCore() {
        ensureUnifiedUiAssets();

        const servicePrefix = getServicePrefix();
        const isKnownServicePath = isKnownServiceShellPath(location.pathname || '');
        if (shouldCreateFallbackSidebar() && servicePrefix && Object.keys(SERVICE_LINKS).includes(servicePrefix)) {
            const serviceTitle = servicePrefix.includes('bohemian-marketing')
                ? '보헤미안 마케팅 AI'
                : servicePrefix.includes('instagram-cardnews')
                    ? 'Instagram 카드뉴스 자동화'
                    : servicePrefix.includes('webapp-builder')
                        ? '웹앱 빌더'
                        : servicePrefix.includes('/platform')
                            ? 'SoftFactory 허브'
                            : servicePrefix.includes('review')
                                ? '리뷰 대시보드'
                            : servicePrefix.includes('sns-auto')
                                    ? 'SNS 자동화'
                                    : servicePrefix.includes('ai-automation')
                                        ? 'AI 자동화'
                                        : servicePrefix.includes('coocook')
                                            ? 'CooCook'
                                            : servicePrefix.includes('growth-automation')
                                                ? 'Growth Automation'
                                            : 'SoftFactory 서비스';
            createFallbackSidebarForService(servicePrefix, serviceTitle);
        } else if (isKnownServicePath && shouldCreateFallbackSidebar() && !document.querySelector('aside')) {
            createFallbackSidebarForService('/platform/', 'SoftFactory 허브');
        }

        applyShellStyling();
        const nav = document.querySelector('aside nav');
        const hasStructuredSource = nav && (nav.querySelector('details.soft-nav-group') || nav.querySelector('[data-sf-group]'));
        if (!hasStructuredSource) {
            syncCoreServiceLinks();
            syncSubprojectLinks();
        }
        standardizeSidebarTree();
        syncCurrentPageMenuState();
        bindSidebarTreeControls();
        applyKoreanTextCleanup();
        enhanceContentSegmentation();
        bindSidebarEvents();
    }

    // ============ Keyboard Navigation ============
    document.addEventListener('keydown', function(e) {
        refreshDomRefs();
        if (e.key === 'Escape' && sidebar && sidebar.classList.contains('sidebar-open')) {
            closeSidebar();
        }
    });

    // ============ Viewport Height Fix (iOS) ============
    function setVhProperty() {
        const vh = window.innerHeight * 0.01;
        document.documentElement.style.setProperty('--vh', vh + 'px');
    }
    setVhProperty();
    window.addEventListener('resize', setVhProperty);

    // ============ Prevent Double-Tap Zoom ============
    let lastTouchEnd = 0;
    document.addEventListener('touchend', function(e) {
        const now = Date.now();
        if (now - lastTouchEnd <= 300) {
            e.preventDefault();
        }
        lastTouchEnd = now;
    }, false);

    // ============ Active State for Touch ============
    document.addEventListener('touchstart', function() {}, { passive: true });

    // ============ Auto-hide address bar on scroll (mobile) ============
    if (window.innerWidth <= 768) {
        let ticking = false;
        const mainContent = getPrimaryContentContainer() || document.querySelector('.flex-1.overflow-y-auto');
        if (mainContent) {
            mainContent.addEventListener('scroll', function() {
                if (!ticking) {
                    ticking = true;
                    requestAnimationFrame(() => { ticking = false; });
                }
            }, { passive: true });
        }
    }

    bindCore();

})();

(function () {
    const CHANNELS = {
        instagram: {
            key: 'instagram',
            label: 'Instagram',
            icon: '📸',
            formats: ['instagram-carousel-4-5', 'instagram-feed-1-1', 'instagram-story-9-16'],
            limits: { slide_min: 4, slide_max: 10 },
            policy: '카드뉴스 권장: 4:5 또는 1:1, 1080px 기준, 텍스트 오버레이 과다 제한'
        },
        threads: {
            key: 'threads',
            label: 'Threads',
            icon: '🧵',
            formats: ['threads-carousel-1-1', 'threads-story-4-5'],
            limits: { slide_min: 3, slide_max: 10 },
            policy: '텍스트는 2~3줄/슬라이드 단위, 브랜드 톤과 해시태그 가독성 유지'
        },
        x: {
            key: 'x',
            label: 'X(트윗/스레드)',
            icon: '✖',
            formats: ['x-feed-16-9', 'x-card-16-9'],
            limits: { slide_min: 1, slide_max: 12 },
            policy: '썸네일형 카드 1200x675(16:9) 기반, 요약형 카피 우선'
        }
    };

    const DEFAULT_FORMATS = {
        'instagram-carousel-4-5': { id: 'instagram-carousel-4-5', label: 'Instagram 캐러셀 4:5', width: 1080, height: 1350, ratio: '4:5', pixel: '1080×1350' },
        'instagram-feed-1-1': { id: 'instagram-feed-1-1', label: 'Instagram 피드 1:1', width: 1080, height: 1080, ratio: '1:1', pixel: '1080×1080' },
        'instagram-story-9-16': { id: 'instagram-story-9-16', label: 'Instagram 스토리 9:16', width: 1080, height: 1920, ratio: '9:16', pixel: '1080×1920' },
        'threads-carousel-1-1': { id: 'threads-carousel-1-1', label: 'Threads 캐러셀 1:1', width: 1080, height: 1080, ratio: '1:1', pixel: '1080×1080' },
        'threads-story-4-5': { id: 'threads-story-4-5', label: 'Threads 카드 4:5', width: 1080, height: 1350, ratio: '4:5', pixel: '1080×1350' },
        'x-feed-16-9': { id: 'x-feed-16-9', label: 'X 카드 16:9', width: 1200, height: 675, ratio: '16:9', pixel: '1200×675' },
        'x-card-16-9': { id: 'x-card-16-9', label: 'X 링크카드 16:9', width: 1200, height: 675, ratio: '16:9', pixel: '1200×675' }
    };

    const FONT_PRESETS = ['Inter', 'Pretendard', 'Noto Sans KR', 'Apple SD Gothic Neo', 'Roboto', 'Montserrat'];

    const DEFAULT_AI_PROVIDERS = {
        openai: {
            keyLabel: 'OpenAI API Key',
            placeholder: 'sk-...',
            defaultEngine: 'gpt-4o-mini'
        },
        gemini: {
            keyLabel: 'Gemini API Key',
            placeholder: 'AIza...',
            defaultEngine: 'gemini-1.5-flash'
        }
    };

    const safe = (value, fallback = '') => {
        if (value === null || typeof value === 'undefined') return fallback;
        return value;
    };

    function getChannelLibrary() {
        return CHANNELS;
    }

    function getDefaultFormats() {
        return DEFAULT_FORMATS;
    }

    function getDefaultFonts() {
        return FONT_PRESETS;
    }

    function getAiProviders() {
        return DEFAULT_AI_PROVIDERS;
    }

    function normalizeChannels(selectedChannels) {
        if (!Array.isArray(selectedChannels)) return [];
        return selectedChannels
            .filter((channel) => channel && channel.platform)
            .map((channel) => ({
                platform: String(channel.platform).toLowerCase(),
                format: safe(channel.format, 'instagram-carousel-4-5'),
                include_hashtags: Boolean(channel.include_hashtags ?? true),
                posting_time: safe(channel.posting_time, null)
            }));
    }

    function buildDraftPayload(input = {}) {
        const payload = {
            topic: safe(input.topic, '').trim(),
            tone: safe(input.tone, 'balanced'),
            slide_count: Math.max(1, Number(input.slide_count || 6)),
            template_id: safe(input.template_id, ''),
            account_ids: Array.isArray(input.account_ids) ? input.account_ids : [],
            channels: normalizeChannels(input.channels || []),
            keywords: Array.isArray(input.keywords) ? input.keywords : [],
            design: input.design || {},
            ai: input.ai || { provider: 'openai', apiKey: '' },
            automation: {
                enabled: Boolean(input.automation?.enabled),
                frequency: safe(input.automation?.frequency, 'daily'),
                max_posts_per_day: Number(input.automation?.max_posts_per_day || 1),
                timezone: safe(input.automation?.timezone, 'Asia/Seoul')
            }
        };

        const selectedFormat = getDefaultFormats()[payload.channels?.[0]?.format] || null;
        if (selectedFormat) payload.render_target = selectedFormat;
        return payload;
    }

    function buildTemplatePayload(input = {}) {
        const structureText = safe(input.structure, '');
        const structure = Array.isArray(structureText)
            ? structureText
            : String(structureText || '')
                .split('\n')
                .map((item) => item.trim())
                .filter(Boolean);

        return {
            id: safe(input.id, ''),
            name: safe(input.name, '새 템플릿'),
            tone: safe(input.tone, 'balanced'),
            description: safe(input.description, ''),
            slides: Math.max(1, Number(input.slides || input.slideCount || 6)),
            structure,
            design: {
                fontFamily: safe(input.fontFamily, 'Inter'),
                titleSize: Number(input.titleSize || 18),
                bodySize: Number(input.bodySize || 13),
                titleAlign: safe(input.titleAlign, 'left'),
                bodyAlign: safe(input.bodyAlign, 'left'),
                titlePosition: safe(input.titlePosition, 'top'),
                textColor: safe(input.textColor, '#f8fafc'),
                accentColor: safe(input.accentColor, '#6366f1'),
                backgroundColor: safe(input.backgroundColor, '#0f172a')
            },
            format: safe(input.format, 'instagram-carousel-4-5'),
            tags: Array.isArray(input.tags) ? input.tags : []
        };
    }

    function makeStyleVars(design) {
        const d = design || {};
        return {
            '--card-font-family': d.fontFamily || 'Inter',
            '--card-title-size': `${Number(d.titleSize || 18)}px`,
            '--card-body-size': `${Number(d.bodySize || 13)}px`,
            '--card-text-color': d.textColor || '#f8fafc',
            '--card-accent-color': d.accentColor || '#6366f1',
            '--card-bg': d.backgroundColor || '#0f172a',
            '--card-title-align': d.titleAlign || 'left',
            '--card-body-align': d.bodyAlign || 'left'
        };
    }

    window.CardNewsAutomationCore = {
        CHANNELS,
        DEFAULT_FORMATS: DEFAULT_FORMATS,
        FONT_PRESETS,
        DEFAULT_AI_PROVIDERS,
        getChannelLibrary,
        getDefaultFormats,
        getDefaultFonts,
        getAiProviders,
        normalizeChannels,
        buildDraftPayload,
        buildTemplatePayload,
        makeStyleVars
    };
})();

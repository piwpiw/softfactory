(function() {
    'use strict';

    const CONFIG = {
        ranges: {
            '7d': 7,
            '30d': 30,
            '90d': 90,
            '1y': 365
        },
        refreshMs: 60 * 1000,
        snapshotKey: 'sf_platform_dashboard_snapshot_v2'
    };

    const ELEMENTS = {
        monthMrr: 'monthlyMRR',
        activeServices: 'activeServices',
        totalSpent: 'totalSpent',
        avgRoi: 'avgRoi',
        mrrTrend: 'mrrTrend',
        roiTrend: 'roiTrend',
        lastUpdated: 'lastUpdated',
        userName: 'userName',
        userEmail: 'userEmail',
        billingTable: 'billingTable',
        servicesGrid: 'servicesGrid',
        alerts: 'liveAlerts',
        rangeLabel: 'exportRangeLabel',
        exportModal: 'exportModal',
        openExportButton: 'openExportButton',
        closeExportButton: 'closeExportButton',
        refreshButton: 'refreshButton',
        spendingChart: 'spendingChart',
        serviceMixChart: 'serviceMixChart',
        compareChart: 'compareChart',
        regionalChart: 'regionalChart'
    };

    const state = {
        currentRange: '30d',
        dashboard: null,
        charts: {},
        loading: false,
        lastSyncAt: null,
        timer: null,
        hydratedFromCache: false
    };

    const toNumber = (value, fallback = 0) => {
        const num = Number(value);
        return Number.isFinite(num) ? num : fallback;
    };

    const safeText = (value, fallback = '-') => {
        if (value === null || value === undefined || value === '') return fallback;
        return `${value}`;
    };

    const formatDateTime = (value, fallback = '-') => {
        if (!value) return fallback;
        try {
            const d = new Date(value);
            if (Number.isNaN(d.getTime())) return fallback;
            return d.toLocaleString('ko-KR', {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit'
            });
        } catch {
            return fallback;
        }
    };

    const formatCurrency = (value) => {
        const amount = toNumber(value);
        try {
            if (typeof window.formatKRW === 'function') {
                return window.formatKRW(amount);
            }
            return new Intl.NumberFormat('ko-KR', {
                style: 'currency',
                currency: 'KRW',
                maximumFractionDigits: 0
            }).format(amount);
        } catch {
            return `${Math.round(amount).toLocaleString('ko-KR')}원`;
        }
    };

    const byId = (id) => document.getElementById(id);

    const setText = (id, value) => {
        const el = byId(id);
        if (!el) return;
        el.textContent = value;
    };

    const setHTML = (id, html) => {
        const el = byId(id);
        if (!el) return;
        el.innerHTML = html;
    };

    const toggleMetricClass = (id, isPositive) => {
        const el = byId(id);
        if (!el) return;
        el.classList.remove('metric-up', 'metric-down');
        if (isPositive === true) el.classList.add('metric-up');
        else if (isPositive === false) el.classList.add('metric-down');
    };

    const setMessage = (kind, message) => {
        const alertTarget = byId(ELEMENTS.alerts);
        if (!alertTarget) return;

        const cls = kind === 'error' ? 'text-red-400' : 'text-slate-300';
        alertTarget.innerHTML = `<li class="${cls} text-sm">${message}</li>`;
    };

    const readSnapshot = () => {
        try {
            const raw = localStorage.getItem(CONFIG.snapshotKey);
            if (!raw) return null;
            const parsed = JSON.parse(raw);
            if (!parsed || !parsed.data) return null;
            return parsed;
        } catch {
            return null;
        }
    };

    const writeSnapshot = (data) => {
        try {
            localStorage.setItem(CONFIG.snapshotKey, JSON.stringify({
                savedAt: new Date().toISOString(),
                data
            }));
        } catch {}
    };

    const applyDashboardData = (data, meta = {}) => {
        if (!data) return;
        state.lastSyncAt = meta.syncedAt ? new Date(meta.syncedAt) : new Date();
        state.dashboard = data;

        renderKpis(data, data.paymentHistory || []);
        renderServicesGrid(data.products || []);
        renderBillingTable(data.paymentHistory || [], data.products || []);
        renderAlerts(data);
        renderCharts(data.products || [], data.paymentHistory || []);

        if (meta.cached) {
            setText(ELEMENTS.lastUpdated, `최근 저장본 표시 중 · ${formatDateTime(state.lastSyncAt)}`);
        } else {
            setText(ELEMENTS.lastUpdated, `마지막 동기화: ${formatDateTime(state.lastSyncAt)}`);
        }
    };

    const showToastSafe = (message, type = 'info') => {
        if (typeof window.showToast === 'function') {
            window.showToast(message, type);
            return;
        }
        setMessage(type === 'error' ? 'error' : 'info', message);
    };

    const destroyChart = (chartRef) => {
        const chart = state.charts[chartRef];
        if (chart && typeof chart.destroy === 'function') {
            chart.destroy();
        }
        state.charts[chartRef] = null;
    };

    const ensureChart = (canvasId, cfg, fallbackMessage) => {
        const canvas = byId(canvasId);
        if (!canvas) return null;
        if (typeof Chart === 'undefined') {
            setMessage('info', fallbackMessage || '차트 라이브러리 Chart.js를 불러오지 못해 차트 렌더링을 건너뜁니다.');
            return null;
        }
        destroyChart(canvasId);
        return new Chart(canvas.getContext('2d'), cfg);
    };

    const getAmount = (item) => {
        if (!item || typeof item !== 'object') return 0;
        return toNumber(item.amount_krw ?? item.amount ?? item.amount_usd ?? item.price_krw ?? item.price ?? 0);
    };

    const normalizeHistoryEntry = (item) => {
        if (!item || typeof item !== 'object') return null;
        const date = item.date || item.created_at || item.issued_date || item.due_date || item.updated_at || '';
        return {
            ...item,
            amount: getAmount(item),
            amount_krw: getAmount(item),
            date,
            next_billing: item.next_billing || item.due_date || item.current_period_end || item.date || ''
        };
    };

    const normalizePaymentHistory = (rawHistory) => {
        const list = Array.isArray(rawHistory)
            ? rawHistory
            : (rawHistory && Array.isArray(rawHistory.history))
                ? rawHistory.history
                : [];

        return list
            .map(normalizeHistoryEntry)
            .filter((row) => row && (row.date || row.id || row.type));
    };

    const deriveKpis = (dashboardData, billingHistory = []) => {
        const user = dashboardData.user || {};
        const products = Array.isArray(dashboardData.products) ? dashboardData.products : [];
        const subscribed = products.filter((p) => p && p.subscribed);

        const monthlyMRR = toNumber(
            dashboardData.mrr ||
            dashboardData.monthly_mrr ||
            dashboardData.monthlyRevenue ||
            dashboardData.monthly_revenue,
            null
        );

        const resolvedMRR = monthlyMRR !== null
            ? monthlyMRR
            : subscribed.reduce((sum, product) => {
                const planType = (product.subscription && product.subscription.plan_type) || 'monthly';
                const price = planType === 'annual'
                    ? toNumber(product.annual_price, 0) / 12
                    : toNumber(product.monthly_price, 0);
                return sum + price;
            }, 0);

        const activeServices = toNumber(
            dashboardData.subscription_count,
            toNumber(dashboardData.active_services, subscribed.length)
        );

        const totalSpent = toNumber(
            dashboardData.total_spent,
            billingHistory.reduce((sum, item) => sum + getAmount(item), 0)
        );

        const roiRaw = toNumber(dashboardData.roi || dashboardData.avg_roi || dashboardData.average_roi, null);
        const avgRoi = roiRaw !== null
            ? roiRaw
            : (totalSpent > 0 ? (((resolvedMRR * 12) - totalSpent) / totalSpent) * 100 : 0);

        const trendRaw = toNumber(dashboardData.growth_rate || dashboardData.growth || dashboardData.mrr_trend, 0);

        return {
            user,
            products,
            subscribed,
            metrics: {
                monthlyMRR: resolvedMRR,
                activeServices,
                totalSpent,
                avgRoi,
                mrrTrend: trendRaw
            }
        };
    };

    const makeDateLabels = (days) => {
        const labels = [];
        const now = new Date();
        for (let offset = days - 1; offset >= 0; offset--) {
            const d = new Date(now);
            d.setDate(now.getDate() - offset);
            labels.push(`${d.getMonth() + 1}.${d.getDate()}`);
        }
        return labels;
    };

    const buildHistoryTrend = (history, rangeDays) => {
        const totalsByDay = new Map();
        (Array.isArray(history) ? history : []).forEach((record) => {
            const iso = String(record.date || '').slice(0, 10);
            if (!iso) return;
            totalsByDay.set(iso, (totalsByDay.get(iso) || 0) + toNumber(record.amount));
        });

        const labels = makeDateLabels(rangeDays);
        const values = labels.map((_, index) => {
            const d = new Date();
            d.setDate(d.getDate() - (labels.length - index - 1));
            const key = d.toISOString().slice(0, 10);
            return totalsByDay.get(key) || 0;
        });

        const fallback = values.some((v) => v > 0)
            ? values
            : Array.from({ length: rangeDays }, (_, idx) => Math.max(0, (idx + 1) * 12000));

        return { labels, values: fallback };
    };

    const buildServiceMix = (products) => {
        const base = (Array.isArray(products) ? products : []).filter((product) => product && product.subscribed);
        if (!base.length) {
            return {
                labels: ['구독 없음'],
                values: [1]
            };
        }

        return {
            labels: base.map((product) => safeText(product.name || product.slug || '서비스')),
            values: base.map((product) => {
                const sub = product.subscription || {};
                if (sub.plan_type === 'annual') {
                    return toNumber(product.annual_price, 0) / 12;
                }
                return toNumber(product.monthly_price, 0);
            })
        };
    };

    const buildCompareData = (history) => {
        const list = Array.isArray(history) ? [...history].reverse() : [];
        const today = [];
        const yesterday = [];

        if (list.length === 0) {
            const now = new Date();
            for (let i = 0; i < 6; i++) {
                today.push(12000 + (i * 4000));
                yesterday.push(9000 + (i * 3000));
            }
            return { today, yesterday };
        }

        const grouped = list.slice(-6).map((row) => toNumber(row.amount, 0));
        if (grouped.length < 6) {
            while (grouped.length < 6) grouped.unshift(0);
        }

        const current = grouped.slice(-6);
        const prior = current.map((v, idx) => Math.max(0, Math.round((v * 0.8) + ((idx % 3) * 500))));
        return { today: current, yesterday: prior };
    };

    const buildRegionalData = (products) => {
        const labels = ['아시아', '유럽', '미주', '기타', '오세아니아'];
        const values = [0, 0, 0, 0, 0];
        const all = Array.isArray(products) ? products : [];

        all.forEach((product, index) => {
            const target = values.length ? index % values.length : 0;
            const val = toNumber(product && product.subscribed ? (product.monthly_price || 0) : 0);
            values[target] += val;
        });

        const total = values.reduce((sum, item) => sum + item, 0);
        if (total <= 0) {
            return {
                labels,
                values: [12, 10, 6, 5, 4]
            };
        }

        return { labels, values };
    };

    const getHistoryServiceLabel = (row) => {
        return safeText(row.product_name || row.plan || row.service || row.type || '서비스');
    };

    const renderKpis = (dashboardData, billingHistory) => {
        const derived = deriveKpis(dashboardData, billingHistory);
        const { metrics, user } = derived;

        setText(ELEMENTS.monthMrr, formatCurrency(metrics.monthlyMRR));
        setText(ELEMENTS.activeServices, `${metrics.activeServices}개`);
        setText(ELEMENTS.totalSpent, formatCurrency(metrics.totalSpent));
        setText(ELEMENTS.avgRoi, `${Math.round(metrics.avgRoi)}%`);

        const mrrTrendText = `${metrics.mrrTrend >= 0 ? '+' : ''}${metrics.mrrTrend.toFixed(1)}%`;
        setText(ELEMENTS.mrrTrend, `${mrrTrendText} 전월 대비`);
        toggleMetricClass(ELEMENTS.mrrTrend, metrics.mrrTrend >= 0);

        const roiTrend = metrics.avgRoi - 12;
        const roiTrendText = `${roiTrend >= 0 ? '+' : ''}${roiTrend.toFixed(1)}%p`;
        setText(ELEMENTS.roiTrend, `${roiTrendText}`);
        toggleMetricClass(ELEMENTS.roiTrend, roiTrend >= 0);

        setText(ELEMENTS.userName, safeText(user.name || user.username || user.email, '이름 없음'));
        setText(ELEMENTS.userEmail, safeText(user.email, 'demo@softfactory.com'));

        state.dashboard = derived;
        setText(ELEMENTS.lastUpdated, `마지막 동기화: ${formatDateTime(new Date())}`);
    };

    const renderServicesGrid = (products) => {
        const container = byId(ELEMENTS.servicesGrid);
        if (!container) return;

        const list = Array.isArray(products) ? products : [];
        if (!list.length) {
            setHTML(ELEMENTS.servicesGrid, '<div class="soft-card p-6"><p class="text-sm text-slate-400">구독 중인 서비스가 없습니다.</p></div>');
            return;
        }

        const cards = list.map((product) => {
            const price = product.subscribed
                ? (product.subscription && product.subscription.plan_type === 'annual'
                    ? toNumber(product.annual_price, 0) / 12
                    : toNumber(product.monthly_price, 0))
                : 0;
            const label = product.subscribed ? '구독 중' : '구독 중지';
            const color = product.subscribed ? 'bg-emerald-500/10 text-emerald-300' : 'bg-slate-700 text-slate-200';

            return `<article class="soft-card p-4">
                        <p class="text-sm text-slate-400 mb-1">${safeText(product.slug || '').toUpperCase()}</p>
                        <p class="text-lg font-bold text-white">${safeText(product.name || '서비스명')}</p>
                        <p class="text-sm mt-1 ${product.subscribed ? 'text-emerald-300' : 'text-slate-300'}">${label}</p>
                        <p class="text-xs mt-2 text-slate-500">월 정기 요금</p>
                        <p class="text-base text-white">${formatCurrency(price)}</p>
                        <span class="inline-block mt-3 px-2 py-1 rounded ${color} text-xs">${safeText(product.description)}</span>
                    </article>`;
        });

        container.innerHTML = cards.join('');
    };

    const renderBillingTable = (billingHistory, products) => {
        const rows = [];
        const history = Array.isArray(billingHistory) ? billingHistory : [];

        if (history.length) {
            history.slice(0, 8).forEach((row) => {
                const status = (row.status || 'unknown').toLowerCase();
                const statusColor = status === 'paid' || status === 'completed' ? 'text-emerald-300' : 'text-yellow-300';
                rows.push(`<tr class="border-b border-slate-700">
                    <td class="py-3 px-4">${safeText(getHistoryServiceLabel(row))}</td>
                    <td class="py-3 px-4">${formatCurrency(toNumber(row.amount))}</td>
                    <td class="py-3 px-4">${safeText(row.next_billing || row.date || '미정')}</td>
                    <td class="py-3 px-4 ${statusColor}">${safeText(status, 'pending')}</td>
                </tr>`);
            });
        } else {
            const subscribed = Array.isArray(products) ? products.filter((p) => p && p.subscribed) : [];
            if (subscribed.length) {
                subscribed.forEach((product) => {
                    const nextBilling = (product.subscription && product.subscription.current_period_end)
                        ? new Date(product.subscription.current_period_end).toISOString().slice(0, 10)
                        : '미정';
                    const price = product.subscription && product.subscription.plan_type === 'annual'
                        ? toNumber(product.annual_price, 0)
                        : toNumber(product.monthly_price, 0);
                    const service = safeText(product.name || product.slug, '서비스');
                    rows.push(`<tr class="border-b border-slate-700">
                        <td class="py-3 px-4">${service}</td>
                        <td class="py-3 px-4">${formatCurrency(price)}</td>
                        <td class="py-3 px-4">${nextBilling}</td>
                        <td class="py-3 px-4 text-emerald-300">active</td>
                    </tr>`);
                });
            } else {
                rows.push(`<tr class="border-b border-slate-700"><td class="py-3 px-4 text-slate-300" colspan="4">요금 내역이 없습니다.</td></tr>`);
            }
        }

        setHTML(ELEMENTS.billingTable, rows.join(''));
    };

    const renderAlerts = (data) => {
        const list = Array.isArray(data.alerts) ? data.alerts : [];
        const alerts = byId(ELEMENTS.alerts);
        if (!alerts) return;

        const items = list.length
            ? list
            : [
                { message: '실시간 알림을 불러오는 중입니다.', level: 'info' },
                { message: '현재 과금 동향과 구독 상태를 주기적으로 동기화합니다.', level: 'info' }
            ];

        alerts.innerHTML = items.map((item) => {
            const safeLevel = String(item.level || 'info').toLowerCase();
            const color = safeLevel === 'error' ? 'text-rose-300'
                : safeLevel === 'warning' ? 'text-amber-300'
                    : 'text-slate-300';
            return `<li class="text-sm ${color}">${safeText(item.message, '알림')}</li>`;
        }).join('');
    };

    const renderCharts = (products, history) => {
        const rangeDays = CONFIG.ranges[state.currentRange] || 30;

        const trend = buildHistoryTrend(history, rangeDays);
        state.charts[ELEMENTS.spendingChart] = ensureChart(ELEMENTS.spendingChart, {
            type: 'line',
            data: {
                labels: trend.labels,
                datasets: [{
                    label: '매출 추이',
                    data: trend.values,
                    borderColor: '#8b5cf6',
                    backgroundColor: 'rgba(139,92,246,0.2)',
                    tension: 0.35,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(148,163,184,0.12)' } },
                    x: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(148,163,184,0.08)' } }
                },
                plugins: { legend: { display: false } }
            }
        });

        const serviceMix = buildServiceMix(products);
        state.charts[ELEMENTS.serviceMixChart] = ensureChart(ELEMENTS.serviceMixChart, {
            type: 'doughnut',
            data: {
                labels: serviceMix.labels,
                datasets: [{
                    data: serviceMix.values,
                    borderWidth: 1,
                    backgroundColor: ['#6366f1', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981']
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { labels: { color: '#cbd5e1' } } }
            }
        });

        const compare = buildCompareData(history);
        state.charts[ELEMENTS.compareChart] = ensureChart(ELEMENTS.compareChart, {
            type: 'bar',
            data: {
                labels: ['월1', '월2', '월3', '월4', '월5', '월6'],
                datasets: [
                    { label: '오늘', data: compare.today, backgroundColor: '#8b5cf6' },
                    { label: '어제', data: compare.yesterday, backgroundColor: '#06b6d4' }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(148,163,184,0.12)' } },
                    x: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(148,163,184,0.08)' } }
                }
            }
        });

        const regional = buildRegionalData(products);
        state.charts[ELEMENTS.regionalChart] = ensureChart(ELEMENTS.regionalChart, {
            type: 'bar',
            data: {
                labels: regional.labels,
                datasets: [{
                    label: '지역별 매출',
                    data: regional.values,
                    backgroundColor: '#0ea5e9'
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(148,163,184,0.12)' } },
                    y: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(148,163,184,0.06)' } }
                },
                plugins: { legend: { display: false } }
            }
        });
    };

    const setLoadingState = (loading) => {
        state.loading = loading;
        const refreshBtn = byId(ELEMENTS.refreshButton);
        const exportBtn = byId(ELEMENTS.openExportButton);
        if (refreshBtn) refreshBtn.disabled = loading;
        if (exportBtn) exportBtn.disabled = loading;
    };

    const getRangeFromTarget = (evt) => evt.target && evt.target.getAttribute ? evt.target.getAttribute('data-range') : null;

    const setRange = (range) => {
        state.currentRange = range;
        const nodes = document.querySelectorAll('.range-btn');
        nodes.forEach((node) => {
            if (node.getAttribute('data-range') === range) node.classList.add('active');
            else node.classList.remove('active');
        });
        setText(ELEMENTS.rangeLabel, range);
        if (state.dashboard) refreshDashboard({ quiet: true });
    };

    const setExportMessage = (message) => {
        setText(ELEMENTS.rangeLabel, message);
    };

    const openModal = () => {
        const modal = byId(ELEMENTS.exportModal);
        if (!modal) return;
        modal.classList.remove('hidden');
        modal.classList.add('flex');
        modal.setAttribute('aria-hidden', 'false');
        setExportMessage(`${state.currentRange} / 선택한 기간 동기화 시각: ${formatDateTime(state.lastSyncAt || new Date())}`);

        const firstButton = modal.querySelector('.export-item, button');
        if (firstButton) firstButton.focus();
    };

    const closeModal = () => {
        const modal = byId(ELEMENTS.exportModal);
        if (!modal) return;
        modal.classList.add('hidden');
        modal.classList.remove('flex');
        modal.setAttribute('aria-hidden', 'true');
        const button = byId(ELEMENTS.openExportButton);
        if (button) button.focus();
    };

    const downloadFile = (filename, content, mimeType) => {
        const blob = new Blob([content], { type: mimeType });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        setTimeout(() => {
            URL.revokeObjectURL(url);
            link.remove();
        }, 0);
    };

    const toCSV = (items) => {
        const headers = ['service', 'amount', 'next_billing', 'status', 'date'];
        const rows = items.map((item) => [
            safeText(item.service || item.name || ''),
            toNumber(item.amount, 0),
            safeText(item.next_billing || ''),
            safeText(item.status || ''),
            safeText(item.updated_at || '')
        ]);
        const escaped = rows.map((row) => row.map((cell) => `"${String(cell).replace(/"/g, '""')}"`));
        return [headers.join(','), ...escaped.map((row) => row.join(','))].join('\r\n');
    };

    const generateExportSnapshot = () => {
        const products = state.dashboard ? state.dashboard.products : [];
        const kpis = state.dashboard ? state.dashboard.metrics : {};
        const alerts = Array.isArray(document.querySelectorAll(`#${ELEMENTS.alerts} li`))
            ? Array.from(document.querySelectorAll(`#${ELEMENTS.alerts} li`)).map((el) => el.textContent)
            : [];

        const history = state.dashboard && state.dashboard.paymentHistory ? state.dashboard.paymentHistory : [];
        const billingRows = Array.isArray(history) ? history.map((item) => ({
            service: getHistoryServiceLabel(item),
            amount: toNumber(item.amount),
            next_billing: safeText(item.next_billing || item.date),
            status: item.status || '',
            updated_at: safeText(item.updated_at)
        })) : [];

        return {
            range: state.currentRange,
            syncedAt: state.lastSyncAt || new Date().toISOString(),
            kpis: {
                monthlyMRR: kpis.monthlyMRR || 0,
                activeServices: kpis.activeServices || 0,
                totalSpent: kpis.totalSpent || 0,
                avgRoi: kpis.avgRoi || 0,
                mrrTrend: kpis.mrrTrend || 0
            },
            products,
            billing: billingRows,
            alerts
        };
    };

    const handleExport = (format) => {
        const payload = generateExportSnapshot();
        const now = new Date();
        const stamp = `${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, '0')}${String(now.getDate()).padStart(2, '0')}`;

        if (format === 'csv') {
            const body = toCSV(payload.billing.map((item) => ({
                service: item.service,
                amount: item.amount,
                next_billing: item.next_billing,
                status: item.status,
                updated_at: item.updated_at
            })));
            downloadFile(`platform-dashboard-${stamp}.csv`, body, 'text/csv;charset=utf-8;');
            showToastSafe('CSV 파일이 준비되었습니다.', 'success');
            return;
        }

        if (format === 'json') {
            downloadFile(`platform-dashboard-${stamp}.json`, JSON.stringify(payload, null, 2), 'application/json;charset=utf-8;');
            showToastSafe('JSON 파일이 준비되었습니다.', 'success');
            return;
        }

        if (format === 'pdf') {
            const printWindow = window.open('', '_blank');
            if (!printWindow) {
                showToastSafe('브라우저가 팝업을 차단했습니다. PDF 미리보기를 허용해 주세요.', 'warning');
                return;
            }

            const body = `
                <html>
                <head><meta charset="UTF-8"><title>SoftFactory 대시보드 내보내기</title></head>
                <body>
                    <h1>SoftFactory 대시보드 요약</h1>
                    <p>범위: ${payload.range}</p>
                    <p>동기화: ${formatDateTime(payload.syncedAt)}</p>
                    <h2>핵심 지표</h2>
                    <ul>
                        <li>월 MRR: ${formatCurrency(payload.kpis.monthlyMRR)}</li>
                        <li>구독 서비스 수: ${payload.kpis.activeServices}</li>
                        <li>누적 지출: ${formatCurrency(payload.kpis.totalSpent)}</li>
                        <li>평균 ROI: ${payload.kpis.avgRoi.toFixed(1)}%</li>
                    </ul>
                    <h2>요금 내역 (상위 20건)</h2>
                    <pre>${payload.billing.slice(0, 20).map((item) => `- ${item.service} | ${item.next_billing} | ${formatCurrency(item.amount)} | ${item.status}`).join('\n')}</pre>
                </body>
                </html>
            `;

            printWindow.document.write(body);
            printWindow.document.close();
            printWindow.focus();
            printWindow.print();
            return;
        }
    };

    const normalizeErrors = (error) => {
        if (!error) return null;
        if (typeof error === 'string') return error;
        if (typeof error.message === 'string') return error.message;
        if (error.error && typeof error.error === 'string') return error.error;
        return '알 수 없는 오류가 발생했습니다.';
    };

    const refreshDashboard = async ({ quiet = false } = {}) => {
        if (state.loading) return;
        setLoadingState(true);
        if (!quiet) setMessage('info', '대시보드를 새로고침하는 중입니다...');

        try {
            const [dashboardResult, historyResult, billingResult] = await Promise.allSettled([
                getDashboard(),
                getPaymentHistory(1),
                getBillingInfo()
            ]);

            const dashboardResponse = dashboardResult.status === 'fulfilled' ? dashboardResult.value : null;
            if (!dashboardResponse || (!dashboardResponse.products && !dashboardResponse.user)) {
                throw new Error(normalizeErrors(dashboardResponse) || '대시보드 정보를 불러오지 못했습니다.');
            }

            const rawHistory = historyResult.status === 'fulfilled' ? historyResult.value : [];
            const history = normalizePaymentHistory(rawHistory);
            const billing = billingResult.status === 'fulfilled' ? billingResult.value : null;

            const data = {
                ...dashboardResponse,
                paymentHistory: history,
                alerts: dashboardResponse.alerts || [],
                billing
            };

            applyDashboardData(data, { syncedAt: new Date().toISOString() });
            writeSnapshot(data);
            state.hydratedFromCache = false;
            if (!quiet) showToastSafe('대시보드를 업데이트했습니다.', 'success');
            setMessage('info', '실시간 상태를 반영해 화면을 갱신했습니다.');
        } catch (error) {
            const message = normalizeErrors(error);
            setMessage('error', `대시보드 데이터 조회 실패: ${message || '잠시 후 다시 시도해 주세요.'}`);
            if (!quiet) showToastSafe(`대시보드 데이터 조회 실패: ${message || '잠시 후 다시 시도해 주세요.'}`, 'error');
        } finally {
            setLoadingState(false);
        }
    };

    const bindEvents = () => {
        const rangeButtons = document.querySelectorAll('.range-btn');
        rangeButtons.forEach((button) => {
            button.addEventListener('click', (event) => {
                const range = getRangeFromTarget(event);
                if (!range || !CONFIG.ranges[range]) return;
                setRange(range);
            });
        });

        const refreshButton = byId(ELEMENTS.refreshButton);
        if (refreshButton) {
            refreshButton.addEventListener('click', () => refreshDashboard());
        }

        const openExportButton = byId(ELEMENTS.openExportButton);
        if (openExportButton) {
            openExportButton.addEventListener('click', openModal);
        }

        const closeExportButton = byId(ELEMENTS.closeExportButton);
        if (closeExportButton) {
            closeExportButton.addEventListener('click', closeModal);
        }

        const modal = byId(ELEMENTS.exportModal);
        if (modal) {
            modal.addEventListener('click', (event) => {
                if (event.target === modal) closeModal();
            });
            modal.querySelectorAll('.export-item').forEach((button) => {
                button.addEventListener('click', (event) => {
                    const format = event.currentTarget.getAttribute('data-export-format');
                    if (format) handleExport(format);
                    closeModal();
                });
            });
        }

        document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape') closeModal();
        });

        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                if (state.timer) clearInterval(state.timer);
                state.timer = null;
                return;
            }
            if (!state.timer) {
                state.timer = setInterval(() => {
                    refreshDashboard({ quiet: true }).catch(() => {});
                }, CONFIG.refreshMs);
            }
            refreshDashboard({ quiet: true }).catch(() => {});
        });
    };

    const validateAndBootstrap = async () => {
        if (byId(ELEMENTS.monthMrr) === null) return;

        bindEvents();
        setRange(state.currentRange);

        const cached = readSnapshot();
        if (cached && cached.data) {
            applyDashboardData(cached.data, { cached: true, syncedAt: cached.savedAt });
            state.hydratedFromCache = true;
            setMessage('info', '최근 저장본을 먼저 표시하고 최신 상태를 불러오는 중입니다...');
        }

        if (state.timer) clearInterval(state.timer);
        state.timer = setInterval(() => {
            refreshDashboard({ quiet: true }).catch(() => {});
        }, CONFIG.refreshMs);

        await refreshDashboard();
        showToastSafe('화면 표준화 점검이 완료되었고, 동기화가 시작되었습니다.', 'info');
    };

    document.addEventListener('DOMContentLoaded', validateAndBootstrap);
})();

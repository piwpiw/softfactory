/**
 * Common API Module - Used by all SoftFactory pages
 * DEMO MODE: Use passkey "demo2026" to bypass authentication
 */

const API_BASE = 'http://localhost:8000';
const DEMO_PASSKEY = 'demo2026';
const DEMO_USER = {
    id: 999,
    email: 'demo@softfactory.com',
    name: 'Demo User',
    role: 'user'
};

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
    // If in demo mode, mock the response
    if (isDemoMode()) {
        return mockApiFetch(path, options);
    }

    const url = `${API_BASE}${path}`;
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers
    };

    // Add auth token if available
    const token = localStorage.getItem('access_token');
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    let response = await fetch(url, {
        ...options,
        headers
    });

    // If 401, try to refresh token
    if (response.status === 401) {
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
            const refreshResp = await fetch(`${API_BASE}/api/auth/refresh`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ refresh_token: refreshToken })
            });

            if (refreshResp.ok) {
                const refreshData = await refreshResp.json();
                localStorage.setItem('access_token', refreshData.access_token);
                localStorage.setItem('refresh_token', refreshData.refresh_token);

                // Retry original request
                headers['Authorization'] = `Bearer ${refreshData.access_token}`;
                response = await fetch(url, {
                    ...options,
                    headers
                });
            } else {
                // Refresh failed - redirect to login
                localStorage.clear();
                window.location.href = '/web/platform/login.html';
            }
        }
    }

    return response;
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
                { id: 1, title: 'Skincare Product Launch', product_name: 'GlowSkin Pro', category: 'beauty', reward_value: '₩150,000 키트', max_reviewers: 20, current_reviewers: 5, deadline: '2026-03-24', status: 'active', applications: 5, image: '💄' },
                { id: 2, title: 'Coffee Brand Review', product_name: 'BeanBliss', category: 'food', reward_value: '₩50,000 카드', max_reviewers: 15, current_reviewers: 3, deadline: '2026-03-19', status: 'active', applications: 3, image: '☕' },
                { id: 3, title: 'Tech Gadget Review', product_name: 'SmartHub X3', category: 'tech', reward_value: '₩75,000 보너스', max_reviewers: 10, current_reviewers: 8, deadline: '2026-03-14', status: 'active', applications: 8, image: '⌚' }
            ]
        };
    }
    if (path.match(/\/api\/review\/campaigns\/\d+$/)) {
        const campaignId = parseInt(path.match(/\/(\d+)$/)[1]);
        const campaigns = {
            1: { id: 1, title: 'Skincare Product Launch', product_name: 'GlowSkin Pro', category: 'beauty', reward_value: '₩150,000 키트', description: 'Review our new skincare line', deadline: '2026-03-24', status: 'active' },
            2: { id: 2, title: 'Coffee Brand Review', product_name: 'BeanBliss', category: 'food', reward_value: '₩50,000 카드', description: 'Try our premium coffee', deadline: '2026-03-19', status: 'active' },
            3: { id: 3, title: 'Tech Gadget Review', product_name: 'SmartHub X3', category: 'tech', reward_value: '₩75,000 보너스', description: 'Review smartwatch', deadline: '2026-03-14', status: 'active' }
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

function showToast(message, type = 'success') {
    const icons = {
        success: '✅',
        error: '❌',
        warning: '⚠️',
        info: 'ℹ️'
    };
    const colors = {
        success: 'bg-green-600 border-green-500',
        error: 'bg-red-600 border-red-500',
        warning: 'bg-yellow-600 border-yellow-500',
        info: 'bg-blue-600 border-blue-500'
    };

    const toast = document.createElement('div');
    toast.className = `fixed bottom-4 right-4 px-4 py-3 rounded-lg text-white z-50 border flex items-center gap-3 animate-fadeIn ${colors[type] || colors.success}`;
    toast.innerHTML = `<span>${icons[type] || icons.success}</span><span>${message}</span><button class="ml-2 text-lg leading-none">&times;</button>`;

    const closeBtn = toast.querySelector('button');
    closeBtn.onclick = () => toast.remove();

    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 4000);
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

/**
 * Handle network errors
 */
window.addEventListener('offline', () => {
    showError('인터넷 연결이 끊어졌습니다');
});

window.addEventListener('online', () => {
    showSuccess('인터넷 연결 복구됨');
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

// Payment & Billing
async function getBillingInfo() {
    const response = await apiFetch('/api/payment/billing-info');
    return response.json();
}

async function getPaymentHistory() {
    const response = await apiFetch('/api/payment/history');
    return response.json();
}

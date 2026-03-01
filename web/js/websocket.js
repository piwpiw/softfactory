/**
 * SoftFactory WebSocket Client v1.0
 * Real-time notification and event streaming
 *
 * FEATURES:
 * - Socket.IO client with automatic reconnection
 * - Multiple namespace support (sns, orders, chat, notifications)
 * - Event buffering and offline persistence
 * - Local storage caching
 * - Typing indicators and presence management
 * - Auto-reconnect with exponential backoff
 * - Type-safe event emitters
 *
 * USAGE:
 *   const ws = new WebSocketClient();
 *   ws.connect();
 *   ws.on('sns', 'publish_success', (data) => console.log(data));
 *   ws.emit('sns', 'publish_start', { post_id: 123 });
 *
 * @module websocket
 * @version 1.0
 */

class WebSocketClient {
    constructor() {
        this.apiBase = window.__SF_API_BASE_RESOLVED || 'http://localhost:9000';
        this.sockets = {
            sns: null,
            orders: null,
            chat: null,
            notifications: null,
        };
        this.eventListeners = {};
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 10;
        this.reconnectDelay = 1000;
        this.isConnected = false;
        this.eventBuffer = [];
        this.maxBufferSize = 100;
        this.typingTimeouts = {};
        this.cacheEnabled = true;
        this.cacheTTL = 3600000; // 1 hour

        this._initEventListeners();
    }

    /**
     * Connect to WebSocket server
     * @returns {Promise<boolean>}
     */
    async connect() {
        try {
            const token = localStorage.getItem('auth_token');
            if (!token) {
                console.warn('[WebSocket] No auth token available, skipping connection');
                return false;
            }

            // Dynamically load Socket.IO client
            if (!window.io) {
                await this._loadSocketIOClient();
            }

            const auth = { token };

            // Connect to all namespaces
            await Promise.all([
                this._connectNamespace('sns', '/sns', auth),
                this._connectNamespace('orders', '/orders', auth),
                this._connectNamespace('chat', '/chat', auth),
                this._connectNamespace('notifications', '/notifications', auth),
            ]);

            this.isConnected = true;
            this.reconnectAttempts = 0;
            this._emitEvent('websocket', 'connected', { timestamp: new Date().toISOString() });

            console.log('[WebSocket] Connected to all namespaces');
            return true;
        } catch (error) {
            console.error('[WebSocket] Connection failed:', error);
            this._scheduleReconnect();
            return false;
        }
    }

    /**
     * Connect to a specific namespace
     * @private
     */
    async _connectNamespace(name, namespace, auth) {
        return new Promise((resolve, reject) => {
            const socket = window.io(this.apiBase + namespace, {
                auth,
                reconnection: true,
                reconnectionDelay: 1000,
                reconnectionDelayMax: 5000,
                reconnectionAttempts: this.maxReconnectAttempts,
                transports: ['websocket', 'polling'],
            });

            socket.on('connect', () => {
                console.log(`[WebSocket] Connected to ${namespace}`);
                this._setupNamespaceListeners(name, socket);
                resolve();
            });

            socket.on('error', (error) => {
                console.error(`[WebSocket] Error on ${namespace}:`, error);
                reject(error);
            });

            socket.on('disconnect', (reason) => {
                console.warn(`[WebSocket] Disconnected from ${namespace}:`, reason);
                this.isConnected = false;
                this._scheduleReconnect();
            });

            this.sockets[name] = socket;
        });
    }

    /**
     * Load Socket.IO client library
     * @private
     */
    async _loadSocketIOClient() {
        return new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = 'https://cdn.socket.io/4.5.4/socket.io.min.js';
            script.onload = resolve;
            script.onerror = reject;
            document.head.appendChild(script);
        });
    }

    /**
     * Setup event listeners for a namespace
     * @private
     */
    _setupNamespaceListeners(namespace, socket) {
        // Generic listeners for all namespaces
        socket.on('connected', (data) => this._emitEvent(namespace, 'connected', data));
        socket.on('error', (data) => this._emitEvent(namespace, 'error', data));

        // SNS namespace events
        if (namespace === 'sns') {
            socket.on('publish_started', (data) => this._handlePublishStart(data));
            socket.on('publish_success', (data) => this._handlePublishSuccess(data));
            socket.on('publish_failed', (data) => this._handlePublishFail(data));
            socket.on('post_liked', (data) => this._handlePostLiked(data));
            socket.on('post_commented', (data) => this._handlePostCommented(data));
            socket.on('user_online', (data) => this._handleUserOnline(data));
            socket.on('user_offline', (data) => this._handleUserOffline(data));
        }

        // Orders namespace events
        if (namespace === 'orders') {
            socket.on('order_updated', (data) => this._handleOrderUpdated(data));
            socket.on('shipment_update', (data) => this._handleShipmentUpdate(data));
            socket.on('delivery_confirmed', (data) => this._handleDeliveryConfirmed(data));
        }

        // Chat namespace events
        if (namespace === 'chat') {
            socket.on('message_received', (data) => this._handleMessageReceived(data));
            socket.on('user_typing', (data) => this._handleUserTyping(data));
            socket.on('message_read', (data) => this._handleMessageRead(data));
            socket.on('user_online', (data) => this._handleChatUserOnline(data));
            socket.on('user_offline', (data) => this._handleChatUserOffline(data));
        }

        // Notifications namespace events
        if (namespace === 'notifications') {
            socket.on('notification', (data) => this._handleNotification(data));
        }
    }

    /**
     * Emit event to a specific namespace
     * @param {string} namespace - 'sns', 'orders', 'chat', or 'notifications'
     * @param {string} event - Event name
     * @param {object} data - Event data
     */
    emit(namespace, event, data = {}) {
        if (!this.sockets[namespace] || !this.sockets[namespace].connected) {
            this._bufferEvent(namespace, event, data);
            console.warn(`[WebSocket] ${namespace} not connected, buffering event: ${event}`);
            return;
        }

        this.sockets[namespace].emit(event, data);
        this._cacheEvent(namespace, event, data);
    }

    /**
     * Register event listener
     * @param {string} namespace - Namespace to listen on
     * @param {string} event - Event name
     * @param {function} callback - Callback function
     */
    on(namespace, event, callback) {
        const key = `${namespace}:${event}`;
        if (!this.eventListeners[key]) {
            this.eventListeners[key] = [];
        }
        this.eventListeners[key].push(callback);
    }

    /**
     * Remove event listener
     * @param {string} namespace
     * @param {string} event
     * @param {function} callback
     */
    off(namespace, event, callback) {
        const key = `${namespace}:${event}`;
        if (this.eventListeners[key]) {
            this.eventListeners[key] = this.eventListeners[key].filter(cb => cb !== callback);
        }
    }

    /**
     * Send SNS publish event
     */
    publishStart(postId, platforms) {
        this.emit('sns', 'publish_start', {
            post_id: postId,
            platforms: platforms,
        });
    }

    /**
     * Send chat message
     */
    sendMessage(recipientId, messageText) {
        this.emit('chat', 'message', {
            recipient_id: recipientId,
            message: messageText,
        });
    }

    /**
     * Set typing indicator
     */
    setTyping(recipientId, isTyping) {
        this.emit('chat', 'typing', {
            recipient_id: recipientId,
            is_typing: isTyping,
        });
    }

    /**
     * Mark message as read
     */
    markMessageRead(senderId, messageId) {
        this.emit('chat', 'message_read', {
            sender_id: senderId,
            message_id: messageId,
        });
    }

    /**
     * Disconnect from WebSocket server
     */
    disconnect() {
        Object.values(this.sockets).forEach(socket => {
            if (socket) socket.disconnect();
        });
        this.isConnected = false;
        console.log('[WebSocket] Disconnected');
    }

    /**
     * Reconnect to server
     * @private
     */
    _scheduleReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error('[WebSocket] Max reconnection attempts reached');
            return;
        }

        this.reconnectAttempts++;
        const delay = Math.min(this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1), 30000);

        console.log(`[WebSocket] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);

        setTimeout(() => this.connect(), delay);
    }

    /**
     * Buffer events when offline
     * @private
     */
    _bufferEvent(namespace, event, data) {
        if (this.eventBuffer.length >= this.maxBufferSize) {
            this.eventBuffer.shift(); // Remove oldest
        }

        this.eventBuffer.push({
            namespace,
            event,
            data,
            timestamp: Date.now(),
        });

        this._persistBuffer();
    }

    /**
     * Flush buffered events
     * @private
     */
    async _flushBuffer() {
        if (this.eventBuffer.length === 0) return;

        const buffer = [...this.eventBuffer];
        this.eventBuffer = [];

        for (const item of buffer) {
            await new Promise(resolve => {
                setTimeout(() => {
                    if (this.sockets[item.namespace]?.connected) {
                        this.sockets[item.namespace].emit(item.event, item.data);
                    }
                    resolve();
                }, 10);
            });
        }

        this._persistBuffer();
    }

    /**
     * Persist buffer to localStorage
     * @private
     */
    _persistBuffer() {
        if (this.cacheEnabled) {
            localStorage.setItem('ws_event_buffer', JSON.stringify(this.eventBuffer));
        }
    }

    /**
     * Cache event for offline access
     * @private
     */
    _cacheEvent(namespace, event, data) {
        if (!this.cacheEnabled) return;

        const cacheKey = `ws_cache_${namespace}_${event}`;
        const cacheData = {
            data,
            timestamp: Date.now(),
        };

        localStorage.setItem(cacheKey, JSON.stringify(cacheData));
    }

    /**
     * Retrieve cached event
     * @private
     */
    _getCachedEvent(namespace, event) {
        if (!this.cacheEnabled) return null;

        const cacheKey = `ws_cache_${namespace}_${event}`;
        const cached = localStorage.getItem(cacheKey);

        if (!cached) return null;

        try {
            const { data, timestamp } = JSON.parse(cached);
            if (Date.now() - timestamp > this.cacheTTL) {
                localStorage.removeItem(cacheKey);
                return null;
            }
            return data;
        } catch (e) {
            console.error('[WebSocket] Cache parse error:', e);
            return null;
        }
    }

    /**
     * Emit internal event
     * @private
     */
    _emitEvent(namespace, event, data) {
        const key = `${namespace}:${event}`;
        if (this.eventListeners[key]) {
            this.eventListeners[key].forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`[WebSocket] Event listener error (${key}):`, error);
                }
            });
        }
    }

    /**
     * Initialize event listeners
     * @private
     */
    _initEventListeners() {
        // Listen for auth token changes
        window.addEventListener('storage', (e) => {
            if (e.key === 'auth_token') {
                if (e.newValue) {
                    console.log('[WebSocket] Auth token updated, reconnecting');
                    this.disconnect();
                    setTimeout(() => this.connect(), 1000);
                }
            }
        });

        // Listen for online/offline
        window.addEventListener('online', () => {
            console.log('[WebSocket] Online, attempting reconnection');
            this.connect();
        });

        window.addEventListener('offline', () => {
            console.log('[WebSocket] Offline');
            this.isConnected = false;
        });
    }

    // ========================================================================
    // EVENT HANDLERS
    // ========================================================================

    _handlePublishStart(data) {
        console.log('[SNS] Publish started:', data);
        this._emitEvent('sns', 'publish_start', data);
        this._showNotification('Publishing...', `Publishing to ${data.platforms.join(', ')}`);
    }

    _handlePublishSuccess(data) {
        console.log('[SNS] Publish success:', data);
        this._emitEvent('sns', 'publish_success', data);
        this._showNotification('success', data.message || 'Published successfully', 'check_circle');
    }

    _handlePublishFail(data) {
        console.error('[SNS] Publish failed:', data);
        this._emitEvent('sns', 'publish_failed', data);
        this._showNotification('error', `Failed to publish to ${data.platform}: ${data.error}`, 'error');
    }

    _handlePostLiked(data) {
        console.log('[SNS] Post liked:', data);
        this._emitEvent('sns', 'post_liked', data);
        this._showNotification('info', '좋아요를 받았습니다!', 'favorite');
    }

    _handlePostCommented(data) {
        console.log('[SNS] Post commented:', data);
        this._emitEvent('sns', 'post_commented', data);
        this._showNotification('info', `${data.commenter_name}님이 댓글을 달았습니다`, 'comment');
    }

    _handleUserOnline(data) {
        console.log('[SNS] User online:', data.user_id);
        this._emitEvent('sns', 'user_online', data);
    }

    _handleUserOffline(data) {
        console.log('[SNS] User offline:', data.user_id);
        this._emitEvent('sns', 'user_offline', data);
    }

    _handleOrderUpdated(data) {
        console.log('[Orders] Order updated:', data);
        this._emitEvent('orders', 'order_updated', data);
        this._showNotification('info', data.message || '주문 상태가 업데이트되었습니다', 'shopping_cart');
    }

    _handleShipmentUpdate(data) {
        console.log('[Orders] Shipment update:', data);
        this._emitEvent('orders', 'shipment_update', data);
        this._showNotification('info', `배송: ${data.location}`, 'local_shipping');
    }

    _handleDeliveryConfirmed(data) {
        console.log('[Orders] Delivery confirmed:', data);
        this._emitEvent('orders', 'delivery_confirmed', data);
        this._showNotification('success', '배송 완료!', 'done_all');
    }

    _handleMessageReceived(data) {
        console.log('[Chat] Message received:', data);
        this._emitEvent('chat', 'message_received', data);
    }

    _handleUserTyping(data) {
        console.log('[Chat] User typing:', data);
        this._emitEvent('chat', 'user_typing', data);
    }

    _handleMessageRead(data) {
        console.log('[Chat] Message read:', data);
        this._emitEvent('chat', 'message_read', data);
    }

    _handleChatUserOnline(data) {
        console.log('[Chat] User online:', data.user_id);
        this._emitEvent('chat', 'user_online', data);
    }

    _handleChatUserOffline(data) {
        console.log('[Chat] User offline:', data.user_id);
        this._emitEvent('chat', 'user_offline', data);
    }

    _handleNotification(data) {
        console.log('[Notification]', data);
        this._emitEvent('notifications', 'notification', data);
        this._showNotification(data.type, data.message, 'notifications');
    }

    /**
     * Show visual notification
     * @private
     */
    _showNotification(type, message, icon = 'info') {
        // Try to use existing UI notification system
        if (typeof showToast === 'function') {
            showToast(message, type === 'error' ? 'danger' : type);
        } else if (window.Notification && Notification.permission === 'granted') {
            new Notification('SoftFactory', {
                body: message,
                icon: `/icon/${icon}.png`,
            });
        }
    }
}

// ============================================================================
// GLOBAL INSTANCE
// ============================================================================

// Create and export global WebSocket instance
window.ws = new WebSocketClient();

// Auto-connect on page load if authenticated
window.addEventListener('load', () => {
    if (localStorage.getItem('auth_token')) {
        window.ws.connect().catch(error => {
            console.warn('[WebSocket] Auto-connection failed:', error);
        });
    }
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = WebSocketClient;
}

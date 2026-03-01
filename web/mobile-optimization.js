/**
 * SoftFactory Mobile Optimization v1.0
 * Handles hamburger menu, sidebar toggle, touch gestures, and mobile-specific behavior
 */

(function() {
    'use strict';

    // ============ Sidebar Toggle ============
    const hamburger = document.querySelector('.hamburger');
    const sidebar = document.querySelector('aside');
    let overlay = null;

    function createOverlay() {
        if (overlay) return overlay;
        overlay = document.createElement('div');
        overlay.className = 'sidebar-overlay';
        overlay.addEventListener('click', closeSidebar);
        document.body.appendChild(overlay);
        return overlay;
    }

    function openSidebar() {
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

    // Close sidebar on nav link click (mobile)
    if (sidebar) {
        sidebar.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', () => {
                if (window.innerWidth <= 768) {
                    closeSidebar();
                }
            });
        });
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

    // ============ Keyboard Navigation ============
    document.addEventListener('keydown', function(e) {
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
        const mainContent = document.querySelector('main') || document.querySelector('.flex-1.overflow-y-auto');
        if (mainContent) {
            mainContent.addEventListener('scroll', function() {
                if (!ticking) {
                    ticking = true;
                    requestAnimationFrame(() => { ticking = false; });
                }
            }, { passive: true });
        }
    }

})();

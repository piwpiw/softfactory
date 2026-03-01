/**
 * QR Code Generator Module for SNS Automation
 * Integrates with qrcode.js library for generating dynamic QR codes
 *
 * Usage:
 * generateQRCode('https://example.com/bio/username', 'qr-container-id')
 *
 * @module qr-code-generator
 * @version 1.0
 * @since 2026-02-26
 */

/**
 * Generate and display QR code
 * @param {string} text - Text/URL to encode
 * @param {string} containerId - ID of container element
 * @param {number} size - QR code size in pixels (default: 256)
 * @param {string} errorCorrection - Error correction level (L, M, Q, H)
 * @returns {Promise<void>}
 */
async function generateQRCode(text, containerId, size = 256, errorCorrection = 'H') {
    try {
        const container = document.getElementById(containerId);
        if (!container) {
            throw new Error(`Container element with ID "${containerId}" not found`);
        }

        // Clear previous QR code
        container.innerHTML = '';

        // Create canvas for QR code
        const canvas = document.createElement('canvas');
        canvas.id = 'qrcode-canvas';
        container.appendChild(canvas);

        // Generate QR code using qrcode library
        QRCode.toCanvas(canvas, text, {
            errorCorrectionLevel: errorCorrection,
            type: 'image/png',
            width: size,
            margin: 2,
            color: {
                dark: '#000000',
                light: '#FFFFFF'
            }
        }, (error) => {
            if (error) {
                console.error('QR Code generation failed:', error);
                showError('QR 코드 생성 실패');
            }
        });

        return canvas;
    } catch (error) {
        console.error('QR Code error:', error);
        showError('QR 코드 생성 오류: ' + error.message);
    }
}

/**
 * Download QR code as image
 * @param {string} filename - Filename for download (without extension)
 * @param {string} format - File format (png, jpg, webp)
 * @returns {void}
 */
function downloadQRCode(filename = 'qrcode', format = 'png') {
    try {
        const canvas = document.getElementById('qrcode-canvas');
        if (!canvas) {
            showError('QR 코드가 생성되지 않았습니다');
            return;
        }

        const link = document.createElement('a');
        link.href = canvas.toDataURL(`image/${format}`);
        link.download = `${filename}.${format}`;
        link.click();
        showSuccess(`${filename}.${format} 다운로드됨`);
    } catch (error) {
        showError('다운로드 실패: ' + error.message);
    }
}

/**
 * Copy QR code to clipboard as image
 * @returns {Promise<void>}
 */
async function copyQRCodeToClipboard() {
    try {
        const canvas = document.getElementById('qrcode-canvas');
        if (!canvas) {
            showError('QR 코드가 생성되지 않았습니다');
            return;
        }

        canvas.toBlob((blob) => {
            const item = new ClipboardItem({ 'image/png': blob });
            navigator.clipboard.write([item]).then(() => {
                showSuccess('QR 코드가 클립보드에 복사되었습니다');
            }).catch(err => {
                showError('클립보드 복사 실패');
            });
        });
    } catch (error) {
        showError('복사 실패: ' + error.message);
    }
}

/**
 * Generate short URL slug for bio link
 * @param {string} username - User's username
 * @param {string} bioTitle - Bio title/name
 * @returns {string} Generated slug (e.g., "bio-username-123abc")
 */
function generateBioSlug(username = '', bioTitle = '') {
    const timestamp = Date.now().toString(36);
    const random = Math.random().toString(36).substr(2, 6);
    const slugBase = (bioTitle || username || 'bio')
        .toLowerCase()
        .replace(/[^a-z0-9-]/g, '-')
        .replace(/-+/g, '-')
        .substr(0, 20);

    return `${slugBase}-${timestamp}-${random}`;
}

/**
 * Create bio link URL with generated slug
 * @param {string} slug - Generated slug
 * @param {string} baseDomain - Base domain (default: window.location.origin)
 * @returns {string} Full bio link URL
 */
function createBioLinkURL(slug, baseDomain = window.location.origin) {
    return `${baseDomain}/bio/${slug}`;
}

/**
 * Batch generate QR codes for multiple links
 * @param {Array} links - Array of link objects [{url, title}, ...]
 * @param {string} containerId - Parent container ID
 * @returns {Promise<void>}
 */
async function generateBatchQRCodes(links, containerId) {
    try {
        const container = document.getElementById(containerId);
        if (!container) {
            throw new Error(`Container not found: ${containerId}`);
        }

        container.innerHTML = '';

        for (const link of links) {
            const itemDiv = document.createElement('div');
            itemDiv.className = 'flex flex-col items-center gap-2 p-4 bg-slate-800 rounded-lg';

            const titleP = document.createElement('p');
            titleP.className = 'text-sm font-medium text-white text-center';
            titleP.textContent = link.title;

            const canvasDiv = document.createElement('div');
            canvasDiv.className = 'bg-white p-2 rounded';
            canvasDiv.id = `qr-${link.title.replace(/\s+/g, '-')}`;

            const downloadBtn = document.createElement('button');
            downloadBtn.className = 'text-xs px-2 py-1 bg-green-600 hover:bg-green-700 text-white rounded transition';
            downloadBtn.textContent = '다운로드';
            downloadBtn.onclick = () => downloadQRCode(link.title);

            itemDiv.appendChild(titleP);
            itemDiv.appendChild(canvasDiv);
            itemDiv.appendChild(downloadBtn);
            container.appendChild(itemDiv);

            // Generate QR for this link
            await generateQRCode(link.url, `qr-${link.title.replace(/\s+/g, '-')}`, 200);
        }

        showSuccess(`${links.length}개의 QR 코드가 생성되었습니다`);
    } catch (error) {
        showError('QR 코드 배치 생성 실패: ' + error.message);
    }
}

/**
 * Share QR code on social media
 * @param {string} platform - Social platform (twitter, facebook, linkedin)
 * @param {string} text - Text to share
 * @returns {void}
 */
function shareQRCode(platform, text = '내 Link in Bio를 공유합니다') {
    try {
        const canvas = document.getElementById('qrcode-canvas');
        if (!canvas) {
            showError('QR 코드가 생성되지 않았습니다');
            return;
        }

        // Share text with link
        const url = window.location.href;
        const shareUrls = {
            twitter: `https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}&url=${encodeURIComponent(url)}`,
            facebook: `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(url)}`,
            linkedin: `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(url)}`,
            whatsapp: `https://wa.me/?text=${encodeURIComponent(text + ' ' + url)}`
        };

        if (shareUrls[platform]) {
            window.open(shareUrls[platform], '_blank', 'width=600,height=400');
            showSuccess(`${platform} 공유 준비 완료`);
        }
    } catch (error) {
        showError('공유 실패: ' + error.message);
    }
}

// Auto-load QR code library if not already loaded
if (typeof QRCode === 'undefined') {
    const script = document.createElement('script');
    script.src = 'https://cdnjs.cloudflare.com/ajax/libs/qrcode.js/1.5.3/qrcode.min.js';
    script.onerror = () => console.error('Failed to load QR code library');
    document.head.appendChild(script);
}

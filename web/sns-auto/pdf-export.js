/**
 * PDF Export Module for SNS Automation
 * Generates PDF reports for revenue, competitor analysis, and more
 *
 * Dependencies:
 * - jsPDF: https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js
 * - html2canvas: https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js
 *
 * @module pdf-export
 * @version 1.0
 * @since 2026-02-26
 */

/**
 * Export revenue dashboard as PDF
 * @param {string} filename - Output filename
 * @returns {Promise<void>}
 */
async function exportMonetizationReport(filename = 'monetization-report') {
    try {
        showInfo('PDF 생성 중...');

        const doc = new jsPDF({
            orientation: 'portrait',
            unit: 'mm',
            format: 'a4'
        });

        const pageWidth = doc.internal.pageSize.getWidth();
        const pageHeight = doc.internal.pageSize.getHeight();
        let yPosition = 10;

        // Header
        doc.setFontSize(20);
        doc.text('💰 수익화 대시보드 리포트', pageWidth / 2, yPosition, { align: 'center' });
        yPosition += 10;

        // Date
        doc.setFontSize(10);
        doc.setTextColor(128, 128, 128);
        doc.text(`생성일: ${new Date().toLocaleString('ko-KR')}`, pageWidth / 2, yPosition, { align: 'center' });
        yPosition += 10;

        // Metrics Summary
        doc.setTextColor(0, 0, 0);
        doc.setFontSize(12);
        doc.text('📊 주요 지표', 10, yPosition);
        yPosition += 8;

        const totalRevenue = document.getElementById('totalRevenue')?.textContent || '₩0';
        const avgROI = document.getElementById('avgROI')?.textContent || '0%';
        const affiliateRevenue = document.getElementById('affiliateRevenue')?.textContent || '₩0';
        const totalClicks = document.getElementById('totalClicks')?.textContent || '0';

        doc.setFontSize(10);
        doc.text(`총 수익: ${totalRevenue}`, 10, yPosition);
        yPosition += 7;
        doc.text(`평균 ROI: ${avgROI}`, 10, yPosition);
        yPosition += 7;
        doc.text(`어필리에이트 수익: ${affiliateRevenue}`, 10, yPosition);
        yPosition += 7;
        doc.text(`총 클릭: ${totalClicks}`, 10, yPosition);
        yPosition += 12;

        // Revenue Chart
        doc.setFontSize(12);
        doc.text('📈 수익 추이', 10, yPosition);
        yPosition += 8;

        const chartElement = document.getElementById('revenueChart');
        if (chartElement) {
            try {
                const canvas = await html2canvas(chartElement, {
                    backgroundColor: '#0f172a'
                });
                const imgData = canvas.toDataURL('image/png');
                doc.addImage(imgData, 'PNG', 10, yPosition, 190, 80);
                yPosition += 85;
            } catch (e) {
                doc.text('차트를 생성할 수 없습니다', 10, yPosition);
                yPosition += 10;
            }
        }

        // Revenue Sources
        doc.setFontSize(12);
        doc.text('🎯 상위 수익원', 10, yPosition);
        yPosition += 8;

        const revenueSources = [
            { name: 'Google Ads', amount: '₩450,000' },
            { name: 'Amazon Affiliate', amount: '₩320,000' },
            { name: 'Sponsored Posts', amount: '₩280,000' },
            { name: 'Link in Bio', amount: '₩150,000' }
        ];

        doc.setFontSize(10);
        revenueSources.forEach((source) => {
            if (yPosition > pageHeight - 20) {
                doc.addPage();
                yPosition = 10;
            }
            doc.text(`${source.name}`, 10, yPosition);
            doc.text(source.amount, 150, yPosition);
            yPosition += 7;
        });

        // Footer
        yPosition = pageHeight - 10;
        doc.setFontSize(8);
        doc.setTextColor(128, 128, 128);
        doc.text(`SoftFactory SNS Automation - ${new Date().getFullYear()}`, pageWidth / 2, yPosition, { align: 'center' });

        // Save PDF
        doc.save(`${filename}.pdf`);
        showSuccess(`${filename}.pdf 다운로드됨`);
    } catch (error) {
        console.error('PDF export error:', error);
        showError('PDF 생성 실패: ' + error.message);
    }
}

/**
 * Export competitor analysis as PDF
 * @param {string} filename - Output filename
 * @returns {Promise<void>}
 */
async function exportCompetitorAnalysis(filename = 'competitor-analysis') {
    try {
        showInfo('경쟁사 분석 PDF 생성 중...');

        const doc = new jsPDF({
            orientation: 'portrait',
            unit: 'mm',
            format: 'a4'
        });

        const pageWidth = doc.internal.pageSize.getWidth();
        const pageHeight = doc.internal.pageSize.getHeight();
        let yPosition = 10;

        // Header
        doc.setFontSize(20);
        doc.text('👁️ 경쟁사 분석 리포트', pageWidth / 2, yPosition, { align: 'center' });
        yPosition += 10;

        // Date
        doc.setFontSize(10);
        doc.setTextColor(128, 128, 128);
        doc.text(`생성일: ${new Date().toLocaleString('ko-KR')}`, pageWidth / 2, yPosition, { align: 'center' });
        yPosition += 10;

        // Competitors Section
        doc.setTextColor(0, 0, 0);
        doc.setFontSize(12);
        doc.text('📊 추적 중인 경쟁사', 10, yPosition);
        yPosition += 8;

        // Get competitor cards
        const competitorCards = document.querySelectorAll('.space-y-4 > .bg-slate-800');
        const competitorCount = Math.min(competitorCards.length, 3); // Max 3 competitors per report

        if (competitorCount === 0) {
            doc.setFontSize(10);
            doc.text('추적 중인 경쟁사가 없습니다', 10, yPosition);
            yPosition += 10;
        } else {
            for (let i = 0; i < competitorCount; i++) {
                if (yPosition > pageHeight - 50) {
                    doc.addPage();
                    yPosition = 10;
                }

                const card = competitorCards[i];
                const username = card.querySelector('.font-bold.text-white')?.textContent || 'Unknown';
                const platform = card.querySelector('.text-xs.text-slate-400')?.textContent || 'Unknown';

                doc.setFontSize(11);
                doc.setTextColor(100, 100, 100);
                doc.text(`${username} (${platform})`, 10, yPosition);
                yPosition += 6;

                // Metrics
                doc.setFontSize(10);
                const metrics = card.querySelectorAll('.text-center');
                const metricLabels = ['팔로워', '참여율', '주간 게시물', '최상위 콘텐츠'];

                metrics.forEach((metric, idx) => {
                    const label = metricLabels[idx] || `항목 ${idx + 1}`;
                    const value = metric.querySelector('.text-xl')?.textContent || 'N/A';
                    const trend = metric.querySelector('.text-xs')?.textContent || '';
                    doc.text(`${label}: ${value} ${trend}`, 15, yPosition);
                    yPosition += 6;
                });

                yPosition += 5;
            }
        }

        // Comparison Section
        yPosition += 5;
        doc.setFontSize(12);
        doc.text('📈 성장률 비교', 10, yPosition);
        yPosition += 8;

        const comparisonData = [
            { name: '나', growth: '12%' },
            { name: 'fashion_guru', growth: '18%' },
            { name: 'tech_reviewer', growth: '25%' }
        ];

        doc.setFontSize(10);
        comparisonData.forEach((item) => {
            if (yPosition > pageHeight - 20) {
                doc.addPage();
                yPosition = 10;
            }
            doc.text(`${item.name}`, 10, yPosition);
            doc.text(item.growth, 150, yPosition);
            yPosition += 7;
        });

        // Footer
        yPosition = pageHeight - 10;
        doc.setFontSize(8);
        doc.setTextColor(128, 128, 128);
        doc.text(`SoftFactory SNS Automation - ${new Date().getFullYear()}`, pageWidth / 2, yPosition, { align: 'center' });

        // Save PDF
        doc.save(`${filename}.pdf`);
        showSuccess(`${filename}.pdf 다운로드됨`);
    } catch (error) {
        console.error('PDF export error:', error);
        showError('PDF 생성 실패: ' + error.message);
    }
}

/**
 * Export viral content insights as PDF
 * @param {string} filename - Output filename
 * @returns {Promise<void>}
 */
async function exportViralInsights(filename = 'viral-insights') {
    try {
        showInfo('바이럴 인사이트 PDF 생성 중...');

        const doc = new jsPDF({
            orientation: 'portrait',
            unit: 'mm',
            format: 'a4'
        });

        const pageWidth = doc.internal.pageSize.getWidth();
        const pageHeight = doc.internal.pageSize.getHeight();
        let yPosition = 10;

        // Header
        doc.setFontSize(20);
        doc.text('🚀 바이럴 콘텐츠 인사이트', pageWidth / 2, yPosition, { align: 'center' });
        yPosition += 10;

        // Date
        doc.setFontSize(10);
        doc.setTextColor(128, 128, 128);
        doc.text(`생성일: ${new Date().toLocaleString('ko-KR')}`, pageWidth / 2, yPosition, { align: 'center' });
        yPosition += 10;

        // Trending Hashtags
        doc.setTextColor(0, 0, 0);
        doc.setFontSize(12);
        doc.text('📈 트렌딩 해시태그', 10, yPosition);
        yPosition += 8;

        const trendingData = [
            { tag: '#트렌드', growth: '+45%', posts: '1.2M' },
            { tag: '#SNS', growth: '+32%', posts: '850K' },
            { tag: '#마케팅', growth: '+28%', posts: '720K' },
            { tag: '#콘텐츠', growth: '+35%', posts: '950K' },
            { tag: '#브랜딩', growth: '+22%', posts: '580K' }
        ];

        doc.setFontSize(10);
        trendingData.forEach((item) => {
            if (yPosition > pageHeight - 30) {
                doc.addPage();
                yPosition = 10;
            }
            doc.text(`${item.tag}`, 10, yPosition);
            doc.text(`${item.growth}`, 80, yPosition);
            doc.text(item.posts, 140, yPosition);
            yPosition += 7;
        });

        // Content Type Recommendations
        yPosition += 5;
        doc.setFontSize(12);
        doc.text('💡 추천 콘텐츠 타입', 10, yPosition);
        yPosition += 8;

        const contentTypes = [
            { emoji: '🎬', type: '쇼츠', engagement: '15-20%' },
            { emoji: '🤣', type: '밈', engagement: '35%+' },
            { emoji: '🎥', type: 'Transition', engagement: 'Top 5%' },
            { emoji: '📱', type: '팁 영상', engagement: '높음' }
        ];

        doc.setFontSize(10);
        contentTypes.forEach((item) => {
            if (yPosition > pageHeight - 20) {
                doc.addPage();
                yPosition = 10;
            }
            doc.text(`${item.emoji} ${item.type}`, 10, yPosition);
            doc.text(item.engagement, 140, yPosition);
            yPosition += 7;
        });

        // Viral Checklist
        yPosition += 5;
        doc.setFontSize(12);
        doc.text('✅ 바이럴 체크리스트', 10, yPosition);
        yPosition += 8;

        const checklist = [
            '트렌딩 해시태그 5개 이상',
            '처음 3초 내 훅 삽입',
            'CTA (Call-to-Action) 포함',
            '댓글 유도 질문 추가',
            '자막 또는 텍스트 오버레이',
            '음향 효과/음악 포함',
            '주제와 톤 일치'
        ];

        doc.setFontSize(10);
        checklist.forEach((item) => {
            if (yPosition > pageHeight - 20) {
                doc.addPage();
                yPosition = 10;
            }
            doc.text(`☐ ${item}`, 10, yPosition);
            yPosition += 7;
        });

        // Tips Section
        yPosition += 5;
        if (yPosition > pageHeight - 40) {
            doc.addPage();
            yPosition = 10;
        }

        doc.setFontSize(12);
        doc.text('💡 바이럴 팁', 10, yPosition);
        yPosition += 8;

        doc.setFontSize(10);
        const tips = [
            '처음 3초 내 관심을 끌고, 시청자가 댓글을 남기도록 유도하는 콘텐츠가 가장 많이 공유됩니다.',
            '트렌딩 사운드와 해시태그 활용이 바이럴 가능성을 높입니다.',
            '일관된 게시 스케줄로 알고리즘 친화적인 채널을 만들어보세요.'
        ];

        tips.forEach((tip) => {
            const lines = doc.splitTextToSize(tip, 180);
            lines.forEach((line) => {
                if (yPosition > pageHeight - 20) {
                    doc.addPage();
                    yPosition = 10;
                }
                doc.text(line, 10, yPosition);
                yPosition += 5;
            });
            yPosition += 3;
        });

        // Footer
        yPosition = pageHeight - 10;
        doc.setFontSize(8);
        doc.setTextColor(128, 128, 128);
        doc.text(`SoftFactory SNS Automation - ${new Date().getFullYear()}`, pageWidth / 2, yPosition, { align: 'center' });

        // Save PDF
        doc.save(`${filename}.pdf`);
        showSuccess(`${filename}.pdf 다운로드됨`);
    } catch (error) {
        console.error('PDF export error:', error);
        showError('PDF 생성 실패: ' + error.message);
    }
}

/**
 * Export generic section as PDF
 * @param {string} containerId - ID of element to export
 * @param {string} filename - Output filename
 * @param {string} title - PDF title
 * @returns {Promise<void>}
 */
async function exportSectionAsPDF(containerId, filename, title) {
    try {
        showInfo('PDF 생성 중...');

        const element = document.getElementById(containerId);
        if (!element) {
            showError(`요소를 찾을 수 없습니다: ${containerId}`);
            return;
        }

        const canvas = await html2canvas(element, {
            backgroundColor: '#0f172a'
        });

        const imgData = canvas.toDataURL('image/png');
        const doc = new jsPDF({
            orientation: 'portrait',
            unit: 'mm',
            format: 'a4'
        });

        const imgWidth = 210; // A4 width in mm
        const imgHeight = (canvas.height * imgWidth) / canvas.width;

        doc.addImage(imgData, 'PNG', 0, 0, imgWidth, imgHeight);
        doc.save(`${filename}.pdf`);

        showSuccess(`${filename}.pdf 다운로드됨`);
    } catch (error) {
        console.error('PDF export error:', error);
        showError('PDF 생성 실패: ' + error.message);
    }
}

// Auto-load PDF libraries if not already loaded
if (typeof jsPDF === 'undefined') {
    const script1 = document.createElement('script');
    script1.src = 'https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js';
    document.head.appendChild(script1);

    const script2 = document.createElement('script');
    script2.src = 'https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js';
    document.head.appendChild(script2);
}

/**
 * PDF Export Module for SNS Automation
 * Replaces legacy encoding-broken strings and normalizes Korean output.
 *
 * Dependencies:
 * - jsPDF: https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js
 * - html2canvas: https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js
 *
 * @module pdf-export
 */

/**
 * 수익 대시보드 PDF 내보내기
 * @param {string} filename
 */
async function exportMonetizationReport(filename = 'monetization-report') {
    try {
        showInfo('수익 리포트를 생성합니다.');

        const doc = new jsPDF({
            orientation: 'portrait',
            unit: 'mm',
            format: 'a4'
        });

        const pageWidth = doc.internal.pageSize.getWidth();
        const pageHeight = doc.internal.pageSize.getHeight();
        let yPosition = 10;

        const totalRevenue = document.getElementById('totalRevenue')?.textContent || '0';
        const avgROI = document.getElementById('avgROI')?.textContent || '0%';
        const affiliateRevenue = document.getElementById('affiliateRevenue')?.textContent || '0';
        const totalClicks = document.getElementById('totalClicks')?.textContent || '0';

        doc.setFontSize(20);
        doc.text('SoftFactory 수익 리포트', pageWidth / 2, yPosition, { align: 'center' });
        yPosition += 10;

        doc.setFontSize(10);
        doc.setTextColor(128, 128, 128);
        doc.text(`생성일: ${new Date().toLocaleString('ko-KR')}`, pageWidth / 2, yPosition, { align: 'center' });
        yPosition += 10;

        doc.setFontSize(12);
        doc.setTextColor(0, 0, 0);
        doc.text('핵심 지표', 10, yPosition);
        yPosition += 8;

        doc.setFontSize(10);
        doc.text(`총 수익: ${totalRevenue}`, 10, yPosition);
        yPosition += 7;
        doc.text(`평균 ROI: ${avgROI}`, 10, yPosition);
        yPosition += 7;
        doc.text(`제휴 수익: ${affiliateRevenue}`, 10, yPosition);
        yPosition += 7;
        doc.text(`총 클릭: ${totalClicks}`, 10, yPosition);
        yPosition += 12;

        doc.setFontSize(12);
        doc.text('수익 추이', 10, yPosition);
        yPosition += 8;

        const chartElement = document.getElementById('revenueChart');
        if (chartElement) {
            try {
                const canvas = await html2canvas(chartElement, { backgroundColor: '#0f172a' });
                const imgData = canvas.toDataURL('image/png');
                doc.addImage(imgData, 'PNG', 10, yPosition, 190, 80);
                yPosition += 85;
            } catch (e) {
                doc.text('차트 이미지를 캡처하지 못했습니다.', 10, yPosition);
                yPosition += 10;
            }
        }

        doc.setFontSize(12);
        doc.text('수익원', 10, yPosition);
        yPosition += 8;

        const revenueSources = [
            { name: 'Google Ads', amount: '₩50,000' },
            { name: 'Amazon Affiliate', amount: '₩20,000' },
            { name: 'Sponsored Posts', amount: '₩80,000' },
            { name: 'Link in Bio', amount: '₩50,000' }
        ];

        doc.setFontSize(10);
        revenueSources.forEach((source) => {
            if (yPosition > pageHeight - 20) {
                doc.addPage();
                yPosition = 10;
            }
            doc.text(source.name, 10, yPosition);
            doc.text(source.amount, 150, yPosition);
            yPosition += 7;
        });

        yPosition = pageHeight - 10;
        doc.setFontSize(8);
        doc.setTextColor(128, 128, 128);
        doc.text(`SoftFactory SNS Automation - ${new Date().getFullYear()}`, pageWidth / 2, yPosition, { align: 'center' });

        doc.save(`${filename}.pdf`);
        showSuccess(`${filename}.pdf 다운로드 완료`);
    } catch (error) {
        console.error('PDF export error:', error);
        showError('PDF 생성 실패: ' + error.message);
    }
}

/**
 * 경쟁사 분석 PDF 내보내기
 * @param {string} filename
 */
async function exportCompetitorAnalysis(filename = 'competitor-analysis') {
    try {
        showInfo('경쟁사 분석 리포트를 생성합니다.');

        const doc = new jsPDF({
            orientation: 'portrait',
            unit: 'mm',
            format: 'a4'
        });

        const pageWidth = doc.internal.pageSize.getWidth();
        const pageHeight = doc.internal.pageSize.getHeight();
        let yPosition = 10;

        doc.setFontSize(20);
        doc.text('경쟁사 분석 리포트', pageWidth / 2, yPosition, { align: 'center' });
        yPosition += 10;

        doc.setFontSize(10);
        doc.setTextColor(128, 128, 128);
        doc.text(`생성일: ${new Date().toLocaleString('ko-KR')}`, pageWidth / 2, yPosition, { align: 'center' });
        yPosition += 10;

        doc.setTextColor(0, 0, 0);
        doc.setFontSize(12);
        doc.text('상위 경쟁사', 10, yPosition);
        yPosition += 8;

        const competitorCards = document.querySelectorAll('.space-y-4 > .bg-slate-800');
        const competitorCount = Math.min(competitorCards.length, 3);

        if (competitorCount === 0) {
            doc.setFontSize(10);
            doc.text('비교 가능한 경쟁사가 없습니다.', 10, yPosition);
            yPosition += 10;
        } else {
            const metricLabels = ['팔로워', '좋아요', '댓글', '전환율'];
            for (let i = 0; i < competitorCount; i++) {
                if (yPosition > pageHeight - 50) {
                    doc.addPage();
                    yPosition = 10;
                }

                const card = competitorCards[i];
                const username = card.querySelector('.font-bold.text-white')?.textContent || '알 수 없음';
                const platform = card.querySelector('.text-xs.text-slate-400')?.textContent || 'Unknown';

                doc.setFontSize(11);
                doc.setTextColor(100, 100, 100);
                doc.text(`${username} (${platform})`, 10, yPosition);
                yPosition += 6;

                doc.setFontSize(10);
                const metrics = card.querySelectorAll('.text-center');
                metrics.forEach((metric, idx) => {
                    const label = metricLabels[idx] || `지표 ${idx + 1}`;
                    const value = metric.querySelector('.text-xl')?.textContent || 'N/A';
                    const trend = metric.querySelector('.text-xs')?.textContent || '';
                    doc.text(`${label}: ${value} ${trend}`, 15, yPosition);
                    yPosition += 6;
                });

                yPosition += 5;
            }
        }

        yPosition += 5;
        doc.setFontSize(12);
        doc.text('비교 데이터', 10, yPosition);
        yPosition += 8;

        const comparisonData = [
            { name: 'beauty_master', growth: '12%' },
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

        yPosition = pageHeight - 10;
        doc.setFontSize(8);
        doc.setTextColor(128, 128, 128);
        doc.text(`SoftFactory SNS Automation - ${new Date().getFullYear()}`, pageWidth / 2, yPosition, { align: 'center' });

        doc.save(`${filename}.pdf`);
        showSuccess(`${filename}.pdf 다운로드 완료`);
    } catch (error) {
        console.error('PDF export error:', error);
        showError('PDF 생성 실패: ' + error.message);
    }
}

/**
 * 바이럴 인사이트 PDF 내보내기
 * @param {string} filename
 */
async function exportViralInsights(filename = 'viral-insights') {
    try {
        showInfo('바이럴 인사이트 리포트를 생성합니다.');

        const doc = new jsPDF({
            orientation: 'portrait',
            unit: 'mm',
            format: 'a4'
        });

        const pageWidth = doc.internal.pageSize.getWidth();
        const pageHeight = doc.internal.pageSize.getHeight();
        let yPosition = 10;

        doc.setFontSize(20);
        doc.text('바이럴 인사이트 리포트', pageWidth / 2, yPosition, { align: 'center' });
        yPosition += 10;

        doc.setFontSize(10);
        doc.setTextColor(128, 128, 128);
        doc.text(`생성일: ${new Date().toLocaleString('ko-KR')}`, pageWidth / 2, yPosition, { align: 'center' });
        yPosition += 10;

        doc.setTextColor(0, 0, 0);
        doc.setFontSize(12);
        doc.text('트렌드 키워드', 10, yPosition);
        yPosition += 8;

        const trendingData = [
            { tag: '#마케팅', growth: '+45%', posts: '1.2M' },
            { tag: '#SNS', growth: '+32%', posts: '850K' },
            { tag: '#브랜딩', growth: '+28%', posts: '720K' },
            { tag: '#성과', growth: '+35%', posts: '950K' },
            { tag: '#콘텐츠', growth: '+22%', posts: '580K' }
        ];

        doc.setFontSize(10);
        trendingData.forEach((item) => {
            if (yPosition > pageHeight - 30) {
                doc.addPage();
                yPosition = 10;
            }
            doc.text(`${item.tag}`, 10, yPosition);
            doc.text(item.growth, 80, yPosition);
            doc.text(item.posts, 140, yPosition);
            yPosition += 7;
        });

        yPosition += 5;
        doc.setFontSize(12);
        doc.text('추천 콘텐츠 유형', 10, yPosition);
        yPosition += 8;

        const contentTypes = [
            { emoji: '🧭', type: '가이드형', engagement: '15-20%' },
            { emoji: '🗣️', type: '토론형', engagement: '35%+' },
            { emoji: '🎞️', type: '전환형', engagement: 'Top 5%' },
            { emoji: '📱', type: '숏폼', engagement: '꾸준' }
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

        yPosition += 5;
        doc.setFontSize(12);
        doc.text('실행 체크리스트', 10, yPosition);
        yPosition += 8;

        const checklist = [
            '주제 5개 이상 후보군 생성',
            '3종 문구 버전 A/B 테스트',
            'CTA 문구를 명확하게 설정',
            '이미지/썸네일 미리보기 검수',
            '반응 예측 메시지 사전 점검',
            '발행 시간대를 실험적으로 3시간대 교차 테스트',
            '성과 이탈 지점 원인 분석'
        ];

        doc.setFontSize(10);
        checklist.forEach((item) => {
            if (yPosition > pageHeight - 20) {
                doc.addPage();
                yPosition = 10;
            }
            doc.text(`- ${item}`, 10, yPosition);
            yPosition += 7;
        });

        yPosition += 5;
        if (yPosition > pageHeight - 40) {
            doc.addPage();
            yPosition = 10;
        }
        doc.setFontSize(12);
        doc.text('운영 팁', 10, yPosition);
        yPosition += 8;

        doc.setFontSize(10);
        const tips = [
            '응답율이 낮은 콘텐츠는 제목, 썸네일, 첫 문장을 함께 조정하세요.',
            '콘텐츠당 해시태그는 4~8개로 제한하고 핵심 키워드 우선 노출을 권장합니다.',
            '발행 직후 30분 안의 댓글 응답이 매출 전환에 가장 높은 영향을 줍니다.'
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

        yPosition = pageHeight - 10;
        doc.setFontSize(8);
        doc.setTextColor(128, 128, 128);
        doc.text(`SoftFactory SNS Automation - ${new Date().getFullYear()}`, pageWidth / 2, yPosition, { align: 'center' });

        doc.save(`${filename}.pdf`);
        showSuccess(`${filename}.pdf 다운로드 완료`);
    } catch (error) {
        console.error('PDF export error:', error);
        showError('PDF 생성 실패: ' + error.message);
    }
}

/**
 * 일반 영역을 PDF로 저장
 * @param {string} containerId
 * @param {string} filename
 * @param {string} title
 */
async function exportSectionAsPDF(containerId, filename, title) {
    try {
        showInfo(`${title || '섹션'} PDF를 생성합니다.`);

        const element = document.getElementById(containerId);
        if (!element) {
            showError(`대상 요소를 찾을 수 없습니다: ${containerId}`);
            return;
        }

        const canvas = await html2canvas(element, { backgroundColor: '#0f172a' });
        const imgData = canvas.toDataURL('image/png');

        const doc = new jsPDF({
            orientation: 'portrait',
            unit: 'mm',
            format: 'a4'
        });

        const imgWidth = 210;
        const imgHeight = (canvas.height * imgWidth) / canvas.width;
        doc.addImage(imgData, 'PNG', 0, 0, imgWidth, imgHeight);
        doc.save(`${filename}.pdf`);

        showSuccess(`${filename}.pdf 다운로드 완료`);
    } catch (error) {
        console.error('PDF export error:', error);
        showError('PDF 생성 실패: ' + error.message);
    }
}

if (typeof jsPDF === 'undefined') {
    const script1 = document.createElement('script');
    script1.src = 'https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js';
    document.head.appendChild(script1);

    const script2 = document.createElement('script');
    script2.src = 'https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js';
    document.head.appendChild(script2);
}

# WCAG 2.1 AA 접근성 구현 가이드

**버전:** 1.0
**작성 날짜:** 2026-02-26
**타겟 레벨:** WCAG 2.1 Level AA

---

## 목차

1. [빠른 시작](#빠른-시작)
2. [핵심 원칙](#핵심-원칙)
3. [HTML 마크업](#html-마크업)
4. [CSS 스타일링](#css-스타일링)
5. [JavaScript 상호작용](#javascript-상호작용)
6. [테스트 및 검증](#테스트-및-검증)
7. [일반적인 실수](#일반적인-실수)
8. [참고 자료](#참고-자료)

---

## 빠른 시작

### 모든 페이지에서 필수 사항

```html
<!-- 1. 언어 선언 -->
<html lang="ko">

<!-- 2. 메타 설명 -->
<meta name="description" content="페이지 설명">

<!-- 3. 접근성 CSS 포함 -->
<link rel="stylesheet" href="../accessibility.css">

<!-- 4. Skip to main content -->
<a href="#main" class="skip-to-main">메인 콘텐츠로 이동</a>

<!-- 5. 의미론적 마크업 -->
<main id="main">
    <header>...</header>
    <section>...</section>
    <footer>...</footer>
</main>
```

---

## 핵심 원칙

### 1. POUR 원칙
- **Perceivable (인지 가능):** 모든 사용자가 콘텐츠를 감지할 수 있어야 함
- **Operable (작동 가능):** 모든 사용자가 기능을 조작할 수 있어야 함
- **Understandable (이해 가능):** 모든 사용자가 콘텐츠를 이해할 수 있어야 함
- **Robust (견고):** 모든 기술과 호환되어야 함

### 2. 우선순위
1. **구조 (HTML):** 의미론적 태그 사용
2. **스타일 (CSS):** 포커스, 대비, 크기
3. **상호작용 (JS):** 키보드, 스크린 리더

### 3. 포함 설계 (Inclusive Design)
- 장애인만을 위한 것이 아님
- 모든 사용자의 경험을 향상시킴
- 성능, 접근성, 사용성이 함께 개선됨

---

## HTML 마크업

### ✅ 의미론적 HTML

**원칙:** 기능에 맞는 태그를 사용하세요.

```html
<!-- ❌ 잘못됨: div로 구조를 표현 -->
<div class="nav">
    <div class="nav-item"><a href="#">홈</a></div>
</div>

<!-- ✅ 올바름: nav로 의미 표현 -->
<nav>
    <a href="#">홈</a>
</nav>
```

#### 일반적인 의미론적 요소

| 태그 | 용도 | 예시 |
|------|------|------|
| `<main>` | 페이지 주요 콘텐츠 | 한 번만 사용 |
| `<header>` | 소개, 로고, 검색 | 섹션마다 가능 |
| `<nav>` | 네비게이션 영역 | 주요 메뉴 |
| `<section>` | 관련 콘텐츠 그룹 | 제목이 필요함 |
| `<article>` | 독립적 콘텐츠 | 블로그 포스트 등 |
| `<aside>` | 부수 콘텐츠 | 사이드바 |
| `<footer>` | 하단 정보 | 저작권, 링크 |

---

### 폼 필드 라벨

**원칙:** 모든 입력 필드는 `<label>`과 연결되어야 합니다.

```html
<!-- ❌ 잘못됨: 라벨과 연결 안 됨 -->
<label>이메일</label>
<input type="email">

<!-- ✅ 올바름: for와 id로 연결 -->
<label for="email">이메일</label>
<input type="email" id="email" required>

<!-- ✅ 대안: label 내부에 input 포함 -->
<label>
    이메일
    <input type="email" required>
</label>

<!-- ✅ 추가: aria-label 사용 (선택적) -->
<label for="email">이메일</label>
<input
    type="email"
    id="email"
    required
    aria-label="이메일 주소"
    aria-describedby="email-hint">
<p id="email-hint">예: user@example.com</p>
```

---

### 이미지 및 아이콘

**원칙:** 모든 시각적 콘텐츠는 대체 텍스트를 가져야 합니다.

```html
<!-- ✅ 정보 이미지: alt 텍스트 필수 -->
<img src="logo.png" alt="SoftFactory 로고" width="40" height="40">

<!-- ✅ 장식 이미지: aria-hidden 사용 -->
<div aria-hidden="true">🎉</div>

<!-- ✅ SVG 아이콘 -->
<svg aria-label="검색" aria-hidden="true">
    <path d="..."></path>
</svg>

<!-- ✅ 배경 이미지: role과 aria-label -->
<div
    role="img"
    aria-label="판매 차트"
    style="background: url('chart.png')">
</div>
```

---

### 제목 구조

**원칙:** h1 → h2 → h3 순서로, 레벨을 건너뛰지 마세요.

```html
<!-- ✅ 올바른 구조 -->
<h1>SoftFactory 대시보드</h1>

<section>
    <h2>판매 분석</h2>
    <p>...</p>

    <h3>월별 매출</h3>
    <p>...</p>
</section>

<section>
    <h2>사용자 관리</h2>
    <p>...</p>
</section>

<!-- ❌ 잘못된 구조 (건너뜀) -->
<h1>제목</h1>
<h3>소제목</h3> <!-- h2를 건너뜸 -->
```

---

### 버튼과 링크

**원칙:** 의도에 따라 올바른 요소를 사용하세요.

```html
<!-- ✅ 링크: 네비게이션 -->
<a href="/profile">프로필</a>

<!-- ✅ 버튼: 동작 -->
<button type="submit">제출</button>
<button type="button" aria-label="메뉴 열기">☰</button>

<!-- ✅ 링크처럼 보이는 버튼 (드물게) -->
<button style="background:none; border:none; text-decoration:underline;">
    링크 같은 버튼
</button>

<!-- ❌ 링크를 버튼처럼 사용 (금지) -->
<a href="javascript:void(0)" onclick="doSomething()">동작</a>
```

---

### ARIA (Accessible Rich Internet Applications)

**원칙:** HTML이 불충분할 때만 ARIA를 사용하세요.

```html
<!-- ✅ 탭 컨트롤 -->
<div role="tablist">
    <button
        role="tab"
        aria-selected="true"
        aria-controls="panel1">
        탭 1
    </button>
    <div role="tabpanel" id="panel1">
        콘텐츠 1
    </div>
</div>

<!-- ✅ 실시간 알림 -->
<div role="status" aria-live="polite">
    저장되었습니다.
</div>

<!-- ✅ 에러 메시지 -->
<div role="alert" aria-live="assertive">
    오류: 필드를 입력하세요.
</div>

<!-- ✅ 숨겨진 제목 -->
<h2 class="sr-only">관련 상품</h2>

<!-- ✅ 아이콘에 설명 추가 -->
<svg aria-label="중요">...</svg>
```

---

## CSS 스타일링

### 포커스 표시기

**원칙:** 모든 상호작용 요소는 명확한 포커스 표시를 가져야 합니다.

```css
/* ✅ WCAG AA: 3px 아웃라인 */
button:focus,
input:focus,
a:focus,
[tabindex]:focus {
    outline: 3px solid #ec4899;
    outline-offset: 2px;
}

/* ✅ Focus-visible (보다 정교함) */
button:focus-visible {
    outline: 3px solid #ec4899;
    outline-offset: 2px;
}

/* ❌ 금지: outline 제거 */
button:focus {
    outline: none; /* 절대 금지! */
}
```

---

### 색상 대비 (Color Contrast)

**원칙:** 텍스트와 배경 대비는 4.5:1 이상이어야 합니다 (AA 기준).

```css
/* ✅ 충분한 대비: 16:1 */
body {
    background-color: #0f172a;
    color: #e2e8f0;
}

/* ✅ 충분한 대비: 4.8:1 */
label {
    background-color: #1e293b;
    color: #cbd5e1;
}

/* ✅ 링크: 3:1 이상 (AA) */
a {
    color: #60a5fa; /* 3.5:1 on dark bg */
}

/* ❌ 부족한 대비: 2:1 */
.weak-contrast {
    background-color: #0f172a;
    color: #94a3b8; /* 2:1 - FAIL */
}
```

#### 대비 검증 도구
- WebAIM Contrast Checker: https://webaim.org/resources/contrastchecker/
- Stark (Figma): https://www.getstark.co/

---

### 터치 타겟 크기

**원칙:** 터치 가능한 요소는 최소 48x48px이어야 합니다.

```css
/* ✅ 충분한 크기 */
button {
    min-height: 48px;
    min-width: 48px;
    padding: 12px 16px;
}

input[type="checkbox"],
input[type="radio"] {
    min-height: 48px;
    min-width: 48px;
}

/* ❌ 너무 작음 */
.small-button {
    padding: 4px 8px; /* ~24x24px - 접근할 수 없음 */
}
```

---

### 모션 및 애니메이션

**원칙:** 사용자가 애니메이션을 비활성화할 수 있어야 합니다.

```css
/* ✅ prefers-reduced-motion 존중 */
@media (prefers-reduced-motion: reduce) {
    *,
    *::before,
    *::after {
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
        scroll-behavior: auto !important;
    }
}

/* ✅ 모션 안전하게 */
.fade-in {
    animation: fadeIn 0.3s ease-out;
}

@media (prefers-reduced-motion: reduce) {
    .fade-in {
        animation: none;
    }
}
```

---

### 스크린 리더 전용 텍스트

**원칙:** 스크린 리더만 읽어야 할 텍스트는 `.sr-only`를 사용하세요.

```css
.sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap;
    border-width: 0;
}
```

```html
<!-- ✅ 사용 예시 -->
<h2 class="sr-only">관련 상품</h2>
<div class="product-grid">...</div>

<!-- ✅ Skip 링크 -->
<a href="#main" class="sr-only">메인 콘텐츠로 이동</a>
```

---

## JavaScript 상호작용

### 키보드 지원

**원칙:** 마우스로 할 수 있는 모든 작업은 키보드로도 가능해야 합니다.

```javascript
/* ✅ 키보드 이벤트 처리 */
element.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        doAction();
    }
    if (e.key === 'Escape') {
        closeModal();
    }
});

/* ✅ 포커스 관리 */
document.addEventListener('keydown', (e) => {
    if (e.key === 'Tab') {
        // Tab은 기본 동작 (포커스 이동)
        return;
    }
});

/* ✅ 역포커스 (Shift+Tab) */
// 자동으로 지원됨 (특별 처리 불필요)
```

---

### 스크린 리더 공지

**원칙:** 동적 콘텐츠 변경사항을 스크린 리더에 알려야 합니다.

```javascript
/* ✅ 상태 메시지 (polite) */
function announceSuccess(message) {
    const announcement = document.createElement('div');
    announcement.setAttribute('role', 'status');
    announcement.setAttribute('aria-live', 'polite');
    announcement.setAttribute('aria-atomic', 'true');
    announcement.className = 'sr-only';
    announcement.textContent = message;

    document.body.appendChild(announcement);

    // 자동 제거
    setTimeout(() => announcement.remove(), 1000);
}

/* ✅ 오류 메시지 (assertive) */
function announceError(message) {
    const announcement = document.createElement('div');
    announcement.setAttribute('role', 'alert');
    announcement.setAttribute('aria-live', 'assertive');
    announcement.className = 'sr-only';
    announcement.textContent = message;

    document.body.appendChild(announcement);
}

/* ✅ 사용 */
announceSuccess('저장되었습니다!');
announceError('오류: 필드를 입력하세요.');
```

---

### 포커스 관리

**원칙:** 포커스가 어디에 있는지 항상 명확해야 합니다.

```javascript
/* ✅ 포커스 저장 및 복원 */
class Modal {
    open() {
        this.previouslyFocused = document.activeElement;
        this.modal.showModal();
        this.modal.querySelector('input').focus();
    }

    close() {
        this.modal.close();
        this.previouslyFocused.focus();
    }
}

/* ✅ 포커스 트래핑 (모달 내) */
function setupFocusTrap(modalElement) {
    const focusableElements = modalElement.querySelectorAll(
        'button, input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );

    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];

    modalElement.addEventListener('keydown', (e) => {
        if (e.key !== 'Tab') return;

        if (e.shiftKey) {
            if (document.activeElement === firstElement) {
                e.preventDefault();
                lastElement.focus();
            }
        } else {
            if (document.activeElement === lastElement) {
                e.preventDefault();
                firstElement.focus();
            }
        }
    });
}
```

---

### 폼 검증

**원칙:** 에러는 명확하고 수정 가능해야 합니다.

```javascript
/* ✅ 접근 가능한 폼 검증 */
function validateForm(form) {
    const errors = [];

    // 검증
    if (!form.email.value) {
        errors.push({
            field: form.email,
            message: '이메일을 입력하세요.'
        });
    }

    if (errors.length > 0) {
        // 에러 컨테이너
        const errorContainer = document.createElement('div');
        errorContainer.setAttribute('role', 'alert');
        errorContainer.className = 'error-summary';
        errorContainer.innerHTML = '<h2>오류를 수정하세요:</h2>';

        errors.forEach(error => {
            const errorItem = document.createElement('div');
            errorItem.innerHTML =
                `<a href="#${error.field.id}">${error.message}</a>`;
            errorContainer.appendChild(errorItem);

            // 필드에 aria-invalid 표시
            error.field.setAttribute('aria-invalid', 'true');
            error.field.setAttribute('aria-describedby', `${error.field.id}-error`);
        });

        form.prepend(errorContainer);
        errorContainer.querySelector('a').focus();
    }
}
```

---

## 테스트 및 검증

### 자동화된 테스트

```bash
# 설치
pip install pytest selenium webdriver-manager

# 실행
pytest tests/test_accessibility.py -v

# 특정 테스트
pytest tests/test_accessibility.py::TestLoginPageAccessibility::test_form_elements_have_labels -v
```

---

### 수동 테스트 체크리스트

#### 1. 키보드 네비게이션
- [ ] Tab으로 모든 요소에 접근 가능
- [ ] Shift+Tab으로 역방향 이동
- [ ] Enter/Space로 버튼 활성화
- [ ] Escape로 모달 닫기

#### 2. 스크린 리더 (NVDA - 무료)
- [ ] 페이지 제목 읽음
- [ ] 헤딩 구조 명확
- [ ] 링크 텍스트 이해 가능
- [ ] 폼 라벨 연결
- [ ] 버튼 목적 명확

#### 3. 색상 대비
- [ ] 텍스트: 4.5:1 이상
- [ ] 링크: 3:1 이상
- [ ] 버튼: 3:1 이상

#### 4. 확대/축소
- [ ] 200% 확대에서 가독성 유지
- [ ] 수평 스크롤 없음
- [ ] 모든 기능 접근 가능

---

### 브라우저 도구

#### Chrome DevTools
1. F12 → Lighthouse
2. Accessibility 섹션 확인
3. 100/100 목표

#### axe DevTools (확장 프로그램)
1. 설치: https://www.deque.com/axe/devtools/
2. 페이지에서 실행
3. 모든 문제 수정

#### WAVE (확장 프로그램)
1. 설치: https://wave.webaim.org/extension/
2. 페이지 분석
3. 에러 및 경고 확인

---

## 일반적인 실수

### 실수 1: outline 제거

```css
/* ❌ 절대 금지 */
button:focus {
    outline: none;
}

/* ✅ 올바름 */
button:focus {
    outline: 3px solid #ec4899;
    outline-offset: 2px;
}
```

---

### 실수 2: 이미지 대체 텍스트 누락

```html
<!-- ❌ 잘못됨 -->
<img src="chart.png">

<!-- ✅ 올바름 -->
<img src="chart.png" alt="월별 판매 차트, 1월 100만원, 2월 120만원">
```

---

### 실수 3: 폼 라벨 연결 안 함

```html
<!-- ❌ 잘못됨 -->
<label>이메일</label>
<input type="email">

<!-- ✅ 올바름 -->
<label for="email">이메일</label>
<input id="email" type="email">
```

---

### 실제 4: 색상만으로 정보 표현

```html
<!-- ❌ 잘못됨: 색상만 사용 -->
<button style="background: red">제거</button>

<!-- ✅ 올바름: 색상 + 텍스트/아이콘 -->
<button style="background: red">
    🗑️ 제거
</button>
```

---

### 실수 5: 자동 재생 미디어

```html
<!-- ❌ 잘못됨: 자동 재생 -->
<audio autoplay>
    <source src="sound.mp3">
</audio>

<!-- ✅ 올바름: 사용자 제어 -->
<audio controls>
    <source src="sound.mp3">
</audio>
```

---

## 참고 자료

### 공식 표준
- **WCAG 2.1:** https://www.w3.org/WAI/WCAG21/quickref/
- **WAI-ARIA:** https://www.w3.org/WAI/ARIA/apg/

### 도구
- **WebAIM:** https://webaim.org/
- **Deque:** https://www.deque.com/
- **WAVE:** https://wave.webaim.org/

### 스크린 리더
- **NVDA (무료, Windows):** https://www.nvaccess.org/
- **JAWS (유료, Windows):** https://www.freedomscientific.com/
- **VoiceOver (무료, Mac/iOS):** 내장

### 온라인 학습
- **WebAIM 튜토리얼:** https://webaim.org/articles/
- **a11y 프로젝트:** https://www.a11yproject.com/
- **Udacity 접근성:** https://www.udacity.com/course/web-accessibility

---

## 체크리스트

### 새 페이지 추가 시

- [ ] `<html lang="ko">` 선언
- [ ] `<main>` 요소 추가
- [ ] `<header>`, `<footer>` 의미론적 사용
- [ ] 모든 이미지에 `alt` 텍스트
- [ ] 모든 폼에 `<label>` 연결
- [ ] 모든 버튼에 `aria-label` 또는 텍스트
- [ ] 포커스 표시기 확인 (3px 아웃라인)
- [ ] 색상 대비 검증 (4.5:1+)
- [ ] 48x48px 터치 타겟
- [ ] Skip to main 링크
- [ ] `accessibility.css` 포함
- [ ] 키보드 네비게이션 테스트
- [ ] NVDA로 스크린 리더 테스트

### 배포 전

- [ ] Lighthouse 100/100
- [ ] axe DevTools 오류 0개
- [ ] WAVE 에러 0개
- [ ] 수동 테스트 완료
- [ ] 스크린 리더 테스트 완료

---

**마지막 업데이트:** 2026-02-26
**라이선스:** MIT
**관리자:** SoftFactory Accessibility Team

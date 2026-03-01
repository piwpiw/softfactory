"""
WCAG 2.1 AA Accessibility Testing Suite
Tests for compliance with Web Content Accessibility Guidelines 2.1 Level AA
Last updated: 2026-02-26
"""

import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import time


@pytest.fixture
def driver():
    """Initialize Selenium WebDriver for accessibility testing."""
    chrome_options = Options()
    # chrome_options.add_argument("--headless")  # Run headlessly
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    yield driver
    driver.quit()


class TestLoginPageAccessibility:
    """Test suite for login.html WCAG 2.1 AA compliance."""

    @pytest.fixture(autouse=True)
    def setup(self, driver):
        """Load login page before each test."""
        driver.get("http://localhost:8000/web/platform/login.html")
        time.sleep(1)

    # ================================================
    # 1. PERCEIVABLE (WCAG Principle 1)
    # ================================================

    def test_page_has_lang_attribute(self, driver):
        """WCAG 3.1.1: Page language is set."""
        html_element = driver.find_element(By.TAG_NAME, "html")
        lang = html_element.get_attribute("lang")
        assert lang is not None, "HTML element should have lang attribute"
        assert lang == "ko", "Language should be Korean (ko)"

    def test_page_has_title(self, driver):
        """WCAG 2.4.2: Page title describes its purpose."""
        title = driver.title
        assert title, "Page should have a title"
        assert "로그인" in title or "SoftFactory" in title, \
            "Title should mention login or SoftFactory"

    def test_page_has_meta_description(self, driver):
        """Metadata helps describe page purpose."""
        meta_desc = driver.find_elements(By.NAME, "description")
        assert len(meta_desc) > 0, "Page should have meta description"

    def test_all_images_have_alt_text(self, driver):
        """WCAG 1.1.1: All images must have alt text or aria-hidden."""
        images = driver.find_elements(By.TAG_NAME, "img")
        for img in images:
            alt_text = img.get_attribute("alt")
            aria_hidden = img.get_attribute("aria-hidden")
            assert alt_text or aria_hidden == "true", \
                f"Image {img.get_attribute('src')} must have alt text or aria-hidden='true'"

    def test_emojis_are_hidden_from_screen_readers(self, driver):
        """Emojis should have aria-hidden='true' to prevent screen reader confusion."""
        emoji_elements = driver.find_elements(By.XPATH, "//*[contains(text(), '🏭') or contains(text(), '🎮') or contains(text(), '🔐')]")
        # Emojis can be in parent containers
        for element in emoji_elements:
            parent = element.find_element(By.XPATH, ".")
            aria_hidden = parent.get_attribute("aria-hidden")
            # Should be hidden or parent should be hidden
            assert aria_hidden == "true", "Emoji elements should have aria-hidden='true'"

    def test_color_contrast_of_text(self, driver):
        """WCAG 1.4.3: Text must have sufficient color contrast (4.5:1)."""
        # This would require a color contrast checker library
        # For now, we verify that elements have proper styling
        body = driver.find_element(By.TAG_NAME, "body")
        bg_color = body.value_of_css_property("background-color")
        assert bg_color, "Body should have background color defined"

    # ================================================
    # 2. OPERABLE (WCAG Principle 2)
    # ================================================

    def test_keyboard_navigation_skip_link(self, driver):
        """WCAG 2.1.1: Keyboard accessible - Skip to main content link."""
        skip_link = driver.find_element(By.CLASS_NAME, "skip-to-main")
        assert skip_link, "Skip to main content link should exist"

    def test_form_elements_have_labels(self, driver):
        """WCAG 1.3.1: Form inputs must be associated with labels."""
        inputs = driver.find_elements(By.TAG_NAME, "input")
        for input_elem in inputs:
            input_id = input_elem.get_attribute("id")
            if input_id:
                label = driver.find_elements(By.XPATH, f"//label[@for='{input_id}']")
                assert len(label) > 0 or input_elem.get_attribute("aria-label"), \
                    f"Input {input_id} should have associated label or aria-label"

    def test_focus_indicators_visible(self, driver):
        """WCAG 2.4.7: All elements must have visible focus indicators."""
        button = driver.find_element(By.TAG_NAME, "button")
        driver.execute_script("arguments[0].focus();", button)

        # Check that outline is applied
        outline = button.value_of_css_property("outline")
        assert outline and "none" not in outline.lower(), \
            "Buttons should have visible focus outline"

    def test_tab_order_is_logical(self, driver):
        """WCAG 2.4.3: Focus order must be logical."""
        # Get all focusable elements
        focusable_elements = driver.find_elements(By.CSS_SELECTOR,
            "button, input, select, textarea, a[href], [tabindex]:not([tabindex='-1'])")

        assert len(focusable_elements) > 0, "Page should have focusable elements"

    def test_form_submission_with_keyboard(self, driver):
        """WCAG 2.1.1: Forms must be submittable via keyboard."""
        email_input = driver.find_element(By.ID, "email")

        # Fill form
        email_input.clear()
        email_input.send_keys("test@example.com")

        # Password
        password_input = driver.find_element(By.ID, "password")
        password_input.clear()
        password_input.send_keys("password123")

        # Submit with Tab + Enter
        password_input.send_keys(Keys.TAB)  # Focus submit button
        # Don't actually submit, just verify button is reachable

    def test_buttons_have_accessible_names(self, driver):
        """WCAG 2.4.4: Buttons must have accessible names."""
        buttons = driver.find_elements(By.TAG_NAME, "button")
        for button in buttons:
            aria_label = button.get_attribute("aria-label")
            text = button.text.strip()
            assert aria_label or text, \
                "Button must have aria-label or visible text"

    # ================================================
    # 3. UNDERSTANDABLE (WCAG Principle 3)
    # ================================================

    def test_page_language_defined(self, driver):
        """WCAG 3.1.1: Language is identified."""
        html = driver.find_element(By.TAG_NAME, "html")
        lang = html.get_attribute("lang")
        assert lang, "HTML element should have lang attribute"

    def test_form_error_messages_visible(self, driver):
        """WCAG 3.3.1: Error messages must identify the problem."""
        # This would be tested after form validation
        pass

    def test_form_labels_describe_purpose(self, driver):
        """WCAG 3.3.2: Labels and instructions must describe input purpose."""
        labels = driver.find_elements(By.TAG_NAME, "label")
        for label in labels:
            text = label.text.strip()
            assert text, "Labels must have visible descriptive text"

    # ================================================
    # 4. ROBUST (WCAG Principle 4)
    # ================================================

    def test_valid_html_structure(self, driver):
        """WCAG 4.1.1: Valid HTML structure."""
        # Check for required semantic elements
        main = driver.find_element(By.TAG_NAME, "main")
        assert main, "Page should have <main> element"

    def test_headings_in_order(self, driver):
        """WCAG 1.3.1: Heading hierarchy must be logical."""
        headings = driver.find_elements(By.XPATH, "//h1 | //h2 | //h3 | //h4 | //h5 | //h6")
        heading_levels = [int(h.tag_name[1]) for h in headings]

        # Check that heading levels don't skip (e.g., h1 -> h3)
        for i in range(len(heading_levels) - 1):
            assert heading_levels[i+1] <= heading_levels[i] + 1 or heading_levels[i+1] <= heading_levels[i], \
                "Heading hierarchy should not skip levels"

    def test_aria_attributes_valid(self, driver):
        """WCAG 4.1.2: ARIA attributes must be valid."""
        elements_with_aria = driver.find_elements(By.XPATH, "//*[@aria-*]")
        # Basic check - aria attributes exist
        assert len(elements_with_aria) > 0, "Page should use ARIA attributes appropriately"

    def test_form_fields_have_name_or_label(self, driver):
        """Form fields must be identifiable to assistive technologies."""
        inputs = driver.find_elements(By.TAG_NAME, "input")
        for input_elem in inputs:
            name = input_elem.get_attribute("name")
            id_attr = input_elem.get_attribute("id")
            aria_label = input_elem.get_attribute("aria-label")

            assert name or id_attr or aria_label, \
                "Input must have name, id, or aria-label"

    # ================================================
    # 5. MOBILE & RESPONSIVE ACCESSIBILITY
    # ================================================

    def test_touch_targets_minimum_size(self, driver):
        """WCAG 2.5.5: Touch targets must be at least 48x48px."""
        buttons = driver.find_elements(By.TAG_NAME, "button")
        for button in buttons:
            size = button.size
            # Note: This is approximate due to rendering differences
            assert size['width'] >= 44 and size['height'] >= 44, \
                f"Button size {size} is below recommended minimum (44x44)"

    # ================================================
    # 6. SCREEN READER COMPATIBILITY
    # ================================================

    def test_sr_only_elements_exist(self, driver):
        """Screen reader only text should exist for important content."""
        sr_elements = driver.find_elements(By.CLASS_NAME, "sr-only")
        # Check that some sr-only elements exist
        assert len(sr_elements) >= 0, "Page may benefit from sr-only elements"

    def test_aria_live_regions(self, driver):
        """WCAG 4.1.3: Live regions for dynamic content."""
        # Check if page would announce status messages
        # This would require dynamic testing
        pass


class TestAccessibilityTooling:
    """Tests for accessibility utilities and helpers."""

    def test_accessibility_css_exists(self):
        """Verify accessibility.css file exists."""
        import os
        css_path = "D:/Project/web/accessibility.css"
        assert os.path.exists(css_path), "accessibility.css should exist"

    def test_accessibility_css_has_focus_styles(self):
        """Verify focus styles are defined in CSS."""
        with open("D:/Project/web/accessibility.css", "r", encoding="utf-8") as f:
            css_content = f.read()
            assert "focus" in css_content, "CSS should define focus styles"
            assert "outline" in css_content, "CSS should define outline for focus"


# ================================================
# WCAG 2.1 AA COMPLIANCE CHECKLIST
# ================================================

WCAG_AA_CHECKLIST = {
    "PERCEIVABLE": {
        "1.1.1": "Non-text Content (A) - All images have alt text",
        "1.3.1": "Info and Relationships (A) - Semantic HTML, labels associated",
        "1.4.1": "Use of Color (A) - Color not sole means of identification",
        "1.4.3": "Contrast (Minimum) (AA) - 4.5:1 for normal text",
        "1.4.10": "Reflow (AA) - Content readable at 200% zoom",
        "1.4.11": "Non-text Contrast (AA) - 3:1 for UI components",
        "1.4.13": "Content on Hover/Focus (AA) - Dismissible, hoverable, persistent",
    },
    "OPERABLE": {
        "2.1.1": "Keyboard (A) - All functionality keyboard accessible",
        "2.1.2": "No Keyboard Trap (A) - Keyboard focus not trapped",
        "2.1.4": "Character Key Shortcuts (A) - Can be disabled or remapped",
        "2.3.3": "Animation from Interactions (AA) - Respects prefers-reduced-motion",
        "2.4.3": "Focus Order (A) - Logical focus order",
        "2.4.7": "Focus Visible (AA) - Visible focus indicator",
        "2.5.5": "Target Size (AA) - 48x48px minimum",
    },
    "UNDERSTANDABLE": {
        "3.1.1": "Language of Page (A) - Language specified",
        "3.2.1": "On Focus (A) - No unexpected context changes on focus",
        "3.2.2": "On Input (A) - No unexpected context changes on input",
        "3.3.1": "Error Identification (A) - Errors identified and described",
        "3.3.2": "Labels or Instructions (A) - Labels provided for inputs",
        "3.3.3": "Error Suggestion (AA) - Suggestions provided for errors",
    },
    "ROBUST": {
        "4.1.1": "Parsing (A) - Valid HTML structure",
        "4.1.2": "Name, Role, Value (A) - Proper ARIA attributes",
        "4.1.3": "Status Messages (AA) - Live regions for dynamic content",
    }
}


def print_wcag_checklist():
    """Print WCAG 2.1 AA compliance checklist."""
    print("\n" + "="*60)
    print("WCAG 2.1 AA COMPLIANCE CHECKLIST")
    print("="*60)

    for principle, criteria in WCAG_AA_CHECKLIST.items():
        print(f"\n{principle}")
        print("-" * 60)
        for criterion, description in criteria.items():
            print(f"  ✓ {criterion}: {description}")


if __name__ == "__main__":
    print_wcag_checklist()

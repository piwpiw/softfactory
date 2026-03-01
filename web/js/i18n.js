/**
 * i18n Module — Multi-language Support for JARVIS Platform
 * Handles language detection, switching, translation, and formatting
 *
 * Usage:
 *   - t('key') → Get translation for key
 *   - setLanguage('en') → Switch to English
 *   - getLanguage() → Get current language
 *   - formatDate(date, 'en') → Format date per locale
 */

class I18nManager {
  constructor() {
    // Translation cache
    this.translations = {};

    // Current language
    this.currentLanguage = this.detectLanguage();

    // Supported languages
    this.supportedLanguages = ['ko', 'en', 'ja', 'zh'];

    // Language names for display
    this.languageNames = {
      'ko': '한국어',
      'en': 'English',
      'ja': '日本語',
      'zh': '中文'
    };

    // Locale data for formatting
    this.localeData = {
      'ko': {
        dateFormat: 'YYYY-MM-DD',
        timeFormat: 'HH:mm:ss',
        decimalSeparator: '.',
        thousandsSeparator: ',',
        currencySymbol: '₩',
        currencyCode: 'KRW'
      },
      'en': {
        dateFormat: 'YYYY-MM-DD',
        timeFormat: 'HH:mm:ss',
        decimalSeparator: '.',
        thousandsSeparator: ',',
        currencySymbol: '$',
        currencyCode: 'USD'
      },
      'ja': {
        dateFormat: 'YYYY年MM月DD日',
        timeFormat: 'HH:mm:ss',
        decimalSeparator: '.',
        thousandsSeparator: ',',
        currencySymbol: '¥',
        currencyCode: 'JPY'
      },
      'zh': {
        dateFormat: 'YYYY年MM月DD日',
        timeFormat: 'HH:mm:ss',
        decimalSeparator: '.',
        thousandsSeparator: ',',
        currencySymbol: '¥',
        currencyCode: 'CNY'
      }
    };
  }

  /**
   * Detect user's preferred language
   * Priority: URL param > localStorage > browser language > default (en)
   */
  detectLanguage() {
    // Check URL parameter
    const urlParams = new URLSearchParams(window.location.search);
    const urlLang = urlParams.get('lang');
    if (urlLang && this.supportedLanguages.includes(urlLang)) {
      return urlLang;
    }

    // Check localStorage
    const savedLang = localStorage.getItem('language');
    if (savedLang && this.supportedLanguages.includes(savedLang)) {
      return savedLang;
    }

    // Check browser language
    const browserLang = navigator.language || navigator.userLanguage;
    const baseLang = browserLang.split('-')[0];
    if (this.supportedLanguages.includes(baseLang)) {
      return baseLang;
    }

    // Default to English
    return 'en';
  }

  /**
   * Load translation file for a specific language
   */
  async loadLanguage(lang) {
    if (this.translations[lang]) {
      return this.translations[lang];
    }

    try {
      const response = await fetch(`/locales/${lang}.json`);
      if (!response.ok) throw new Error(`Failed to load ${lang} locale`);

      this.translations[lang] = await response.json();
      return this.translations[lang];
    } catch (error) {
      console.error(`Error loading language ${lang}:`, error);
      // Fallback to English
      if (lang !== 'en') {
        return this.loadLanguage('en');
      }
      return {};
    }
  }

  /**
   * Initialize i18n (load current language)
   */
  async init() {
    await this.loadLanguage(this.currentLanguage);

    // Set HTML lang attribute
    document.documentElement.lang = this.currentLanguage;

    // Apply initial translations
    this.applyTranslations();

    // Setup language switcher listeners
    this.setupLanguageSwitcher();
  }

  /**
   * Get current language
   */
  getLanguage() {
    return this.currentLanguage;
  }

  /**
   * Set new language
   */
  async setLanguage(lang) {
    if (!this.supportedLanguages.includes(lang)) {
      console.warn(`Language ${lang} not supported`);
      return;
    }

    // Load language if not cached
    if (!this.translations[lang]) {
      await this.loadLanguage(lang);
    }

    this.currentLanguage = lang;
    localStorage.setItem('language', lang);
    document.documentElement.lang = lang;

    // Apply translations
    this.applyTranslations();

    // Trigger custom event
    const event = new CustomEvent('languageChanged', { detail: { language: lang } });
    document.dispatchEvent(event);
  }

  /**
   * Get translation for a key
   * Supports nested keys with dot notation: 'form.email'
   * Supports interpolation: t('validation_min_length', { min: 5 })
   */
  t(key, params = {}) {
    let translation = this.translations[this.currentLanguage]?.[key];

    if (!translation) {
      console.warn(`Translation key not found: ${key}`);
      return key;
    }

    // Handle interpolation
    Object.keys(params).forEach(param => {
      translation = translation.replace(
        new RegExp(`{{${param}}}`, 'g'),
        params[param]
      );
    });

    return translation;
  }

  /**
   * Apply translations to DOM
   * Elements with data-i18n attribute will be translated
   */
  applyTranslations() {
    const elements = document.querySelectorAll('[data-i18n]');

    elements.forEach(element => {
      const key = element.getAttribute('data-i18n');
      const translation = this.t(key);

      // Determine where to apply translation
      const attr = element.getAttribute('data-i18n-attr');

      if (attr) {
        // Apply to specific attribute
        element.setAttribute(attr, translation);
      } else if (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA') {
        // For input fields, use placeholder or value
        if (element.type === 'submit' || element.type === 'button') {
          element.value = translation;
        } else {
          element.placeholder = translation;
        }
      } else {
        // For other elements, set text content
        element.textContent = translation;
      }
    });

    // Handle aria-labels and titles
    const ariaElements = document.querySelectorAll('[data-i18n-aria]');
    ariaElements.forEach(element => {
      const key = element.getAttribute('data-i18n-aria');
      const translation = this.t(key);
      element.setAttribute('aria-label', translation);
    });

    const titleElements = document.querySelectorAll('[data-i18n-title]');
    titleElements.forEach(element => {
      const key = element.getAttribute('data-i18n-title');
      const translation = this.t(key);
      element.title = translation;
    });
  }

  /**
   * Setup language switcher UI
   */
  setupLanguageSwitcher() {
    // Create language selector if not exists
    const existingSelector = document.getElementById('language-selector');
    if (!existingSelector) {
      this.createLanguageSelector();
    }

    // Attach click handlers
    const switches = document.querySelectorAll('[data-lang-switch]');
    switches.forEach(el => {
      el.addEventListener('click', (e) => {
        const lang = e.target.getAttribute('data-lang-switch');
        this.setLanguage(lang);
      });
    });
  }

  /**
   * Create language selector dropdown
   */
  createLanguageSelector() {
    const selector = document.createElement('div');
    selector.id = 'language-selector';
    selector.className = 'language-selector';

    const button = document.createElement('button');
    button.className = 'language-selector-toggle';
    button.innerHTML = `<span>${this.languageNames[this.currentLanguage]}</span>`;
    button.setAttribute('data-i18n', 'settings_language');

    const menu = document.createElement('div');
    menu.className = 'language-selector-menu';

    this.supportedLanguages.forEach(lang => {
      const option = document.createElement('button');
      option.className = `language-option ${lang === this.currentLanguage ? 'active' : ''}`;
      option.textContent = this.languageNames[lang];
      option.setAttribute('data-lang-switch', lang);
      option.addEventListener('click', (e) => {
        e.preventDefault();
        this.setLanguage(lang);
        button.innerHTML = `<span>${this.languageNames[lang]}</span>`;
        menu.querySelectorAll('.language-option').forEach(el => {
          el.classList.remove('active');
        });
        e.target.classList.add('active');
      });
      menu.appendChild(option);
    });

    button.addEventListener('click', () => {
      menu.classList.toggle('active');
    });

    selector.appendChild(button);
    selector.appendChild(menu);

    // Add to nav if exists
    const nav = document.querySelector('nav');
    if (nav) {
      nav.appendChild(selector);
    }
  }

  /**
   * Format date according to locale
   */
  formatDate(date, lang = this.currentLanguage) {
    if (!(date instanceof Date)) {
      date = new Date(date);
    }

    const locale = this.localeData[lang];
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    const seconds = String(date.getSeconds()).padStart(2, '0');

    let result = locale.dateFormat
      .replace('YYYY', year)
      .replace('MM', month)
      .replace('DD', day);

    if (locale.dateFormat.includes('HH')) {
      result = locale.dateFormat
        .replace('YYYY', year)
        .replace('MM', month)
        .replace('DD', day)
        .replace('HH', hours)
        .replace('mm', minutes)
        .replace('ss', seconds);
    }

    return result;
  }

  /**
   * Format time according to locale
   */
  formatTime(date, lang = this.currentLanguage) {
    if (!(date instanceof Date)) {
      date = new Date(date);
    }

    const locale = this.localeData[lang];
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    const seconds = String(date.getSeconds()).padStart(2, '0');

    return locale.timeFormat
      .replace('HH', hours)
      .replace('mm', minutes)
      .replace('ss', seconds);
  }

  /**
   * Format number according to locale
   */
  formatNumber(num, lang = this.currentLanguage, decimals = 0) {
    const locale = this.localeData[lang];

    const parts = num.toFixed(decimals).split('.');
    const integerPart = parts[0];
    const decimalPart = parts[1] || '';

    // Add thousands separator
    const formatted = integerPart.replace(/\B(?=(\d{3})+(?!\d))/g, locale.thousandsSeparator);

    if (decimalPart) {
      return formatted + locale.decimalSeparator + decimalPart;
    }
    return formatted;
  }

  /**
   * Format currency according to locale
   */
  formatCurrency(amount, lang = this.currentLanguage) {
    const locale = this.localeData[lang];
    const formatted = this.formatNumber(amount, lang, 2);

    // Format depends on language convention
    switch (lang) {
      case 'ko':
      case 'ja':
      case 'zh':
        return `${formatted}${locale.currencySymbol}`;
      default:
        return `${locale.currencySymbol}${formatted}`;
    }
  }

  /**
   * Format relative time (e.g., "2 hours ago")
   */
  formatRelativeTime(date, lang = this.currentLanguage) {
    const now = new Date();
    const diff = now - (date instanceof Date ? date : new Date(date));

    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (seconds < 60) {
      return this.t('time_just_now');
    } else if (minutes < 60) {
      return `${minutes} ${this.t('time_minutes_ago')}`;
    } else if (hours < 24) {
      return `${hours} ${this.t('time_hours_ago')}`;
    } else {
      return `${days} ${this.t('time_days_ago')}`;
    }
  }

  /**
   * Get all supported languages
   */
  getSupportedLanguages() {
    return this.supportedLanguages.map(lang => ({
      code: lang,
      name: this.languageNames[lang]
    }));
  }

  /**
   * Check if language is supported
   */
  isLanguageSupported(lang) {
    return this.supportedLanguages.includes(lang);
  }
}

// Create global instance
window.i18n = new I18nManager();

// Auto-initialize on DOM ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    window.i18n.init();
  });
} else {
  window.i18n.init();
}

// Export for use in modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = I18nManager;
}

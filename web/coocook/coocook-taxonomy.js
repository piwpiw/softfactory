(function () {
    const countryMenuMeta = {
        KR: {
            key: 'KR',
            label: '대한민국',
            flag: '🇰🇷',
            menu: {
                beauty: { key: 'beauty', label: '뷰티', emoji: '💄', keywordHint: '뷰티', menuHint: '뷰티케어' },
                food: { key: 'food', label: '푸드', emoji: '🍽', keywordHint: '식품', menuHint: '식품/푸드' },
                tech: { key: 'tech', label: '테크', emoji: '🛠', keywordHint: '가전', menuHint: 'IT/가전' },
                review: { key: '리뷰', label: '리뷰', emoji: '📝', keywordHint: '리뷰', menuHint: '베스트셀러' },
                lifestyle: { key: '라이프', label: '라이프', emoji: '🌿', keywordHint: '라이프스타일', menuHint: '리빙/라이프' }
            }
        },
        US: {
            key: 'US',
            label: '미국',
            flag: '🇺🇸',
            menu: {
                beauty: { key: 'beauty', label: 'Beauty', emoji: '🧴', keywordHint: 'beauty', menuHint: 'Beauty & Wellness' },
                food: { key: 'food', label: 'Food', emoji: '🍱', keywordHint: 'food', menuHint: 'Food & Grocery' },
                tech: { key: 'tech', label: 'Tech', emoji: '💻', keywordHint: 'tech', menuHint: 'Electronics' },
                review: { key: '리뷰', label: 'Review', emoji: '📝', keywordHint: 'review', menuHint: 'Trending Picks' }
            }
        },
        JP: {
            key: 'JP',
            label: '일본',
            flag: '🇯🇵',
            menu: {
                beauty: { key: 'beauty', label: 'ビューティー', emoji: '💄', keywordHint: '美容', menuHint: 'Beauty' },
                food: { key: 'food', label: 'フード', emoji: '🍱', keywordHint: '食', menuHint: 'Food' },
                tech: { key: 'tech', label: 'テック', emoji: '📱', keywordHint: 'ガジェット', menuHint: 'Electronics' },
                lifestyle: { key: '라이프', label: 'ライフ', emoji: '🌿', keywordHint: '生活', menuHint: 'Lifestyle' }
            }
        },
        SG: {
            key: 'SG',
            label: '싱가포르',
            flag: '🇸🇬',
            menu: {
                beauty: { key: 'beauty', label: 'Beauty', emoji: '✨', keywordHint: 'beauty', menuHint: 'Beauty' },
                food: { key: 'food', label: 'Food', emoji: '🍜', keywordHint: 'food', menuHint: 'Food' },
                lifestyle: { key: '라이프', label: 'Lifestyle', emoji: '🌿', keywordHint: 'lifestyle', menuHint: 'Home & Life' }
            }
        },
        GB: {
            key: 'GB',
            label: '영국',
            flag: '🇬🇧',
            menu: {
                beauty: { key: 'beauty', label: 'Beauty', emoji: '💄', keywordHint: 'beauty', menuHint: 'Beauty' },
                tech: { key: 'tech', label: 'Tech', emoji: '🧰', keywordHint: 'tech', menuHint: 'Tech' },
                lifestyle: { key: '라이프', label: 'Lifestyle', emoji: '🌿', keywordHint: 'lifestyle', menuHint: 'Lifestyle' }
            }
        },
        DE: {
            key: 'DE',
            label: '독일',
            flag: '🇩🇪',
            menu: {
                food: { key: 'food', label: 'Essen', emoji: '🍞', keywordHint: 'essen', menuHint: 'Food' },
                tech: { key: 'tech', label: 'Technik', emoji: '🛠', keywordHint: 'technik', menuHint: 'Electronics' },
                review: { key: '리뷰', label: 'Review', emoji: '📝', keywordHint: 'review', menuHint: 'Top Rated' }
            }
        }
    };

    const COUNTRY_MENU_DEFAULT_LABELS = {
        beauty: '뷰티',
        food: '푸드',
        tech: '테크',
        review: '리뷰',
        라이프: '라이프',
        lifestyle: '라이프'
    };

    const countryCuisineDefaults = {
        KR: 'Korean',
        US: 'American',
        JP: 'Japanese',
        SG: 'Japanese',
        GB: 'French',
        DE: 'German',
        IT: 'Italian',
        FR: 'French',
        ES: 'Spanish',
        MX: 'Mexican',
        CN: 'Chinese',
        TW: 'Chinese',
        HK: 'Chinese',
        TH: 'Thai',
        VN: 'Vietnamese',
        IN: 'Indian',
        TR: 'Turkish',
        CA: 'American',
        AU: 'American'
    };

    function normalizeCountry(value) {
        const normalized = String(value || '').toUpperCase().trim();
        return countryMenuMeta[normalized] ? normalized : 'KR';
    }

    function getCountryMeta(value) {
        return countryMenuMeta[normalizeCountry(value)] || countryMenuMeta.KR;
    }

    function getCountryMenus(country) {
        return Object.values(getCountryMeta(country).menu);
    }

    function normalizeMenuCategoryHint(value, countryMenu) {
        const normalized = String(value || "").trim().toLowerCase();
        if (!normalized || !countryMenu) {
            return "";
        }
        const keys = Object.keys(countryMenu);
        const directKey = keys.find((key) => key.toLowerCase() === normalized);
        if (directKey) {
            return directKey;
        }

        const directMetaKey = keys.find((key) => {
            return String(countryMenu[key]?.key || "").toLowerCase() === normalized;
        });
        if (directMetaKey) {
            return directMetaKey;
        }

        const directLabel = keys.find((key) => {
            return String(countryMenu[key]?.label || "").toLowerCase() === normalized;
        });
        if (directLabel) {
            return directLabel;
        }

        const directKeyword = keys.find((key) => {
            const keyword = String(countryMenu[key]?.keywordHint || "").toLowerCase();
            return keyword && (keyword === normalized || keyword.includes(normalized) || normalized.includes(keyword));
        });
        if (directKeyword) {
            return directKeyword;
        }

        const directMenuHint = keys.find((key) => {
            const hint = String(countryMenu[key]?.menuHint || "").toLowerCase();
            return hint && (hint === normalized || hint.includes(normalized) || normalized.includes(hint));
        });
        if (directMenuHint) {
            return directMenuHint;
        }
        return "";
    }

    function getRecipeCategoryAsMenu(countryMenu, category) {
        const normalized = normalizeMenuCategory(category);
        const fromMenuCategory = normalizeMenuCategoryHint(category, countryMenu);
        if (fromMenuCategory) {
            return fromMenuCategory;
        }
        if (countryMenu.food) {
            return "food";
        }
        if (countryMenu.beauty && (normalized === "review" || normalized === "lifestyle")) {
            return COUNTRY_MENU_DEFAULT_LABELS[normalized] || "beauty";
        }
        return Object.keys(countryMenu)[0] || "beauty";
    }

    function getCountryMenu(country, category) {
        const menus = getCountryMeta(country).menu;
        const normalized = getRecipeCategoryAsMenu(menus, category);
        return menus[normalized] || Object.values(menus)[0] || null;
    }

    function getAvailableCountries() {
        return Object.keys(countryMenuMeta);
    }

    function resolveDefaultCuisine(country) {
        return countryCuisineDefaults[normalizeCountry(country)] || 'Korean';
    }

    function getAvailableCuisineKeys() {
        return Object.keys(cuisineMeta);
    }

    function getAvailableMenuCategoryKeys() {
        return Object.keys(menuCategoryMeta);
    }

    function getAvailableIngredientCategoryKeys() {
        return Object.keys(ingredientCategoryMeta);
    }

    const cuisineMeta = {
        Korean: {
            key: 'Korean',
            label: '한식',
            flag: '🇰🇷',
            emoji: '🍚',
            accent: 'text-rose-300',
            chipClass: 'bg-rose-500/15 text-rose-200 border border-rose-400/30',
            panelClass: 'from-rose-500/20 via-orange-500/10 to-amber-500/10',
            image: 'https://images.unsplash.com/photo-1498654896293-37aacf113fd9?auto=format&fit=crop&w=900&q=80',
            promise: '담백한 구성으로 한 끼를 정제하고, 감각적인 플레이팅까지 완성하는 라이트 감성 레시피'
        },
        Italian: {
            key: 'Italian',
            label: '이탈리아',
            flag: '🇮🇹',
            emoji: '🍝',
            accent: 'text-emerald-300',
            chipClass: 'bg-emerald-500/15 text-emerald-200 border border-emerald-400/30',
            panelClass: 'from-emerald-500/20 via-lime-500/10 to-yellow-500/10',
            image: 'https://images.unsplash.com/photo-1516100882582-96c3a05fe590?auto=format&fit=crop&w=900&q=80',
            promise: '향신료와 올리브 오일의 균형으로 풍미를 극대화한 한 끼 중심 레시피'
        },
        Japanese: {
            key: 'Japanese',
            label: '일식',
            flag: '🇯🇵',
            emoji: '🍣',
            accent: 'text-sky-300',
            chipClass: 'bg-sky-500/15 text-sky-200 border border-sky-400/30',
            panelClass: 'from-sky-500/20 via-cyan-500/10 to-indigo-500/10',
            image: 'https://images.unsplash.com/photo-1579871494447-9811cf80d66c?auto=format&fit=crop&w=900&q=80',
            promise: '정갈한 재료 배치와 절제된 소스로 핵심의 맛을 끌어내는 현대식 일식'
        },
        French: {
            key: 'French',
            label: '프랑스',
            flag: '🇫🇷',
            emoji: '🧀',
            accent: 'text-violet-300',
            chipClass: 'bg-violet-500/15 text-violet-200 border border-violet-400/30',
            panelClass: 'from-violet-500/20 via-fuchsia-500/10 to-rose-500/10',
            image: 'https://images.unsplash.com/photo-1547592180-85f173990554?auto=format&fit=crop&w=900&q=80',
            promise: '재료의 농도와 버터 베이스로 깊은 풍미를 만드는 레스토랑 감성 레시피'
        },
        Mexican: {
            key: 'Mexican',
            label: '멕시코',
            flag: '🇲🇽',
            emoji: '🌮',
            accent: 'text-amber-300',
            chipClass: 'bg-amber-500/15 text-amber-200 border border-amber-400/30',
            panelClass: 'from-amber-500/20 via-orange-500/10 to-red-500/10',
            image: 'https://images.unsplash.com/photo-1552332386-f8dd00dc2f85?auto=format&fit=crop&w=900&q=80',
            promise: '맵기와 산뜻한 산미를 절묘하게 맞춘 길거리식 감성의 강한 캐릭터 요리'
        }
    };

    const menuCategoryMeta = {
        stew: { key: 'stew', label: '찌개', emoji: '🍲', chipClass: 'bg-orange-500/15 text-orange-200 border border-orange-400/30' },
        noodle: { key: 'noodle', label: '면', emoji: '🍜', chipClass: 'bg-yellow-500/15 text-yellow-200 border border-yellow-400/30' },
        rice: { key: 'rice', label: '밥', emoji: '🍚', chipClass: 'bg-lime-500/15 text-lime-200 border border-lime-400/30' },
        grill: { key: 'grill', label: '그릴', emoji: '🍖', chipClass: 'bg-rose-500/15 text-rose-200 border border-rose-400/30' },
        bakery: { key: 'bakery', label: '베이커리', emoji: '🍰', chipClass: 'bg-violet-500/15 text-violet-200 border border-violet-400/30' },
        street: { key: 'street', label: '길거리', emoji: '🌮', chipClass: 'bg-amber-500/15 text-amber-200 border border-amber-400/30' },
        main: { key: 'main', label: '메인', emoji: '🍽️', chipClass: 'bg-slate-500/20 text-slate-200 border border-slate-400/30' }
    };

    const ingredientCategoryMeta = {
        produce: { key: 'produce', label: '채소', emoji: '🥬', chipClass: 'bg-emerald-500/15 text-emerald-200 border border-emerald-400/30' },
        protein: { key: 'protein', label: '육류/단백질', emoji: '🥩', chipClass: 'bg-rose-500/15 text-rose-200 border border-rose-400/30' },
        grain: { key: 'grain', label: '곡물', emoji: '🌾', chipClass: 'bg-yellow-500/15 text-yellow-200 border border-yellow-400/30' },
        condiment: { key: 'condiment', label: '양념', emoji: '🧂', chipClass: 'bg-slate-500/20 text-slate-200 border border-slate-400/30' },
        dairy: { key: 'dairy', label: '유제품', emoji: '🧀', chipClass: 'bg-indigo-500/15 text-indigo-200 border border-indigo-400/30' },
        seafood: { key: 'seafood', label: '해산물', emoji: '🦞', chipClass: 'bg-sky-500/15 text-sky-200 border border-sky-400/30' },
        spice: { key: 'spice', label: '향신료', emoji: '🌶️', chipClass: 'bg-red-500/15 text-red-200 border border-red-400/30' }
    };

    const ingredientLookup = {
        '돼지고기': 'protein',
        '소고기': 'protein',
        '닭고기': 'protein',
        '해산물': 'seafood',
        '새우': 'seafood',
        '오징어': 'seafood',
        '연어': 'seafood',
        '달걀': 'protein',
        '계란': 'protein',
        '두부': 'protein',
        '콩': 'protein',
        '치즈': 'dairy',
        '우유': 'dairy',
        '버터': 'dairy',
        '크림': 'dairy',
        '김치': 'condiment',
        '고추장': 'condiment',
        '간장': 'condiment',
        '된장': 'condiment',
        '올리브유': 'condiment',
        '올리브오일': 'condiment',
        '파슬리': 'condiment',
        '마늘': 'condiment',
        '양파': 'produce',
        '감자': 'produce',
        '고구마': 'produce',
        '당근': 'produce',
        '브로콜리': 'produce',
        '파': 'produce',
        '버섯': 'produce',
        '토마토': 'produce',
        '양배추': 'produce',
        '식초': 'condiment',
        '후추': 'spice',
        '맛술': 'condiment',
        '간장': 'condiment',
        '김': 'condiment',
        '현미': 'grain',
        '쌀': 'grain',
        '파스타': 'grain',
        '밀가루': 'grain',
        '빵가루': 'grain',
        '면': 'grain',
        '바질': 'spice',
        '오레가노': 'spice'
    };

    Object.assign(countryMenuMeta, {
        IT: {
            key: 'IT',
            label: '이탈리아',
            flag: '🇮🇹',
            menu: {
                food: { key: 'food', label: 'Food', emoji: '🍝', keywordHint: 'pasta', menuHint: 'Regional Food' },
                bakery: { key: 'bakery', label: 'Bakery', emoji: '🥐', keywordHint: 'bakery', menuHint: 'Bakery' },
                lifestyle: { key: 'lifestyle', label: 'Lifestyle', emoji: '🍷', keywordHint: 'lifestyle', menuHint: 'Lifestyle' }
            }
        },
        FR: {
            key: 'FR',
            label: '프랑스',
            flag: '🇫🇷',
            menu: {
                food: { key: 'food', label: 'Food', emoji: '🧀', keywordHint: 'bistro', menuHint: 'Cuisine' },
                bakery: { key: 'bakery', label: 'Bakery', emoji: '🥖', keywordHint: 'patisserie', menuHint: 'Bakery' },
                lifestyle: { key: 'lifestyle', label: 'Lifestyle', emoji: '🍷', keywordHint: 'lifestyle', menuHint: 'Lifestyle' }
            }
        },
        ES: {
            key: 'ES',
            label: '스페인',
            flag: '🇪🇸',
            menu: {
                food: { key: 'food', label: 'Food', emoji: '🥘', keywordHint: 'tapas', menuHint: 'Tapas' },
                lifestyle: { key: 'lifestyle', label: 'Lifestyle', emoji: '🍊', keywordHint: 'lifestyle', menuHint: 'Mediterranean' },
                review: { key: 'review', label: 'Review', emoji: '📝', keywordHint: 'review', menuHint: 'Chef Picks' }
            }
        },
        MX: {
            key: 'MX',
            label: '멕시코',
            flag: '🇲🇽',
            menu: {
                food: { key: 'food', label: 'Food', emoji: '🌮', keywordHint: 'street food', menuHint: 'Street Food' },
                lifestyle: { key: 'lifestyle', label: 'Lifestyle', emoji: '🌶️', keywordHint: 'fiesta', menuHint: 'Lifestyle' },
                review: { key: 'review', label: 'Review', emoji: '📝', keywordHint: 'review', menuHint: 'Top Rated' }
            }
        },
        CN: {
            key: 'CN',
            label: '중국',
            flag: '🇨🇳',
            menu: {
                food: { key: 'food', label: 'Food', emoji: '🥟', keywordHint: '중식', menuHint: 'Regional Cuisine' },
                tech: { key: 'tech', label: 'Tech', emoji: '📱', keywordHint: 'smart kitchen', menuHint: 'Kitchen Tech' },
                lifestyle: { key: 'lifestyle', label: 'Lifestyle', emoji: '🫖', keywordHint: 'tea', menuHint: 'Tea & Dining' }
            }
        },
        TW: {
            key: 'TW',
            label: '대만',
            flag: '🇹🇼',
            menu: {
                food: { key: 'food', label: 'Food', emoji: '🧋', keywordHint: 'street food', menuHint: 'Night Market' },
                lifestyle: { key: 'lifestyle', label: 'Lifestyle', emoji: '🍵', keywordHint: 'tea', menuHint: 'Tea' },
                review: { key: 'review', label: 'Review', emoji: '📝', keywordHint: 'review', menuHint: 'Popular' }
            }
        },
        HK: {
            key: 'HK',
            label: '홍콩',
            flag: '🇭🇰',
            menu: {
                food: { key: 'food', label: 'Food', emoji: '🥢', keywordHint: 'dim sum', menuHint: 'Dim Sum' },
                lifestyle: { key: 'lifestyle', label: 'Lifestyle', emoji: '🧋', keywordHint: 'cafe', menuHint: 'Cafe' },
                review: { key: 'review', label: 'Review', emoji: '📝', keywordHint: 'review', menuHint: 'Trending' }
            }
        },
        TH: {
            key: 'TH',
            label: '태국',
            flag: '🇹🇭',
            menu: {
                food: { key: 'food', label: 'Food', emoji: '🍜', keywordHint: 'thai food', menuHint: 'Street Food' },
                lifestyle: { key: 'lifestyle', label: 'Lifestyle', emoji: '🥥', keywordHint: 'lifestyle', menuHint: 'Tropical' },
                review: { key: 'review', label: 'Review', emoji: '📝', keywordHint: 'review', menuHint: 'Chef Choice' }
            }
        },
        VN: {
            key: 'VN',
            label: '베트남',
            flag: '🇻🇳',
            menu: {
                food: { key: 'food', label: 'Food', emoji: '🍜', keywordHint: 'pho', menuHint: 'Street Food' },
                lifestyle: { key: 'lifestyle', label: 'Lifestyle', emoji: '☕', keywordHint: 'coffee', menuHint: 'Cafe' },
                review: { key: 'review', label: 'Review', emoji: '📝', keywordHint: 'review', menuHint: 'Local Picks' }
            }
        },
        IN: {
            key: 'IN',
            label: '인도',
            flag: '🇮🇳',
            menu: {
                food: { key: 'food', label: 'Food', emoji: '🍛', keywordHint: 'curry', menuHint: 'Regional Curry' },
                lifestyle: { key: 'lifestyle', label: 'Lifestyle', emoji: '🫓', keywordHint: 'spice', menuHint: 'Spice Pantry' },
                review: { key: 'review', label: 'Review', emoji: '📝', keywordHint: 'review', menuHint: 'Chef Choice' }
            }
        },
        TR: {
            key: 'TR',
            label: '튀르키예',
            flag: '🇹🇷',
            menu: {
                food: { key: 'food', label: 'Food', emoji: '🥙', keywordHint: 'kebab', menuHint: 'Grill' },
                bakery: { key: 'bakery', label: 'Bakery', emoji: '🥮', keywordHint: 'baklava', menuHint: 'Dessert' },
                lifestyle: { key: 'lifestyle', label: 'Lifestyle', emoji: '☕', keywordHint: 'coffee', menuHint: 'Coffee' }
            }
        },
        CA: {
            key: 'CA',
            label: '캐나다',
            flag: '🇨🇦',
            menu: {
                food: { key: 'food', label: 'Food', emoji: '🥞', keywordHint: 'brunch', menuHint: 'Comfort Food' },
                lifestyle: { key: 'lifestyle', label: 'Lifestyle', emoji: '🍁', keywordHint: 'maple', menuHint: 'Local Pantry' },
                review: { key: 'review', label: 'Review', emoji: '📝', keywordHint: 'review', menuHint: 'Local Picks' }
            }
        },
        AU: {
            key: 'AU',
            label: '호주',
            flag: '🇦🇺',
            menu: {
                food: { key: 'food', label: 'Food', emoji: '🥩', keywordHint: 'bbq', menuHint: 'BBQ' },
                lifestyle: { key: 'lifestyle', label: 'Lifestyle', emoji: '☕', keywordHint: 'brunch', menuHint: 'Brunch' },
                review: { key: 'review', label: 'Review', emoji: '📝', keywordHint: 'review', menuHint: 'Trending' }
            }
        }
    });

    Object.assign(cuisineMeta, {
        American: {
            key: 'American',
            label: '아메리칸',
            flag: '🇺🇸',
            emoji: '🍔',
            accent: 'text-cyan-300',
            chipClass: 'bg-cyan-500/15 text-cyan-200 border border-cyan-400/30',
            panelClass: 'from-cyan-500/20 via-sky-500/10 to-blue-500/10',
            image: 'https://images.unsplash.com/photo-1550547660-d9450f859349?auto=format&fit=crop&w=900&q=80',
            promise: '브런치와 바비큐, 캐주얼 다이닝 흐름을 빠르게 연결하는 익숙한 베이스'
        },
        Chinese: {
            key: 'Chinese',
            label: '중식',
            flag: '🇨🇳',
            emoji: '🥟',
            accent: 'text-red-300',
            chipClass: 'bg-red-500/15 text-red-200 border border-red-400/30',
            panelClass: 'from-red-500/20 via-amber-500/10 to-orange-500/10',
            image: 'https://images.unsplash.com/photo-1563245372-f21724e3856d?auto=format&fit=crop&w=900&q=80',
            promise: '볶음, 찜, 면 요리를 중심으로 빠른 풍미 대비를 만드는 고밀도 요리 흐름'
        },
        Thai: {
            key: 'Thai',
            label: '태국',
            flag: '🇹🇭',
            emoji: '🍜',
            accent: 'text-lime-300',
            chipClass: 'bg-lime-500/15 text-lime-200 border border-lime-400/30',
            panelClass: 'from-lime-500/20 via-emerald-500/10 to-yellow-500/10',
            image: 'https://images.unsplash.com/photo-1569562211093-4ed0d0758f12?auto=format&fit=crop&w=900&q=80',
            promise: '허브와 산미, 매운맛이 한 번에 올라오는 동남아 특유의 선명한 레시피 흐름'
        },
        Vietnamese: {
            key: 'Vietnamese',
            label: '베트남',
            flag: '🇻🇳',
            emoji: '🍲',
            accent: 'text-emerald-300',
            chipClass: 'bg-emerald-500/15 text-emerald-200 border border-emerald-400/30',
            panelClass: 'from-emerald-500/20 via-teal-500/10 to-cyan-500/10',
            image: 'https://images.unsplash.com/photo-1515669097368-22e68427d265?auto=format&fit=crop&w=900&q=80',
            promise: '가벼운 육수와 허브, 생채소가 살아 있는 균형형 식사 흐름'
        },
        Indian: {
            key: 'Indian',
            label: '인도',
            flag: '🇮🇳',
            emoji: '🍛',
            accent: 'text-amber-300',
            chipClass: 'bg-amber-500/15 text-amber-200 border border-amber-400/30',
            panelClass: 'from-amber-500/20 via-orange-500/10 to-rose-500/10',
            image: 'https://images.unsplash.com/photo-1585937421612-70a008356fbe?auto=format&fit=crop&w=900&q=80',
            promise: '스파이스 레이어와 소스 농도를 중심으로 한 진한 향신 흐름'
        },
        Spanish: {
            key: 'Spanish',
            label: '스페인',
            flag: '🇪🇸',
            emoji: '🥘',
            accent: 'text-orange-300',
            chipClass: 'bg-orange-500/15 text-orange-200 border border-orange-400/30',
            panelClass: 'from-orange-500/20 via-amber-500/10 to-yellow-500/10',
            image: 'https://images.unsplash.com/photo-1515443961218-a51367888e4b?auto=format&fit=crop&w=900&q=80',
            promise: '해산물과 쌀, 타파스 식 구성을 연결하는 지중해형 요리 흐름'
        },
        Turkish: {
            key: 'Turkish',
            label: '튀르키예',
            flag: '🇹🇷',
            emoji: '🥙',
            accent: 'text-rose-300',
            chipClass: 'bg-rose-500/15 text-rose-200 border border-rose-400/30',
            panelClass: 'from-rose-500/20 via-red-500/10 to-orange-500/10',
            image: 'https://images.unsplash.com/photo-1544025162-d76694265947?auto=format&fit=crop&w=900&q=80',
            promise: '그릴과 플랫브레드, 요거트 소스로 완성되는 풍부한 한 접시 중심 흐름'
        },
        German: {
            key: 'German',
            label: '독일',
            flag: '🇩🇪',
            emoji: '🥨',
            accent: 'text-yellow-300',
            chipClass: 'bg-yellow-500/15 text-yellow-200 border border-yellow-400/30',
            panelClass: 'from-yellow-500/20 via-amber-500/10 to-slate-500/10',
            image: 'https://images.unsplash.com/photo-1603360946369-dc9bb6258143?auto=format&fit=crop&w=900&q=80',
            promise: '고기와 빵, 감자 중심의 묵직한 컴포트 푸드 흐름'
        }
    });

    Object.assign(menuCategoryMeta, {
        dessert: { key: 'dessert', label: '디저트', emoji: '🍮', chipClass: 'bg-pink-500/15 text-pink-200 border border-pink-400/30' },
        soup: { key: 'soup', label: '수프', emoji: '🥣', chipClass: 'bg-orange-500/15 text-orange-200 border border-orange-400/30' },
        brunch: { key: 'brunch', label: '브런치', emoji: '🥞', chipClass: 'bg-cyan-500/15 text-cyan-200 border border-cyan-400/30' },
        salad: { key: 'salad', label: '샐러드', emoji: '🥗', chipClass: 'bg-green-500/15 text-green-200 border border-green-400/30' },
        bowl: { key: 'bowl', label: '볼', emoji: '🥣', chipClass: 'bg-indigo-500/15 text-indigo-200 border border-indigo-400/30' }
    });

    Object.assign(ingredientCategoryMeta, {
        herb: { key: 'herb', label: '허브', emoji: '🌿', chipClass: 'bg-green-500/15 text-green-200 border border-green-400/30' },
        sauce: { key: 'sauce', label: '소스', emoji: '🥫', chipClass: 'bg-orange-500/15 text-orange-200 border border-orange-400/30' },
        fruit: { key: 'fruit', label: '과일', emoji: '🍋', chipClass: 'bg-yellow-500/15 text-yellow-200 border border-yellow-400/30' }
    });

    Object.assign(ingredientLookup, {
        '아보카도': 'fruit',
        '옥수수': 'produce',
        '레몬': 'fruit',
        '라임': 'fruit',
        '고수': 'herb',
        '민트': 'herb',
        '타임': 'herb',
        '로즈마리': 'herb',
        '쌀국수': 'grain',
        '바게트': 'grain',
        '난': 'grain',
        '요거트': 'dairy',
        '커리': 'sauce',
        '카레': 'sauce',
        '토르티야': 'grain',
        '두반장': 'sauce',
        '굴소스': 'sauce',
        '코코넛밀크': 'dairy',
        '병아리콩': 'protein',
        '렌틸콩': 'protein',
        '새송이버섯': 'produce',
        '케일': 'produce',
        '시금치': 'produce',
        '파프리카': 'produce',
        '딜': 'herb',
        '쌀밥': 'grain',
        '타마린드': 'sauce',
        '사워크림': 'dairy',
        '토마토소스': 'sauce',
        '사프란': 'spice'
    });

    const affiliateMeta = {
        disclosure: '연동 링크는 파트너스/제휴 URL 정책에 따라 수익 배분이 달라집니다.',
        cuisineKeywords: {
            Korean: '한식 레시피',
            Italian: '이탈리아 밀키트',
            Japanese: '일식 재료',
            French: '프랑스 레시피',
            Mexican: '멕시칸 푸드'
        },
        categoryKeywords: {
            stew: '전국 별미 찌개 재료',
            noodle: '면 요리 재료',
            rice: '밥 요리 재료',
            grill: '그릴용 고기 도구',
            bakery: '베이커리 밀가루',
            street: '간편 길거리 음식',
            main: '메인 요리 재료'
        },
        ingredientKeywords: {
            produce: '신선한 채소',
            protein: '프리미엄 단백질',
            grain: '곡물 식자재',
            condiment: '요리 양념',
            dairy: '유제품 베이직',
            seafood: '해산물 큐레이션',
            spice: '양념 세트'
        }
    };

    Object.assign(affiliateMeta.cuisineKeywords, {
        American: '브런치 밀키트',
        Chinese: '중식 재료',
        Thai: '태국 요리 재료',
        Vietnamese: '베트남 요리 재료',
        Indian: '인도 커리 키트',
        Spanish: '파에야 재료',
        Turkish: '케밥 재료',
        German: '독일식 컴포트푸드'
    });

    Object.assign(affiliateMeta.categoryKeywords, {
        dessert: '디저트 베이킹 재료',
        soup: '수프 베이스 재료',
        brunch: '브런치 재료',
        salad: '샐러드 재료',
        bowl: '볼 메뉴 재료'
    });

    Object.assign(affiliateMeta.ingredientKeywords, {
        herb: '허브 세트',
        sauce: '요리 소스',
        fruit: '신선 과일'
    });

    function recipe(id, name, cuisine, category, difficulty, prepTime, rating, reviews, chef, chefLabel, image, thumb, price, story, ingredients) {
        return {
            id,
            name,
            cuisine,
            category,
            difficulty,
            prepTime,
            rating,
            reviews,
            chef,
            chefLabel,
            image,
            thumb,
            price,
            story,
            ingredients
        };
    }

    const recipeCatalog = [
        recipe(1, '김치부대찌개', 'Korean', 'stew', 'Easy', 20, 4.8, 156, 'Chef Park', '한식 마스터', '🍲', 'https://images.unsplash.com/photo-1598866594230-6e0f4fb6d0a6?auto=format&fit=crop&w=900&q=80', 25000, '맵기와 깊이를 살린 한식 찌개형 메인', [
            { name: '김치', quantity: 1, unit: '컵', price: 5000 },
            { name: '돼지고기', quantity: 200, unit: 'g', price: 8000 },
            { name: '두부', quantity: 1, unit: '모', price: 3000 },
            { name: '양파', quantity: 1, unit: '개', price: 700 }
        ]),
        recipe(2, '크림 파스타', 'Italian', 'noodle', 'Medium', 30, 4.6, 98, 'Chef Marco', '이탈리아 푸드', '🍝', 'https://images.unsplash.com/photo-1555949258-eb67b1ef0a9a?auto=format&fit=crop&w=900&q=80', 32000, '부드러운 소스로 농도 있는 한 접시', [
            { name: '파스타', quantity: 200, unit: 'g', price: 3500 },
            { name: '크림', quantity: 1, unit: '컵', price: 3000 },
            { name: '마늘', quantity: 4, unit: '쪽', price: 500 },
            { name: '치즈', quantity: 1, unit: '컵', price: 5000 }
        ]),
        recipe(3, '연어 오니기리', 'Japanese', 'rice', 'Hard', 45, 4.9, 203, 'Chef Tanaka', '초밥 큐레이터', '🍙', 'https://images.unsplash.com/photo-1553621042-f6e147245754?auto=format&fit=crop&w=900&q=80', 38000, '식감과 비주얼을 같이 챙기는 정교한 한입', [
            { name: '쌀', quantity: 2, unit: '컵', price: 4500 },
            { name: '연어', quantity: 150, unit: 'g', price: 14000 },
            { name: '김', quantity: 3, unit: '장', price: 200 },
            { name: '간장', quantity: 2, unit: '큰술', price: 400 }
        ]),
        recipe(4, '허니 갈릭 스테이크', 'French', 'grill', 'Hard', 40, 4.7, 145, 'Chef Dubois', '클래식 셰프', '🥩', 'https://images.unsplash.com/photo-1551782450-a2132b4ba21d?auto=format&fit=crop&w=900&q=80', 45000, '불향과 허브 향이 깊게 올라오는 고급스러운 메인', [
            { name: '소고기', quantity: 300, unit: 'g', price: 22000 },
            { name: '버터', quantity: 20, unit: 'g', price: 1000 },
            { name: '마늘', quantity: 6, unit: '쪽', price: 500 },
            { name: '후추', quantity: 1, unit: '작은술', price: 200 }
        ]),
        recipe(5, '치미창가', 'Mexican', 'street', 'Easy', 25, 4.5, 87, 'Chef Garcia', '멕시칸 소울', '🌮', 'https://images.unsplash.com/photo-1505253758473-96b701848f43?auto=format&fit=crop&w=900&q=80', 20000, '재료만 맞추면 빠르게 완성되는 길거리 감성', [
            { name: '토르티야', quantity: 5, unit: '장', price: 2500 },
            { name: '닭고기', quantity: 180, unit: 'g', price: 5000 },
            { name: '아보카도', quantity: 1, unit: '개', price: 2500 },
            { name: '파슬리', quantity: 1, unit: '큰술', price: 800 }
        ]),
        recipe(6, '해물 찌개', 'Korean', 'stew', 'Easy', 25, 4.7, 134, 'Chef Park', '한식 마스터', '🍲', 'https://images.unsplash.com/photo-1587248720327-9f5fc2f4eb6f?auto=format&fit=crop&w=900&q=80', 22000, '해물의 풍미를 살린 한 끼 완성형 한식', [
            { name: '해산물', quantity: 1, unit: '접시', price: 12000 },
            { name: '감자', quantity: 2, unit: '개', price: 1200 },
            { name: '양파', quantity: 1, unit: '개', price: 700 },
            { name: '고추장', quantity: 1, unit: '큰술', price: 700 }
        ]),
        recipe(7, '토마토 리조또', 'Italian', 'rice', 'Medium', 35, 4.4, 76, 'Chef Marco', '이탈리아 푸드', '🍚', 'https://images.unsplash.com/photo-1551882547-ff40c63fe5fa?auto=format&fit=crop&w=900&q=80', 35000, '크리미하고 촉촉한 리조또 플레이팅', [
            { name: '파스타', quantity: 200, unit: 'g', price: 3500 },
            { name: '토마토', quantity: 2, unit: '개', price: 2500 },
            { name: '치즈', quantity: 1, unit: '컵', price: 6000 },
            { name: '양파', quantity: 1, unit: '개', price: 700 }
        ]),
        recipe(8, '규카츠', 'Japanese', 'rice', 'Medium', 30, 4.6, 112, 'Chef Tanaka', '초밥 큐레이터', '🍛', 'https://images.unsplash.com/photo-1585032226651-759b368d0f3c?auto=format&fit=crop&w=900&q=80', 28000, '겉바속촉의 기본에 충실한 도시락형 인기 메뉴', [
            { name: '돼지고기', quantity: 250, unit: 'g', price: 9000 },
            { name: '달걀', quantity: 2, unit: '개', price: 1200 },
            { name: '밥', quantity: 1, unit: '그릇', price: 1500 },
            { name: '파슬리', quantity: 1, unit: '큰술', price: 800 }
        ]),
        recipe(9, '레몬 타르트', 'French', 'bakery', 'Hard', 120, 4.8, 89, 'Chef Dubois', '클래식 셰프', '🥧', 'https://images.unsplash.com/photo-1464306076886-debede4d6f8c?auto=format&fit=crop&w=900&q=80', 18000, '단맛과 산미를 정교하게 밸런싱한 디저트', [
            { name: '버터', quantity: 1, unit: '컵', price: 3500 },
            { name: '달걀', quantity: 3, unit: '개', price: 1800 },
            { name: '밀가루', quantity: 1, unit: '컵', price: 1200 },
            { name: '우유', quantity: 1, unit: '컵', price: 2500 }
        ]),
        recipe(10, '타코 부대', 'Mexican', 'street', 'Medium', 40, 4.5, 65, 'Chef Garcia', '멕시칸 소울', '🌯', 'https://images.unsplash.com/photo-1562967915-4f64f8f2f0c2?auto=format&fit=crop&w=900&q=80', 26000, '한 번 만들고 바로 공유하고 싶은 매운 길거리 퀵 메뉴', [
            { name: '옥수수', quantity: 3, unit: '개', price: 1200 },
            { name: '소고기', quantity: 200, unit: 'g', price: 10000 },
            { name: '치즈', quantity: 1, unit: '컵', price: 4500 },
            { name: '고추', quantity: 2, unit: '개', price: 400 }
        ]),
        recipe(11, '마파두부 덮밥', 'Chinese', 'bowl', 'Medium', 28, 4.7, 119, 'Chef Lin', '사천 홈키친', '🥢', 'https://images.unsplash.com/photo-1547592180-85f173990554?auto=format&fit=crop&w=900&q=80', 27000, '매콤한 두반장 소스와 두부를 밥 위에 빠르게 얹는 고밀도 한 그릇', [
            { name: '두부', quantity: 1, unit: '모', price: 3000 },
            { name: '두반장', quantity: 2, unit: '큰술', price: 1600 },
            { name: '쌀밥', quantity: 2, unit: '공기', price: 3000 },
            { name: '파', quantity: 1, unit: '대', price: 700 }
        ]),
        recipe(12, '팟타이', 'Thai', 'noodle', 'Medium', 24, 4.8, 131, 'Chef Arun', '방콕 스트리트', '🍜', 'https://images.unsplash.com/photo-1559314809-0f31657def5e?auto=format&fit=crop&w=900&q=80', 29000, '새콤달콤한 소스와 면, 허브가 한번에 들어오는 대표적인 태국식 한 접시', [
            { name: '쌀국수', quantity: 200, unit: 'g', price: 3200 },
            { name: '새우', quantity: 180, unit: 'g', price: 9800 },
            { name: '타마린드', quantity: 2, unit: '큰술', price: 1800 },
            { name: '고수', quantity: 1, unit: '줌', price: 1200 }
        ]),
        recipe(13, '쌀국수', 'Vietnamese', 'soup', 'Easy', 22, 4.6, 104, 'Chef Nguyen', '사이공 브로스', '🍲', 'https://images.unsplash.com/photo-1529042410759-befb1204b468?auto=format&fit=crop&w=900&q=80', 24000, '가벼운 육수와 허브, 라임으로 마무리하는 베트남식 면 수프', [
            { name: '쌀국수', quantity: 180, unit: 'g', price: 3200 },
            { name: '소고기', quantity: 150, unit: 'g', price: 9500 },
            { name: '라임', quantity: 1, unit: '개', price: 900 },
            { name: '고수', quantity: 1, unit: '줌', price: 1200 }
        ]),
        recipe(14, '버터 치킨 커리', 'Indian', 'main', 'Medium', 38, 4.8, 142, 'Chef Aditi', '델리 스파이스 랩', '🍛', 'https://images.unsplash.com/photo-1603894584373-5ac82b2ae398?auto=format&fit=crop&w=900&q=80', 33000, '버터와 토마토소스, 향신료가 겹겹이 쌓이는 진한 커리 플레이트', [
            { name: '닭고기', quantity: 220, unit: 'g', price: 6500 },
            { name: '토마토소스', quantity: 1, unit: '컵', price: 2200 },
            { name: '버터', quantity: 30, unit: 'g', price: 1200 },
            { name: '난', quantity: 2, unit: '장', price: 2500 }
        ]),
        recipe(15, '파에야', 'Spanish', 'rice', 'Hard', 46, 4.7, 91, 'Chef Lucia', '바르셀로나 테이블', '🥘', 'https://images.unsplash.com/photo-1515443961218-a51367888e4b?auto=format&fit=crop&w=900&q=80', 36000, '해산물과 사프란 향이 살아 있는 지중해식 대표 쌀요리', [
            { name: '쌀', quantity: 2, unit: '컵', price: 4500 },
            { name: '해산물', quantity: 1, unit: '접시', price: 13000 },
            { name: '사프란', quantity: 1, unit: '봉', price: 3000 },
            { name: '토마토', quantity: 2, unit: '개', price: 2500 }
        ]),
        recipe(16, '도너 케밥 플레이트', 'Turkish', 'grill', 'Medium', 34, 4.6, 88, 'Chef Demir', '이스탄불 그릴', '🥙', 'https://images.unsplash.com/photo-1544025162-d76694265947?auto=format&fit=crop&w=900&q=80', 31000, '요거트 소스와 그릴 고기, 플랫브레드가 균형을 이루는 한 접시', [
            { name: '소고기', quantity: 220, unit: 'g', price: 12000 },
            { name: '요거트', quantity: 1, unit: '컵', price: 2800 },
            { name: '난', quantity: 2, unit: '장', price: 2500 },
            { name: '토마토', quantity: 1, unit: '개', price: 1200 }
        ]),
        recipe(17, '프렌치 토스트 브런치', 'American', 'brunch', 'Easy', 18, 4.5, 77, 'Chef Olivia', '뉴욕 브런치 룸', '🥞', 'https://images.unsplash.com/photo-1484723091739-30a097e8f929?auto=format&fit=crop&w=900&q=80', 21000, '과일과 크림, 토스트로 가볍게 완성하는 아메리칸 브런치 구성', [
            { name: '빵가루', quantity: 2, unit: '컵', price: 1800 },
            { name: '달걀', quantity: 3, unit: '개', price: 1800 },
            { name: '우유', quantity: 1, unit: '컵', price: 2500 },
            { name: '레몬', quantity: 1, unit: '개', price: 900 }
        ]),
        recipe(18, '슈니첼 플레이트', 'German', 'main', 'Medium', 33, 4.4, 64, 'Chef Bauer', '베를린 키친', '🥨', 'https://images.unsplash.com/photo-1603360946369-dc9bb6258143?auto=format&fit=crop&w=900&q=80', 30000, '바삭한 커틀릿과 감자, 허브 버터를 묶은 독일식 컴포트 푸드', [
            { name: '돼지고기', quantity: 220, unit: 'g', price: 9000 },
            { name: '빵가루', quantity: 1, unit: '컵', price: 1200 },
            { name: '감자', quantity: 2, unit: '개', price: 1200 },
            { name: '로즈마리', quantity: 1, unit: '줌', price: 1200 }
        ])
    ].map((item) => ({
        ...item,
        ingredients: item.ingredients.map((ingredient) => ({
            ...ingredient,
            category: ingredient.category || inferIngredientCategory(ingredient.name),
        })),
    }));

    function normalizeCuisine(value) {
        return cuisineMeta[value] ? value : 'Korean';
    }

    function normalizeMenuCategory(value) {
        return menuCategoryMeta[value] ? value : 'main';
    }

    function normalizeIngredientCategory(value) {
        return ingredientCategoryMeta[value] ? value : 'produce';
    }

    function inferIngredientCategory(name) {
        return normalizeIngredientCategory(ingredientLookup[name] || 'produce');
    }

    function normalizeIngredientName(value) {
        return String(value || '').trim().toLowerCase();
    }

    function getCuisineMeta(value) {
        return cuisineMeta[normalizeCuisine(value)];
    }

    function getMenuCategoryMeta(value) {
        return menuCategoryMeta[normalizeMenuCategory(value)];
    }

    function getIngredientCategoryMeta(value) {
        return ingredientCategoryMeta[normalizeIngredientCategory(value)];
    }

    function formatCurrency(value) {
        return new Intl.NumberFormat('ko-KR', {
            style: 'currency',
            currency: 'KRW',
            maximumFractionDigits: 0
        }).format(value);
    }

    function parseState() {
        const params = new URLSearchParams(window.location.search);
        const rawCountry = params.get('country') || params.get('region') || '';
        return {
            cuisine: params.get('cuisine') || '',
            category: params.get('category') || '',
            country: rawCountry ? normalizeCountry(rawCountry) : '',
            menu: params.get('menu') || '',
            difficulty: params.get('difficulty') || '',
            ingredientCategory: params.get('ingredientCategory') || '',
            ingredient: params.get('ingredient') || '',
            recipe: params.get('recipe') || '',
            view: params.get('view') || '',
        };
    }

    function buildHref(page, params = {}) {
        const currentState = parseState();
        const merged = {
            ...currentState,
            ...params
        };
        const search = new URLSearchParams();
        const hasExplicitCountry = Object.prototype.hasOwnProperty.call(params, 'country');
        Object.entries(merged).forEach(([key, value]) => {
            if (value === null || value === undefined || value === '') {
                if (key === 'country' && hasExplicitCountry) {
                    search.delete('country');
                }
                return;
            }
            if (key === 'country' && !normalizeCountry(value)) {
                return;
            }
            search.set(key, String(value));
        });
        const query = search.toString();
        return query ? `${page}?${query}` : page;
    }

    function updateUrl(params) {
        const href = buildHref(window.location.pathname.split('/').pop(), params);
        window.history.replaceState({}, '', href);
    }

    function safeChefEmoji(raw, cuisine) {
        if (raw && /[\u{1F300}-\u{1FAFF}\u2600-\u27BF]/u.test(raw)) {
            return raw;
        }
        return getCuisineMeta(cuisine).emoji;
    }

    function buildAffiliateUrl(keyword, context = {}) {
        const baseUrl = 'https://link.coupang.com/re/';
        const normalizedCountry = normalizeCountry(context.country);
        const params = new URLSearchParams({
            q: keyword,
            source: 'coocook'
        });
        if (context.cuisine) params.set('cuisine', context.cuisine);
        if (context.category) params.set('category', context.category);
        if (context.recipeId) params.set('recipe_id', String(context.recipeId));
        if (context.ingredient) params.set('ingredient', context.ingredient);
        if (normalizedCountry) params.set('country', normalizedCountry);
        const menu = getCountryMenu(normalizedCountry, context.category);
        if (menu && menu.key) params.set('menu', menu.key);
        return `${baseUrl}?${params.toString()}`;
    }

    function getCuisineAffiliate(cuisine, context = {}) {
        const normalized = normalizeCuisine(cuisine);
        const meta = getCuisineMeta(normalized);
        const keyword = affiliateMeta.cuisineKeywords[normalized] || `${meta.label} 레시피`;
        return {
            scope: 'cuisine',
            keyword,
            label: `${meta.flag} ${meta.label} 추천 상품`,
            emoji: meta.emoji,
            url: buildAffiliateUrl(keyword, { ...context, cuisine: normalized }),
            disclosure: affiliateMeta.disclosure
        };
    }

    function getCategoryAffiliate(category, cuisine = '', context = {}) {
        const normalized = normalizeMenuCategory(category);
        const meta = getMenuCategoryMeta(normalized);
        const keyword = affiliateMeta.categoryKeywords[normalized] || `${meta.label} 요리 재료`;
        return {
            scope: 'category',
            keyword,
            label: `${meta.emoji} ${meta.label} 핵심 상품`,
            emoji: meta.emoji,
            url: buildAffiliateUrl(keyword, { ...context, cuisine, category: normalized }),
            disclosure: affiliateMeta.disclosure
        };
    }

    function getIngredientAffiliate(ingredientCategory, ingredientName = '', context = {}) {
        const normalized = normalizeIngredientCategory(ingredientCategory);
        const meta = getIngredientCategoryMeta(normalized);
        const keyword = ingredientName ? `${ingredientName} ${affiliateMeta.ingredientKeywords[normalized]}` : affiliateMeta.ingredientKeywords[normalized];
        return {
            scope: 'ingredient',
            keyword,
            label: `${meta.emoji} ${meta.label} 상품`,
            emoji: meta.emoji,
            url: buildAffiliateUrl(keyword, { ...context, ingredient: ingredientName }),
            disclosure: affiliateMeta.disclosure
        };
    }

    function getRecipeAffiliates(recipe, context = {}) {
        const cuisine = normalizeCuisine(recipe.cuisine);
        const category = normalizeMenuCategory(recipe.category);
        return [
            getCuisineAffiliate(cuisine, context),
            getCategoryAffiliate(category, cuisine, { ...context, category }),
            ...recipe.ingredients.slice(0, 2).map((ingredient) => getIngredientAffiliate(ingredient.category, ingredient.name, { ...context, category }))
        ];
    }

    function mergeShoppingItems(recipes) {
        const merged = new Map();
        recipes.forEach((recipe) => {
            recipe.ingredients.forEach((ingredient) => {
                const key = `${ingredient.name}::${ingredient.unit}`;
                if (!merged.has(key)) {
                    merged.set(key, {
                        name: ingredient.name,
                        category: ingredient.category,
                        unit: ingredient.unit,
                        qty: 0,
                        totalQuantity: 0,
                        sources: new Set(),
                        price: 0
                    });
                }
                const current = merged.get(key);
                current.qty += Number(ingredient.quantity) || 0;
                current.price += Number(ingredient.price) || 0;
                current.sources.add(recipe.name);
            });
        });
        return Array.from(merged.values())
            .map((item) => ({
                ...item,
                quantity: item.qty,
                sources: [...item.sources],
                totalPrice: item.price,
            }))
            .sort((a, b) => b.totalPrice - a.totalPrice);
    }

    function enrichChef(chef) {
        const cuisine = chef.cuisine || chef.cuisine_type || 'Korean';
        const category = chef.category || 'main';
        const categoryNormalized = normalizeMenuCategory(category);
        return {
            ...chef,
            cuisine,
            category: categoryNormalized,
            image: chef.image || safeChefEmoji(chef.avatar, cuisine),
            avatar: chef.image || safeChefEmoji(chef.avatar, cuisine),
            cuisineMeta: getCuisineMeta(cuisine),
            affiliate: getCuisineAffiliate(cuisine),
            menuCategoryMeta: getMenuCategoryMeta(categoryNormalized),
            categoryMeta: getMenuCategoryMeta(categoryNormalized)
        };
    }

    function enrichRecipe(recipeItem) {
        const cuisine = normalizeCuisine(recipeItem.cuisine);
        const category = normalizeMenuCategory(recipeItem.category);
        const ingredients = (recipeItem.ingredients || []).map((ingredient) => ({
            ...ingredient,
            category: normalizeIngredientCategory(ingredient.category)
        }));
        return {
            ...recipeItem,
            cuisine,
            category,
            cuisineMeta: getCuisineMeta(cuisine),
            categoryMeta: getMenuCategoryMeta(category),
            ingredients,
            affiliateLinks: getRecipeAffiliates({ ...recipeItem, cuisine, category, ingredients }, { cuisine, category, country: normalizeCountry(recipeItem.country) })
        };
    }

    const enrichedRecipes = recipeCatalog.map((recipeItem) => enrichRecipe(recipeItem));

    const defaultChefCatalog = [
        { id: 101, name: 'Chef Park', cuisine: 'Korean', category: 'stew', avatar: '🍲', rating: 4.9, rating_count: 128, price_per_session: 26000, location: '서울 종로구', bio: '국물 요리와 집밥형 클래스에 강한 한식 셰프', specialties: ['한식', '찌개', '집밥'] },
        { id: 102, name: 'Chef Marco', cuisine: 'Italian', category: 'noodle', avatar: '🍝', rating: 4.8, rating_count: 102, price_per_session: 35000, location: '서울 강남구', bio: '파스타와 리조또를 감각적으로 구성하는 이탈리아 셰프', specialties: ['파스타', '리조또', '플레이팅'] },
        { id: 103, name: 'Chef Tanaka', cuisine: 'Japanese', category: 'rice', avatar: '🍙', rating: 4.8, rating_count: 133, price_per_session: 32000, location: '서울 서초구', bio: '밥과 해산물 중심의 절제된 일식 클래스를 운영', specialties: ['오니기리', '도시락', '해산물'] },
        { id: 104, name: 'Chef Dubois', cuisine: 'French', category: 'bakery', avatar: '🥐', rating: 4.7, rating_count: 91, price_per_session: 42000, location: '서울 성동구', bio: '디저트와 소스 베이스 수업에 강한 프렌치 셰프', specialties: ['타르트', '소스', '디저트'] },
        { id: 105, name: 'Chef Garcia', cuisine: 'Mexican', category: 'street', avatar: '🌮', rating: 4.6, rating_count: 88, price_per_session: 28000, location: '서울 마포구', bio: '타코와 길거리 감성 메뉴를 빠르게 익히는 멕시칸 셰프', specialties: ['타코', '스트리트푸드', '살사'] },
        { id: 106, name: 'Chef Lin', cuisine: 'Chinese', category: 'bowl', avatar: '🥢', rating: 4.7, rating_count: 74, price_per_session: 30000, location: '서울 용산구', bio: '중식 팬워크와 소스 레이어링을 다루는 셰프', specialties: ['마파두부', '볶음', '중식소스'] },
        { id: 107, name: 'Chef Arun', cuisine: 'Thai', category: 'noodle', avatar: '🍜', rating: 4.8, rating_count: 69, price_per_session: 31000, location: '서울 송파구', bio: '산미와 허브 중심의 태국식 면 요리에 특화', specialties: ['팟타이', '허브', '태국소스'] },
        { id: 108, name: 'Chef Nguyen', cuisine: 'Vietnamese', category: 'soup', avatar: '🍲', rating: 4.6, rating_count: 82, price_per_session: 29000, location: '서울 동작구', bio: '쌀국수와 생채소 구성의 균형을 잡는 베트남 셰프', specialties: ['쌀국수', '허브', '육수'] },
        { id: 109, name: 'Chef Aditi', cuisine: 'Indian', category: 'main', avatar: '🍛', rating: 4.9, rating_count: 95, price_per_session: 34000, location: '서울 이태원', bio: '향신료 블렌딩과 커리 베이스가 강한 인도 셰프', specialties: ['커리', '스파이스', '난'] },
        { id: 110, name: 'Chef Lucia', cuisine: 'Spanish', category: 'rice', avatar: '🥘', rating: 4.7, rating_count: 57, price_per_session: 36000, location: '서울 한남동', bio: '지중해식 쌀요리와 타파스 구성을 전개하는 셰프', specialties: ['파에야', '타파스', '해산물'] },
        { id: 111, name: 'Chef Demir', cuisine: 'Turkish', category: 'grill', avatar: '🥙', rating: 4.6, rating_count: 61, price_per_session: 33000, location: '서울 광진구', bio: '그릴과 플랫브레드를 조합하는 튀르키예 셰프', specialties: ['케밥', '그릴', '요거트소스'] },
        { id: 112, name: 'Chef Olivia', cuisine: 'American', category: 'brunch', avatar: '🥞', rating: 4.5, rating_count: 53, price_per_session: 25000, location: '서울 연남동', bio: '브런치와 가벼운 홈다이닝 메뉴가 강한 셰프', specialties: ['브런치', '토스트', '플레이트'] },
        { id: 113, name: 'Chef Bauer', cuisine: 'German', category: 'main', avatar: '🥨', rating: 4.4, rating_count: 45, price_per_session: 31000, location: '서울 반포동', bio: '독일식 컴포트 푸드와 베이크드 사이드 메뉴에 강한 셰프', specialties: ['슈니첼', '감자', '컴포트푸드'] }
    ];

    function pushToIndex(map, key, item) {
        if (!key) return;
        if (!map.has(key)) {
            map.set(key, []);
        }
        map.get(key).push(item);
    }

    function buildRecipeIndexes(recipes) {
        const indexes = {
            all: [...recipes],
            byId: new Map(),
            byChef: new Map(),
            byCuisine: new Map(),
            byCategory: new Map(),
            byDifficulty: new Map(),
            byIngredientCategory: new Map(),
            byCountryMenu: new Map()
        };

        recipes.forEach((recipeItem) => {
            indexes.byId.set(recipeItem.id, recipeItem);
            pushToIndex(indexes.byChef, recipeItem.chef, recipeItem);
            pushToIndex(indexes.byCuisine, recipeItem.cuisine, recipeItem);
            pushToIndex(indexes.byCategory, recipeItem.category, recipeItem);
            pushToIndex(indexes.byDifficulty, recipeItem.difficulty, recipeItem);
            (recipeItem.ingredients || []).forEach((ingredient) => {
                pushToIndex(indexes.byIngredientCategory, ingredient.category, recipeItem);
            });
            getAvailableCountries().forEach((country) => {
                const menuKey = getRecipeCategoryAsMenu(getCountryMeta(country).menu, recipeItem.category);
                pushToIndex(indexes.byCountryMenu, `${country}:${menuKey}`, recipeItem);
            });
        });

        return indexes;
    }

    function createRecipeQueryEngine(recipes) {
        const recipeIndexes = buildRecipeIndexes(recipes);
        const recipeQueryCache = new Map();

        function queryRecipes(filters = {}) {
            const country = normalizeCountry(filters.country || '');
            const cuisine = filters.cuisine ? normalizeCuisine(filters.cuisine) : '';
            const category = filters.category ? normalizeMenuCategory(filters.category) : '';
            const difficulty = filters.difficulty || '';
            const menu = filters.menu || '';
            const chef = filters.chef || '';
            const ingredientCategory = filters.ingredientCategory ? normalizeIngredientCategory(filters.ingredientCategory) : '';
            const ingredient = normalizeIngredientName(filters.ingredient || '');
            const cacheKey = JSON.stringify({ country, cuisine, category, difficulty, menu, chef, ingredientCategory, ingredient });

            if (recipeQueryCache.has(cacheKey)) {
                return [...recipeQueryCache.get(cacheKey)];
            }

            const candidateSets = [];
            if (chef) candidateSets.push(recipeIndexes.byChef.get(chef) || []);
            if (cuisine) candidateSets.push(recipeIndexes.byCuisine.get(cuisine) || []);
            if (category) candidateSets.push(recipeIndexes.byCategory.get(category) || []);
            if (difficulty) candidateSets.push(recipeIndexes.byDifficulty.get(difficulty) || []);
            if (ingredientCategory) candidateSets.push(recipeIndexes.byIngredientCategory.get(ingredientCategory) || []);
            if (menu) candidateSets.push(recipeIndexes.byCountryMenu.get(`${country}:${menu}`) || []);

            const base = candidateSets.length
                ? [...candidateSets].sort((a, b) => a.length - b.length)[0]
                : recipeIndexes.all;

            const filtered = base.filter((recipeItem) => {
                if (chef && recipeItem.chef !== chef) return false;
                if (cuisine && recipeItem.cuisine !== cuisine) return false;
                if (category && recipeItem.category !== category) return false;
                if (difficulty && recipeItem.difficulty !== difficulty) return false;
                if (menu && getRecipeCategoryAsMenu(getCountryMeta(country).menu, recipeItem.category) !== menu) return false;
                if (ingredientCategory && !(recipeItem.ingredients || []).some((ingredientItem) => ingredientItem.category === ingredientCategory)) return false;
                if (ingredient && !(recipeItem.ingredients || []).some((ingredientItem) => normalizeIngredientName(ingredientItem.name).includes(ingredient))) return false;
                return true;
            });

            recipeQueryCache.set(cacheKey, filtered);
            return [...filtered];
        }

        return {
            recipeIndexes,
            recipeQueryCache,
            queryRecipes
        };
    }

    const defaultRecipeEngine = createRecipeQueryEngine(enrichedRecipes);
    const recipeIndexes = defaultRecipeEngine.recipeIndexes;
    const recipeQueryCache = defaultRecipeEngine.recipeQueryCache;
    const queryRecipes = defaultRecipeEngine.queryRecipes;

    function getRecipesByIds(ids = []) {
        return ids
            .map((id) => recipeIndexes.byId.get(Number(id) || id))
            .filter(Boolean);
    }

    function getChefRecipes(chefName, options = {}) {
        const recipes = queryRecipes({ ...options, chef: chefName });
        const limit = Number(options.limit || 0);
        return limit > 0 ? recipes.slice(0, limit) : recipes;
    }

    function getDefaultChefs() {
        return defaultChefCatalog.map((chef) => enrichChef(chef));
    }

    function buildFeedPosts() {
        return enrichedRecipes.slice(0, 9).map((recipeItem) => ({
            id: recipeItem.id,
            recipeId: recipeItem.id,
            author: `${recipeItem.chef} · ${recipeItem.chefLabel || 'Chef'}`,
            time: '2시간 전',
            avatar: recipeItem.cuisineMeta.emoji,
            title: recipeItem.name,
            image: recipeItem.image,
            thumb: recipeItem.thumb,
            content: `${recipeItem.story} ${recipeItem.cuisineMeta.label} 무드로 이어지는 다음 동선을 같이 확인해보세요.`,
            cuisine: recipeItem.cuisine,
            category: recipeItem.category,
            type: recipeItem.category === 'dessert' ? 'review' : 'tip',
            likes: Math.floor(Math.random() * 220) + 40,
            comments: Math.floor(Math.random() * 60),
            liked: false,
            affiliateLinks: recipeItem.affiliateLinks
        }));
    }

    window.CooCookTaxonomy = {
        cuisineMeta,
        menuCategoryMeta,
        ingredientCategoryMeta,
        recipeCatalog: enrichedRecipes,
        affiliateMeta,
        normalizeCuisine,
        normalizeMenuCategory,
        normalizeIngredientCategory,
        inferIngredientCategory,
        getCuisineMeta,
        getMenuCategoryMeta,
        getIngredientCategoryMeta,
        normalizeCountry,
        getCountryMenus,
        getCountryMenu,
        getAvailableCountries,
        getAvailableCuisineKeys,
        getAvailableMenuCategoryKeys,
        getAvailableIngredientCategoryKeys,
        resolveDefaultCuisine,
        getCountryMeta,
        normalizeMenuCategoryHint,
        getRecipeCategoryAsMenu,
        formatCurrency,
        parseState,
        buildHref,
        updateUrl,
        buildAffiliateUrl,
        getCuisineAffiliate,
        getCategoryAffiliate,
        getIngredientAffiliate,
        getRecipeAffiliates,
        buildRecipeIndexes,
        createRecipeQueryEngine,
        queryRecipes,
        getChefRecipes,
        getRecipesByIds,
        getDefaultChefs,
        enrichChef,
        enrichRecipe,
        mergeShoppingItems,
        buildFeedPosts
    };
})();


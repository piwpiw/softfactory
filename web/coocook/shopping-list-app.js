if (typeof hasAuthSession === "function" && hasAuthSession()) {
    requireAuth();
}
if (typeof setupSessionActionButton === "function") {
    setupSessionActionButton();
}

const taxonomy = window.CooCookTaxonomy;
const state = taxonomy.parseState();
const allRecipes = [...taxonomy.recipeCatalog];

let selectedRecipeIds = [];
let shoppingItems = [];
let modalCountry = state.country || "KR";
let modalCuisine = state.cuisine || "";
let modalMenu = state.menu || "";

function getActiveCountry() {
    return state.country || "KR";
}

function getActiveCuisine() {
    return state.cuisine || taxonomy.resolveDefaultCuisine(getActiveCountry());
}

function getModalCountry() {
    return modalCountry || "";
}

function getCountryMenus(country) {
    return taxonomy.getCountryMenus(country || "KR");
}

function initializeSelection() {
    state.country = getActiveCountry();
    state.cuisine = getActiveCuisine();

    const requestedRecipe = allRecipes.find((recipe) => String(recipe.id) === String(state.recipe));
    const filteredRecipes = taxonomy.queryRecipes({
        country: state.country,
        cuisine: state.cuisine,
        menu: state.menu || "",
        category: state.category || "",
    });
    const baseRecipes = requestedRecipe
        ? [requestedRecipe]
        : filteredRecipes.slice(0, 2);
    const fallbackRecipes = baseRecipes.length ? baseRecipes : allRecipes.slice(0, 2);

    selectedRecipeIds = [...new Set(fallbackRecipes.map((recipe) => recipe.id))];
    shoppingItems = taxonomy.mergeShoppingItems(fallbackRecipes).map((item) => ({
        ...item,
        checked: Boolean(item.checked),
    }));
}

function getSelectedRecipes() {
    return selectedRecipeIds
        .map((id) => allRecipes.find((recipe) => recipe.id === id))
        .filter(Boolean);
}

function refreshItems() {
    const previousItems = shoppingItems;
    shoppingItems = taxonomy.mergeShoppingItems(getSelectedRecipes()).map((item) => {
        const existing = previousItems.find((current) => current.name === item.name);
        return {
            ...item,
            checked: existing ? Boolean(existing.checked) : false,
        };
    });
}

function toggleItem(itemName) {
    const target = shoppingItems.find((item) => item.name === itemName);
    if (!target) {
        return;
    }
    target.checked = !target.checked;
    render();
}

function clearAll() {
    selectedRecipeIds = [];
    shoppingItems = [];
    render();
}

function openCreateModal() {
    modalCountry = state.country || getActiveCountry();
    modalCuisine = state.cuisine || "";
    modalMenu = state.menu || "";
    renderCreateModal();
    document.getElementById("createModal").classList.remove("hidden");
    document.getElementById("createModal").classList.add("flex");
}

function closeCreateModal() {
    document.getElementById("createModal").classList.add("hidden");
    document.getElementById("createModal").classList.remove("flex");
}

function toggleModalCountry(value) {
    modalCountry = modalCountry === value ? "" : value;
    modalCuisine = "";
    modalMenu = "";
    renderCreateModal();
}

function toggleModalCuisine(value) {
    modalCuisine = modalCuisine === value ? "" : value;
    modalMenu = "";
    renderCreateModal();
}

function toggleModalMenu(value) {
    modalMenu = modalMenu === value ? "" : value;
    renderCreateModal();
}

function buildModalButton(active, label, activeClass) {
    const inactiveClass = "bg-slate-800 text-slate-300 hover:bg-slate-700";
    return `class="rounded-full px-3 py-1 text-sm ${active ? activeClass : inactiveClass}"`;
}

function renderCreateModal() {
    const activeCountry = getModalCountry();
    const countryFilters = [{
        key: "",
        label: "전체 국가",
        icon: "🌍",
    }].concat(taxonomy.getAvailableCountries().map((key) => {
        const meta = taxonomy.getCountryMeta(key);
        return { key, label: meta.label, icon: meta.flag };
    })).map((item) => {
        const active = modalCountry === item.key;
        return `<button onclick="toggleModalCountry('${item.key}')" ${buildModalButton(active, item.label, "bg-orange-600 text-white")}>${item.icon} ${item.label}</button>`;
    }).join("");

    const cuisineFilters = [{
        key: "",
        label: "전체 요리",
        icon: "🍽",
    }].concat(taxonomy.getAvailableCuisineKeys().map((key) => {
        const meta = taxonomy.getCuisineMeta(key);
        return { key, label: meta.label, icon: meta.flag };
    })).map((item) => {
        const active = modalCuisine === item.key;
        return `<button onclick="toggleModalCuisine('${item.key}')" ${buildModalButton(active, item.label, "bg-orange-600 text-white")}>${item.icon} ${item.label}</button>`;
    }).join("");

    const menuFilters = [{
        key: "",
        label: "전체 메뉴",
        icon: "🧾",
    }].concat(getCountryMenus(activeCountry).map((menu) => ({
        key: menu.key,
        label: menu.label,
        icon: menu.emoji,
    }))).map((item) => {
        const active = modalMenu === item.key;
        return `<button onclick="toggleModalMenu('${item.key}')" ${buildModalButton(active, item.label, "bg-emerald-600 text-white")}>${item.icon} ${item.label}</button>`;
    }).join("");

    document.getElementById("modalRecipeFilters").innerHTML = `
        <div class="w-full rounded-xl border border-slate-700 p-3">
            <p class="text-xs text-slate-400">국가</p>
            <div class="mt-2 flex flex-wrap gap-2">${countryFilters}</div>
        </div>
        <div class="w-full rounded-xl border border-slate-700 p-3">
            <p class="text-xs text-slate-400">요리</p>
            <div class="mt-2 flex flex-wrap gap-2">${cuisineFilters}</div>
        </div>
        <div class="w-full rounded-xl border border-slate-700 p-3">
            <p class="text-xs text-slate-400">메뉴</p>
            <div class="mt-2 flex flex-wrap gap-2">${menuFilters}</div>
        </div>
    `;

    const filteredRecipes = taxonomy.queryRecipes({
        country: activeCountry,
        cuisine: modalCuisine || "",
        menu: modalMenu || "",
    });

    document.getElementById("recipesList").innerHTML = filteredRecipes.length ? filteredRecipes.map((recipe) => {
        return `<label class="rounded-2xl border border-slate-800 bg-slate-950/70 p-4">
            <div class="flex items-start gap-4">
                <input type="checkbox" class="mt-1 h-4 w-4" value="${recipe.id}" ${selectedRecipeIds.includes(recipe.id) ? "checked" : ""}>
                <img src="${recipe.thumb}" alt="${recipe.name}" class="h-20 w-24 rounded-xl object-cover">
                <div class="min-w-0 flex-1">
                    <div class="flex flex-wrap gap-2">
                        <span class="rounded-full px-3 py-1 text-xs ${recipe.cuisineMeta.chipClass}">${recipe.cuisineMeta.flag} ${recipe.cuisineMeta.label}</span>
                        <span class="rounded-full px-3 py-1 text-xs ${recipe.categoryMeta.chipClass}">${recipe.categoryMeta.emoji} ${recipe.categoryMeta.label}</span>
                    </div>
                    <p class="mt-3 font-semibold text-white">${recipe.image} ${recipe.name}</p>
                    <p class="mt-1 text-xs text-slate-400">${recipe.story}</p>
                </div>
            </div>
        </label>`;
    }).join("") : `<div class="rounded-2xl border border-dashed border-slate-700 p-6 text-center text-sm text-slate-400">현재 필터에 맞는 레시피가 없습니다.</div>`;
}

function appendSelectedRecipes() {
    const checkedIds = Array.from(document.querySelectorAll("#recipesList input:checked"))
        .map((input) => Number(input.value));

    selectedRecipeIds = [...new Set(checkedIds)];
    refreshItems();

    const representative = getSelectedRecipes()[0];
    if (representative) {
        state.country = representative.country || modalCountry || getActiveCountry();
        state.cuisine = representative.cuisine;
        state.category = representative.category;
        state.menu = modalMenu || taxonomy.getRecipeCategoryAsMenu(getCountryMenus(state.country), representative.category);
        state.recipe = representative.id;
        taxonomy.updateUrl(state);
    }

    closeCreateModal();
    render();
}

function renderContextBanner() {
    const selectedRecipes = getSelectedRecipes();
    const representative = selectedRecipes[0];
    const checkedCount = shoppingItems.filter((item) => item.checked).length;
    const totalPrice = shoppingItems.reduce((sum, item) => sum + item.price, 0);

    if (representative) {
        const countryMeta = taxonomy.getCountryMeta(representative.country || getActiveCountry());
        const cuisineMeta = taxonomy.getCuisineMeta(representative.cuisine);
        const categoryMeta = taxonomy.getMenuCategoryMeta(representative.category);

        document.getElementById("contextBanner").innerHTML = `
            <div class="grid lg:grid-cols-[1.05fr_0.95fr]">
                <img src="${representative.thumb}" alt="${representative.name}" class="h-72 w-full object-cover">
                <div class="bg-gradient-to-br ${cuisineMeta.panelClass} p-6">
                    <p class="inline-flex rounded-full px-3 py-1 text-xs font-semibold ${cuisineMeta.chipClass}">
                        ${countryMeta.flag} ${countryMeta.label}
                    </p>
                    <h1 class="mt-4 text-3xl font-extrabold text-white">${representative.name} 장보기</h1>
                    <p class="mt-3 text-sm leading-7 text-slate-100">
                        ${representative.story} · ${categoryMeta.emoji} ${categoryMeta.label} 문맥에 맞춰 필요한 재료를 자동으로 재정리했습니다.
                    </p>
                </div>
            </div>
        `;
    } else {
        document.getElementById("contextBanner").innerHTML = `
            <div class="bg-slate-900 p-10 text-center">
                <p class="text-lg font-semibold text-white">선택된 레시피가 없습니다.</p>
                <p class="mt-2 text-sm text-slate-400">레시피를 추가하면 쇼핑리스트가 바로 구성됩니다.</p>
            </div>
        `;
    }

    document.getElementById("totalPrice").textContent = taxonomy.formatCurrency(totalPrice);
    document.getElementById("listHeadline").textContent = `${shoppingItems.length}개 재료`;
    document.getElementById("listCopy").textContent = selectedRecipes.length
        ? `${selectedRecipes.length}개 레시피 기준으로 필요한 재료를 카테고리별로 묶었습니다.`
        : "레시피를 추가하면 재료 목록이 바로 생성됩니다.";

    document.getElementById("summaryStats").innerHTML = [
        { label: "선택 레시피", value: `${selectedRecipes.length}개` },
        { label: "체크 완료", value: `${checkedCount}개` },
        { label: "예상 총액", value: taxonomy.formatCurrency(totalPrice) },
    ].map((stat) => {
        return `<div class="rounded-2xl border border-slate-800 bg-slate-950/70 p-4">
            <p class="text-xs text-slate-400">${stat.label}</p>
            <p class="mt-2 text-lg font-semibold text-white">${stat.value}</p>
        </div>`;
    }).join("");
}

function renderItemsByCategory() {
    const grouped = shoppingItems.reduce((acc, item) => {
        acc[item.category] = acc[item.category] || [];
        acc[item.category].push(item);
        return acc;
    }, {});

    const categoryKeys = Object.keys(grouped);
    document.getElementById("itemsByCategory").innerHTML = categoryKeys.length ? categoryKeys.map((key) => {
        const meta = taxonomy.getIngredientCategoryMeta(key);
        return `<section class="glass-card rounded-3xl border border-slate-800 p-5">
            <div class="flex items-center justify-between">
                <span class="rounded-full px-3 py-1 text-sm font-medium ${meta.chipClass}">${meta.emoji} ${meta.label}</span>
                <span class="text-xs text-slate-400">${grouped[key].length}개</span>
            </div>
            <div class="mt-4 space-y-3">
                ${grouped[key].map((item) => {
                    const affiliate = taxonomy.getIngredientAffiliate(item.category, item.name, { country: getActiveCountry(), menu: state.menu });
                    return `<div class="item-card rounded-2xl border border-slate-800 bg-slate-950/70 p-4">
                        <div class="flex items-start justify-between gap-3">
                            <label class="flex flex-1 items-start gap-3">
                                <input type="checkbox" class="mt-1 h-4 w-4" ${item.checked ? "checked" : ""} onchange="toggleItem('${item.name}')">
                                <div>
                                    <p class="font-semibold ${item.checked ? "text-slate-500 line-through" : "text-white"}">${item.name}</p>
                                    <p class="mt-1 text-xs text-slate-400">${item.quantity}${item.unit} · ${taxonomy.formatCurrency(item.price)}</p>
                                    <p class="mt-2 text-xs text-slate-500">출처: ${item.sources.join(", ")}</p>
                                </div>
                            </label>
                            <div class="text-right">
                                <span class="block text-xs text-slate-400">${item.checked ? "완료" : "미완료"}</span>
                                <a href="${affiliate.url}" target="_blank" rel="noopener noreferrer sponsored" class="mt-2 inline-block text-xs text-orange-300">추천 상품</a>
                            </div>
                        </div>
                    </div>`;
                }).join("")}
            </div>
        </section>`;
    }).join("") : `<div class="rounded-3xl border border-slate-800 bg-slate-900 p-10 text-center">
        <p class="text-lg font-semibold text-white">선택된 품목이 없습니다.</p>
        <p class="mt-2 text-sm text-slate-400">레시피를 추가하면 필요한 재료가 자동으로 보입니다.</p>
    </div>`;
}

function renderSidebar() {
    const selectedRecipes = getSelectedRecipes();
    const representative = selectedRecipes[0];
    const groupedCost = shoppingItems.reduce((acc, item) => {
        acc[item.category] = (acc[item.category] || 0) + item.price;
        return acc;
    }, {});

    document.getElementById("categorySummary").innerHTML = Object.entries(groupedCost).map(([key, total]) => {
        const meta = taxonomy.getIngredientCategoryMeta(key);
        return `<div class="rounded-2xl bg-slate-950/70 p-4">
            <div class="flex items-center justify-between">
                <span class="rounded-full px-3 py-1 text-xs ${meta.chipClass}">${meta.emoji} ${meta.label}</span>
                <span class="text-sm font-semibold text-white">${taxonomy.formatCurrency(total)}</span>
            </div>
        </div>`;
    }).join("") || `<p class="text-sm text-slate-400">재료가 없습니다.</p>`;

    document.getElementById("selectedRecipes").innerHTML = selectedRecipes.map((recipe) => {
        const href = taxonomy.buildHref("recipes.html", {
            country: recipe.country || getActiveCountry(),
            cuisine: recipe.cuisine,
            category: recipe.category,
            menu: state.menu || "",
            recipe: recipe.id,
        });
        return `<a href="${href}" class="flex items-center gap-3 rounded-2xl bg-slate-950/70 p-3 hover:bg-slate-800">
            <img src="${recipe.thumb}" alt="${recipe.name}" class="h-16 w-16 rounded-xl object-cover">
            <div>
                <p class="font-semibold text-white">${recipe.image} ${recipe.name}</p>
                <p class="text-xs text-slate-400">${recipe.cuisineMeta.flag} ${recipe.cuisineMeta.label} · ${recipe.categoryMeta.emoji} ${recipe.categoryMeta.label}</p>
            </div>
        </a>`;
    }).join("") || `<p class="text-sm text-slate-400">선택된 레시피가 없습니다.</p>`;

    if (representative) {
        const routeContext = {
            country: representative.country || getActiveCountry(),
            cuisine: representative.cuisine,
            category: representative.category,
            menu: state.menu || "",
            recipe: representative.id,
        };
        document.getElementById("nextRoutes").innerHTML = [
            { icon: "📖", title: "같은 레시피 보기", href: taxonomy.buildHref("recipes.html", routeContext) },
            { icon: "📰", title: "같은 피드 보기", href: taxonomy.buildHref("feed.html", routeContext) },
            { icon: "🧭", title: "허브로 돌아가기", href: taxonomy.buildHref("index.html", routeContext) },
        ].map((route) => {
            return `<a href="${route.href}" class="flex items-center justify-between rounded-2xl bg-slate-950/70 px-4 py-3 text-sm text-white hover:bg-slate-800">
                <span>${route.icon} ${route.title}</span>
                <span class="text-slate-400">바로가기</span>
            </a>`;
        }).join("");

        document.getElementById("flowActions").innerHTML = [
            { icon: "📖", title: "레시피 상세 열기", href: taxonomy.buildHref("recipes.html", routeContext) },
            { icon: "📰", title: "연관 피드 확인", href: taxonomy.buildHref("feed.html", routeContext) },
        ].map((route) => {
            return `<a href="${route.href}" class="flex items-center justify-between rounded-2xl border border-slate-800 bg-slate-950/70 px-4 py-3 text-sm text-white hover:bg-slate-800">
                <span>${route.icon} ${route.title}</span>
                <span class="text-slate-400">열기</span>
            </a>`;
        }).join("");

        const affiliateLinks = taxonomy.getRecipeAffiliates(representative, routeContext);
        document.getElementById("affiliatePanel").innerHTML = affiliateLinks.map((item) => {
            return `<a href="${item.url}" target="_blank" rel="noopener noreferrer sponsored" class="block rounded-2xl bg-slate-950/70 px-4 py-3 text-sm text-white hover:bg-slate-800">
                <div class="flex items-center justify-between">
                    <span>${item.emoji} ${item.label}</span>
                    <span class="text-slate-400">열기</span>
                </div>
                <p class="mt-2 text-xs text-slate-500">${item.keyword}</p>
            </a>`;
        }).join("");
    } else {
        document.getElementById("nextRoutes").innerHTML = `<p class="text-sm text-slate-400">추천 경로가 없습니다.</p>`;
        document.getElementById("flowActions").innerHTML = `<button onclick="openCreateModal()" class="w-full rounded-2xl bg-orange-600 px-4 py-3 text-sm font-medium text-white hover:bg-orange-500">레시피 추가하기</button>`;
        document.getElementById("affiliatePanel").innerHTML = `<p class="text-sm text-slate-400">레시피를 선택하면 제휴 링크가 표시됩니다.</p>`;
    }

    document.getElementById("affiliateDisclosure").textContent = taxonomy.affiliateMeta.disclosure;
}

function render() {
    renderContextBanner();
    renderItemsByCategory();
    renderSidebar();
}

function init() {
    initializeSelection();
    render();

    document.getElementById("createModal").addEventListener("click", (event) => {
        if (event.target.id === "createModal") {
            closeCreateModal();
        }
    });
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
} else {
    init();
}

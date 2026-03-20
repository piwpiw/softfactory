if (typeof hasAuthSession === "function" && hasAuthSession()) {
  requireAuth();
}

const taxonomy = window.CooCookTaxonomy;
const state = taxonomy.parseState();
let allChefs = [];
function ensurePriceRange() {
  let input = document.getElementById("priceRange");
  if (input) return input;
  input = document.createElement("input");
  input.type = "range";
  input.id = "priceRange";
  input.min = "15000";
  input.max = "70000";
  input.value = "45000";
  input.className = "hidden";
  document.body.appendChild(input);
  return input;
}
function resolveDefaultCuisine() {
    return taxonomy.resolveDefaultCuisine(getActiveCountry());
}

function getActiveCountry() {
  return state.country || "KR";
}

function getActiveCuisine() {
    return state.cuisine || resolveDefaultCuisine();
}

function getActiveMenu() {
  return state.menu || "";
}

function getActiveCategory() {
  return state.category || "";
}

function getCountryFilters() {
  return [
    { key: "", label: "전체", emoji: "🌍" },
  ].concat(
    taxonomy.getAvailableCountries().map((key) => {
      const meta = taxonomy.getCountryMeta(key);
      return { key, label: meta.label, emoji: meta.flag };
    })
  );
}

function getCuisineFilters() {
  return [{ key: "", label: "전체", emoji: "🍽" }]
    .concat(taxonomy.getAvailableCuisineKeys().map((key) => ({
      key,
      label: taxonomy.getCuisineMeta(key).label,
      emoji: taxonomy.getCuisineMeta(key).flag,
    })));
}

function getMenuFilters() {
  return [{ key: "", label: "전체", emoji: "🧩" }]
    .concat(taxonomy.getCountryMenus(getActiveCountry()).map((menu) => ({
      key: menu.key,
      label: menu.label,
      emoji: menu.emoji,
    })));
}

function getCategoryFilters() {
  return [{ key: "", label: "전체", emoji: "📂" }]
    .concat(taxonomy.getAvailableMenuCategoryKeys().map((key) => ({
      key,
      label: taxonomy.getMenuCategoryMeta(key).label,
      emoji: taxonomy.getMenuCategoryMeta(key).emoji,
    })));
}

function inferCategoryFromRecipes(chefName) {
  const recipe = taxonomy.getChefRecipes(chefName, { limit: 1 })[0];
  return recipe ? recipe.category : "main";
}

function setFilter(key, value) {
  state[key] = state[key] === value ? "" : value;
  if (key === "country") {
    state.cuisine = resolveDefaultCuisine();
    state.category = "";
    state.menu = "";
  }
  if (key === "cuisine") {
    state.category = "";
  }
  if (key === "menu") {
    state.category = "";
  }
  state.country = taxonomy.normalizeCountry(state.country);
  taxonomy.updateUrl(state);
  renderFilters();
  renderChefs();
  renderTrail();
}

function renderFilters() {
  const quickFilters = document.getElementById("quickFilters");
  const countryChips = getCountryFilters().map((item) => {
    const active = state.country === item.key && item.key !== "";
    return `<button onclick="setFilter('country', '${item.key}')" class="px-3 py-1.5 rounded-full border text-xs font-semibold ${active ? "bg-orange-600 text-white border-orange-600" : "border-slate-700 text-slate-300"}">${item.emoji} ${item.label}</button>`;
  }).join("");

  const cuisineChips = getCuisineFilters().map((item) => {
    const active = state.cuisine === item.key && item.key !== "";
    return `<button onclick="setFilter('cuisine', '${item.key}')" class="px-3 py-1.5 rounded-full border text-xs font-semibold ${active ? "bg-orange-600 text-white border-orange-600" : "border-slate-700 text-slate-300"}">${item.emoji} ${item.label}</button>`;
  }).join("");

  const menuChips = getMenuFilters().map((item) => {
    const active = state.menu === item.key && item.key !== "";
    return `<button onclick="setFilter('menu', '${item.key}')" class="px-3 py-1.5 rounded-full border text-xs font-semibold ${active ? "bg-emerald-600 text-white border-emerald-600" : "border-slate-700 text-slate-300"}">${item.emoji} ${item.label}</button>`;
  }).join("");

  const categoryChips = getCategoryFilters().map((item) => {
    const active = state.category === item.key && item.key !== "";
    return `<button onclick="setFilter('category', '${item.key}')" class="px-3 py-1.5 rounded-full border text-xs font-semibold ${active ? "bg-emerald-600 text-white border-emerald-600" : "border-slate-700 text-slate-300"}">${item.emoji} ${item.label}</button>`;
  }).join("");

  quickFilters.innerHTML = `
    <div>
      <p class="text-xs text-slate-400 mb-2">국가</p>
      <div class="flex flex-wrap gap-2">${countryChips}</div>
    </div>
    <div class="ml-2">
      <p class="text-xs text-slate-400 mb-2">요리</p>
      <div class="flex flex-wrap gap-2">${cuisineChips}</div>
    </div>
    <div class="ml-2">
      <p class="text-xs text-slate-400 mb-2">메뉴</p>
      <div class="flex flex-wrap gap-2">${menuChips}</div>
    </div>
    <div class="ml-2">
      <p class="text-xs text-slate-400 mb-2">카테고리</p>
      <div class="flex flex-wrap gap-2">${categoryChips}</div>
    </div>
  `;
}

function renderTrail() {
  const price = Number(ensurePriceRange().value);
  const activeCuisine = state.cuisine || getActiveCuisine();
  const activeMenu = getActiveMenu();
  const activeCountryMeta = taxonomy.getCountryMeta(getActiveCountry());
  const menuMeta = taxonomy.getCountryMenus(getActiveCountry()).find((item) => item.key === activeMenu);
  const categoryMeta = state.category ? taxonomy.getMenuCategoryMeta(state.category) : null;
  const parts = [
    `${activeCountryMeta.label} (${activeCountryMeta.flag})`,
    activeCuisine ? taxonomy.getCuisineMeta(activeCuisine).label : "전체 요리",
    menuMeta ? menuMeta.label : "전체 메뉴",
    categoryMeta ? categoryMeta.label : "전체 카테고리",
  ];
  document.getElementById("affinityTrail").textContent = `조건: ${parts.join(" / ")} · 최대 ${price.toLocaleString()}원`;
}

function matchesFilters(chef) {
  const maxPrice = Number(ensurePriceRange().value);
  const cuisine = chef.cuisine || "Korean";
  const activeMenu = getActiveMenu();
  const category = inferCategoryFromRecipes(chef.name);
  const menuMatch = activeMenu
    ? (taxonomy.getCountryMenu(getActiveCountry(), category)?.key || "") === activeMenu
    : true;
  const cuisineMatch = !state.cuisine || cuisine === state.cuisine;
  const categoryMatch = !state.category || category === state.category;
  const inPrice = Number(chef.price_per_session || 0) <= maxPrice;
  return cuisineMatch && categoryMatch && menuMatch && inPrice;
}

function renderChefs() {
  const grid = document.getElementById("chefsGrid");
  const filtered = (allChefs || []).filter(matchesFilters);
  if (!filtered.length) {
    grid.innerHTML = `<div class="col-span-full text-center text-slate-400 py-14">조건에 맞는 셰프가 없습니다. 필터를 조정해보세요.</div>`;
    return;
  }

  grid.innerHTML = filtered.map((chef) => {
    const cuisineMeta = taxonomy.getCuisineMeta(chef.cuisine || "Korean");
    const category = inferCategoryFromRecipes(chef.name || "");
    const categoryMeta = taxonomy.getMenuCategoryMeta(category);
    const recipeId = taxonomy.getChefRecipes(chef.name, { limit: 1 })[0]?.id || "";
    const routeContext = {
      country: getActiveCountry(),
      cuisine: chef.cuisine || "",
      category,
      menu: getActiveMenu(),
    };
    const affiliate = chef.affiliate || taxonomy.getCuisineAffiliate(chef.cuisine || "Korean", { country: getActiveCountry() });

    return `
      <article class="bg-gradient-to-br from-orange-900/30 to-orange-900/10 rounded-lg p-6 border-2 border-orange-600 hover:border-opacity-100 transition">
        <div class="flex items-center gap-3">
          <span class="text-4xl">${chef.avatar || cuisineMeta.emoji}</span>
          <div class="flex-1">
            <h3 class="text-lg font-bold text-white">${chef.name}</h3>
            <p class="text-sm text-slate-400">${cuisineMeta.label} · ${categoryMeta.label}</p>
          </div>
        </div>
        <div class="mt-4 flex items-center justify-between">
          <span class="text-yellow-400 text-sm">⭐ ${chef.rating}</span>
          <span class="text-slate-500 text-xs">(${chef.rating_count}명 리뷰)</span>
        </div>
        <p class="text-lg font-bold text-white mt-4">${(chef.price_per_session || 0).toLocaleString()}원/회</p>
        <p class="text-xs text-slate-400 mt-1">${chef.location}</p>
        <p class="mt-3 text-xs text-orange-300">${affiliate.label}</p>
        <div class="mt-4 grid gap-2">
          <a href="${taxonomy.buildHref('recipes.html', routeContext)}" target="_self" class="inline-block text-xs bg-orange-600 hover:bg-orange-500 rounded px-3 py-2 text-white text-center">레시피 보기</a>
          <a href="${taxonomy.buildHref('feed.html', routeContext)}" target="_self" class="inline-block text-xs bg-slate-800 hover:bg-slate-700 rounded px-3 py-2 text-white text-center">피드 보기</a>
          <a href="${taxonomy.buildHref('shopping-list.html', { ...routeContext, recipe: recipeId })}" target="_self" class="inline-block text-xs bg-slate-800 hover:bg-slate-700 rounded px-3 py-2 text-white text-center">장바구니로 연결</a>
          <a href="${affiliate.url}" target="_blank" rel="noopener noreferrer sponsored" class="inline-block text-xs bg-emerald-600 hover:bg-emerald-500 rounded px-3 py-2 text-white text-center">추천 상품</a>
        </div>
      </article>
    `;
  }).join("");
}

function applyPriceLabel() {
  const price = Number(ensurePriceRange().value);
  document.getElementById("priceRangeLabel").textContent = `15,000원 - ${price.toLocaleString()}원`;
  renderChefs();
  renderTrail();
}

async function init() {
  const requestedCuisine = getActiveCuisine();
  try {
    const result = await getChefs(1, requestedCuisine || "", "");
    const rows = result?.chefs || result || [];
    allChefs = (rows || []).map((chef) => taxonomy.enrichChef ? taxonomy.enrichChef(chef) : { ...chef, cuisine: chef.cuisine_type || "Korean" });
  } catch (error) {
    allChefs = taxonomy.getDefaultChefs().length ? taxonomy.getDefaultChefs() : [
      { id: 1, name: "Chef Park", cuisine: "Korean", avatar: "🧑🏽‍🍳", rating: 4.9, rating_count: 98, price_per_session: 26000, location: "서울 종로구", category: "stew" },
      { id: 2, name: "Chef Marco", cuisine: "Italian", avatar: "👨🏽‍🍳", rating: 4.8, rating_count: 88, price_per_session: 35000, location: "서울 강남구", category: "noodle" },
      { id: 3, name: "Chef Tanaka", cuisine: "Japanese", avatar: "👨🏿‍🍳", rating: 4.7, rating_count: 120, price_per_session: 32000, location: "서울 서초구", category: "rice" },
    ].map((chef) => taxonomy.enrichChef ? taxonomy.enrichChef(chef) : chef);
    if (typeof showWarning === "function") {
      showWarning("셰프 API가 지연되어 샘플 데이터로 표시합니다.");
    }
  }

  state.cuisine = requestedCuisine || state.cuisine || "";
  renderFilters();
  renderTrail();
  renderChefs();
  applyPriceLabel();
  ensurePriceRange().addEventListener("input", applyPriceLabel);
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", init);
} else {
  init();
}

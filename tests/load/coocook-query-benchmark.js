#!/usr/bin/env node

const fs = require("fs");
const path = require("path");
const vm = require("vm");
const { performance } = require("perf_hooks");

function loadTaxonomy() {
  const taxonomyPath = path.resolve(__dirname, "../../web/coocook/coocook-taxonomy.js");
  const source = fs.readFileSync(taxonomyPath, "utf8");
  const sandbox = {
    window: {},
    console,
    URL,
    URLSearchParams,
    encodeURIComponent,
    decodeURIComponent,
    setTimeout,
    clearTimeout,
  };

  vm.createContext(sandbox);
  vm.runInContext(source, sandbox, { filename: taxonomyPath });
  return sandbox.window.CooCookTaxonomy;
}

function cloneRecipes(recipes, multiplier) {
  const cloned = [];
  for (let batch = 0; batch < multiplier; batch += 1) {
    for (const recipe of recipes) {
      cloned.push({
        ...recipe,
        id: `${recipe.id}-${batch + 1}`,
        name: `${recipe.name} #${batch + 1}`,
        ingredients: (recipe.ingredients || []).map((ingredient) => ({ ...ingredient })),
      });
    }
  }
  return cloned;
}

function buildFilterSuite() {
  return [
    { country: "KR", cuisine: "Korean", category: "stew" },
    { country: "JP", cuisine: "Japanese", category: "rice", ingredientCategory: "seafood" },
    { country: "IT", cuisine: "Italian", menu: "food", ingredientCategory: "grain" },
    { country: "US", cuisine: "American", ingredientCategory: "protein" },
    { country: "MX", cuisine: "Mexican", category: "street", ingredient: "토마토" },
    { country: "FR", cuisine: "French", menu: "bakery", difficulty: "중급" },
    { country: "VN", cuisine: "Vietnamese", ingredientCategory: "produce" },
    { country: "TH", cuisine: "Thai", menu: "food", ingredient: "새우" },
    { country: "DE", cuisine: "German", category: "main" },
    { country: "KR", menu: "food", ingredientCategory: "condiment" },
  ];
}

function measureRun(fn, suite, iterations) {
  const started = performance.now();
  let totalResults = 0;
  for (let i = 0; i < iterations; i += 1) {
    const filters = suite[i % suite.length];
    totalResults += fn(filters).length;
  }
  return {
    durationMs: performance.now() - started,
    totalResults,
  };
}

function benchmarkEngine(taxonomy, multiplier, iterations) {
  const recipes = cloneRecipes(taxonomy.recipeCatalog, multiplier);
  const engine = taxonomy.createRecipeQueryEngine(recipes);
  const suite = buildFilterSuite();

  const cold = measureRun(engine.queryRecipes, suite, iterations);
  const warm = measureRun(engine.queryRecipes, suite, iterations);

  return {
    datasetSize: recipes.length,
    multiplier,
    iterations,
    coldMs: Number(cold.durationMs.toFixed(2)),
    warmMs: Number(warm.durationMs.toFixed(2)),
    avgColdMs: Number((cold.durationMs / iterations).toFixed(4)),
    avgWarmMs: Number((warm.durationMs / iterations).toFixed(4)),
    totalResults: warm.totalResults,
    cacheEntries: engine.recipeQueryCache.size,
  };
}

function main() {
  const taxonomy = loadTaxonomy();
  const iterations = Number(process.argv[2] || 1500);
  const multipliers = [1, 5, 20, 50];
  const report = multipliers.map((multiplier) => benchmarkEngine(taxonomy, multiplier, iterations));

  console.log(JSON.stringify({
    generatedAt: new Date().toISOString(),
    iterations,
    benchmark: report,
  }, null, 2));
}

main();

/**
 * dependency-cruiser config
 *
 * Enforces the layered architecture: types -> config -> repo -> service ->
 * runtime -> ui. Imports may flow only upward (toward types).
 *
 * Reads .claude/harness-scope.json to adapt rule severity:
 *   greenfield — all layer rules at error, repo-wide.
 *   brownfield — harness-managed paths at error, legacy paths at warn.
 *
 * The Python structural test in tests/structural/test_layering.py performs
 * the same check via regex; this provides deeper graph analysis (cycles,
 * orphans, transitive violations).
 */

const fs = require("fs");
const path = require("path");

// -- Load harness scope -------------------------------------------------------
let scope = {
  version: 1,
  mode: "greenfield",
  managed_paths: ["src/**"],
  legacy_paths: [],
  baselines: {},
};
try {
  const scopePath = path.join(__dirname, ".claude", "harness-scope.json");
  scope = JSON.parse(fs.readFileSync(scopePath, "utf8"));
} catch (_) {
  // Scope file missing or unparseable — use greenfield defaults.
}

const isBrownfield = scope.mode === "brownfield";
const managedPaths = scope.managed_paths || ["src/**"];
const legacyPaths = scope.legacy_paths || [];

/**
 * Convert a glob like "src/new-feature/**" to a dep-cruiser path regex.
 * Handles ** (any depth) and * (single directory level).
 */
function globToPathRegex(glob) {
  let pat = glob
    .replace(/\./g, "\\.")
    .replace(/\*\*/g, "___DBLSTAR___")
    .replace(/\*/g, "[^/]*")
    .replace(/___DBLSTAR___/g, ".*");
  return "^" + pat;
}

const managedPathRegexes = managedPaths.map(globToPathRegex);
const legacyPathRegexes = legacyPaths.map(globToPathRegex);

// -- Common rules -------------------------------------------------------------
const baseRules = [
  {
    name: "no-circular",
    severity: "error",
    comment:
      "Circular dependencies make the dependency graph unparseable and " +
      "usually indicate a missing abstraction. Refactor to remove the cycle.",
    from: {},
    to: { circular: true },
  },
  {
    name: "no-orphans",
    severity: "warn",
    comment:
      "Orphan modules (no inbound imports) are usually dead code. " +
      "Either reference them, delete them, or document why they exist.",
    from: {
      orphan: true,
      pathNot: [
        "\\.(spec|test)\\.(ts|tsx|js|jsx)$",
        "\\.d\\.ts$",
        "src/runtime/index\\.ts$",
        "src/ui/index\\.ts$",
      ],
    },
    to: {},
  },
];

// -- Layer rules --------------------------------------------------------------
//
// In greenfield mode: one rule set at severity "error", repo-wide.
// In brownfield mode: two rule sets — error for managed paths, warn for legacy.
//
// If a path matches both managed and legacy globs, managed takes precedence
// (the first match in the rules array wins in dep-cruiser since the
// combined-depth logic ranks by specificity; we rely on the error rules
// appearing first and dep-cruiser's rule ordering).
//
// When no managed_paths are defined (empty brownfield scope), all layer rules
// run at "warn" so CI is visible but not blocking.

function layerRule(name, comment, fromLayer, allowedAbove) {
  const forbidden = [];
  const layers = ["types", "config", "repo", "service", "runtime", "ui"];
  const fromIndex = layers.indexOf(fromLayer);
  const forbiddenLayers = layers.filter(
    (_, i) => i > fromIndex && !allowedAbove.includes(layers[i])
  );

  if (forbiddenLayers.length === 0) return [];

  const toPattern = "^src/(" + forbiddenLayers.join("|") + ")/";
  const fromPattern = "^src/" + fromLayer + "/";

  if (isBrownfield && managedPathRegexes.length > 0) {
    // Managed paths at error
    forbidden.push({
      name: name,
      severity: "error",
      comment:
        comment +
        " [harness-managed]",
      from: { path: fromPattern, pathNot: legacyPathRegexes.map(r => r).join("|") || undefined },
      to: { path: toPattern },
    });
    // Legacy paths at warn
    forbidden.push({
      name: name + "-legacy",
      severity: "warn",
      comment:
        comment +
        " [legacy — baselined, not blocking]",
      from: { path: fromPattern },
      to: { path: toPattern },
    });
  } else if (isBrownfield && managedPathRegexes.length === 0) {
    // No managed paths — all warn
    forbidden.push({
      name: name,
      severity: "warn",
      comment: comment + " [legacy — no managed paths configured]",
      from: { path: fromPattern },
      to: { path: toPattern },
    });
  } else {
    // Greenfield — all error
    forbidden.push({
      name: name,
      severity: "error",
      comment: comment,
      from: { path: fromPattern },
      to: { path: toPattern },
    });
  }

  return forbidden;
}

const layerRules = [
  ...layerRule("types-no-deps", "src/types may not depend on other layers.", "types", []),
  ...layerRule("config-up-only", "src/config may only import from src/types.", "config", ["types"]),
  ...layerRule("repo-up-only", "src/repo may import from src/types and src/config only.", "repo", ["types", "config"]),
  ...layerRule("service-up-only", "src/service may import from src/types, config, repo only.", "service", ["types", "config", "repo"]),
  ...layerRule("runtime-up-only", "src/runtime may not import from src/ui.", "runtime", ["types", "config", "repo", "service"]),
];

// -- Export -------------------------------------------------------------------
module.exports = {
  forbidden: [...baseRules, ...layerRules],
  options: {
    doNotFollow: { path: "node_modules" },
    tsConfig: { fileName: "tsconfig.json" },
    tsPreCompilationDeps: true,
    enhancedResolveOptions: {
      exportsFields: ["exports"],
      conditionNames: ["import", "require", "node", "default"],
    },
    reporterOptions: {
      text: { highlightFocused: true },
    },
  },
};

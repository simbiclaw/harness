/**
 * dependency-cruiser config
 *
 * Enforces the layered architecture: types -> config -> repo -> service ->
 * runtime -> ui. Imports may flow only upward (toward types).
 *
 * The Python structural test in tests/structural/test_layering.py performs
 * the same check via regex; this provides deeper graph analysis (cycles,
 * orphans, transitive violations).
 */
module.exports = {
  forbidden: [
    {
      name: 'no-circular',
      severity: 'error',
      comment:
        'Circular dependencies make the dependency graph unparseable and ' +
        'usually indicate a missing abstraction. Refactor to remove the cycle.',
      from: {},
      to: { circular: true },
    },
    {
      name: 'no-orphans',
      severity: 'warn',
      comment:
        'Orphan modules (no inbound imports) are usually dead code. ' +
        'Either reference them, delete them, or document why they exist.',
      from: {
        orphan: true,
        pathNot: [
          '\\.(spec|test)\\.(ts|tsx|js|jsx)$',
          '\\.d\\.ts$',
          'src/runtime/index\\.ts$',
          'src/ui/index\\.ts$',
        ],
      },
      to: {},
    },
    {
      name: 'types-no-deps',
      severity: 'error',
      comment:
        'src/types is the foundation layer. It may not depend on other ' +
        'layers in src/.',
      from: { path: '^src/types/' },
      to: { path: '^src/(config|repo|service|runtime|ui)/' },
    },
    {
      name: 'config-up-only',
      severity: 'error',
      comment:
        'src/config may only import from src/types.',
      from: { path: '^src/config/' },
      to: { path: '^src/(repo|service|runtime|ui)/' },
    },
    {
      name: 'repo-up-only',
      severity: 'error',
      comment:
        'src/repo may import from src/types and src/config only.',
      from: { path: '^src/repo/' },
      to: { path: '^src/(service|runtime|ui)/' },
    },
    {
      name: 'service-up-only',
      severity: 'error',
      comment:
        'src/service may import from src/types, src/config, src/repo only.',
      from: { path: '^src/service/' },
      to: { path: '^src/(runtime|ui)/' },
    },
    {
      name: 'runtime-up-only',
      severity: 'error',
      comment:
        'src/runtime may not import from src/ui. UI is the top of the stack.',
      from: { path: '^src/runtime/' },
      to: { path: '^src/ui/' },
    },
  ],
  options: {
    doNotFollow: { path: 'node_modules' },
    tsConfig: { fileName: 'tsconfig.json' },
    tsPreCompilationDeps: true,
    enhancedResolveOptions: {
      exportsFields: ['exports'],
      conditionNames: ['import', 'require', 'node', 'default'],
    },
    reporterOptions: {
      text: { highlightFocused: true },
    },
  },
};

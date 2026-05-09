// ESLint flat config. Minimal at bootstrap; expand via ExecPlans.
export default [
  {
    ignores: ['dist/**', 'node_modules/**', '.claude/**', '*.cjs'],
  },
  {
    files: ['**/*.{ts,tsx,js,jsx,mts,cts}'],
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: 'module',
    },
    rules: {
      'no-unused-vars': 'warn',
      'no-undef': 'error',
      'prefer-const': 'warn',
      'no-var': 'error',
    },
  },
];

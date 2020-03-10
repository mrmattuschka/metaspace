const autoprefixer = require('autoprefixer')
const tailwindcss = require('tailwindcss')
const postcssPurgecss = require('@fullhuman/postcss-purgecss')
const postcss = require('postcss')
const tailwindDefaults = require('tailwindcss/defaultConfig')

const tailwindcssWithConfig = tailwindcss({
  // Reference: https://tailwindcss.com/docs/configuration
  // Defaults: https://github.com/tailwindcss/tailwindcss/blob/master/stubs/defaultConfig.stub.js
  theme: {
    fontFamily: {
      sans: ['Roboto', 'SUPERSCIPT_OVERRIDE', 'Helvetica', 'sans-serif'],
    },
    inset: {
      ...tailwindDefaults.theme.inset,
      '1/2': '50%',
    },
    opacity: {
      ...tailwindDefaults.theme.opacity,
      '1': '0.01',
    },
    placeholderColor: '#C0C4CC',
    spacing: {
      ...tailwindDefaults.theme.spacing,
      auto: 'auto',
    },
    zIndex: {
      ...tailwindDefaults.theme.zIndex,
      '-10': '-10', // Use .-z-10 not .z--10
      '-20': '-20',
    },
  },
  variants: {},
  plugins: [],
  corePlugins: {
    // Disable preflight, as it actively removes parts of the browser stylesheet that existing code relies on,
    // e.g. increased font size & weight on h1, h2, etc. elements.
    // More info: https://tailwindcss.com/docs/preflight/#app
    preflight: false,
  }
})

const purgecss = postcssPurgecss({
  content: [
    './public/**/*.html',
    './src/**/*.vue',
    './src/**/*.tsx',
    './src/**/*.ts',
  ],
  defaultExtractor: content => content.match(/[\w-/:%]+(?<!:)/g) || [],
})

// WORKAROUND: limit purgecss to the tailwind classes only, because purgecss has too many issues that interfere
// with the existing CSS, primarily:
// https://github.com/FullHuman/purgecss/issues/277 Attribute-based selectors are removed even when whitelisted,
// which breaks ElementUI's "[class^='el-icon']" selectors and vue-component's scoped CSS.
//
// https://github.com/FullHuman/purgecss/issues/300 It's heinously slow because it re-reads all input content files
//
const purgecssTailwindOnly = postcss.plugin('postcss-plugin-purgecss-tailwind', () => {
  return async (root, result) => {
    if (root && root.source && root.source.input && /tailwind/i.test(root.source.input.file)) {
      await purgecss(root, result)
    }
  }
})

module.exports = {
  plugins: [
    tailwindcssWithConfig,
    autoprefixer,
    ...(process.env.NODE_ENV === 'production' ? [purgecssTailwindOnly] : []),
  ]
}


// This is a minimal config.
// If you need the full config, get it from here:
// https://unpkg.com/browse/tailwindcss@latest/stubs/defaultConfig.stub.js
const plugin = require("tailwindcss/plugin");


const focusedWithinParentPlugin = plugin(function ({ addVariant, e }) {
    addVariant("focused-within-parent", ({ container }) => {
      container.walkRules((rule) => {
        rule.selector = `:focus-within > .focused-within-parent\\:${rule.selector.slice(1)}`;
      });
    });
  });

module.exports = {
    mode: "jit",
    purge: [
        '../../*/templates/**/*.html',
        '../../**/forms.py',
        '../../*/templatetags/*.py',
    ],
    darkMode: false, // or 'media' or 'class'
    theme: {
        extend: {
            fontFamily: {
                'stencil': ['Stardos Stencil', 'sans-serif'],
                'brand': ['Rubik', 'sans-serif'],
            },
            transitionProperty: {
                'height': 'height',
                'width': 'width',
            },
            screens: {
                'xs-landscape': '500px'
            }
        },
    },
    variants: {
        extend: {},
    },
    plugins: [
        require('@tailwindcss/typography'),
        require('@tailwindcss/forms'),
        require('@tailwindcss/line-clamp'),
        require('@tailwindcss/aspect-ratio'),
        focusedWithinParentPlugin,
    ],
}

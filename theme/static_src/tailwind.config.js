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
        // // Templates within theme app (e.g. base.html)
        // '../templates/**/*.html',
        // // Templates in other apps. Adjust the following line so that it matches
        // // your project structure.
        // '../../templates/**/*.html',
    ],
    darkMode: false, // or 'media' or 'class'
    theme: {
        extend: {
            fontFamily: {
                'stencil': ['Allerta Stencil', 'sans-serif'],
                'brand': ['Rubik', 'sans-serif'],
            },
            transitionProperty: {
                'height': 'height',
                'width': 'width',
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

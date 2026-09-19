'use strict';

// Preserve TeX delimiters and contents until MathJax runs in the browser.
// Without this extension, Marked treats underscores inside TeX as emphasis.
hexo.extend.filter.register('marked:extensions', function (extensions) {
  extensions.push({
    name: 'mathBlock',
    level: 'block',
    start(src) {
      return src.indexOf('$$');
    },
    tokenizer(src) {
      const match = /^\s{0,3}\$\$\s*\n?([\s\S]+?)\n?\s*\$\$(?:\n|$)/.exec(src);
      if (!match) return;

      return {
        type: 'mathBlock',
        raw: match[0],
        tex: match[1]
      };
    },
    renderer(token) {
      return `<div class="math-display">$$${token.tex}$$</div>\n`;
    }
  });

  extensions.push({
    name: 'mathInline',
    level: 'inline',
    start(src) {
      return src.indexOf('$');
    },
    tokenizer(src) {
      const match = /^\$(?!\$)((?:\\.|[^\\\n$])+?)\$/.exec(src);
      if (!match) return;

      return {
        type: 'mathInline',
        raw: match[0],
        tex: match[1]
      };
    },
    renderer(token) {
      return `$${token.tex}$`;
    }
  });
});

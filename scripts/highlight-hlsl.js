'use strict';

// Highlight.js does not bundle an HLSL grammar. Its GLSL grammar covers the
// shader syntax used in these articles closely enough, while this alias keeps
// the rendered language label accurate.
const hljs = require('highlight.js');
const glsl = require('highlight.js/lib/languages/glsl');

if (!hljs.getLanguage('hlsl')) {
  hljs.registerLanguage('hlsl', glsl);
}

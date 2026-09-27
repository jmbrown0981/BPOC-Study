/* Turns statute citations in already-rendered HTML ("FC 51.02(a)", "CCP Art. 2A.001",
   "Section 22.01, Penal Code", "Family Code Chapter 51") into links to codes.html.
   Only codes that have been built into assets/codes/ (see tools/build_code_search.py)
   get links, and only for sections/chapters that exist in that code's data, so a
   citation to a code that isn't built yet simply stays plain text.

   Usage:  <script src="assets/code-links.js"></script>
           html = CodeLinks.linkify(html);        // after CodeLinks.ready resolves
   Links open in one shared, separate tab/window ("bpoc-codes") so the current page
   (e.g. a quiz in progress) is left alone. */
(function(){
  var script = document.currentScript;
  var siteRoot = new URL('../', script ? script.src : location.href);   // assets/ -> site root
  var DATA = new URL('assets/codes/', siteRoot).href;
  var TARGET = 'bpoc-codes';

  // Citation names -> code ids used by codes.html (same ids as statutes.capitol.texas.gov).
  var LONG = [
    ['Code of Criminal Procedure', 'CR'], ['Health and Safety Code', 'HS'], ['Health &amp; Safety Code', 'HS'],
    ['Alcoholic Beverage Code', 'AL'], ['Transportation Code', 'TN'], ['Government Code', 'GV'],
    ['Education Code', 'ED'], ['Family Code', 'FA'], ['Penal Code', 'PE']
  ];
  var SHORT = [
    ['CCP', 'CR'], ['HSC', 'HS'], ['HS', 'HS'], ['FC', 'FA'], ['PC', 'PE'], ['GV', 'GV'], ['GC', 'GV'],
    ['ED', 'ED'], ['AL', 'AL'], ['TN', 'TN'], ['TC', 'TN']
  ];
  var ALIAS = {};
  LONG.concat(SHORT).forEach(function(p){ ALIAS[p[0].toLowerCase()] = p[1]; });
  function esc(s){ return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); }
  var LONG_RE = LONG.map(function(p){ return esc(p[0]); }).join('|');
  var ANY_RE = LONG_RE + '|' + SHORT.map(function(p){ return esc(p[0]); }).join('|');

  var SEC = '\\d+[A-Za-z]?\\.\\d+[A-Za-z0-9]*';
  var SUB = '(?:\\([A-Za-z0-9-]+\\))*';
  var PRE = '(?:(?:Arts?\\.?|Articles?|Secs?\\.?|Sections?|&sect;&sect;?|§§?)\\s*)?';
  var TAIL = '((?:\\s*(?:,|and|or|through|to|-|–|&amp;)\\s*' + SEC + SUB + ')*)';

  // A: "FC 51.02(a)", "CCP Art. 2A.001, 2A.002", "Penal Code Section 22.01"
  var RE_A = new RegExp('\\b(' + ANY_RE + ')\\s+' + PRE + '(' + SEC + ')(' + SUB + ')' + TAIL, 'g');
  // B: "Section 22.01, Penal Code", "Article 2A.001 of the Code of Criminal Procedure"
  var RE_B = new RegExp('\\b(?:Arts?\\.?|Articles?|Secs?\\.?|Sections?)\\s*(' + SEC + ')(' + SUB + '),?\\s+(?:of\\s+the\\s+)?(' + LONG_RE + ')\\b', 'g');
  // C: "Family Code Chapter 51", "FC Ch. 52"
  var RE_C = new RegExp('\\b(' + ANY_RE + ')\\s+(?:Chapter|Ch\\.)\\s*(\\d+[A-Za-z]?)\\b', 'g');
  // D: "Chapter 573, Health and Safety Code"
  var RE_D = new RegExp('\\b(?:Chapter|Ch\\.)\\s*(\\d+[A-Za-z]?),?\\s+(?:of\\s+the\\s+)?(' + LONG_RE + ')\\b', 'g');
  var RE_SEC_G = new RegExp(SEC, 'g');

  var codes = {};   // id -> {name, secs:Set, chs:Set}
  var ready = fetch(DATA + 'codes.json').then(function(r){ return r.ok ? r.json() : []; }).then(function(list){
    return Promise.all(list.map(function(c){
      return fetch(DATA + c.code + '/toc.json').then(function(r){ return r.json(); }).then(function(toc){
        codes[c.code] = {
          name: c.name,
          secs: new Set(toc.sections.map(function(s){ return s[0].toLowerCase(); })),
          chs: new Set(toc.chapters.map(function(ch){ return ch.n.toLowerCase(); }))
        };
      }).catch(function(){});
    }));
  }).catch(function(){});

  function codeFor(alias){ return ALIAS[alias.toLowerCase()]; }
  function link(text, code, key, isChapter){
    var c = codes[code];
    if(!c) return null;
    key = key.toLowerCase();
    if(isChapter ? !c.chs.has(key) : !c.secs.has(key)) return null;
    var href = new URL('codes.html?code=' + code + (isChapter ? '&ch=' : '&sec=') + encodeURIComponent(key.toUpperCase()), siteRoot).href;
    var label = c.name + (isChapter ? ' Chapter ' : ' § ') + key.toUpperCase();
    return '<a class="code-link" href="' + href + '" target="' + TARGET + '" title="Open ' + label + ' (separate tab)">' + text + '</a>';
  }

  // Apply fn to text outside tags and outside existing <a> elements.
  function mapText(html, fn){
    var parts = html.split(/(<[^>]*>)/), depth = 0;
    for(var i = 0; i < parts.length; i++){
      var p = parts[i];
      if(p.charAt(0) === '<'){
        if(/^<a[\s>]/i.test(p)) depth++;
        else if(/^<\/a>/i.test(p)) depth = Math.max(0, depth - 1);
      } else if(p && depth === 0){
        parts[i] = fn(p);
      }
    }
    return parts.join('');
  }

  function linkify(html){
    if(!html) return html;
    html = mapText(html, function(t){
      return t.replace(RE_A, function(all, alias, sec, sub, tail){
        var code = codeFor(alias);
        var head = all.slice(0, all.length - tail.length);
        var first = link(head, code, sec, false) || head;
        var rest = tail.replace(RE_SEC_G, function(n){ return link(n, code, n, false) || n; });
        return first + rest;
      });
    });
    html = mapText(html, function(t){
      return t.replace(RE_B, function(all, sec, sub, name){ return link(all, codeFor(name), sec, false) || all; });
    });
    html = mapText(html, function(t){
      return t.replace(RE_C, function(all, alias, ch){ return link(all, codeFor(alias), ch, true) || all; });
    });
    html = mapText(html, function(t){
      return t.replace(RE_D, function(all, ch, name){ return link(all, codeFor(name), ch, true) || all; });
    });
    return html;
  }

  var style = document.createElement('style');
  style.textContent = 'a.code-link{color:inherit;text-decoration:underline;text-decoration-style:dotted;text-underline-offset:2px;}' +
    'a.code-link::after{content:"\\2197";font-size:0.8em;margin-left:1px;opacity:0.7;}' +
    'a.code-link:hover{color:#B08B3C;text-decoration-style:solid;}';
  (document.head || document.documentElement).appendChild(style);

  window.CodeLinks = {ready: ready, linkify: linkify, isBuilt: function(code){ return !!codes[code]; }};
})();

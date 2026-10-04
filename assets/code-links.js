/* Turns statute citations in already-rendered HTML ("FC 51.02(a)", "CCP Art. 2A.001",
   "Section 22.01, Penal Code", "Family Code Chapter 51") into links to codes.html.
   Only codes that have been built into assets/codes/ (see tools/build_code_search.py)
   get links, and only for sections/chapters that exist in that code's data, so a
   citation to a code that isn't built yet simply stays plain text (and links on its
   own once that code is built).

   Usage:  <script src="assets/code-links.js"></script>
           html = CodeLinks.linkify(html);                 // after CodeLinks.ready resolves
           html = CodeLinks.linkify(html, {context:true, secCode:'PE'});
   The second form (used by quiz explanations) also links citations that don't name
   their code, by reading the surrounding text left to right:
     - "Art. 38.22" / "Article 14.03"  -> Code of Criminal Procedure (only CCP uses articles)
     - "§ 36.02" / "Sec. 20A.01"       -> the last non-CCP code named earlier in the text,
                                          else opts.secCode (the bank's main code), else no link
     - a bare number "under 481.112"   -> the last code cited earlier in the text, else opts.secCode
   BPOC/LO/Day/Chapter numbers are never treated as sections, and naming something that isn't
   a Texas statute (TAC, CFR, U.S.C., a rule) stops later uncoded citations from linking.
   Links open in one shared, separate tab/window ("bpoc-codes") so the current page
   (e.g. a quiz in progress) is left alone. */
(function(){
  var script = document.currentScript;
  var siteRoot = new URL('../', script ? script.src : location.href);   // assets/ -> site root
  var DATA = new URL('assets/codes/', siteRoot).href;
  var TARGET = 'bpoc-codes';

  // Citation names -> code ids used by codes.html (same ids as statutes.capitol.texas.gov).
  // Longer names first where one contains another ("Local Government Code" before "Government Code").
  var APOS = "(?:'|’|&#39;|&#x27;)";
  var LONG = [
    ['Code of Criminal Procedure', 'CR'], ['Health and Safety Code', 'HS'], ['Health &amp; Safety Code', 'HS'],
    ['Alcoholic Beverage Code', 'AL'], ['Transportation Code', 'TN'], ['Local Government Code', 'LG'],
    ['Local Gov' + APOS + 't Code', 'LG', true], ['Government Code', 'GV'], ['Gov' + APOS + 't Code', 'GV', true],
    ['Education Code', 'ED'], ['Family Code', 'FA'], ['Penal Code', 'PE'], ['Occupations Code', 'OC'],
    ['Occ. Code', 'OC'], ['Human Resources Code', 'HR'], ['Business and Commerce Code', 'BC'],
    ['Business &amp; Commerce Code', 'BC'], ['Civil Practice and Remedies Code', 'CP'], ['Finance Code', 'FI'],
    ['Agriculture Code', 'AG'], ['Ag. Code', 'AG'], ['AB Code', 'AL'], ['Property Code', 'PR'],
    ['Parks and Wildlife Code', 'PW'], ['Election Code', 'EL'], ['Water Code', 'WA'], ['Utilities Code', 'UT'],
    // Texas Administrative Code: only Title 37 (TCOLE, Part 7) is built, so only Title-37 / TCOLE wording maps to it;
    // a bare "TAC" (e.g. "43 TAC 217.27", a TxDOT rule) stays unlinked.
    ['37 TAC', 'TAC'], ['37 Tex. Admin. Code', 'TAC'], ['TCOLE Rules', 'TAC'], ['TCOLE Rule', 'TAC']
  ];
  var SHORT = [
    ['CCP', 'CR'], ['HSC', 'HS'], ['HS', 'HS'], ['FC', 'FA'], ['PC', 'PE'], ['GV', 'GV'], ['GC', 'GV'],
    ['ED', 'ED'], ['AL', 'AL'], ['TN', 'TN'], ['TC', 'TN'], ['TRC', 'TN'], ['OC', 'OC'], ['HRC', 'HR'],
    ['BCC', 'BC'], ['LGC', 'LG'], ['CPRC', 'CP']
  ];
  // Names that look like code citations but are not Texas statutes; they only block context.
  var NOT_STATUTE = "TAC|CFR|C\\.F\\.R\\.|U\\.S\\.C\\.|USC|FMVSS|Administrative Code|Admin\\. Code|Rules?";

  function esc(s){ return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); }
  // long names tolerate extra spaces and "Code Of Criminal Procedure"-style capitals
  function longPat(p){
    if(p[2]) return p[0].replace(/ /g, '\\s+');   // already a regex source
    return esc(p[0]).split(' ').map(function(w){ return /^(of|and)$/.test(w) ? '[' + w[0] + w[0].toUpperCase() + ']' + w.slice(1) : w; }).join('\\s+');
  }
  var LONG_RES = LONG.map(function(p){ return {re: new RegExp('^' + longPat(p) + '$', 'i'), code: p[1]}; });
  var SHORT_MAP = {};
  SHORT.forEach(function(p){ SHORT_MAP[p[0].toLowerCase()] = p[1]; });
  var LONG_RE = LONG.map(longPat).join('|');
  var ANY_RE = LONG_RE + '|' + SHORT.map(function(p){ return esc(p[0]); }).join('|');

  var SEC = '\\d+[A-Za-z]?\\.\\d+[A-Za-z0-9]*';
  var SUB = '(?:\\([A-Za-z0-9-]+\\))*';
  var PRE = '(?:(?:Arts?\\.?|Articles?|Secs?\\.?|Sections?|&sect;&sect;?|§§?)\\s*)?';
  var LIST_SEP = '(?:\\s*,?\\s*(?:and|or|through|to)\\s+|\\s*(?:,|-|–|/|&amp;)\\s*)';
  var TAIL = '((?:' + LIST_SEP + SEC + SUB + ')*)';

  // A: "FC 51.02(a)", "CCP Art. 2A.001, 2A.002", "Penal Code Section 22.01"
  var RE_A = new RegExp('\\b(' + ANY_RE + ')[,.]?\\s+' + PRE + '(' + SEC + ')(' + SUB + ')' + TAIL, 'g');
  // B: "Section 22.01, Penal Code", "Article 2A.001 of the Code of Criminal Procedure"
  // B and D ignore case so all-caps statute text ("SECTION 1.07, PENAL CODE") links too
  var RE_B = new RegExp('\\b(?:Arts?\\.?|Articles?|Secs?\\.?|Sections?)\\s*(' + SEC + ')(' + SUB + '),?\\s+(?:of\\s+the\\s+)?(' + LONG_RE + ')\\b','gi');
  // C: "Family Code Chapter 51", "FC Ch. 52"
  var RE_C = new RegExp('\\b(' + ANY_RE + ')[,.]?\\s+(?:Chapter|Ch\\.)\\s*(\\d+[A-Za-z]?)\\b', 'g');
  // D: "Chapter 573, Health and Safety Code"
  var RE_D = new RegExp('\\b(?:Chapter|Ch\\.)\\s*(\\d+[A-Za-z]?),?\\s+(?:of\\s+the\\s+)?(' + LONG_RE + ')\\b','gi');
  var RE_SEC_G = new RegExp(SEC, 'g');

  // Context pass tokens (one left-to-right scan). Groups:
  //  1 named code (sets context)   2 not-a-statute name (blocks context)   3 BPOC/LO-style number list (skipped)
  //  4 article cite + 5 its tail   6 section cite + 7 its tail + 8 ", Penal Code"-style suffix (9 = the name)
  //  10 bare number + 11 its tail
  var RE_CTX = new RegExp(
    '\\b(' + LONG_RE + '|(?:' + SHORT.map(function(p){ return esc(p[0]); }).join('|') + ')(?=[,.]?\\s+(?:' + PRE + '(?:\\d|Chapter|Ch\\.)|offenses?\\b|sections?\\b|articles?\\b)))\\b' +
    '|\\b(' + NOT_STATUTE + ')(?![A-Za-z])' +
    '|\\b((?:BPOC|LOs?|Day|Days|Chapter|Ch\\.|Q|Unit|Module)\\s*\\d+(?:\\.\\d+)*(?:' + LIST_SEP + '\\d+(?:\\.\\d+)*)*)' +
    '|\\b(?:Arts?\\.?|Articles?)\\s*(' + SEC + SUB + ')' + TAIL +
    '|(?:\\b(?:Secs?\\.?|Sections?)|&sect;(?:&sect;)?|§§?)\\s*(' + SEC + SUB + ')' + TAIL +
      '(,?\\s+(?:of\\s+the\\s+)?(' + ANY_RE + '|' + NOT_STATUTE + ')\\b)?' +
    '|(?<![\\w$.,\\d])(\\d{1,3}[A-Za-z]?\\.\\d{2,5}[A-Za-z0-9]*' + SUB + ')(?![\\d%])' + TAIL,
    'g');

  var codes = {};   // id -> {name, secs:Set, chs:Set}
  var ready = fetch(DATA + 'codes.json', {cache:'no-cache'}).then(function(r){ return r.ok ? r.json() : []; }).then(function(list){
    return Promise.all(list.map(function(c){
      return fetch(DATA + c.code + '/toc.json', {cache:'no-cache'}).then(function(r){ return r.json(); }).then(function(toc){
        codes[c.code] = {
          name: c.name,
          secs: new Set(toc.sections.map(function(s){ return s[0].toLowerCase(); })),
          chs: new Set(toc.chapters.map(function(ch){ return ch.n.toLowerCase(); }))
        };
      }).catch(function(){});
    }));
  }).catch(function(){});

  function codeFor(alias){
    var n = alias.replace(/\s+/g, ' ');
    if(SHORT_MAP[n.toLowerCase()] && n === n.toUpperCase()) return SHORT_MAP[n.toLowerCase()];
    for(var i = 0; i < LONG_RES.length; i++) if(LONG_RES[i].re.test(n)) return LONG_RES[i].code;
    return SHORT_MAP[n.toLowerCase()];
  }
  function link(text, code, key, isChapter){
    var c = codes[code];
    if(!c) return null;
    key = key.toLowerCase();
    if(isChapter ? !c.chs.has(key) : !c.secs.has(key)) return null;
    var href = new URL('codes.html?code=' + code + (isChapter ? '&ch=' : '&sec=') + encodeURIComponent(key.toUpperCase()), siteRoot).href;
    var label = c.name + (isChapter ? ' Chapter ' : ' § ') + key.toUpperCase();
    return '<a class="code-link" href="' + href + '" target="' + TARGET + '" title="Open ' + label + ' (separate tab)">' + text + '</a>';
  }
  function has(code, sec){ return !!(codes[code] && codes[code].secs.has(sec.toLowerCase())); }
  function secOf(s){ return s.replace(/\(.*$/, ''); }
  // link "head" (whose section is sec) and every section number in tail, all in one code
  function linkRun(head, sec, tail, code){
    var first = (code && link(head, code, secOf(sec), false)) || head;
    var rest = tail.replace(RE_SEC_G, function(n){ return (code && link(n, code, n, false)) || n; });
    return first + rest;
  }

  // Apply fn to text outside tags and outside existing <a> elements; onTag sees every tag.
  function mapText(html, fn, onTag){
    var parts = html.split(/(<[^>]*>)/), depth = 0;
    for(var i = 0; i < parts.length; i++){
      var p = parts[i];
      if(p.charAt(0) === '<'){
        if(/^<a[\s>]/i.test(p)) depth++;
        else if(/^<\/a>/i.test(p)) depth = Math.max(0, depth - 1);
        if(onTag) onTag(p);
      } else if(p && depth === 0){
        parts[i] = fn(p);
      }
    }
    return parts.join('');
  }

  function contextPass(html, secCode){
    var last = null, lastSec = null;
    function setCode(code){ last = code; if(code !== 'CR') lastSec = code; }
    return mapText(html, function(t){
      return t.replace(RE_CTX, function(all, named, notStat, numRef, artSec, artTail, sSec, sTail, sSuffix, sName, bare, bareTail){
        if(named){ setCode(codeFor(named) || 'X'); return all; }
        if(notStat){
          // in the TCOLE rules bank (secCode TAC), "Rule 217.7" means a TAC rule
          if(secCode === 'TAC' && /^Rules?$/.test(notStat)){ setCode('TAC'); return all; }
          last = lastSec = 'X'; return all;
        }
        if(numRef) return all;
        if(artSec){
          last = 'CR';
          return linkRun(all.slice(0, all.length - artTail.length), artSec, artTail, 'CR');
        }
        if(sSec){
          sSuffix = sSuffix || '';
          var code;
          if(sName){ code = codeFor(sName) || 'X'; setCode(code); }
          else { code = lastSec || secCode || null; if(code) last = code; }
          if(!code || code === 'X') return all;
          var core = all.slice(0, all.length - sSuffix.length);
          return linkRun(core.slice(0, core.length - sTail.length), sSec, sTail, code) + sSuffix;
        }
        if(bare){
          // CCP provisions are normally written "Art. x"; a bare number after a CCP cite is read as the
          // bank's own code when that code has the section, otherwise as CCP
          var bc = (last === 'CR' && secCode && secCode !== 'CR' && has(secCode, secOf(bare))) ? secCode : (last || secCode || null);
          if(!bc || bc === 'X') return all;
          return linkRun(bare, bare, bareTail, bc);
        }
        return all;
      });
    }, function(tag){
      var m = /^<a[^>]*codes\.html\?code=(\w+)/i.exec(tag);
      if(m) setCode(m[1]);
    });
  }

  function linkify(html, opts){
    if(!html) return html;
    html = mapText(html, function(t){
      return t.replace(RE_A, function(all, alias, sec, sub, tail){
        var code = codeFor(alias);
        var head = all.slice(0, all.length - tail.length);
        return linkRun(head, sec, tail, code);
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
    if(opts && opts.context) html = contextPass(html, opts.secCode || null);
    return html;
  }

  var style = document.createElement('style');
  style.textContent = 'a.code-link{color:inherit;text-decoration:underline;text-decoration-style:dotted;text-underline-offset:2px;}' +
    'a.code-link::after{content:"\\2197";font-size:0.8em;margin-left:1px;opacity:0.7;}' +
    'a.code-link:hover{color:#B08B3C;text-decoration-style:solid;}';
  (document.head || document.documentElement).appendChild(style);

  window.CodeLinks = {ready: ready, linkify: linkify, isBuilt: function(code){ return !!codes[code]; }};
})();

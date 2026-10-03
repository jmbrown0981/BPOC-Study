/* Turns BPOC and case-law references in already-rendered HTML into links:
     "BPOC 10.3"                  -> study.html?ch=10#lo-10-3   (LO heading in that chapter)
     "BPOC 33.24/33.25", "BPOC 20.1-20.11", "BPOC 32.17 and 32.25"   -> each number links
     "BPOC Chapter 24", "BPOC Ch. 32"                                 -> study.html?ch=24
     "Terry v. Ohio", "U.S. v. Sokolow", "Cruz v. Laramie"            -> case-law.html#case-<slug>
   Companion to code-links.js (statutes -> codes.html); run it after CodeLinks.linkify. Text
   already inside an <a> is left alone, so the two never double-link.

   Case names come from assets/case-law-data.js (CASE_LAW_CATEGORIES); only cases listed there
   link, and only by their full "A v. B" name or a known short form of it, so a made-up
   distractor like "Payton v. New Jersey" stays plain text. Chapter titles for link tooltips
   come from assets/chapters-manifest.js (CHAPTER_MANIFEST) when it's loaded.
   An LO with no matching heading in the chapter (study.html) just opens the chapter.

   Links open in shared, separate tabs ("bpoc-study", "bpoc-cases") so a quiz in progress is
   left alone, the same way code links use "bpoc-codes".

   Usage:  <script src="assets/case-law-data.js"></script>
           <script src="assets/chapters-manifest.js"></script>   (optional, tooltips)
           <script src="assets/ref-links.js"></script>
           html = RefLinks.linkify(html);                         // synchronous */
(function(){
  var script = document.currentScript;
  var siteRoot = new URL('../', script ? script.src : location.href);   // assets/ -> site root
  var STUDY_TARGET = 'bpoc-study', CASE_TARGET = 'bpoc-cases';

  /* ---------- chapters ---------- */
  var chapters = {};
  if(typeof CHAPTER_MANIFEST !== 'undefined'){
    CHAPTER_MANIFEST.forEach(function(c){ chapters[c.num] = c.title; });
  } else {
    for(var n = 1; n <= 43; n++) chapters[n] = null;
  }

  /* ---------- cases ---------- */
  // Same slug rule as case-law.html's slugify(), which builds the #case-<slug> card ids.
  function slugify(s){ return s.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, ''); }
  function esc(s){ return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); }

  // Short forms seen in the banks: "U.S." for "United States", "Waco" for "City of Waco",
  // "Ceballos" for "Estate of Ceballos", "Laramie" for "City of Laramie", and a trailing
  // ", Texas" dropped.
  function partyForms(p){
    var out = [p];
    if(p === 'United States') out.push('U.S.');
    var m = /^(?:City|Estate|County) of (.+)$/.exec(p);
    if(m) out.push(m[1]);
    if(p.indexOf(', ') > 0) out = out.concat(partyForms(p.slice(0, p.indexOf(', '))));
    return out;
  }

  var caseByForm = {};   // normalized "A v. B" -> {name, slug}
  var forms = [];
  var cats = (typeof CASE_LAW_CATEGORIES !== 'undefined') ? CASE_LAW_CATEGORIES : [];
  cats.forEach(function(cat){
    cat.cases.forEach(function(c){
      var parts = c.name.split(' v. ');
      if(parts.length !== 2) return;
      var info = {name: c.name, slug: slugify(c.name), cite: c.cite, year: c.year};
      partyForms(parts[0]).forEach(function(a){
        partyForms(parts[1]).forEach(function(b){
          var key = a + ' v. ' + b;
          if(!caseByForm[key]){ caseByForm[key] = info; forms.push(key); }
        });
      });
    });
  });
  // Longest first so "City of Waco v. Williams" wins over "Waco v. Williams".
  forms.sort(function(x, y){ return y.length - x.length; });
  function formPat(f){ return esc(f).replace(/ /g, '\\s+'); }
  var RE_CASE = forms.length
    ? new RegExp('(?<![A-Za-z0-9.])(' + forms.map(formPat).join('|') + ')(?![A-Za-z0-9])', 'g')
    : null;
  function norm(s){ return s.replace(/\s+/g, ' '); }

  /* ---------- BPOC ---------- */
  var LO = '(\\d{1,2})\\.(\\d{1,2}[A-Za-z]?)(?![\\d.]*\\d)';
  var LIST_SEP = '(?:\\s*(?:,|/|&amp;|–|-)\\s*|\\s+(?:and|or|through|to)\\s+)';
  var RE_BPOC = new RegExp('\\bBPOC\\s+' + LO + '((?:' + LIST_SEP + '\\d{1,2}\\.\\d{1,2}[A-Za-z]?(?![\\d.]*\\d))*)', 'g');
  var RE_BPOC_CH = /\bBPOC\s+(?:Chapter|Ch\.)\s*(\d{1,2})\b/g;
  var RE_LO_G = /(\d{1,2})\.(\d{1,2}[A-Za-z]?)(?![\d.]*\d)/g;

  function studyLink(text, ch, lo){
    if(!(ch in chapters)) return null;
    var href = new URL('study.html?ch=' + ch + (lo ? '#lo-' + ch + '-' + lo : ''), siteRoot).href;
    var title = 'Open BPOC Ch ' + ch + (chapters[ch] ? ' — ' + chapters[ch] : '') + (lo ? ', LO ' + ch + '.' + lo : '') + ' (separate tab)';
    return '<a class="ref-link" href="' + href + '" target="' + STUDY_TARGET + '" title="' + title.replace(/"/g, '&quot;') + '">' + text + '</a>';
  }
  function caseLink(text, info){
    var href = new URL('case-law.html#case-' + info.slug, siteRoot).href;
    var title = 'Open ' + info.name + ', ' + info.cite + ' (' + info.year + ') in Case Law (separate tab)';
    return '<a class="ref-link" href="' + href + '" target="' + CASE_TARGET + '" title="' + title.replace(/"/g, '&quot;') + '">' + text + '</a>';
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
      return t.replace(RE_BPOC_CH, function(all, ch){ return studyLink(all, +ch, null) || all; });
    });
    html = mapText(html, function(t){
      return t.replace(RE_BPOC, function(all, ch, lo, tail){
        var head = all.slice(0, all.length - tail.length);
        var first = studyLink(head, +ch, lo) || head;
        var rest = tail.replace(RE_LO_G, function(n, c2, lo2){ return studyLink(n, +c2, lo2) || n; });
        return first + rest;
      });
    });
    if(RE_CASE){
      html = mapText(html, function(t){
        return t.replace(RE_CASE, function(all){
          var info = caseByForm[norm(all)];
          return info ? caseLink(all, info) : all;
        });
      });
    }
    return html;
  }

  var style = document.createElement('style');
  style.textContent = 'a.ref-link{color:inherit;text-decoration:underline;text-decoration-style:dotted;text-underline-offset:2px;}' +
    'a.ref-link::after{content:"\\2197";font-size:0.8em;margin-left:1px;opacity:0.7;}' +
    'a.ref-link:hover{color:#B08B3C;text-decoration-style:solid;}';
  (document.head || document.documentElement).appendChild(style);

  window.RefLinks = {linkify: linkify, caseCount: Object.keys(caseByForm).length};
})();

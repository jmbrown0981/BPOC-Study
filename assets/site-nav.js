/* Site-wide navigation bar, added to the footer of every page.
   Each page loads this with a relative path (e.g. "../assets/site-nav.js"); links are
   resolved against this script's own location, so it works at any folder depth.
   To add/rename a section, edit NAV_LINKS. */
(function(){
  var NAV_LINKS = [
    {href: 'index.html',      label: 'Home'},
    {href: 'study.html',      label: 'Study Reference'},
    {href: 'flashcards.html', label: 'Flashcards'},
    {href: 'alt-quiz.html',   label: 'Alt Quiz'},
    {href: 'case-law.html',   label: 'Case Law'},
    {href: 'codes.html',      label: 'Texas Codes'},
    {href: 'links.html',      label: 'Useful Links'}
  ];

  var script = document.currentScript;
  var siteRoot = new URL('../', script ? script.src : location.href); // assets/ -> site root

  function build(){
    if(document.getElementById('site-nav')) return;
    var style = document.createElement('style');
    style.textContent =
      '#site-nav{max-width:840px;margin:34px auto 0;padding:14px 12px 4px;border-top:1px solid #C9BF9F;' +
      'display:flex;flex-wrap:wrap;justify-content:center;gap:6px 8px;font-family:"IBM Plex Sans",system-ui,sans-serif;}' +
      '#site-nav a{font-size:12.5px;font-weight:600;text-decoration:none;color:#132339;background:#fff;' +
      'border:1px solid #C9BF9F;border-radius:999px;padding:6px 13px;line-height:1.2;white-space:nowrap;}' +
      '#site-nav a:hover{border-color:#B08B3C;color:#B08B3C;}' +
      '#site-nav a[aria-current="page"]{background:#132339;border-color:#132339;color:#F3EFE4;}' +
      'footer #site-nav{margin-top:0;margin-bottom:14px;}';
    document.head.appendChild(style);

    var nav = document.createElement('nav');
    nav.id = 'site-nav';
    nav.setAttribute('aria-label', 'Site sections');
    var here = location.pathname.replace(/\/$/, '/index.html');
    NAV_LINKS.forEach(function(l){
      var url = new URL(l.href, siteRoot);
      var a = document.createElement('a');
      a.href = url.href;
      a.textContent = l.label;
      if(url.pathname === here) a.setAttribute('aria-current', 'page');
      nav.appendChild(a);
    });

    var footer = document.querySelector('footer');
    if(footer) footer.insertBefore(nav, footer.firstChild);
    else document.body.appendChild(nav);
  }

  if(document.readyState === 'loading') document.addEventListener('DOMContentLoaded', build);
  else build();
})();

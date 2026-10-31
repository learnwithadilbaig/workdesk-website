#!/usr/bin/env python3
"""Build the WorkDesk website.

    python3 src/build.py                 # writes docs/ (the deployable site)
    python3 src/build.py --preview DIR   # also writes a preview copy for a single-page viewer

Pages live in src/pages/*.html. Each starts with a front-matter comment:

    <!--
    title: Payroll Software in Pakistan | WorkDesk
    description: One or two sentences for search results (140-160 characters).
    nav: products
    crumbs: Features=features.html; Payroll & Fines
    type: WebPage
    -->

Macros inside pages and partials:
    {{tick}}            the double-tick mark (inline SVG)
    {{icon:name}}       a line icon from ICONS below
    {{include:name}}    src/partials/name.html
    {{cfg:key}}         a value from src/config.json
    {{login}} {{signup}} {{home}}   links that respect config.json
"""
import datetime
import html
import json
import os
import re
import shutil
import sys

SRC = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(SRC)
CFG = json.load(open(os.path.join(SRC, 'config.json')))
LOGO = json.load(open(os.path.join(SRC, 'assets', 'logo-paths.json')))
SITE = CFG['site_url'].rstrip('/')

ICONS = {
    'people': '<circle cx="9" cy="8" r="3.5"/><path d="M2.5 20c.6-3.6 3.2-5.5 6.5-5.5s5.9 1.9 6.5 5.5"/><path d="M16 4.6a3.5 3.5 0 0 1 0 6.8M18.5 14.8c1.7.8 2.8 2.5 3 5.2"/>',
    'clock': '<circle cx="12" cy="12" r="8.5"/><path d="M12 7.5V12l3 2"/>',
    'wallet': '<rect x="3" y="6" width="18" height="13" rx="3"/><path d="M3 10h18M16 14.5h2"/>',
    'task': '<rect x="4" y="4" width="16" height="16" rx="4"/><path d="M8.5 12l2.5 2.5 4.5-5"/>',
    'star': '<path d="M12 3.8l2.5 5.1 5.6.8-4 3.9 1 5.6-5.1-2.7-5 2.7 1-5.6-4.1-3.9 5.6-.8z"/>',
    'chart': '<path d="M4 20V10M10 20V4M16 20v-7M21 20H3"/>',
    'home': '<path d="M4 11l8-6.5 8 6.5V20H4z"/><path d="M10 20v-5h4v5"/>',
    'layers': '<path d="M12 3.5l9 5-9 5-9-5z"/><path d="M3 13l9 5 9-5"/>',
    'check': '<path d="M3.5 12.5l4 4L15 9"/><path d="M11.5 15.5l1 1L20 9"/>',
    'sliders': '<path d="M5 20v-6M5 10V4M12 20v-8M12 8V4M19 20v-4M19 12V4M3 14h4M10 8h4M17 16h4"/>',
    'lock': '<rect x="5" y="10.5" width="14" height="10" rx="2.5"/><path d="M8.5 10.5V8a3.5 3.5 0 0 1 7 0v2.5"/>',
    'monitor': '<rect x="3" y="4" width="18" height="12" rx="2.5"/><path d="M9 20h6M12 16v4"/>',
    'phone': '<rect x="7" y="2.5" width="10" height="19" rx="2.5"/><path d="M11 18.5h2"/>',
    'bell': '<path d="M6 16V11a6 6 0 0 1 12 0v5l1.5 2h-15z"/><path d="M10 20.5a2 2 0 0 0 4 0"/>',
    'factory': '<path d="M3 20V10l6 3.5V10l6 3.5V5h4v15z"/>',
    'bag': '<path d="M5 8h14l-1 12H6z"/><path d="M9 8V6.5a3 3 0 0 1 6 0V8"/>',
    'heart': '<path d="M12 20s-7.5-4.6-7.5-10A4.3 4.3 0 0 1 12 7.4 4.3 4.3 0 0 1 19.5 10c0 5.4-7.5 10-7.5 10z"/>',
    'book': '<path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H20v15H6.5A2.5 2.5 0 0 0 4 20.5z"/><path d="M4 20.5A2.5 2.5 0 0 1 6.5 18H20v3H6.5"/>',
    'brief': '<rect x="3" y="7" width="18" height="13" rx="2.5"/><path d="M9 7V5.5A1.5 1.5 0 0 1 10.5 4h3A1.5 1.5 0 0 1 15 5.5V7M3 13h18"/>',
    'truck': '<path d="M2.5 6h11v10h-11zM13.5 10h4l3 3v3h-7z"/><circle cx="6.5" cy="17.5" r="1.8"/><circle cx="17" cy="17.5" r="1.8"/>',
    'rocket': '<path d="M12 15l-3-3c1.5-5 4.5-8 9.5-8.5C18 8.5 15 11.5 12 15z"/><path d="M9 12l-3.5.5L4 15l4 1M12 15l-.5 3.5L9 20l-1-4"/>',
    'mail': '<rect x="3" y="5" width="18" height="14" rx="2.5"/><path d="M3.5 6.5l8.5 6.5 8.5-6.5"/>',
    'chat': '<path d="M4 5h16v11H9l-5 4z"/>',
    'pin': '<path d="M12 21s-6.5-6.1-6.5-11a6.5 6.5 0 0 1 13 0c0 4.9-6.5 11-6.5 11z"/><circle cx="12" cy="10" r="2.3"/>',
    'file': '<path d="M6 3h8l4 4v14H6z"/><path d="M14 3v4h4M9 13h6M9 17h6"/>',
    'shield': '<path d="M12 3l7.5 3v6c0 4.5-3.2 7.7-7.5 9-4.3-1.3-7.5-4.5-7.5-9V6z"/><path d="M8.8 12l2.2 2.2 4.2-4.4"/>',
    'key': '<circle cx="8" cy="15" r="4"/><path d="M11 12l8.5-8.5M16 7l2.5 2.5M14 9l2 2"/>',
    'history': '<path d="M3.5 12a8.5 8.5 0 1 0 2.5-6"/><path d="M3.5 4.5V9H8M12 8v4.5l3 1.8"/>',
    'cloud': '<path d="M7 18.5a4.5 4.5 0 0 1-.6-9 6 6 0 0 1 11.4 1.6A3.8 3.8 0 0 1 17.5 18.5z"/>',
    'handshake': '<path d="M3 11l4-4 3 1.5L13 6l8 5-3 3"/><path d="M7 7l-4 4 6 6 2-1.5M11 15l2 2M13 13l3 3M15 11l3 3"/>',
    'search': '<circle cx="11" cy="11" r="6.5"/><path d="M16 16l4.5 4.5"/>',
    'arrow': '<path d="M5 12h14M13 6l6 6-6 6"/>',
    'plus': '<path d="M12 5v14M5 12h14"/>',
    'calendar': '<rect x="3.5" y="5" width="17" height="15" rx="3"/><path d="M3.5 10h17M8 3v4M16 3v4"/>',
    'user-check': '<circle cx="9" cy="8" r="3.5"/><path d="M2.5 20c.6-3.6 3.2-5.5 6.5-5.5 1.6 0 3 .4 4.1 1.2M15 18l2 2 4-4"/>',
    'map': '<path d="M3 6l6-2.5 6 2.5 6-2.5v14.5l-6 2.5-6-2.5-6 2.5z"/><path d="M9 3.5v14.5M15 6v14.5"/>',
    'spark': '<path d="M12 3v4M12 17v4M3 12h4M17 12h4M6 6l2.5 2.5M15.5 15.5L18 18M6 18l2.5-2.5M15.5 8.5L18 6"/>',
    'download': '<path d="M12 4v11M7 10.5l5 5 5-5M4.5 20h15"/>',
    'globe': '<circle cx="12" cy="12" r="8.5"/><path d="M3.5 12h17M12 3.5c2.5 2.7 3.5 5.5 3.5 8.5s-1 5.8-3.5 8.5c-2.5-2.7-3.5-5.5-3.5-8.5s1-5.8 3.5-8.5z"/>',
}


def icon(name):
    return f'<svg class="i" viewBox="0 0 24 24" aria-hidden="true">{ICONS[name]}</svg>'


TICK = (f'<svg class="mt" viewBox="0 0 {LOGO["tick_w"]} {LOGO["tick_h"]}" aria-hidden="true">'
        '<use class="b" href="#tick-b"/><use class="f" href="#tick-f"/></svg>')
LOGO_SVG = (f'<svg class="logo-svg" viewBox="{LOGO["logo_viewbox"]}" role="img" aria-label="WorkDesk">'
            '<use class="b" href="#wd-back"/><use class="f" href="#wd-front"/><use class="w" href="#wd-word"/></svg>')
SPRITE = (
    '<svg width="0" height="0" style="position:absolute" aria-hidden="true"><defs>'
    f'<symbol id="wd-back" viewBox="{LOGO["logo_viewbox"]}"><path d="{LOGO["back"]}"/></symbol>'
    f'<symbol id="wd-front" viewBox="{LOGO["logo_viewbox"]}"><path d="{LOGO["front"]}"/></symbol>'
    f'<symbol id="wd-word" viewBox="{LOGO["logo_viewbox"]}"><path d="{LOGO["word"]}"/></symbol>'
    f'<symbol id="tick-b" viewBox="{LOGO["tick_viewbox"]}"><path d="{LOGO["back"]}"/></symbol>'
    f'<symbol id="tick-f" viewBox="{LOGO["tick_viewbox"]}"><path d="{LOGO["front"]}"/></symbol>'
    '</defs></svg>')


def parse(path):
    raw = open(path, encoding='utf-8').read()
    m = re.match(r'\s*<!--(.*?)-->', raw, re.S)
    meta = {}
    for line in m.group(1).strip().splitlines():
        k, _, v = line.partition(':')
        meta[k.strip()] = v.strip()
    meta['body'] = raw[m.end():]
    meta['slug'] = os.path.splitext(os.path.basename(path))[0]
    return meta


def url_of(slug):
    return SITE + '/' if slug == 'index' else f'{SITE}/{slug}.html'


def expand(text, preview, depth=0):
    if depth > 4:
        return text
    text = re.sub(r'\{\{include:([\w-]+)\}\}',
                  lambda m: expand(open(os.path.join(SRC, 'partials', m.group(1) + '.html'), encoding='utf-8').read(), preview, depth + 1), text)
    text = re.sub(r'\{\{icon:([\w-]+)\}\}', lambda m: icon(m.group(1)), text)
    text = re.sub(r'\{\{cfg:(\w+)\}\}', lambda m: html.escape(str(CFG.get(m.group(1), ''))), text)
    text = text.replace('{{tick}}', TICK)
    text = text.replace('{{login}}', CFG['app_login_url'] or 'login.html')
    text = text.replace('{{signup}}', CFG['app_signup_url'] or 'signup.html')
    text = text.replace('{{home}}', 'index.html' if preview else './')
    return text


NAV = [
    ('products', 'Products', None),
    ('solutions', 'Solutions', 'solutions.html'),
    ('pricing', 'Pricing', 'pricing.html'),
    ('resources', 'Resources', None),
    ('about', 'About', 'about.html'),
]


def header(active, preview):
    items = []
    for key, label, href in NAV:
        cur = ' aria-current="page"' if key == active else ''
        if key == 'products':
            items.append(
                f'<div class="dd"><button type="button" class="dd-btn"{cur} aria-expanded="false" aria-controls="mega-products">Products {icon("arrow")}</button>'
                '<div class="mega" id="mega-products" hidden>'
                '<a href="people-management.html"><span class="ico">' + icon('people') + '</span><span><b>People</b><small>Employee records, documents, org chart</small></span></a>'
                '<a href="attendance-leave-management.html"><span class="ico">' + icon('clock') + '</span><span><b>Attendance &amp; Leave</b><small>Check-ins, shifts, leave balances</small></span></a>'
                '<a href="payroll-software.html"><span class="ico">' + icon('wallet') + '</span><span><b>Payroll &amp; Fines</b><small>Salaries, deductions, payslips</small></span></a>'
                '<a href="task-project-management.html"><span class="ico">' + icon('task') + '</span><span><b>Tasks &amp; Projects</b><small>Assign work and track it to done</small></span></a>'
                '<a href="performance-scorecards.html"><span class="ico">' + icon('star') + '</span><span><b>Scorecards</b><small>Goals, KPIs and reviews</small></span></a>'
                '<a href="hr-reports-analytics.html"><span class="ico">' + icon('chart') + '</span><span><b>Reports</b><small>Dashboards and exports</small></span></a>'
                '<a class="mega-all" href="features.html">See all features ' + icon('arrow') + '</a>'
                '</div></div>')
        elif key == 'resources':
            items.append(
                f'<div class="dd"><button type="button" class="dd-btn"{cur} aria-expanded="false" aria-controls="mega-resources">Resources {icon("arrow")}</button>'
                '<div class="mega mega-sm" id="mega-resources" hidden>'
                '<a href="blog.html"><span class="ico">' + icon('book') + '</span><span><b>Blog</b><small>Guides on HR and payroll</small></span></a>'
                '<a href="help.html"><span class="ico">' + icon('chat') + '</span><span><b>Help centre</b><small>Set-up guides and answers</small></span></a>'
                '<a href="faq.html"><span class="ico">' + icon('search') + '</span><span><b>FAQ</b><small>Common questions</small></span></a>'
                '<a href="security.html"><span class="ico">' + icon('shield') + '</span><span><b>Security</b><small>How we protect your data</small></span></a>'
                '</div></div>')
        else:
            items.append(f'<a href="{href}"{cur}>{label}</a>')
    return f'''<header class="site">
  <div class="wrap nav">
    <a class="logo" href="{'index.html' if preview else './'}" aria-label="WorkDesk home">{LOGO_SVG}</a>
    <nav class="links" aria-label="Main">{''.join(items)}</nav>
    <div class="right">
      <a class="login" href="{{{{login}}}}">Log in</a>
      <a class="btn btn-primary btn-sm" href="demo.html">Book a demo</a>
    </div>
    <button class="menu-btn" type="button" aria-expanded="false" aria-controls="mobile-nav" aria-label="Open menu">
      <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 7h16M4 12h16M4 17h16"/></svg>
    </button>
  </div>
  <nav class="mobile-nav wrap" id="mobile-nav" hidden aria-label="Mobile">
    <a href="features.html">All features</a><a href="payroll-software.html">Payroll</a><a href="attendance-leave-management.html">Attendance &amp; leave</a>
    <a href="solutions.html">Solutions</a><a href="pricing.html">Pricing</a><a href="blog.html">Blog</a><a href="help.html">Help centre</a><a href="about.html">About</a><a href="{{{{login}}}}">Log in</a>
    <a class="btn btn-primary" href="demo.html">Book a demo</a>
  </nav>
</header>'''


def footer():
    soc = [(k, v) for k, v in CFG['social'].items() if v]
    soc_html = ''.join(f'<a href="{html.escape(v)}" rel="noopener" target="_blank">{k.capitalize() if k != "x" else "X"}</a>' for k, v in soc)
    contact = f'<p class="foot-contact">{icon("mail")} <span>{html.escape(CFG["contact_email"])}</span></p>' if CFG['contact_email'] else ''
    if CFG['phone']:
        contact += f'<p class="foot-contact">{icon("phone")} <span>{html.escape(CFG["phone"])}</span></p>'
    return f'''<footer class="site-foot">
  <div class="wrap">
    <div class="foot">
      <div class="foot-brand">
        <a class="logo" href="{{{{home}}}}" aria-label="WorkDesk home">{LOGO_SVG}</a>
        <p>HR, payroll and work management for growing teams in Pakistan. Every request, ticked off.</p>
        {contact}
        {f'<div class="soc">{soc_html}</div>' if soc_html else ''}
      </div>
      <div><h2 class="foot-h">Product</h2><ul>
        <li><a href="features.html">All features</a></li><li><a href="people-management.html">Employee management</a></li>
        <li><a href="attendance-leave-management.html">Attendance &amp; leave</a></li><li><a href="payroll-software.html">Payroll software</a></li>
        <li><a href="task-project-management.html">Tasks &amp; projects</a></li><li><a href="performance-scorecards.html">Performance scorecards</a></li>
        <li><a href="hr-reports-analytics.html">HR reports</a></li><li><a href="pricing.html">Pricing</a></li></ul></div>
      <div><h2 class="foot-h">Company</h2><ul>
        <li><a href="about.html">About us</a></li><li><a href="solutions.html">Solutions</a></li><li><a href="careers.html">Careers</a></li>
        <li><a href="partners.html">Partners</a></li><li><a href="contact.html">Contact</a></li><li><a href="demo.html">Book a demo</a></li></ul></div>
      <div><h2 class="foot-h">Resources</h2><ul>
        <li><a href="blog.html">Blog</a></li><li><a href="help.html">Help centre</a></li><li><a href="faq.html">FAQ</a></li>
        <li><a href="security.html">Security</a></li></ul></div>
    </div>
    <div class="legal"><span>&copy; <span data-year>2026</span> {html.escape(CFG['company_legal_name'])}. All rights reserved.</span>
      <nav aria-label="Legal"><a href="privacy.html">Privacy policy</a><a href="terms.html">Terms of service</a><a href="security.html">Security</a></nav></div>
  </div>
</footer>'''


def crumbs_html(meta):
    if not meta.get('crumbs'):
        return '', None
    parts = [p.strip() for p in meta['crumbs'].split(';')]
    trail = [('Home', 'index')]
    for p in parts:
        name, _, href = p.partition('=')
        trail.append((name.strip(), href.strip().replace('.html', '') if href else meta['slug']))
    links = []
    for i, (name, slug) in enumerate(trail):
        if i == len(trail) - 1:
            links.append(f'<span aria-current="page">{html.escape(name)}</span>')
        else:
            href = '{{home}}' if slug == 'index' else f'{slug}.html'
            links.append(f'<a href="{href}">{html.escape(name)}</a>')
    ld = {'@type': 'BreadcrumbList', 'itemListElement': [
        {'@type': 'ListItem', 'position': i + 1, 'name': n, 'item': url_of(s)} for i, (n, s) in enumerate(trail)]}
    return '<nav class="crumbs wrap" aria-label="Breadcrumb">' + '<span class="sep">/</span>'.join(links) + '</nav>', ld


def schema(meta, crumbs_ld):
    org = {'@type': 'Organization', '@id': SITE + '/#org', 'name': 'WorkDesk', 'url': SITE + '/',
           'logo': SITE + '/icon-512.png'}
    if CFG['contact_email']:
        org['email'] = CFG['contact_email']
    same = [v for v in CFG['social'].values() if v]
    if same:
        org['sameAs'] = same
    graph = [org]
    page_type = meta.get('type', 'WebPage')
    url = url_of(meta['slug'])
    if meta['slug'] == 'index':
        graph.append({'@type': 'WebSite', '@id': SITE + '/#website', 'name': 'WorkDesk', 'url': SITE + '/',
                      'publisher': {'@id': SITE + '/#org'}, 'inLanguage': 'en'})
    if meta.get('software') == 'yes':
        graph.append({'@type': 'SoftwareApplication', '@id': SITE + '/#software', 'name': 'WorkDesk',
                      'applicationCategory': 'BusinessApplication', 'applicationSubCategory': 'HR and payroll software',
                      'operatingSystem': 'Web', 'url': SITE + '/', 'publisher': {'@id': SITE + '/#org'},
                      'description': 'HR, payroll and work management software: employee records, attendance, leave, payroll with fines and deductions, tasks, performance scorecards and reports.',
                      'featureList': ['Employee management', 'Attendance and shift tracking', 'Leave management',
                                      'Payroll with deductions and fines', 'Task and project management',
                                      'Performance scorecards', 'HR reports and analytics']})
    if page_type == 'BlogPosting':
        graph.append({'@type': 'BlogPosting', 'headline': meta['h1'], 'description': meta['description'],
                      'datePublished': meta['date'], 'dateModified': meta.get('modified', meta['date']),
                      'author': {'@type': 'Organization', 'name': 'WorkDesk team', 'url': SITE + '/about.html'},
                      'publisher': {'@id': SITE + '/#org'}, 'mainEntityOfPage': url, 'image': SITE + '/og-image.png',
                      'inLanguage': 'en'})
    else:
        graph.append({'@type': page_type, 'name': meta['title'], 'description': meta['description'], 'url': url,
                      'isPartOf': {'@id': SITE + '/#website'}, 'inLanguage': 'en'})
    if crumbs_ld:
        graph.append(crumbs_ld)
    return json.dumps({'@context': 'https://schema.org', '@graph': graph}, ensure_ascii=False, separators=(',', ':'))


def render(meta, preview):
    crumbs, crumbs_ld = crumbs_html(meta)
    body = meta['body']
    if meta.get('type') == 'BlogPosting':
        words = len(re.sub(r'<[^>]+>', ' ', body).split())
        meta['reading'] = max(1, round(words / 220))
        body = body.replace('{{reading}}', str(meta['reading']))
    noindex = meta.get('noindex') == 'yes'
    url = url_of(meta['slug'])
    head = f'''<title>{html.escape(meta['title'])}</title>
<meta name="description" content="{html.escape(meta['description'])}">
<link rel="canonical" href="{url}">
{'<meta name="robots" content="noindex, follow">' if noindex else '<meta name="robots" content="index, follow, max-image-preview:large">'}
<meta property="og:type" content="{'article' if meta.get('type') == 'BlogPosting' else 'website'}">
<meta property="og:site_name" content="WorkDesk">
<meta property="og:title" content="{html.escape(meta.get('og_title', meta['title']))}">
<meta property="og:description" content="{html.escape(meta['description'])}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{SITE}/og-image.png">
<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta property="og:locale" content="en_PK">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#16123A">
<link rel="icon" href="favicon.ico" sizes="48x48">
<link rel="icon" href="favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="apple-touch-icon.png">
<link rel="manifest" href="site.webmanifest">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Google+Sans+Flex:opsz,wght,ROND@8..144,400..700,0..100&display=swap">
<link rel="stylesheet" href="styles.css">
<script type="application/ld+json">{schema(meta, crumbs_ld)}</script>'''
    page = f'''{SPRITE}
<a class="skip" href="#main">Skip to content</a>
{header(meta.get('nav', ''), preview)}
<main id="main" class="page-{meta['slug']}">
{crumbs}
{body}
</main>
{footer()}
<script src="main.js" defer></script>'''
    page = expand(page, preview)
    head = expand(head, preview)
    if preview and meta['slug'] == 'index':
        # the preview viewer supplies its own document skeleton for the entry page
        return head.replace('<link rel="canonical"', '<meta name="claude:viewport-fit-sides" content="cover">\n<link rel="canonical"', 1) + '\n' + page
    return ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
            + head + '\n</head>\n<body>\n' + page + '\n</body>\n</html>\n')


def build(out, preview=False):
    if os.path.isdir(out):
        shutil.rmtree(out)
    os.makedirs(out)
    pages = [parse(os.path.join(SRC, 'pages', f)) for f in sorted(os.listdir(os.path.join(SRC, 'pages'))) if f.endswith('.html')]
    for meta in pages:
        open(os.path.join(out, meta['slug'] + '.html'), 'w', encoding='utf-8').write(render(meta, preview))
    for f in os.listdir(os.path.join(SRC, 'static')):
        shutil.copy(os.path.join(SRC, 'static', f), out)
    for f in ('styles.css', 'main.js'):
        shutil.copy(os.path.join(SRC, 'assets', f), out)
    # web manifest with relative icon paths so the site works from a sub-folder too
    json.dump({'name': 'WorkDesk', 'short_name': 'WorkDesk', 'start_url': './', 'display': 'standalone',
               'theme_color': '#16123A', 'background_color': '#16123A',
               'icons': [{'src': 'icon-192.png', 'sizes': '192x192', 'type': 'image/png'},
                         {'src': 'icon-512.png', 'sizes': '512x512', 'type': 'image/png'},
                         {'src': 'maskable-512.png', 'sizes': '512x512', 'type': 'image/png', 'purpose': 'maskable'}]},
              open(os.path.join(out, 'site.webmanifest'), 'w'), indent=2)
    indexable = [m for m in pages if m.get('noindex') != 'yes']
    sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for m in indexable:
        sm.append(f'  <url><loc>{url_of(m["slug"])}</loc><lastmod>{m.get("modified", m.get("date", CFG["updated"]))}</lastmod></url>')
    sm.append('</urlset>')
    open(os.path.join(out, 'sitemap.xml'), 'w').write('\n'.join(sm) + '\n')
    open(os.path.join(out, 'robots.txt'), 'w').write(f'User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n')
    llms = ['# WorkDesk', '', '> WorkDesk is HR, payroll and work management software for growing teams in Pakistan: employee records, attendance and shifts, leave, payroll with deductions and fines, tasks and projects, performance scorecards and reports.', '']
    for title, slugs in [('Product', ['features', 'people-management', 'attendance-leave-management', 'payroll-software', 'task-project-management', 'performance-scorecards', 'hr-reports-analytics', 'solutions', 'pricing']),
                         ('Guides', [m['slug'] for m in pages if m.get('type') == 'BlogPosting']),
                         ('Company', ['about', 'security', 'faq', 'contact'])]:
        llms.append(f'## {title}')
        for s in slugs:
            m = next((p for p in pages if p['slug'] == s), None)
            if m:
                llms.append(f'- [{m.get("h1", m["title"])}]({url_of(s)}): {m["description"]}')
        llms.append('')
    open(os.path.join(out, 'llms.txt'), 'w').write('\n'.join(llms))
    open(os.path.join(out, '.nojekyll'), 'w').write('')
    return pages


if __name__ == '__main__':
    pages = build(os.path.join(ROOT, 'docs'))
    if '--preview' in sys.argv:
        build(sys.argv[sys.argv.index('--preview') + 1], preview=True)
    print(f'built {len(pages)} pages')

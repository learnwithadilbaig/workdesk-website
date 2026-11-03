"""Builds workdesk-gtm-container.json, a Google Tag Manager container to import
(Admin > Import container). Run: python3 analytics/build_gtm.py

It reads the events that src/assets/track.js and src/assets/main.js push to the dataLayer.
If you add an event there, add it to EVENTS below and re-run this script.
"""
import json, os, re, time

HERE = os.path.dirname(os.path.abspath(__file__))
ACC, CON = '0', '0'

# ---------------------------------------------------------------- events
# GA4 event name -> (parameters read from the dataLayer, note shown on the tag in GTM)
EVENTS = {
    'generate_lead':      (['form_name', 'team_size', 'interest', 'topic', 'applicant_type'],
                           'KEY EVENT. Fires only after the form server confirms it received the form (demo, contact, partner, affiliate, careers, signup). Mark generate_lead as a key event in GA4.'),
    'lead_form_start':    (['form_name'], 'First time a visitor types in or clicks into a lead form on this page view. Once per form per page.'),
    'lead_form_error':    (['form_name', 'error_type', 'error_count'],
                           'A submit that did not become a lead. error_type: missing_fields, invalid_email, not_connected (no form endpoint set on the site), send_failed (server error).'),
    'cta_click':          (['cta_text', 'cta_type', 'cta_location', 'cta_url'],
                           'Every button and text link CTA. cta_type: book_demo, sign_up, log_in, pricing, contact, affiliate_apply, feature_page and more. cta_location: header, hero, cta_band, pricing_builder, footer or the section name.'),
    'navigation_click':   (['nav_area', 'link_text', 'link_url'], 'Menu, footer, breadcrumb, logo and in-article links. nav_area: header, header_menu, mobile_menu, footer, breadcrumb, content.'),
    'contact_click':      (['contact_method', 'link_location'], 'Email, phone and WhatsApp links. contact_method: email, phone, whatsapp.'),
    'quote_click':        (['modules', 'module_count', 'employee_count'], 'Get my quote on the pricing page, with the modules and headcount the visitor picked.'),
    'pricing_configure':  (['modules', 'module_count', 'employee_count'], 'Pricing builder settled for 1.5 s after a change (no event per slider tick).'),
    'calculator_use':     (['calculator', 'plan_term', 'plan_amount', 'commission'], 'Affiliate commission calculator settled for 1.5 s after a change.'),
    'faq_open':           (['faq_question', 'faq_section'], 'A question opened on the FAQ, help, pricing or feature pages. Closing sends nothing.'),
    'tab_select':         (['tab_name', 'tab_group'], 'Role tabs (Solutions), profile tabs (People), plan switch (affiliate calculator) and chart filters (Reports).'),
    'interactive_demo':   (['widget', 'link_location'], 'Clicks on the live product demos on the site: leave_approval, report_export.'),
    'menu_open':          (['menu_name'], 'Header mega menus and the mobile menu opened.'),
    'page_not_found':     (['missing_path'], 'A visitor reached the 404 page. Use it to find and fix broken links.'),
    'scroll_depth':       (['percent_scrolled'], 'Scroll depth 25, 50, 75%, once each per page, only after a real scroll. GA4 enhanced measurement adds "scroll" at 90%.'),
}
PARAM_NOTES = {
    'form_name': 'demo, contact, partner, affiliate, careers, signup', 'team_size': 'demo form team-size option',
    'interest': 'demo form module option', 'topic': 'contact form topic option', 'applicant_type': 'partner/affiliate type option',
}

# ---------------------------------------------------------------- helpers
_ids = {'tag': 0, 'trigger': 0, 'variable': 0, 'folder': 0}
def nid(kind):
    _ids[kind] += 1
    return str(_ids[kind])

T = lambda k, v: {'type': 'TEMPLATE', 'key': k, 'value': v}
BOOL = lambda k, v: {'type': 'BOOLEAN', 'key': k, 'value': 'true' if v else 'false'}
INT = lambda k, v: {'type': 'INTEGER', 'key': k, 'value': str(v)}
def table(key, rows):
    return {'type': 'LIST', 'key': key, 'list': [{'type': 'MAP', 'map': [T('parameter', p), T('parameterValue', v)]} for p, v in rows]}
def cond(kind, a, b):
    return {'type': kind, 'parameter': [T('arg0', a), T('arg1', b)]}
FP = str(int(time.time() * 1000))
def base(**kw):
    return {'accountId': ACC, 'containerId': CON, **kw, 'fingerprint': FP}

folders, tags, triggers, variables = [], [], [], []
def folder(name):
    f = base(folderId=nid('folder'), name=name); folders.append(f); return f['folderId']
F_SETUP = folder('1 Setup - consent, internal traffic, GA4 base')
F_EVENTS = folder('2 GA4 events')
F_DLV = folder('3 Data layer variables')

def variable(name, vtype, params, fid=F_SETUP, notes=''):
    v = base(variableId=nid('variable'), name=name, type=vtype, parameter=params, parentFolderId=fid, formatValue={})
    if notes: v['notes'] = notes
    variables.append(v); return name

def trigger(name, ttype, fid, **kw):
    t = base(triggerId=nid('trigger'), name=name, type=ttype, parentFolderId=fid, **kw)
    triggers.append(t); return t['triggerId']

def tag(name, ttype, params, firing, fid, notes='', needs=None):
    """needs: consent types the tag requires (Google's own tags handle consent mode themselves, so they leave this empty)."""
    consent = ({'consentStatus': 'NEEDED', 'consentType': {'type': 'LIST', 'list': [{'type': 'TEMPLATE', 'value': c} for c in needs]}}
               if needs else {'consentStatus': 'NOT_SET'})
    t = base(tagId=nid('tag'), name=name, type=ttype, parameter=params, firingTriggerId=firing,
             tagFiringOption='ONCE_PER_EVENT', monitoringMetadata={'type': 'MAP'},
             consentSettings=consent, parentFolderId=fid)
    if notes: t['notes'] = notes
    tags.append(t); return t['tagId']

# ---------------------------------------------------------------- setup variables
MID = variable('Const - GA4 Measurement ID', 'c', [T('value', 'G-XXXXXXXXXX')],
               notes='REPLACE with your GA4 Measurement ID (GA4 Admin > Data streams > your web stream).')
ALLOW = variable('Const - Allowed hostnames regex', 'c', [T('value', '.*')],
                 notes='Set to your live domain so test copies (Vercel, Hostinger temporary domain, GitHub Pages) never count. Example: ^(www\\.)?workdesk\\.pk$')
COOKIE = variable('Cookie - wd_internal', 'k', [BOOL('decodeCookie', False), T('name', 'wd_internal')])

REAL_JS = r'''function () {
  // Only count real visitors on the live website. Returns false for test copies, local builds and automated browsers.
  var h = (location.hostname || '').toLowerCase();
  var allow = {{Const - Allowed hostnames regex}};
  try { if (allow && !(new RegExp(allow, 'i')).test(h)) return false; } catch (e) {}
  if (!/^https?:$/.test(location.protocol)) return false;
  if (/^(localhost|0\.0\.0\.0|127\.|10\.|192\.168\.|172\.(1[6-9]|2\d|3[01])\.)|\.(local|localhost|test)$|^\[?::1\]?$/.test(h)) return false;
  if (/^\d{1,3}(\.\d{1,3}){3}$/.test(h)) return false;
  if (/-git-[a-z0-9-]+\.vercel\.app$|-(?=[a-z]*\d)[a-z0-9]{9}-[a-z0-9-]+\.vercel\.app$/.test(h)) return false; // Vercel preview deployments
  if (/\.translate\.goog$|googleusercontent\.com$|bingj\.com$|archive\.org$/.test(h)) return false;       // translated and cached copies
  if (navigator.webdriver) return false;                                                                   // automated browsers (Playwright, Selenium)
  if (/(^|[^a-z])bot\b|bot\/|crawl|spider|headlesschrome|lighthouse|ptst|gtmetrix|pingdom|uptimerobot|statuscake/i.test(navigator.userAgent || '')) return false;
  return true;
}'''
REAL = variable('JS - Is real traffic', 'jsm', [T('javascript', REAL_JS)],
                notes='Every GA4 tag fires only when this is true. Edit the hostname constant rather than this code.')
TTYPE = variable('JS - Traffic type', 'jsm', [T('javascript', "function () {\n  // 'internal' for browsers marked with ?wd_internal=1, so the GA4 Internal traffic filter removes your own team's visits\n  return {{Cookie - wd_internal}} === '1' ? 'internal' : undefined;\n}")])

# ---------------------------------------------------------------- data layer variables
def dlv(key):
    return variable(f'DLV - {key}', 'v', [INT('dataLayerVersion', 2), BOOL('setDefaultValue', False), T('name', key)], fid=F_DLV,
                    notes=PARAM_NOTES.get(key, ''))
dlv('content_group')
for params, _ in EVENTS.values():
    for p in params:
        if f'DLV - {p}' not in [v['name'] for v in variables]:
            dlv(p)

# ---------------------------------------------------------------- triggers
REAL_FILTER = [cond('EQUALS', '{{JS - Is real traffic}}', 'true')]
CONSENT_INIT = '2147479572'  # built-in "Consent Initialization - All Pages"
INIT_REAL = trigger('Init - Real traffic', 'INIT', F_SETUP, filter=REAL_FILTER)

# ---------------------------------------------------------------- setup tags
CONSENT_HTML = '''<script>
  // Consent mode v2 defaults. The site has no cookie banner yet, so:
  // EEA, UK and Switzerland: storage off (GA4 sends cookieless pings only, which is what the law there expects without consent).
  // Everywhere else, including Pakistan: analytics on.
  window.dataLayer = window.dataLayer || [];
  function gtag(){ dataLayer.push(arguments); }
  gtag('consent', 'default', {
    ad_storage: 'denied', ad_user_data: 'denied', ad_personalization: 'denied', analytics_storage: 'denied',
    region: ['AT','BE','BG','HR','CY','CZ','DK','EE','FI','FR','DE','GR','HU','IS','IE','IT','LV','LI','LT','LU','MT','NL','NO','PL','PT','RO','SK','SI','ES','SE','GB','CH'],
    wait_for_update: 500
  });
  gtag('consent', 'default', {
    ad_storage: 'granted', ad_user_data: 'granted', ad_personalization: 'granted', analytics_storage: 'granted',
    functionality_storage: 'granted', security_storage: 'granted'
  });
  gtag('set', 'ads_data_redaction', true);
</script>'''
tag('Consent - Defaults (consent mode v2)', 'html', [T('html', CONSENT_HTML), BOOL('supportDocumentWrite', False)], [CONSENT_INIT], F_SETUP,
    notes='Runs before everything else. If you add a cookie banner later, replace this with the banner\'s own GTM template.')

INTERNAL_HTML = '''<script>
  // Visit any page with ?wd_internal=1 once on each browser your team uses; ?wd_internal=0 removes the mark.
  (function () {
    var m = /[?&]wd_internal=(1|0)(&|$)/.exec(location.search);
    if (!m) return;
    var secure = location.protocol === 'https:' ? '; Secure' : '';
    document.cookie = m[1] === '1'
      ? 'wd_internal=1; path=/; max-age=31536000; SameSite=Lax' + secure
      : 'wd_internal=; path=/; max-age=0; SameSite=Lax' + secure;
  })();
</script>'''
tag('Util - Mark internal visitors (wd_internal cookie)', 'html', [T('html', INTERNAL_HTML), BOOL('supportDocumentWrite', False)], [CONSENT_INIT], F_SETUP,
    notes='Sets a first-party cookie so your own visits carry traffic_type=internal and can be filtered out in GA4.')

tag('GA4 - Google tag', 'googtag', [
    T('tagId', '{{Const - GA4 Measurement ID}}'),
    table('configSettingsTable', [('content_group', '{{DLV - content_group}}'), ('traffic_type', '{{JS - Traffic type}}')]),
], [INIT_REAL], F_SETUP, notes='Sends the page_view (once per page load) and the content group: Home, Product, Solutions, Pricing, Conversion, Company, Blog, Support, Legal, Error.')

# ---------------------------------------------------------------- event tags
def ga4_event(name, params, firing, notes):
    return tag(f'GA4 - {name}', 'gaawe', [
        BOOL('sendEcommerceData', False),
        T('eventName', name),
        T('measurementIdOverride', '{{Const - GA4 Measurement ID}}'),
        table('eventSettingsTable', params),
    ], [firing], F_EVENTS, notes=notes)

for ev, (params, notes) in EVENTS.items():
    trig = trigger(f'CE - {ev}', 'CUSTOM_EVENT', F_EVENTS, customEventFilter=[cond('EQUALS', '{{_event}}', ev)], filter=REAL_FILTER)
    ga4_event(ev, [(p, '{{DLV - %s}}' % p) for p in params], trig, notes)

# ================================================================ ad platforms + Clarity
# Each platform stays silent until its ID is pasted into its constant (the code checks the ID's format),
# so nothing is ever sent with a placeholder. None of them get your team's visits or careers applications.
F_SHARED = folder('4 Ads and Clarity - IDs, shared triggers')
F_META, F_TT, F_GADS, F_CLAR = folder('5 Meta Pixel'), folder('6 TikTok Pixel'), folder('7 Google Ads'), folder('8 Microsoft Clarity')

variable('Const - Meta Pixel ID', 'c', [T('value', 'PASTE META PIXEL ID')], fid=F_SHARED,
         notes='Meta Events Manager > Data sources > your pixel > Settings. Numbers only, e.g. 1234567890123456.')
variable('Const - TikTok Pixel ID', 'c', [T('value', 'PASTE TIKTOK PIXEL ID')], fid=F_SHARED,
         notes='TikTok Ads Manager > Tools > Events > Web events > your pixel. Looks like CABCD1234EFGH5678IJK.')
variable('Const - Clarity Project ID', 'c', [T('value', 'PASTE CLARITY PROJECT ID')], fid=F_SHARED,
         notes='clarity.microsoft.com > your project > Settings > Overview. About 10 lowercase letters and numbers.')
variable('Const - Google Ads ID', 'c', [T('value', 'PASTE GOOGLE ADS ID')], fid=F_SHARED,
         notes='Google Ads > Goals > Conversions > your lead conversion > Tag setup > Use Google Tag Manager: the Conversion ID, numbers only (no "AW-").')
variable('Const - Google Ads lead label', 'c', [T('value', 'PASTE LEAD CONVERSION LABEL')], fid=F_SHARED,
         notes='Same screen as the Conversion ID: the Conversion label, e.g. AbC-D_efG-h12_34-567.')
variable('JS - Ad tracking allowed', 'jsm', [T('javascript', '''function () {
  // Real visitors on the live site, minus your own team. Ad platforms and Clarity have no internal-traffic filter, so your team is kept out here.
  return {{JS - Is real traffic}} === true && {{Cookie - wd_internal}} !== '1';
}''')], fid=F_SHARED)
variable('JS - Lead group', 'jsm', [T('javascript', '''function () {
  // customer: demo, contact, signup. partner: partner and affiliate applications.
  // other: careers. Job applicants are not customers, so ad platforms never see them and can't learn to find more of them.
  var f = {{DLV - form_name}};
  if (/^(demo|contact|signup)$/.test(f)) return 'customer';
  if (/^(partner|affiliate)$/.test(f)) return 'partner';
  return 'other';
}''')], fid=F_SHARED)

ADS = [cond('EQUALS', '{{JS - Ad tracking allowed}}', 'true')]
CE = lambda ev: [cond('EQUALS', '{{_event}}', ev)]
GADS_READY = [cond('MATCH_REGEX', '{{Const - Google Ads ID}}', r'^\d{6,15}$')]
INIT_ADS = trigger('Init - Real visitors, not team', 'INIT', F_SHARED, filter=ADS)
LEAD_CUST = trigger('CE - customer lead (demo, contact, signup)', 'CUSTOM_EVENT', F_SHARED, customEventFilter=CE('generate_lead'),
                    filter=ADS + [cond('EQUALS', '{{JS - Lead group}}', 'customer')])
LEAD_PART = trigger('CE - partner or affiliate application', 'CUSTOM_EVENT', F_SHARED, customEventFilter=CE('generate_lead'),
                    filter=ADS + [cond('EQUALS', '{{JS - Lead group}}', 'partner')])
CONTACT = trigger('CE - contact click (ads)', 'CUSTOM_EVENT', F_SHARED, customEventFilter=CE('contact_click'), filter=ADS)
QUOTE = trigger('CE - quote click (ads)', 'CUSTOM_EVENT', F_SHARED, customEventFilter=CE('quote_click'), filter=ADS)
CLAR_EV = trigger('CE - Clarity key moments', 'CUSTOM_EVENT', F_SHARED,
                  customEventFilter=[cond('MATCH_REGEX', '{{_event}}', '^(generate_lead|lead_form_error|quote_click|calculator_use|page_not_found)$')], filter=ADS)
INIT_GADS = trigger('Init - Google Ads ready', 'INIT', F_SHARED, filter=ADS + GADS_READY)
LEAD_GADS = trigger('CE - customer lead (Google Ads ready)', 'CUSTOM_EVENT', F_SHARED, customEventFilter=CE('generate_lead'),
                    filter=ADS + GADS_READY + [cond('EQUALS', '{{JS - Lead group}}', 'customer'),
                                               cond('MATCH_REGEX', '{{Const - Google Ads lead label}}', r'^[A-Za-z0-9_-]{6,}$')])

def html(name, code, firing, fid, needs, notes=''):
    return tag(name, 'html', [T('html', code), BOOL('supportDocumentWrite', False)], [firing], fid, notes=notes, needs=needs)

# ---- Meta Pixel (needs ad_storage consent)
html('Meta - Pixel base and PageView', '''<script>
  // Meta Pixel base code. Does nothing until "Const - Meta Pixel ID" holds a real ID.
  (function () {
    var id = String({{Const - Meta Pixel ID}});
    if (!/^\\d{8,20}$/.test(id)) return;
    !function(f,b,e,v,n,t,s){if(f.fbq)return;n=f.fbq=function(){n.callMethod?
    n.callMethod.apply(n,arguments):n.queue.push(arguments)};
    if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';
    n.queue=[];t=b.createElement(e);t.async=!0;
    t.src=v;s=b.getElementsByTagName(e)[0];
    s.parentNode.insertBefore(t,s)}(window, document,'script',
    'https://connect.facebook.net/en_US/fbevents.js');
    fbq('init', id);
    fbq('track', 'PageView');
  })();
</script>''', INIT_ADS, F_META, ['ad_storage'], 'One PageView per page load, real visitors only.')
html('Meta - Lead', '''<script>
  if (window.fbq) fbq('track', 'Lead', { content_name: {{DLV - form_name}}, content_category: 'website form' });
</script>''', LEAD_CUST, F_META, ['ad_storage'], 'Demo, contact and signup forms accepted by the server. Optimise lead campaigns for this.')
html('Meta - SubmitApplication', '''<script>
  if (window.fbq) fbq('track', 'SubmitApplication', { content_name: {{DLV - form_name}} });
</script>''', LEAD_PART, F_META, ['ad_storage'], 'Partner and affiliate applications, kept separate so customer campaigns are not optimised for partners.')
html('Meta - Contact', '''<script>
  if (window.fbq) fbq('track', 'Contact', { content_name: {{DLV - contact_method}} });
</script>''', CONTACT, F_META, ['ad_storage'])
html('Meta - CustomizeProduct (quote)', '''<script>
  if (window.fbq) fbq('track', 'CustomizeProduct', { content_name: 'pricing quote', num_items: {{DLV - module_count}} });
</script>''', QUOTE, F_META, ['ad_storage'], 'Get my quote on the pricing page.')

# ---- TikTok Pixel (needs ad_storage consent)
html('TikTok - Pixel base and page', '''<script>
  // TikTok Pixel base code. Does nothing until "Const - TikTok Pixel ID" holds a real ID.
  (function () {
    var id = String({{Const - TikTok Pixel ID}});
    if (!/^[A-Z0-9]{10,30}$/.test(id)) return;
    !function (w, d, t) {
      w.TiktokAnalyticsObject=t;var ttq=w[t]=w[t]||[];ttq.methods=["page","track","identify","instances","debug","on","off","once","ready","alias","group","enableCookie","disableCookie","holdConsent","revokeConsent","grantConsent"],ttq.setAndDefer=function(t,e){t[e]=function(){t.push([e].concat(Array.prototype.slice.call(arguments,0)))}};for(var i=0;i<ttq.methods.length;i++)ttq.setAndDefer(ttq,ttq.methods[i]);ttq.instance=function(t){for(var e=ttq._i[t]||[],n=0;n<ttq.methods.length;n++)ttq.setAndDefer(e,ttq.methods[n]);return e},ttq.load=function(e,n){var r="https://analytics.tiktok.com/i18n/pixel/events.js",o=n&&n.partner;ttq._i=ttq._i||{},ttq._i[e]=[],ttq._i[e]._u=r,ttq._t=ttq._t||{},ttq._t[e]=+new Date,ttq._o=ttq._o||{},ttq._o[e]=n||{};n=document.createElement("script");n.type="text/javascript",n.async=!0,n.src=r+"?sdkid="+e+"&lib="+t;e=document.getElementsByTagName("script")[0];e.parentNode.insertBefore(n,e)};
      ttq.load(id);
      ttq.page();
    }(window, document, 'ttq');
  })();
</script>''', INIT_ADS, F_TT, ['ad_storage'], 'One page event per page load, real visitors only.')
html('TikTok - SubmitForm (lead)', '''<script>
  if (window.ttq) ttq.track('SubmitForm', { content_name: {{DLV - form_name}} });
</script>''', LEAD_CUST, F_TT, ['ad_storage'], 'Demo, contact and signup forms accepted by the server. Optimise lead campaigns for this.')
html('TikTok - SubmitApplication', '''<script>
  if (window.ttq) ttq.track('SubmitApplication', { content_name: {{DLV - form_name}} });
</script>''', LEAD_PART, F_TT, ['ad_storage'])
html('TikTok - Contact', '''<script>
  if (window.ttq) ttq.track('Contact', { content_name: {{DLV - contact_method}} });
</script>''', CONTACT, F_TT, ['ad_storage'])

# ---- Google Ads (Google's own tags follow consent mode by themselves)
tag('Google Ads - Google tag (audiences)', 'googtag', [T('tagId', 'AW-{{Const - Google Ads ID}}')], [INIT_GADS], F_GADS,
    notes='Builds remarketing audiences from real visitors. Fires only once "Const - Google Ads ID" is filled in.')
tag('Google Ads - Conversion Linker', 'gclidw', [BOOL('enableCrossDomain', False), BOOL('enableUrlPassthrough', False), BOOL('enableCookieOverrides', False)],
    [INIT_GADS], F_GADS, notes='Stores the ad click ID so a lead can be credited to the ad that brought the visitor.')
tag('Google Ads - Lead conversion', 'awct', [
    BOOL('enableConversionLinker', True), T('conversionCookiePrefix', '_gcl'),
    T('conversionId', '{{Const - Google Ads ID}}'), T('conversionLabel', '{{Const - Google Ads lead label}}'), BOOL('rdp', False),
], [LEAD_GADS], F_GADS, notes='Demo, contact and signup forms accepted by the server. Fires only once both Google Ads constants are filled in.')

# ---- Microsoft Clarity (needs analytics_storage consent)
html('Clarity - Load', '''<script>
  // Microsoft Clarity. Does nothing until "Const - Clarity Project ID" holds a real ID.
  (function () {
    var id = String({{Const - Clarity Project ID}});
    if (!/^[a-z0-9]{6,15}$/.test(id)) return;
    (function(c,l,a,r,i,t,y){
      c[a]=c[a]||function(){(c[a].q=c[a].q||[]).push(arguments)};
      t=l.createElement(r);t.async=1;t.src="https://www.clarity.ms/tag/"+i;
      y=l.getElementsByTagName(r)[0];y.parentNode.insertBefore(t,y);
    })(window, document, "clarity", "script", id);
    var g = {{DLV - content_group}};
    if (g) window.clarity('set', 'content_group', g);
  })();
</script>''', INIT_ADS, F_CLAR, ['analytics_storage'], 'Heatmaps and session recordings of real visitors, tagged with the page content group.')
html('Clarity - Tag key moments', '''<script>
  // Lets you filter Clarity recordings by what happened: generate_lead, lead_form_error, quote_click, calculator_use, page_not_found.
  if (window.clarity) {
    window.clarity('event', {{Event}});
    if ({{Event}} === 'generate_lead') { window.clarity('set', 'lead_form', {{DLV - form_name}}); window.clarity('upgrade', 'lead'); }
    if ({{Event}} === 'lead_form_error') window.clarity('set', 'form_error', {{DLV - error_type}});
  }
</script>''', CLAR_EV, F_CLAR, ['analytics_storage'], '"upgrade" keeps every recording that ends in a lead.')

# ---------------------------------------------------------------- container
BUILTINS = [('PAGE_URL', 'Page URL'), ('PAGE_HOSTNAME', 'Page Hostname'), ('PAGE_PATH', 'Page Path'), ('REFERRER', 'Referrer'),
            ('EVENT', 'Event')]
container = {
    'exportFormatVersion': 2,
    'exportTime': time.strftime('%Y-%m-%d %H:%M:%S'),
    'containerVersion': {
        'path': f'accounts/{ACC}/containers/{CON}/versions/0', 'accountId': ACC, 'containerId': CON, 'containerVersionId': '0',
        'name': 'WorkDesk website tracking v2',
        'description': 'GA4, Meta Pixel, TikTok Pixel, Google Ads and Microsoft Clarity for the WorkDesk website. Real-traffic filter, consent mode v2 defaults, internal traffic kept out, page content groups, leads counted only on confirmed form submission, every CTA, menu, tab, FAQ, calculator and scroll depth.',
        'container': {
            'path': f'accounts/{ACC}/containers/{CON}', 'accountId': ACC, 'containerId': CON, 'name': 'WorkDesk website',
            'publicId': 'GTM-XXXXXXX', 'usageContext': ['WEB'], 'fingerprint': FP, 'tagManagerUrl': 'https://tagmanager.google.com/',
            'features': {k: True for k in ['supportUserPermissions', 'supportEnvironments', 'supportWorkspaces', 'supportBuiltInVariables',
                                            'supportFolders', 'supportTags', 'supportTemplates', 'supportTriggers', 'supportVariables',
                                            'supportVersions', 'supportZones']},
            'tagIds': ['GTM-XXXXXXX'],
        },
        'tag': tags, 'trigger': triggers, 'variable': variables, 'folder': folders,
        'builtInVariable': [{'accountId': ACC, 'containerId': CON, 'type': t, 'name': n} for t, n in BUILTINS],
        'fingerprint': FP, 'tagManagerUrl': 'https://tagmanager.google.com/',
    },
}

# ---------------------------------------------------------------- self-checks
names = {v['name'] for v in variables} | {n for _, n in BUILTINS} | {'_event'}
refs = set(re.findall(r'\{\{([^}]+)\}\}', json.dumps(container)))
missing = refs - names
assert not missing, f'undefined variables: {missing}'
# GTM's importer rejects some characters in names (":" for one), so names stick to a plain, safe set.
SAFE = re.compile(r'^[A-Za-z0-9 ._,()\-]+$')
unsafe = [x['name'] for k in ('tag', 'trigger', 'variable', 'folder') for x in container['containerVersion'][k] if not SAFE.match(x['name'])]
unsafe += [n for n in (container['containerVersion']['name'], container['containerVersion']['container']['name']) if not SAFE.match(n)]
assert not unsafe, f'names with characters GTM may reject: {unsafe}'
for kind, key in [('tag', 'tagId'), ('trigger', 'triggerId'), ('variable', 'variableId')]:
    ids = [x[key] for x in container['containerVersion'][kind]]
    assert len(ids) == len(set(ids)), f'duplicate {kind} ids'
trig_ids = {t['triggerId'] for t in triggers} | {CONSENT_INIT}
for t in tags:
    assert set(t['firingTriggerId']) <= trig_ids, f"{t['name']} fires on an unknown trigger"
used = {p for params, _ in EVENTS.values() for p in params}
for p in used:
    assert f'DLV - {p}' in names

out = os.path.join(HERE, 'workdesk-gtm-container.json')
json.dump(container, open(out, 'w'), indent=2, ensure_ascii=False)
print(f'{out}\n{len(tags)} tags, {len(triggers)} triggers, {len(variables)} variables, {len(folders)} folders; all references resolve')

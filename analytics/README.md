# WorkDesk website tracking: GTM, GA4, Meta Pixel, TikTok Pixel, Google Ads, Microsoft Clarity

- `workdesk-gtm-container.json`: the Google Tag Manager container to import
- `build_gtm.py`: regenerates that file (edit `EVENTS`, then run `python3 analytics/build_gtm.py`)
- On the site, `src/assets/track.js` (clicks, menus, tabs, FAQ, calculators, scroll) and the form code in `src/assets/main.js` push the events. `src/build.py` adds your GTM install code (`gtm_id` in `src/config.json`, currently **GTM-PBFVZPXM**) to every page.

**Don't paste any pixel or Clarity code into the website.** GTM loads all of them. A second copy on the site would count every visit and lead twice.

## 1. Import the container

1. In Tag Manager open container **GTM-PBFVZPXM** and go to *Admin → Import container*.
2. Choose `workdesk-gtm-container.json` and pick a **new** workspace.
3. If the container is empty, choose **Overwrite**. If it already has tags, choose **Merge → Rename conflicting**.

## 2. Paste your IDs (GTM → *Variables*)

Every platform stays switched off until its ID is pasted in, so you can fill them in one at a time.

| Variable | Where to find it | Looks like |
|---|---|---|
| `Const - GA4 Measurement ID` | GA4 → Admin → Data streams → your web stream | `G-AB12CD34EF` |
| `Const - Allowed hostnames regex` | Your live domain | `^(www\.)?workdesk\.pk$` |
| `Const - Meta Pixel ID` | Meta Events Manager → Data sources → your pixel → Settings | `1234567890123456` |
| `Const - TikTok Pixel ID` | TikTok Ads Manager → Tools → Events → Web events → your pixel | `CABCD1234EFGH5678IJK` |
| `Const - Google Ads ID` | Google Ads → Goals → Conversions → your lead action → *Tag setup* → *Use Google Tag Manager* → **Conversion ID** (numbers only, no `AW-`) | `123456789` |
| `Const - Google Ads lead label` | Same screen → **Conversion label** | `AbC-D_efG-h12_34` |
| `Const - Clarity Project ID` | clarity.microsoft.com → your project → *Settings → Overview* | `ab12cd34ef` |

When you create each pixel or project, skip the platform's own install steps (base code, partner integrations) and just copy the ID.
- **TikTok:** choose *Manual setup*.
- **Google Ads:** create the conversion action with the goal *Submit lead form*, then pick *Use Google Tag Manager*.
- **Clarity:** skip the "install tracking code" step.

## 3. Test, then publish

1. Click **Preview** in GTM and open your site.
2. The left panel should list **Consent Initialization**, **Initialization** and **Container Loaded** on every page.
   - If *Initialization* or *Container Loaded* is missing, the install code isn't starting GTM properly. Switch `src/build.py` back to Google's classic install snippet. It's a two-line change.
3. On *Initialization* you should see these tags fire:
   - `GA4 - Google tag`
   - `Meta - Pixel base and PageView`
   - `TikTok - Pixel base and page`
   - `Google Ads - Google tag (audiences)` and `Conversion Linker`
   - `Clarity - Load`
4. Click a button: `GA4 - cta_click` fires.
5. Cross-check each platform:
   - **Meta:** Events Manager → *Test events*
   - **TikTok:** Events Manager → *Test events*
   - **GA4:** *DebugView*
   - **Clarity:** recordings appear within about two hours
6. Click **Submit** in GTM to publish.
7. Deploy the website so the install code is live.

## 4. Platform settings for clean data

**GA4** (*Admin*):
- *Enhanced measurement*: turn **off "Form interactions"**. It counts failed submits; `generate_lead` replaces it.
- *Data filters*: set Internal Traffic and Developer Traffic to **Active**.
- *Unwanted referrals*: add your app's domain and, later, your payment gateway.
- *Configure your domains*: add the website and app domains.
- *Data retention*: 14 months.
- Mark **`generate_lead`** as a key event.
- Register the custom definitions listed at the end of this file.

**Google Ads:**
- Use the `Google Ads - Lead conversion` tag as the **primary** lead conversion.
- If you also import GA4's `generate_lead` into Google Ads, set that import to **secondary**, or each lead counts twice.
- Link Google Ads with GA4.

**Meta:**
- Verify your domain in Business Settings → *Brand safety → Domains*.
- Optimise lead campaigns for **Lead**.
- *Automatic advanced matching* (it sends hashed form details) is optional. If you turn it on, say so in your privacy policy.

**TikTok:** optimise lead campaigns for **SubmitForm**.

**Clarity:**
- Keep masking on *Balanced* or *Strict*, so typed form answers are never recorded.
- Optionally connect GA4 under *Settings → Setup*.

**Privacy policy:** it must list Google Analytics, Google Ads, Meta Pixel, TikTok Pixel and Microsoft Clarity (session recordings). The current policy is still a template.

## What each platform receives

| Website moment | GA4 | Meta | TikTok | Google Ads | Clarity |
|---|---|---|---|---|---|
| Page view | `page_view` + content group | PageView | page | audiences (Google tag) | recording + content group |
| Demo, contact or signup form **accepted by the server** | `generate_lead` (key event) | **Lead** | **SubmitForm** | **Lead conversion** | event + recording kept |
| Partner or affiliate application accepted | `generate_lead` | SubmitApplication | SubmitApplication | – | event + recording kept |
| Careers application accepted | `generate_lead` | – | – | – | event |
| Email, phone or WhatsApp link | `contact_click` | Contact | Contact | – | – |
| "Get my quote" | `quote_click` | CustomizeProduct | – | – | event |
| Failed submit | `lead_form_error` | – | – | – | event + error type |
| Buttons, menus, tabs, FAQ, calculators, scroll, 404 | yes (see below) | – | – | – | calculator and 404 as events |

Careers applicants are kept away from ad platforms on purpose: they aren't customers, and ad platforms would learn to find more job seekers. Partner applications are a separate event so customer campaigns aren't optimised for partners.

## What makes the numbers real

- **Leads count only when your form server confirms it received the form.** Clicks, failed validation and server errors never count. Failed attempts are recorded as `lead_form_error` with the reason.
- **Only the live site counts.** Every tag checks `JS - Is real traffic`, which skips:
  - other hostnames
  - localhost and office IPs
  - Vercel preview links
  - translated or cached copies
  - automated browsers (Playwright, Selenium, Lighthouse, PageSpeed)
  - uptime monitors and bots
- **Your team is kept out.** Open `https://yourdomain/?wd_internal=1` once on each team phone and laptop. GA4 then filters those visits, and Meta, TikTok, Google Ads and Clarity never load for those browsers at all (`?wd_internal=0` undoes it).
- **Placeholders never send.** Each pixel's code checks that its ID has the right format before loading.
- **One page view per page load. Inputs count once.** Sliders and calculators report after the visitor stops (1.5 s). Scroll depth counts each mark once, only after a real scroll.
- **No personal data in GA4.** Names, emails, phone numbers, company names and typed answers never enter the data layer. Only fixed dropdown choices are sent.
- **Consent mode v2.** There's no cookie banner yet, so visitors in the EEA, UK and Switzerland default to "denied":
  - GA4 and Google Ads send cookieless pings only.
  - Meta, TikTok and Clarity don't load at all (they're marked *Additional consent required*).
  - Everyone else, including Pakistan, is measured normally.
  - If you add a cookie banner, replace the `Consent - Defaults` tag with the banner's own GTM template.

## GA4 events

| Event | When it fires | Parameters |
|---|---|---|
| `page_view` | Each page load | `content_group`, `traffic_type` |
| **`generate_lead`** | Form accepted by the server: demo, contact, partner, affiliate, careers, signup | `form_name`, `team_size`, `interest`, `topic`, `applicant_type` |
| `lead_form_start` | First click or keystroke in a lead form | `form_name` |
| `lead_form_error` | A submit that didn't become a lead | `form_name`, `error_type` (missing_fields, invalid_email, not_connected, send_failed), `error_count` |
| `cta_click` | Any button or text-link CTA | `cta_text`, `cta_type`, `cta_location`, `cta_url` |
| `navigation_click` | Menu, mega menu, mobile menu, footer, breadcrumb, logo, in-article links | `nav_area`, `link_text`, `link_url` |
| `contact_click` | Email, phone and WhatsApp links | `contact_method`, `link_location` |
| `quote_click` | "Get my quote" on Pricing | `modules`, `module_count`, `employee_count` |
| `pricing_configure` | Pricing builder changed (once settled) | `modules`, `module_count`, `employee_count` |
| `calculator_use` | Affiliate commission calculator (once settled) | `calculator`, `plan_term`, `plan_amount`, `commission` |
| `faq_open` | A question opened | `faq_question`, `faq_section` |
| `tab_select` | Role tabs, profile tabs, plan switch, chart filters | `tab_name`, `tab_group` |
| `interactive_demo` | Live product demos on the site | `widget`, `link_location` |
| `menu_open` | Mega menu or mobile menu opened | `menu_name` |
| `scroll_depth` | 25, 50, 75% (GA4 adds `scroll` at 90%) | `percent_scrolled` |
| `page_not_found` | The 404 page | `missing_path` |

**Register in GA4 → *Custom definitions*:**

- **Custom dimensions (scope: Event):** `cta_text`, `cta_type`, `cta_location`, `cta_url`, `nav_area`, `contact_method`, `link_location`, `form_name`, `error_type`, `team_size`, `interest`, `topic`, `applicant_type`, `faq_question`, `faq_section`, `tab_name`, `tab_group`, `modules`, `plan_term`, `calculator`, `widget`, `menu_name`, `missing_path`, `percent_scrolled`
- **Custom metrics:**
  - standard unit: `employee_count`, `module_count`, `error_count`
  - currency unit: `plan_amount`, `commission`

## Still blocking real data on the site

- **`form_endpoint` is empty in `src/config.json`.** No form can send yet, so no platform will ever receive a lead. Until it's connected, every attempt shows in GA4 as `lead_form_error` with `error_type = not_connected`.
- **`site_url` still points to GitHub Pages.** Set it to your real domain.
- **`contact_email` is a placeholder.** There's no email link yet for `contact_click` to count.

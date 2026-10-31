# WorkDesk website

Marketing website for WorkDesk, HR, payroll and work management software for growing businesses in Pakistan.

It's a plain static site: no framework, no npm install. A small Python script turns the page files in `src/` into finished HTML in `docs/`, which any static host can serve.

## Structure

```
src/
  build.py          builds the site into docs/
  config.json       site URL, contact details, app links, form endpoint
  pages/            one file per page (27 pages)
  partials/         shared sections: modules grid, module hub, ticker, CTA band
  assets/           styles.css, main.js, logo paths
  static/           favicons, app icons, social share image
docs/               the built site (this is what gets deployed)
```

Each page starts with a short header that sets its SEO title, meta description, breadcrumb and schema type:

```html
<!--
title: Payroll Software in Pakistan | WorkDesk
description: Run payroll from real attendance. ...
nav: products
crumbs: Features=features.html; Payroll & Fines
-->
```

## Build

```bash
python3 src/build.py
```

This writes every page to `docs/` along with `sitemap.xml`, `robots.txt`, `llms.txt` and `site.webmanifest`. Commit `docs/` after building.

To preview locally:

```bash
cd docs && python3 -m http.server 8000
# open http://localhost:8000
```

## Deploy

**GitHub Pages:** in the repository, open Settings, then Pages. Under "Build and deployment", choose "Deploy from a branch", branch `main`, folder `/docs`. The site will be served at `https://learnwithadilbaig.github.io/workdesk-website/`.

**Netlify, Vercel or Cloudflare Pages:** set the publish directory to `docs` and leave the build command empty (or use `python3 src/build.py`).

**Custom domain:** change `site_url` in `src/config.json` to the real domain (for example `https://www.yourdomain.pk`), rebuild, and commit. Canonical URLs, the sitemap and social tags all use this value.

## Before launch

Settings in `src/config.json`:

- [ ] `site_url`: your real domain
- [ ] `contact_email`: replace the placeholder `hello@workdesk.example`
- [ ] `phone`, `whatsapp`, `address`: shown in the footer when set
- [ ] `app_login_url`, `app_signup_url`: "Log in" and "Sign up" then go straight to the app
- [ ] `form_endpoint`: a form service URL (Formspree, Basin, Getform, or your own API). Until it's set, forms show a "not connected yet" note instead of sending.
- [ ] `social`: links to your LinkedIn, Facebook, Instagram, X and YouTube pages

Content to check:

- [ ] **Product claims.** The copy describes features such as fines and deductions, income tax, provident fund and EOBI components, importing attendance machine files, Excel/PDF exports, the mobile app, notifications, multiple branches, activity history and backups. Remove or adjust anything WorkDesk doesn't do yet.
- [ ] **Commitments.** Free standard onboarding, reply times ("within one working day"), and the parallel-payroll support described on several pages.
- [ ] **About, Careers and Partners.** Add your real story, team and partner terms. Real names and faces help both visitors and search rankings.
- [ ] **Privacy policy and terms.** These are templates with `[placeholders]` and a visible review notice. Have a lawyer complete them, then remove the notice.
- [ ] **Sample data.** Names and figures inside the product previews are fictional and labelled "Sample data". Replace them with real screenshots when you have them.
- [ ] **Social proof.** Add customer logos, testimonials and results only once they're real and approved.

## SEO notes

- Each page has a unique title (60 characters or fewer), meta description, canonical URL, Open Graph tags and one H1.
- Structured data (JSON-LD): Organization, WebSite, SoftwareApplication, BreadcrumbList, BlogPosting for articles, and AboutPage/ContactPage where relevant. FAQ sections are plain HTML with no FAQPage markup, because Google no longer shows FAQ rich results.
- `sitemap.xml` lists every indexable page. Log-in, sign-up and 404 are `noindex`.
- `llms.txt` gives AI search tools a short summary of the site with links.
- Target keywords include: HR software in Pakistan, payroll software in Pakistan, attendance management system, leave management, employee management software, performance management, HR reports.
- After launch: verify the site in Google Search Console, submit `sitemap.xml`, and keep adding guides to the blog.

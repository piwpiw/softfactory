# Bohemian Studio WordPress System

## Scope

This repo now includes the first production lane for `Bohemian Studio` WordPress operations:

- WordPress site registration and verification
- research-to-publish pipeline orchestration
- quality audit endpoint
- WordPress operations desk UI
- 10-minute candidate cadence with gated publication

## Runtime Surface

Backend endpoints:

- `GET /api/sns/wordpress/sites`
- `POST /api/sns/wordpress/sites`
- `POST /api/sns/wordpress/sites/:id/test`
- `GET /api/sns/wordpress/templates`
- `GET /api/sns/wordpress/runs`
- `POST /api/sns/wordpress/content-audit`
- `GET /api/sns/wordpress/posts`
- `POST /api/sns/wordpress/posts`

Frontend entry points:

- `web/sns-auto/wordpress.html`
- `web/sns-auto/index.html`
- `web/index.html`

## Content Contract

The pipeline is locked to:

1. Official-source collection
2. Source notes
3. Brief generation
4. Contract validation
5. Auto-fix
6. Quality validation
7. Image generation
8. SEO payload generation
9. Draft or publish to WordPress

Publication defaults:

- candidate generation every 10 minutes
- launch publication cap: 12/day for 72 hours
- steady publication cap: 6/day
- quality threshold: 94/100

## WordPress Packaging

Repo export assets are stored in:

- `wordpress/bohemian-studio-theme`
- `wordpress/bohemian-studio-core`

These packages are intended for manual installation on the live WordPress site until deployment automation is added.

## Live Site Checklist

Apply these in wp-admin:

1. Site title: `Bohemian Studio`
2. Tagline: `팩트로 정리하고 실행으로 연결하는 디지털 매거진`
3. `siteurl` and `home` set to `https://piwpiwwp.mycafe24.com`
4. Timezone: `Asia/Seoul`
5. Feed: summary
6. Comments default off
7. Front page: static `Home`
8. Posts page: `Magazine`
9. Delete sample content and clean unused tags/categories

## Plugin Baseline

Recommended active set:

- `NinjaFirewall`
- `Login Lockdown`
- `Two-Factor`
- `Disable XML-RPC-API`
- `WP Super Cache`
- `Rank Math SEO`
- `Site Kit by Google`
- `Redirection`
- `Bohemian Studio Core`

## Theme Baseline

Design tokens:

- Ink: `#0B1320`
- Paper: `#F6F1E8`
- Teal: `#0F766E`
- Amber: `#C58A2A`
- Moss: `#2F6B4F`

Typography:

- Headline: `MaruBuri`
- Body: `SUIT Variable`

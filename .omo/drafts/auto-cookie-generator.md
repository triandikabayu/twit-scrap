---
slug: auto-cookie-generator
status: writing-plan
intent: clear
pending-action: write .omo/plans/auto-cookie-generator.md
approach: Playwright automated login using stored credentials from twitter_accounts DB
---

# Draft: auto-cookie-generator

## Components (topology ledger)
| id | outcome | status | evidence |
|---|---|---|---|
| scripts/auto_login.py | New Playwright script: fill login form with credentials, submit, wait for home, save cookies | active | Current `scripts/get_cookies.py` requires manual login at x.com/login |
| app/routes/accounts.py:48-76 | Update POST /accounts/{id}/cookies to call auto_login.py instead of get_cookies.py | active | Line 68 references PROJ/'get_cookies.py' (wrong path) |
| Fix broken paths | accounts.py:68 and scrape.py:105 reference paths without scripts/ prefix | active | Files are at scripts/get_cookies.py and scripts/scraper.py |
| Keep get_cookies.py fallback | Preserve for 2FA/email-challenge edge cases | deferred | Not all accounts support automated login |

## Open assumptions (announced defaults)
| assumption | adopted default | rationale | reversible? |
|---|---|---|---|
| X.com login page structure is stable enough for Playwright selectors | Use text-based and placeholder selectors (not brittle data-testid) | X changes data-testid frequently; text labels change less often | Yes: if login breaks, update selectors or fall back to manual flow |
| Credentials from DB are valid | Auto_login.py reports login failure clearly | Cannot verify without attempting login | Yes: manual cookie gen is the fallback |
| No 2FA/email challenges for these accounts | Script handles the simple password-only login path; flags if redirected to challenge | Common case for dummy accounts | Yes: if challenges appear, fall back to manual get_cookies.py |

## Findings (cited - path:lines)
- Current `get_cookies.py` (scripts/get_cookies.py:17-55) opens browser, navigates to x.com/login, waits for user to login manually, then saves cookies
- `scraper.py` (scripts/scraper.py:251-268) loads cookies from JSON and adds them to Playwright context
- Cookie format: Standard Playwright cookies with name, value, domain, path, expires, httpOnly, secure, sameSite (scripts/scraper.py:254-267)
- `twitter_accounts` DB table has columns: id, name, email, username, password, cookies_file (app/models/db.py:71-81)
- Route at app/routes/accounts.py:48-76 currently calls PROJ/'get_cookies.py' — file is at scripts/get_cookies.py (broken)
- Route at app/routes/scrape.py:99-111 calls PROJ/'scraper.py' — file is at scripts/scraper.py (broken)
- X.com login page: standard email/username field, then password field flow

## Decisions (with rationale)
- **Playwright over twikit**: Playwright uses same tech stack (already installed), same cookie format the scraper expects. Converting twikit API tokens to browser cookies is fragile.
- **Credentials from DB + config fallback**: twitter_accounts table already stores credentials. For the default account, fall back to config/settings.py values.
- **Headless=non-hidden**: Use headed mode (browser visible) during login since X may detect headless. Could add `--headless` flag for server deployments.
- **Same cookie format**: Keep identical cookie structure so scraper.py works unchanged.

## Scope IN
- New script: `scripts/auto_login.py` — automated Playwright login
- Update `app/routes/accounts.py` POST /accounts/{id}/cookies
- Fix broken script paths in accounts.py and scrape.py (missing scripts/ prefix)
- Preserve manual `get_cookies.py` as fallback
- Web UI integration (the accounts page already works — backend changes only)

## Scope OUT (Must NOT have)
- ❌ No twikit integration for auth
- ❌ No cookie auto-refresh or expiry monitoring
- ❌ No changes to the scraper flow (scraper.py stays as-is)
- ❌ No UI template changes
- ❌ No database schema changes
- ❌ No changes to the keyword/keyword-selection system

## Open questions
None — all resolved through exploration and user choice.

## Approval gate
status: writing-plan
<!-- When exploration is exhausted and unknowns are answered, set status: awaiting-approval. -->
<!-- That durable record is the loop guard: on a later turn read it and resume at the gate instead of re-running exploration. -->

# auto-cookie-generator - Work Plan

## TL;DR (For humans)

**What you'll get:** The "Generate Cookies" button on the Akun Twitter page will now log in to X automatically using the account's stored username/password — no more manually opening a browser and typing credentials by hand. If automated login fails (wrong password, 2FA challenge), it falls back cleanly to the old manual method.

**Why this approach:** Playwright is already installed and used for scraping. The credentials are already stored in the database. Automating the form-fill is the simplest path — same cookie format, no new libraries, no fragile token conversion.

**What it will NOT do:** ❌ Twiddle with the scraper itself. ❌ Auto-refresh expired cookies. ❌ Change the web UI. ❌ Touch keywords, analysis, or the database schema.

**Effort:** Short
**Risk:** Medium — X.com login page could change its HTML structure and break the selectors. The fallback manual path mitigates this.

**Decisions to sanity-check:**
- Headed browser (visible) by default during login — X detects headless Chrome. Workers can pass `--headless` for server deployments.
- Text-based selectors (`input[autocomplete="username"]`, `[name="password"]`) over brittle `data-testid` attributes.

Your next move: Approve, then `$start-work` to execute. Or request a high-accuracy Momus review first.

---

> **TL;DR (machine):** Short effort, Medium risk (X.com UI changes). New scripts/auto_login.py + route update + path fix. Playwright form-fill with stored credentials. Manual fallback preserved.

## Scope

### Must have
1. `scripts/auto_login.py` — automated Playwright login script accepting `--username`, `--password`, `--output` (and optional `--email`, `--headless`)
2. Update `app/routes/accounts.py` POST `/accounts/{id}/cookies` to call `auto_login.py` with stored DB credentials
3. Fix broken script path in `app/routes/scrape.py:105` (`PROJ/'scraper.py'` → `PROJ/'scripts'/'scraper.py'`)
4. Manual `scripts/get_cookies.py` preserved as-is for fallback

### Must NOT have (guardrails, anti-slop, scope boundaries)
- ❌ No changes to `scripts/scraper.py` or the scraping pipeline
- ❌ No twikit usage for login
- ❌ No database migrations or schema changes
- ❌ No UI template changes (accounts page and scraper page remain identical)
- ❌ No cookie expiry monitoring or auto-refresh
- ❌ No new Python dependencies
- ❌ No changes to keyword, analysis, or data routes

## Verification strategy
> Zero human intervention — all verification is agent-executed.

- **Test decision:** tests-after (we verify by running the script against real X.com)
- **Evidence dir:** `.omo/evidence/`
- **Verification method for each todo:**
  - Unit: python3 scripts/auto_login.py --help exits 0 and shows usage
  - Integration: Run against a test X account; confirm cookie file is created with expected fields
  - Route: POST to accounts endpoint with mock; confirm subprocess is launched
  - Scraper path fix: Check the file path resolves correctly

## Execution strategy

### Parallel execution waves
| Wave | Todos | Description |
|------|-------|-------------|
| Wave 1 | 1 | Create `scripts/auto_login.py` core script |
| Wave 2 | 2, 3 | Update route (depends on 1) + fix scrape path (independent of 1) |

### Dependency matrix
| Todo | Depends on | Blocks | Can parallelize with |
| --- | --- | --- | --- |
| 1. auto_login.py | — | 2 | 3 |
| 2. Update accounts route | 1 | — | — |
| 3. Fix scrape.py path | — | — | 1 |

## Todos
> Implementation + Test = ONE todo. Never separate.
<!-- APPEND TASK BATCHES BELOW THIS LINE WITH edit/apply_patch - never rewrite the headers above. -->
- [x] 1. Create `scripts/auto_login.py` — automated Playwright login script
  **What to do:** Write a new Python script at `scripts/auto_login.py` that:
  - Accepts CLI args: `--username` (required), `--password` (required), `--output` (required, cookie file path), `--email` (optional, for X accounts that need email), `--headless` (optional flag)
  - Launches Playwright Chromium (headed by default, headless with `--headless`), with `--disable-blink-features=AutomationControlled` and a realistic UA
  - Navigates to `https://x.com/login`, waits for the username input field (detect by `autocomplete="username"` attribute)
  - Types the username/email, clicks the "Next" button (text-based selector or `[role="button"]` containing "Next"/"Selanjutnya")
  - Waits for password field (`[name="password"]` or `autocomplete="current-password"`), types password, presses Enter / clicks "Log in" button
  - Waits for redirect to `https://x.com/home` (timeout 60s); if redirected elsewhere (challenge/2FA), print `STATUS:challenge` and exit code 2
  - On success: captures `context.cookies()`, writes to output JSON in same format as `get_cookies.py`
  - Prints `STATUS:ok` + `COOKIES_SAVED:<path>` for the route to parse
  - On failure: prints `STATUS:error` + `MSG:<reason>`, exits with code 1
  - Must NOT: store plaintext credentials in logs, use data-testid selectors (they change frequently), or modify any existing files
  - Must NOT: import or touch `config/settings.py` directly (receives credentials as args)

  **Parallelization:** Wave 1 | Blocked by: — | Blocks: 2
  **References (executor has NO interview context - be exhaustive):**
  - `scripts/get_cookies.py:1-60` — current manual cookie script to use as format reference (same cookie-writing logic, same Playwright context setup, same user-agent)
  - `scripts/scraper.py:251-268` — how cookies are loaded and used (validates domain: `.x.com`, sameSite handling)
  - X.com login page structure (as of June 2026): username input with `autocomplete="username"`, "Next" button, then password input with `autocomplete="current-password"` and `name="password"`
  - `app/routes/accounts.py:48-76` — the route that calls the cookie script (reads `account_id`, constructs output path `cookies_{id}.json`)
  - `requirements.txt:10` — playwright>=1.50 is already installed
  - Cookie format required by scraper.py: fields `name`, `value`, `domain`, `path`, `expires`, `httpOnly`, `secure`, `sameSite` (see `scripts/scraper.py:254-267`)
  - `app/models/db.py:507-514` — `update_account_cookies()` to update the DB record

  **Acceptance criteria (agent-executable):**
  1. `python3 scripts/auto_login.py --help` exits 0, prints usage
  2. `python3 scripts/auto_login.py --output /tmp/test_cookies.json --username "" --password ""` exits 1 with error about missing creds
  3. After running with valid creds, the output JSON at the specified path contains at least `auth_token` and `ct0` cookies with expected Playwright format
  4. The output cookies can be loaded by `scripts/scraper.py`'s cookie-loading code (lines 251-268) without error
  5. Script exits with code 0 on success and prints `STATUS:ok`

  **QA scenarios:**
  - Happy: Run with `--username realuser --password realpass --output /tmp/test_cookies.json` → exits 0, cookie file created with valid X.com session cookies, `STATUS:ok` printed
  - Failure (wrong creds): Run with wrong password → exits 1, `STATUS:error` + `MSG:` printed, no cookie file or empty file
  - Failure (missing args): Run without `--username` → exits 1, prints usage error
  - Failure (headless): Run with `--headless` on a server → may fail if X blocks headless; acceptable limitation, script should print clear error
  - Evidence: `.omo/evidence/task-1-auto-cookie-generator.txt`

  **Commit:** Y | feat: add automated Playwright login script to replace manual browser login

- [x] 2. Update `app/routes/accounts.py` POST endpoint to use auto_login.py
  **What to do:** Modify `app/routes/accounts.py:48-76` (`api_accounts_gen_cookies`):
  - Read account credentials from DB using `db.get_twitter_account(account_id)` (already done at line 53)
  - Instead of calling `str(PROJ / 'get_cookies.py')`, call `str(PROJ / 'scripts' / 'auto_login.py')`
  - Pass `--username`, `--password`, `--output` with the account's stored credentials
  - Parse the script's stdout for `STATUS:ok` / `STATUS:error` / `STATUS:challenge` to determine result
  - On `STATUS:ok`: call `db.update_account_cookies(account_id, cookies_file)`, return `{'status': 'ok', 'cookies_file': cookies_file}`
  - On `STATUS:error`: return `{'status': 'error', 'msg': <reason>}`
  - On `STATUS:challenge`: return `{'status': 'challenge', 'msg': '2FA/challenge detected, use manual fallback', 'command': f'python scripts/get_cookies.py --output {cookies_file}'}`, guide the user to use manual method
  - Keep the remote-server detection logic (lines 56-65) — show appropriate message when accessed from another device
  - Must NOT: change the API response schema that the frontend expects (the scraper.html JS parses status=ok/error/remote)
  - Must NOT: print credentials in logs or error messages
  - Must NOT: modify `get_cookies.py` — it stays as manual fallback

  **Parallelization:** Wave 2 | Blocked by: 1 | Blocks: —
  **References (executor has NO interview context - be exhaustive):**
  - `app/routes/accounts.py:22-45` — existing API patterns for accounts (POST add, DELETE remove)
  - `app/routes/accounts.py:48-76` — THE TARGET CODE to modify (current POST /accounts/{id}/cookies handler)
  - `app/models/db.py:507-514` — `update_account_cookies(account_id, cookies_file)` — updates DB with new cookie path
  - `app/routes/accounts.py:80` — `get_cookies.py` is referenced as fallback UI text in "command" field
  - `app/templates/accounts.html:129-147` — frontend JS `genCookies()` function that handles the API response (status=ok, remote, error). Must not break the contract.
  - `app/templates/accounts.html:149-170` — `showRemoteDialog()` — handles remote-server case, uses d.command to show manual instructions
  - `config/settings.py:7` — COOKIES_FILE = 'cookies.json' (default)
  - The output path format: `cookies_{account_id}.json` (line 58)

  **Acceptance criteria (agent-executable):**
  1. POST to `/api/accounts/3/cookies` with no credentials in DB → returns `status: 'error'` with appropriate message
  2. After auto_login.py succeeds, the account's `cookies_file` field in DB is updated to `cookies_{id}.json`
  3. Response JSON matches existing frontend contract: always has `status` field, plus `cookies_file` on ok, `msg` on error, `command` on challenge
  4. Remote server detection still works: request from non-localhost IP returns `status: 'remote'` with command hint

  **QA scenarios:**
  - Happy: Account with valid creds → POST returns `status: ok`, cookies_file updated, frontend shows ✅ Cookies OK
  - Failure (bad creds): Account with wrong password → POST returns `status: error` with msg, frontend shows error
  - Challenge: Account with 2FA → POST returns `status: challenge` with manual fallback command
  - Remote: Request from non-localhost → returns `status: remote` with command guidance
  - Evidence: `.omo/evidence/task-2-auto-cookie-generator.txt`

  **Commit:** Y | feat: update accounts route to use auto_login.py with stored credentials

- [x] 3. Fix broken script path in `app/routes/scrape.py`
  **What to do:** Change line 105 in `app/routes/scrape.py` from `str(PROJ / 'scraper.py')` to `str(PROJ / 'scripts' / 'scraper.py')`.
  The scraper file lives at `scripts/scraper.py`, not at the project root.
  Must NOT: change any other line in scrape.py. Must NOT: change the import paths inside scraper.py itself (it uses `sys.path.insert` which is fine regardless of where it's called from as long as the file path is correct).

  **Parallelization:** Wave 2 | Blocked by: — | Blocks: —
  **References (executor has NO interview context - be exhaustive):**
  - `app/routes/scrape.py:99-111` — `_scrape_runner()` function, specifically line 105: `sys.executable, str(PROJ / 'scraper.py'),`
  - `scripts/scraper.py:1-304` — validates the file is at scripts/scraper.py
  - `app/routes/accounts.py:67-69` — same bug pattern (but accounts.py is fixed in Todo 2 by replacing the script)
  - `app/helpers.py:11` — `PROJ = Path(__file__).parent.parent` (PROJ = project root)
  - `app/main.py:3-4` — `sys.path.insert` pattern: the project uses scripts/ subdirectory

  **Acceptance criteria (agent-executable):**
  1. After fix, line reads: `str(PROJ / 'scripts' / 'scraper.py')`
  2. `python3 -c "from pathlib import Path; import sys; PROJ=Path('/Users/dika/Documents/project/cf-twit-scrap'); print((PROJ / 'scripts' / 'scraper.py').exists())"` prints True
  3. The scraper subprocess launch should now find the file (previously would raise FileNotFoundError)

  **QA scenarios:**
  - Happy: Read the line after edit → confirms path is `PROJ / 'scripts' / 'scraper.py'`
  - Verification: Check the file exists at the new path
  - Evidence: `.omo/evidence/task-3-auto-cookie-generator.txt`

  **Commit:** Y | fix: correct scraper.py path in scrape route (missing scripts/ prefix)

## Final verification wave
> Runs in parallel after ALL todos. ALL must APPROVE. Surface results and wait for the user's explicit okay before declaring complete.

- [ ] F1. **Plan compliance audit** — Verify every Must Have is implemented and every Must NOT Have is absent. Check there's no scope creep. Read each file changed and confirm only the intended changes were made.
- [ ] F2. **Code quality review** — Review auto_login.py for error handling, credential safety (no logging of passwords), selector robustness, and correct cookie format. Check the route change handles all response types (ok/error/challenge/remote).
- [ ] F3. **Real manual QA** — Run the auto_login.py script against a real X test account. Verify cookies are generated and the scraper can use them. Hit the `/api/accounts/{id}/cookies` endpoint and confirm the web UI shows ✅ Cookies OK.
- [ ] F4. **Scope fidelity** — Confirm no changes to scraper.py, UI templates, DB schema, keywords, or analysis. Check git diff shows exactly the intended 3 files changed.

## Commit strategy
Three commits in sequence:

```
feat: add automated Playwright login script (scripts/auto_login.py)
feat: update accounts route to use auto_login.py with stored credentials
fix: correct scraper.py path in scrape route (missing scripts/ prefix)
```

## Success criteria
1. ✅ "Generate Cookies" button automatically logs in using the account's stored credentials — no manual browser typing needed
2. ✅ Cookie files are saved in the same format the scraper expects
3. ✅ If automated login fails (bad creds, challenge, 2FA), the user is guided to use the manual fallback
4. ✅ The scraper still works — the cookie format and loading path are unchanged
5. ✅ The broken script path in scrape.py is fixed (FileNotFoundError gone)
6. ✅ No UI changes — the accounts page and scraper page look and behave identically

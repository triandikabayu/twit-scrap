import argparse
import asyncio
import json
import re
import sys

from playwright.async_api import async_playwright
from playwright_stealth import Stealth

USER_AGENT = (
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
    'AppleWebKit/537.36 (KHTML, like Gecko) '
    'Chrome/124.0.0.0 Safari/537.36'
)

LOGIN_URL = 'https://x.com/i/jf/onboarding/web?mode=login'
HOME_URL = 'https://x.com/home'


async def _click_continue(page):
    """Click the 'Continue' button on X.com login/onboarding pages."""
    selectors = [
        'div.jf-element:has(> p:text-is("Continue"))',
        'div:has(> p:text-is("Continue"))',
        'p:text-is("Continue")',
        'button:text-is("Continue")',
        '[role="button"]:text-is("Continue")',
    ]
    for sel in selectors:
        try:
            btn = page.locator(sel).first
            if await btn.count():
                await btn.wait_for(timeout=3000)
                await btn.click()
                return True
        except Exception:
            continue
    return False


async def login(
    username: str,
    password: str,
    output_path: str,
    email: str | None = None,
    headless: bool = False,
):
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--no-first-run',
                '--no-default-browser-check',
            ],
        )
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 900},
            user_agent=USER_AGENT,
            locale='en-US',
            timezone_id='America/New_York',
        )
        # Apply stealth patches to avoid X.com bot detection
        stealth = Stealth()
        await stealth.apply_stealth_async(context)
        page = await context.new_page()

        # 1. Go to login page (will redirect to onboarding flow)
        try:
            await page.goto(LOGIN_URL, wait_until='domcontentloaded', timeout=30000)
        except Exception as e:
            print('STATUS:error')
            print(f'MSG:Failed to load login page: {e}')
            await browser.close()
            sys.exit(1)

        await asyncio.sleep(2)

        # 2. Fill username/email
        try:
            username_input = page.locator('input[name="username_or_email"]').first
            await username_input.wait_for(timeout=15000)
            await username_input.fill(email or username)
            await asyncio.sleep(1)
        except Exception as e:
            print('STATUS:error')
            print(f'MSG:Username field not found: {e}')
            await browser.close()
            sys.exit(1)

        # 3. Click Continue
        clicked = await _click_continue(page)
        if not clicked:
            print('STATUS:error')
            print('MSG:Continue button not found after entering username')
            await browser.close()
            sys.exit(1)

        await asyncio.sleep(2)

        # 4. Fill password field
        password_found = False
        password_selectors = [
            'input[name="password"]',
            'input[type="password"]',
            'input[autocomplete="current-password"]',
        ]
        for sel in password_selectors:
            try:
                pw_input = page.locator(sel).first
                if await pw_input.count():
                    await pw_input.wait_for(timeout=5000)
                    await pw_input.fill(password)
                    password_found = True
                    break
            except Exception:
                continue

        if not password_found:
            # Check current URL — maybe we're on a different step
            current_url = page.url
            if 'home' in current_url:
                # Already logged in — cookies might already exist
                pass
            else:
                print('STATUS:error')
                print(f'MSG:Password field not found. Current URL: {current_url}')
                await browser.close()
                sys.exit(1)

        await asyncio.sleep(1)

        # 5. Click Log in button
        login_clicked = False
        login_selectors = [
            'button:has-text("Log in")',
            'button:has-text("Masuk")',
            'div:has(> p:text-is("Log in"))',
            '[data-testid="LoginForm_Login_Button"]',
        ]
        for sel in login_selectors:
            try:
                btn = page.locator(sel).first
                if await btn.count():
                    await btn.wait_for(timeout=3000)
                    await btn.click()
                    login_clicked = True
                    break
            except Exception:
                continue

        if not login_clicked and password_found:
            # Fallback: press Enter
            await page.keyboard.press('Enter')

        # 6. Wait for home page
        try:
            await page.wait_for_url(HOME_URL, timeout=60000)
        except Exception:
            current_url = page.url
            if 'home' in current_url:
                pass  # Already there
            elif 'onboarding' not in current_url and 'login' not in current_url:
                print('STATUS:challenge')
                print(f'MSG:2FA or email challenge detected at: {current_url}')
                await browser.close()
                sys.exit(2)
            else:
                print('STATUS:error')
                print(f'MSG:Timed out waiting for home page. Current URL: {current_url}')
                await browser.close()
                sys.exit(1)

        await asyncio.sleep(3)

        # 7. Save cookies
        cookies = await context.cookies()
        with open(output_path, 'w') as f:
            json.dump(cookies, f, indent=2)

        print('STATUS:ok')
        print(f'COOKIES_SAVED:{output_path}')

        await browser.close()


def main():
    parser = argparse.ArgumentParser(description='Automated X.com login and cookie capture')
    parser.add_argument('--username', required=True, help='X.com username/handle')
    parser.add_argument('--password', required=True, help='X.com password')
    parser.add_argument('--output', required=True, help='Path to save cookie JSON file')
    parser.add_argument('--email', help='Email address (if different from username)')
    parser.add_argument('--headless', action='store_true', help='Run browser in headless mode')
    args = parser.parse_args()

    asyncio.run(login(
        username=args.username,
        password=args.password,
        output_path=args.output,
        email=args.email,
        headless=args.headless,
    ))


if __name__ == '__main__':
    main()

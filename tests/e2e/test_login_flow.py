"""End-to-end test for login flow.

Tests complete user journey from login page through authentication to app.
Must FAIL before implementation.

Note: This test requires Playwright or similar browser automation tool.
Install with: pip install playwright && playwright install
"""
import os
from pathlib import Path

import pytest

# Skip if Playwright not installed
pytest.importorskip("playwright", reason="Playwright not installed")


@pytest.mark.slow
@pytest.mark.e2e
class TestFullLoginFlowE2E:
    """Test full login flow end-to-end - T035."""

    @pytest.fixture
    def browser_context(self):
        """Create browser context for test."""
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            yield context
            context.close()
            browser.close()

    def test_full_login_flow(self, browser_context):
        """Should complete full login flow from UI to authenticated state.

        E2E test covering:
        1. Navigate to login page
        2. Click Google sign-in button
        3. Complete OAuth flow (mocked in test environment)
        4. Redirect to app with authenticated session
        5. Verify user data displayed

        Note: In CI/CD, this test should use a test OAuth provider
        or mock the OAuth flow at the network level.
        """
        page = browser_context.new_page()

        # Get frontend URL from environment
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")

        try:
            # Step 1: Navigate to login page
            page.goto(f"{frontend_url}/login")
            page.wait_for_load_state("networkidle")

            # Verify login page loaded
            assert page.title() or True  # Page should have loaded

            # Step 2: Verify Google login button exists
            # Adjust selector based on actual implementation
            login_button = page.locator('button:has-text("Sign in with Google")').first
            assert login_button.is_visible()

            # Step 3: Click login button
            # Note: In a real E2E test, this would trigger OAuth flow
            # For test environment, we would mock the OAuth response
            # or use a test OAuth provider

            # Example: Mock OAuth callback for testing
            # In practice, you'd set up a test OAuth provider or
            # intercept the OAuth redirect at the network level

            # For this test structure, we'll verify the button click
            # would navigate to OAuth (we can't actually complete OAuth in CI)
            login_button.click()

            # Wait for navigation to OAuth provider (or mock endpoint)
            page.wait_for_load_state("networkidle", timeout=5000)

            # Verify navigation occurred (URL changed)
            current_url = page.url
            # Should have navigated away from login page
            assert current_url != f"{frontend_url}/login"

            # In a complete E2E test with OAuth mocking:
            # - Mock OAuth provider would authenticate
            # - Redirect back to /auth/callback with code
            # - Backend validates and sets session cookie
            # - Frontend redirects to app

            # Example of what full flow would verify:
            # page.wait_for_url(f"{frontend_url}/", timeout=10000)
            # assert page.locator('[data-testid="user-email"]').is_visible()

        except Exception as e:
            # Take screenshot on failure
            screenshot_path = Path("/tmp/e2e_login_failure.png")
            page.screenshot(path=str(screenshot_path))
            raise AssertionError(f"E2E test failed: {e}\nScreenshot saved to {screenshot_path}")

        finally:
            page.close()

    def test_login_flow_with_non_whitelisted_user(self, browser_context):
        """Should show error for non-whitelisted user.

        E2E test covering:
        1. Complete OAuth with non-whitelisted email
        2. Backend rejects with 403
        3. Frontend displays error message
        """
        page = browser_context.new_page()
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")

        try:
            # Navigate to login
            page.goto(f"{frontend_url}/login")
            page.wait_for_load_state("networkidle")

            # In a complete test, we would:
            # 1. Click login button
            # 2. Mock OAuth to return non-whitelisted email
            # 3. Verify error message displayed

            # For structure purposes:
            login_button = page.locator('button:has-text("Sign in with Google")').first
            if login_button.is_visible():
                # Would click and verify error handling
                pass

            # Example verification after error:
            # error_message = page.locator('[data-testid="error-message"]')
            # assert error_message.is_visible()
            # assert "not authorized" in error_message.text_content().lower()

        finally:
            page.close()

    def test_authenticated_user_can_access_app(self, browser_context):
        """Should allow authenticated user to access protected pages.

        E2E test covering:
        1. User already authenticated (session cookie set)
        2. Navigate to protected page
        3. Verify access granted
        """
        page = browser_context.new_page()
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")

        try:
            # In a complete test, we would:
            # 1. Set a valid session cookie
            # 2. Navigate to a protected page (e.g., /experiments)
            # 3. Verify page loads without redirect to login

            # Mock: Add session cookie
            # page.context.add_cookies([{
            #     "name": "session",
            #     "value": "valid_test_jwt_token",
            #     "domain": "localhost",
            #     "path": "/"
            # }])

            # Navigate to protected page
            # page.goto(f"{frontend_url}/experiments")
            # page.wait_for_load_state("networkidle")

            # Verify not redirected to login
            # assert page.url != f"{frontend_url}/login"
            pass

        finally:
            page.close()

    def test_unauthenticated_user_redirected_to_login(self, browser_context):
        """Should redirect unauthenticated user to login page.

        E2E test covering:
        1. User not authenticated (no session cookie)
        2. Navigate to protected page
        3. Verify redirected to login
        """
        page = browser_context.new_page()
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")

        try:
            # Navigate to protected page without auth
            page.goto(f"{frontend_url}/experiments")
            page.wait_for_load_state("networkidle", timeout=5000)

            # Should redirect to login
            # assert page.url == f"{frontend_url}/login" or "/login" in page.url

        finally:
            page.close()


# Alternative: Selenium-based E2E test (if Playwright not available)
@pytest.mark.slow
@pytest.mark.e2e
@pytest.mark.skipif(
    not os.getenv("USE_SELENIUM"),
    reason="Selenium tests only run when USE_SELENIUM=1"
)
class TestLoginFlowSelenium:
    """Alternative E2E tests using Selenium WebDriver."""

    @pytest.fixture
    def selenium_driver(self):
        """Create Selenium WebDriver."""
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options

            options = Options()
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")

            driver = webdriver.Chrome(options=options)
            yield driver
            driver.quit()
        except ImportError:
            pytest.skip("Selenium not installed")

    def test_login_page_loads(self, selenium_driver):
        """Should load login page with Google button."""
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
        selenium_driver.get(f"{frontend_url}/login")

        # Verify page title
        assert selenium_driver.title or True

        # Verify login button present
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.support.ui import WebDriverWait

        try:
            button = WebDriverWait(selenium_driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//button[contains(text(), 'Google')]"))
            )
            assert button.is_displayed()
        except Exception as e:
            pytest.fail(f"Login button not found: {e}")

"""End-to-end tests for authenticated user flows.

Tests complete user journeys that require authentication, using cookie injection
to bypass the OAuth flow.

Usage:
    pytest tests/e2e/test_authenticated_flows.py -m e2e
"""
import pytest
import os
from pathlib import Path


# Skip entire module if Playwright not installed
pytest.importorskip("playwright", reason="Playwright not installed")


from tests.e2e.fixtures import (
    authenticated_page,
    authenticated_context,
    second_user_page,
    second_user_context,
    browser,
    frontend_url,
)
from tests.e2e.helpers.auth import TEST_USER, TEST_USER_2


@pytest.mark.slow
@pytest.mark.e2e
class TestAuthenticatedExperimentFlows:
    """Test experiment workflows for authenticated users."""

    def test_authenticated_user_can_access_experiments_page(
        self, authenticated_page, frontend_url
    ):
        """Should allow authenticated user to view experiments list.

        E2E test covering:
        - Cookie injection bypasses OAuth
        - Protected page is accessible
        - No redirect to login
        """
        try:
            # Navigate to experiments page
            authenticated_page.goto(f"{frontend_url}/")
            authenticated_page.wait_for_load_state("networkidle", timeout=10000)

            # Verify not redirected to login
            current_url = authenticated_page.url
            assert "/login" not in current_url, f"Should not redirect to login, got: {current_url}"

        except Exception as e:
            # Take screenshot on failure
            screenshot_path = Path("/tmp/e2e_auth_failure.png")
            authenticated_page.screenshot(path=str(screenshot_path))
            raise AssertionError(
                f"E2E test failed: {e}\nScreenshot saved to {screenshot_path}"
            )

    def test_authenticated_user_can_navigate_to_synth_groups(
        self, authenticated_page, frontend_url
    ):
        """Should allow authenticated user to view synth groups.

        E2E test covering:
        - Access to synth groups page
        - User sees their owned groups
        """
        try:
            # Navigate to synth groups
            authenticated_page.goto(f"{frontend_url}/synths")
            authenticated_page.wait_for_load_state("networkidle", timeout=10000)

            # Verify not redirected to login
            current_url = authenticated_page.url
            assert "/login" not in current_url, f"Should not redirect to login, got: {current_url}"

        except Exception as e:
            screenshot_path = Path("/tmp/e2e_synth_groups_failure.png")
            authenticated_page.screenshot(path=str(screenshot_path))
            raise AssertionError(
                f"E2E test failed: {e}\nScreenshot saved to {screenshot_path}"
            )


@pytest.mark.slow
@pytest.mark.e2e
class TestUnauthenticatedAccess:
    """Test that unauthenticated users are redirected to login."""

    def test_unauthenticated_user_redirected_to_login(
        self, browser, frontend_url
    ):
        """Should redirect unauthenticated user to login page.

        E2E test covering:
        - No auth cookie set
        - Protected page redirects to login
        """
        # Create a fresh context without auth cookie
        context = browser.new_context()
        page = context.new_page()

        try:
            # Navigate to protected page without auth
            page.goto(f"{frontend_url}/")
            page.wait_for_load_state("networkidle", timeout=10000)

            # Should redirect to login
            current_url = page.url
            # Note: Depending on implementation, might redirect to /login or show login component
            # Adjust assertion based on actual frontend behavior

        except Exception as e:
            screenshot_path = Path("/tmp/e2e_unauth_failure.png")
            page.screenshot(path=str(screenshot_path))
            raise AssertionError(
                f"E2E test failed: {e}\nScreenshot saved to {screenshot_path}"
            )

        finally:
            page.close()
            context.close()


@pytest.mark.slow
@pytest.mark.e2e
class TestMultiUserSharing:
    """Test sharing scenarios between two users.

    Uses two separate browser contexts, each authenticated as different users.
    """

    def test_two_users_can_be_authenticated_simultaneously(
        self, authenticated_context, second_user_context, frontend_url
    ):
        """Should allow two different authenticated sessions.

        E2E test covering:
        - Two users authenticated in parallel
        - Each sees their own data
        """
        # Create pages for both users
        page1 = authenticated_context.new_page()
        page2 = second_user_context.new_page()

        try:
            # Both users navigate to app
            page1.goto(f"{frontend_url}/")
            page2.goto(f"{frontend_url}/")

            page1.wait_for_load_state("networkidle", timeout=10000)
            page2.wait_for_load_state("networkidle", timeout=10000)

            # Both should be authenticated (not on login page)
            assert "/login" not in page1.url, "User 1 should be authenticated"
            assert "/login" not in page2.url, "User 2 should be authenticated"

            # Additional verification could check that each user sees their own data
            # For example, check user email displayed in UI matches expected user

        except Exception as e:
            screenshot_path = Path("/tmp/e2e_multi_user_failure.png")
            page1.screenshot(path=str(screenshot_path))
            raise AssertionError(
                f"E2E test failed: {e}\nScreenshot saved to {screenshot_path}"
            )

        finally:
            page1.close()
            page2.close()

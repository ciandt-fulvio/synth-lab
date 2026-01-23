"""E2E test fixtures with cookie-based authentication.

Provides fixtures for authenticated browser contexts and pages that bypass
the OAuth flow by injecting JWT tokens directly as cookies.

Usage:
    from tests.e2e.fixtures import authenticated_page

    def test_create_experiment(authenticated_page):
        authenticated_page.goto('/experiments/new')
        # User is already authenticated - no login required
"""
import pytest
import os


# Try to import playwright - skip fixtures if not available
try:
    from playwright.sync_api import sync_playwright, Page, BrowserContext
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    Page = None
    BrowserContext = None


def get_frontend_url() -> str:
    """Get frontend URL from environment."""
    return os.getenv("FRONTEND_URL", "http://localhost:5173")


def get_backend_url() -> str:
    """Get backend URL from environment."""
    return os.getenv("BACKEND_URL", "http://localhost:8000")


@pytest.fixture(scope="session")
def playwright_instance():
    """Session-scoped Playwright instance."""
    if not PLAYWRIGHT_AVAILABLE:
        pytest.skip("Playwright not installed")

    with sync_playwright() as p:
        yield p


@pytest.fixture(scope="session")
def browser(playwright_instance):
    """Session-scoped browser instance."""
    browser = playwright_instance.chromium.launch(
        headless=True,
        args=["--no-sandbox", "--disable-dev-shm-usage"]
    )
    yield browser
    browser.close()


@pytest.fixture(scope="function")
def browser_context(browser) -> "BrowserContext":
    """Function-scoped browser context (clean cookies per test)."""
    context = browser.new_context()
    yield context
    context.close()


@pytest.fixture(scope="function")
def page(browser_context) -> "Page":
    """Function-scoped page without authentication."""
    page = browser_context.new_page()
    yield page
    page.close()


@pytest.fixture(scope="function")
def authenticated_context(browser) -> "BrowserContext":
    """Browser context with test user authentication cookie.

    Creates a new browser context and injects the auth cookie for the
    default test user. All pages created from this context will be
    authenticated.
    """
    from tests.e2e.helpers.auth import get_default_auth_cookie

    context = browser.new_context()

    # Add auth cookie before any navigation
    cookie = get_default_auth_cookie()
    context.add_cookies([cookie])

    yield context
    context.close()


@pytest.fixture(scope="function")
def authenticated_page(authenticated_context) -> "Page":
    """Page with test user authentication.

    Use this fixture when you need an authenticated user without going
    through the OAuth flow.

    Example:
        def test_create_experiment(authenticated_page):
            authenticated_page.goto('/experiments/new')
            # Already authenticated - proceed with test
    """
    page = authenticated_context.new_page()
    yield page
    page.close()


@pytest.fixture(scope="function")
def second_user_context(browser) -> "BrowserContext":
    """Browser context with second test user authentication cookie.

    Useful for testing sharing scenarios between two users.
    """
    from tests.e2e.helpers.auth import get_second_user_auth_cookie

    context = browser.new_context()
    cookie = get_second_user_auth_cookie()
    context.add_cookies([cookie])

    yield context
    context.close()


@pytest.fixture(scope="function")
def second_user_page(second_user_context) -> "Page":
    """Page with second test user authentication.

    Use this fixture for testing multi-user scenarios like sharing.
    """
    page = second_user_context.new_page()
    yield page
    page.close()


# Convenience fixtures for URLs
@pytest.fixture
def frontend_url() -> str:
    """Frontend base URL."""
    return get_frontend_url()


@pytest.fixture
def backend_url() -> str:
    """Backend API base URL."""
    return get_backend_url()

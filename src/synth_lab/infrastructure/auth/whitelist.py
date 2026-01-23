"""Whitelist validation for email-based access control.

Parses and validates user emails against a whitelist that supports:
- Exact email matches: user@example.com
- Domain matches: @company.com (matches any email from that domain)

Configuration via WHITELIST environment variable (comma-separated).
"""
from typing import Set, Tuple


def parse_whitelist(whitelist_str: str) -> Tuple[Set[str], Set[str]]:
    """Parse whitelist string into email and domain sets.

    Args:
        whitelist_str: Comma-separated list of emails and domains.
                      Example: "user@example.com,@company.com,admin@test.com"

    Returns:
        Tuple of (emails_set, domains_set) where:
        - emails_set: Set of exact email addresses (lowercase)
        - domains_set: Set of domain names without @ prefix (lowercase)

    Examples:
        >>> parse_whitelist("user@example.com,@company.com")
        ({'user@example.com'}, {'company.com'})

        >>> parse_whitelist("")
        (set(), set())
    """
    if not whitelist_str or not whitelist_str.strip():
        return (set(), set())

    emails: Set[str] = set()
    domains: Set[str] = set()

    entries = [entry.strip() for entry in whitelist_str.split(",")]

    for entry in entries:
        if not entry:
            continue

        # Normalize to lowercase
        entry_lower = entry.lower()

        if entry_lower.startswith("@"):
            # Domain pattern (remove @ prefix)
            domain = entry_lower[1:]
            if domain:
                domains.add(domain)
        else:
            # Exact email
            emails.add(entry_lower)

    return (emails, domains)


def is_whitelisted(email: str, emails: Set[str], domains: Set[str]) -> bool:
    """Check if an email is whitelisted.

    Args:
        email: Email address to check
        emails: Set of whitelisted exact emails (from parse_whitelist)
        domains: Set of whitelisted domains (from parse_whitelist)

    Returns:
        True if email matches whitelist, False otherwise

    Examples:
        >>> emails, domains = parse_whitelist("admin@example.com,@company.com")
        >>> is_whitelisted("admin@example.com", emails, domains)
        True

        >>> is_whitelisted("user@company.com", emails, domains)
        True

        >>> is_whitelisted("hacker@evil.com", emails, domains)
        False
    """
    if not email:
        return False

    # Normalize email to lowercase
    email_lower = email.lower().strip()

    # Check exact email match
    if email_lower in emails:
        return True

    # Check domain match
    if "@" in email_lower:
        domain = email_lower.split("@")[1]
        if domain in domains:
            return True

    return False


def load_whitelist_from_env() -> Tuple[Set[str], Set[str]]:
    """Load and parse whitelist from WHITELIST environment variable.

    Returns:
        Tuple of (emails_set, domains_set)

    Raises:
        ValueError: If WHITELIST environment variable is not set
    """
    import os

    whitelist_str = os.getenv("WHITELIST", "")
    if not whitelist_str:
        raise ValueError(
            "WHITELIST environment variable is required. "
            "Set it to a comma-separated list of emails and domains. "
            "Example: WHITELIST=user@example.com,@company.com"
        )

    return parse_whitelist(whitelist_str)

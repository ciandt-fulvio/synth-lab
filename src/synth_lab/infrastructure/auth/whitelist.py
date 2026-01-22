"""Whitelist validation for user authentication.

This module provides whitelist validation to control which users can access the system.
The whitelist supports:
- Individual email addresses (e.g., "alice@example.com")
- Domain wildcards (e.g., "@company.com" allows all emails from company.com)

Matching is case-insensitive and whitespace is stripped.

Example:
    >>> whitelist = ["alice@example.com", "@company.com"]
    >>> is_whitelisted("alice@example.com", whitelist)
    True
    >>> is_whitelisted("bob@company.com", whitelist)
    True
    >>> is_whitelisted("eve@hacker.com", whitelist)
    False
"""


def is_whitelisted(email: str, whitelist: list[str]) -> bool:
    """Check if an email is whitelisted.

    Args:
        email: The email address to check
        whitelist: List of whitelisted emails and/or domain wildcards (e.g., "@company.com")

    Returns:
        True if the email is whitelisted, False otherwise

    Examples:
        >>> is_whitelisted("alice@example.com", ["alice@example.com"])
        True
        >>> is_whitelisted("bob@company.com", ["@company.com"])
        True
        >>> is_whitelisted("eve@hacker.com", ["alice@example.com"])
        False
    """
    # Normalize email (strip whitespace and lowercase)
    email_normalized = email.strip().lower()

    # Extract domain from email (e.g., "alice@company.com" -> "@company.com")
    if "@" not in email_normalized:
        return False

    email_domain = "@" + email_normalized.split("@")[1]

    # Check each whitelist entry
    for entry in whitelist:
        # Normalize entry (strip whitespace and lowercase)
        entry_normalized = entry.strip().lower()

        # Check if it's a domain wildcard (starts with @)
        if entry_normalized.startswith("@"):
            # Match if the email's domain exactly matches the wildcard
            if email_domain == entry_normalized:
                return True
        else:
            # It's an individual email - check for exact match
            if email_normalized == entry_normalized:
                return True

    # No match found
    return False

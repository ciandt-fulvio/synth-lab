"""Whitelist validation for email-based access control.

Parses and validates user emails against a whitelist that supports:
- Exact email matches: user@example.com
- Domain matches: @company.com (matches any email from that domain)

Configuration:
- WHITELIST_FILE env var: path to a file with comma-separated entries (hot-reloaded)
- WHITELIST env var: comma-separated entries (fallback, requires restart)

References:
    - os.getenv: https://docs.python.org/3/library/os.html#os.getenv
"""
import os
from pathlib import Path
from typing import Optional, Set, Tuple

from loguru import logger

# Module-level cache for file-based whitelist
_whitelist_cache: Optional[Tuple[Set[str], Set[str]]] = None
_whitelist_cache_mtime: float = 0.0
_whitelist_file_path: Optional[str] = None


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

    # Support both comma and newline as separators
    normalized = whitelist_str.replace("\n", ",").replace("\r", ",")
    entries = [entry.strip() for entry in normalized.split(",")]

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


def _load_whitelist_from_file(file_path: str) -> Tuple[Set[str], Set[str]]:
    """Load whitelist from file, using cache if file hasn't changed.

    Checks file modification time to avoid re-parsing unchanged files.

    Args:
        file_path: Path to whitelist file (comma-separated entries)

    Returns:
        Tuple of (emails_set, domains_set)
    """
    global _whitelist_cache, _whitelist_cache_mtime

    if not os.path.isfile(file_path):
        logger.warning(f"Whitelist file not found or not a file: {file_path}")
        if _whitelist_cache is not None:
            return _whitelist_cache
        return (set(), set())

    try:
        mtime = os.path.getmtime(file_path)
    except OSError:
        logger.warning(f"Whitelist file not accessible: {file_path}")
        if _whitelist_cache is not None:
            return _whitelist_cache
        return (set(), set())

    if _whitelist_cache is not None and mtime == _whitelist_cache_mtime:
        return _whitelist_cache

    content = Path(file_path).read_text().strip()
    _whitelist_cache = parse_whitelist(content)
    _whitelist_cache_mtime = mtime
    logger.info(
        f"Whitelist reloaded from {file_path}: "
        f"{len(_whitelist_cache[0])} emails, {len(_whitelist_cache[1])} domains"
    )
    return _whitelist_cache


def load_whitelist_from_env() -> Tuple[Set[str], Set[str]]:
    """Load and parse whitelist from file or environment variable.

    Priority:
        1. WHITELIST_FILE env var → reads from file (hot-reloaded on change)
        2. WHITELIST env var → static value (requires restart)

    Returns:
        Tuple of (emails_set, domains_set)

    Raises:
        ValueError: If neither WHITELIST_FILE nor WHITELIST is configured
    """
    global _whitelist_file_path

    # Cache the file path lookup (env var won't change)
    if _whitelist_file_path is None:
        _whitelist_file_path = os.getenv("WHITELIST_FILE", "")

    if _whitelist_file_path and os.path.isfile(_whitelist_file_path):
        return _load_whitelist_from_file(_whitelist_file_path)

    if _whitelist_file_path:
        logger.warning(
            f"WHITELIST_FILE={_whitelist_file_path} not found or not a file, "
            "falling back to WHITELIST env var"
        )

    # Fallback to WHITELIST env var
    whitelist_str = os.getenv("WHITELIST", "")
    if not whitelist_str:
        raise ValueError(
            "WHITELIST or WHITELIST_FILE environment variable is required. "
            "Set WHITELIST to a comma-separated list of emails and domains, "
            "or WHITELIST_FILE to a path containing the whitelist. "
            "Example: WHITELIST=user@example.com,@company.com"
        )

    return parse_whitelist(whitelist_str)

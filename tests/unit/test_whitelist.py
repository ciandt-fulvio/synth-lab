"""Unit tests for whitelist email validation.

Tests email and domain matching logic for access control whitelist.
Must FAIL before implementation.
"""
import pytest
from synth_lab.infrastructure.auth.whitelist import (
    is_whitelisted,
    parse_whitelist,
)


class TestWhitelistEmailValidation:
    """Test exact email matching in whitelist."""

    def test_exact_email_match(self):
        """Should return True for exact email match."""
        whitelist_str = "user@example.com,admin@company.com"
        emails, domains = parse_whitelist(whitelist_str)

        assert is_whitelisted("user@example.com", emails, domains) is True
        assert is_whitelisted("admin@company.com", emails, domains) is True

    def test_email_not_in_whitelist(self):
        """Should return False for email not in whitelist."""
        whitelist_str = "user@example.com"
        emails, domains = parse_whitelist(whitelist_str)

        assert is_whitelisted("hacker@evil.com", emails, domains) is False

    def test_case_insensitive_email_match(self):
        """Should match emails case-insensitively."""
        whitelist_str = "User@Example.COM"
        emails, domains = parse_whitelist(whitelist_str)

        assert is_whitelisted("user@example.com", emails, domains) is True
        assert is_whitelisted("USER@EXAMPLE.COM", emails, domains) is True

    def test_empty_whitelist(self):
        """Should return False when whitelist is empty."""
        whitelist_str = ""
        emails, domains = parse_whitelist(whitelist_str)

        assert is_whitelisted("user@example.com", emails, domains) is False

    def test_whitespace_handling(self):
        """Should handle whitespace in whitelist entries."""
        whitelist_str = " user@example.com , admin@company.com "
        emails, domains = parse_whitelist(whitelist_str)

        assert is_whitelisted("user@example.com", emails, domains) is True
        assert is_whitelisted("admin@company.com", emails, domains) is True


class TestWhitelistDomainValidation:
    """Test domain pattern matching in whitelist."""

    def test_domain_match(self):
        """Should return True for email from whitelisted domain."""
        whitelist_str = "@company.com"
        emails, domains = parse_whitelist(whitelist_str)

        assert is_whitelisted("anyone@company.com", emails, domains) is True
        assert is_whitelisted("user123@company.com", emails, domains) is True

    def test_domain_not_match(self):
        """Should return False for email from non-whitelisted domain."""
        whitelist_str = "@company.com"
        emails, domains = parse_whitelist(whitelist_str)

        assert is_whitelisted("user@other.com", emails, domains) is False

    def test_subdomain_not_match(self):
        """Should NOT match subdomains by default."""
        whitelist_str = "@company.com"
        emails, domains = parse_whitelist(whitelist_str)

        # Subdomain should not match
        assert is_whitelisted("user@sub.company.com", emails, domains) is False

    def test_multiple_domains(self):
        """Should match any of multiple whitelisted domains."""
        whitelist_str = "@company.com,@partner.org,@client.net"
        emails, domains = parse_whitelist(whitelist_str)

        assert is_whitelisted("user@company.com", emails, domains) is True
        assert is_whitelisted("user@partner.org", emails, domains) is True
        assert is_whitelisted("user@client.net", emails, domains) is True
        assert is_whitelisted("user@hacker.com", emails, domains) is False

    def test_mixed_email_and_domain(self):
        """Should match both exact emails and domain patterns."""
        whitelist_str = "admin@example.com,@company.com"
        emails, domains = parse_whitelist(whitelist_str)

        # Exact email match
        assert is_whitelisted("admin@example.com", emails, domains) is True

        # Domain match
        assert is_whitelisted("anyone@company.com", emails, domains) is True

        # No match
        assert is_whitelisted("user@example.com", emails, domains) is False
        assert is_whitelisted("user@other.com", emails, domains) is False


class TestWhitelistParsing:
    """Test whitelist string parsing."""

    def test_parse_emails_only(self):
        """Should parse email-only whitelist."""
        whitelist_str = "user@example.com,admin@company.com"
        emails, domains = parse_whitelist(whitelist_str)

        assert len(emails) == 2
        assert "user@example.com" in emails
        assert "admin@company.com" in emails
        assert len(domains) == 0

    def test_parse_domains_only(self):
        """Should parse domain-only whitelist."""
        whitelist_str = "@company.com,@partner.org"
        emails, domains = parse_whitelist(whitelist_str)

        assert len(emails) == 0
        assert len(domains) == 2
        assert "company.com" in domains
        assert "partner.org" in domains

    def test_parse_mixed(self):
        """Should parse mixed email and domain whitelist."""
        whitelist_str = "admin@example.com,@company.com,user@test.com,@partner.org"
        emails, domains = parse_whitelist(whitelist_str)

        assert len(emails) == 2
        assert "admin@example.com" in emails
        assert "user@test.com" in emails
        assert len(domains) == 2
        assert "company.com" in domains
        assert "partner.org" in domains

    def test_parse_empty_string(self):
        """Should handle empty whitelist string."""
        emails, domains = parse_whitelist("")

        assert len(emails) == 0
        assert len(domains) == 0

    def test_parse_with_whitespace(self):
        """Should trim whitespace from entries."""
        whitelist_str = " user@example.com , @company.com , admin@test.com "
        emails, domains = parse_whitelist(whitelist_str)

        assert "user@example.com" in emails
        assert "admin@test.com" in emails
        assert "company.com" in domains

    def test_parse_normalizes_case(self):
        """Should normalize email/domain case to lowercase."""
        whitelist_str = "User@Example.COM,@Company.COM"
        emails, domains = parse_whitelist(whitelist_str)

        assert "user@example.com" in emails
        assert "company.com" in domains

"""Unit tests for whitelist validation.

Following Test-First Development:
- Tests are written BEFORE implementation
- Tests MUST fail initially (no implementation exists yet)
- Implementation in src/synth_lab/infrastructure/auth/whitelist.py
"""

import pytest


class TestWhitelistEmailValidation:
    """Test whitelist validation for individual email addresses."""

    def test_email_in_whitelist_returns_true(self):
        """Test that an email explicitly in the whitelist is allowed."""
        from synth_lab.infrastructure.auth.whitelist import is_whitelisted

        whitelist = ["alice@example.com", "bob@company.com"]
        assert is_whitelisted("alice@example.com", whitelist) is True

    def test_email_not_in_whitelist_returns_false(self):
        """Test that an email not in the whitelist is rejected."""
        from synth_lab.infrastructure.auth.whitelist import is_whitelisted

        whitelist = ["alice@example.com"]
        assert is_whitelisted("eve@hacker.com", whitelist) is False

    def test_case_insensitive_email_matching(self):
        """Test that email matching is case-insensitive."""
        from synth_lab.infrastructure.auth.whitelist import is_whitelisted

        whitelist = ["Alice@Example.COM"]
        assert is_whitelisted("alice@example.com", whitelist) is True

    def test_empty_whitelist_rejects_all(self):
        """Test that an empty whitelist rejects all emails."""
        from synth_lab.infrastructure.auth.whitelist import is_whitelisted

        whitelist = []
        assert is_whitelisted("alice@example.com", whitelist) is False

    def test_whitespace_in_email_is_stripped(self):
        """Test that whitespace in emails is properly handled."""
        from synth_lab.infrastructure.auth.whitelist import is_whitelisted

        whitelist = [" alice@example.com "]
        assert is_whitelisted("alice@example.com", whitelist) is True


class TestWhitelistDomainValidation:
    """Test whitelist validation for domain wildcards."""

    def test_domain_wildcard_allows_matching_emails(self):
        """Test that @domain.com wildcard allows all emails from that domain."""
        from synth_lab.infrastructure.auth.whitelist import is_whitelisted

        whitelist = ["@company.com"]
        assert is_whitelisted("alice@company.com", whitelist) is True
        assert is_whitelisted("bob@company.com", whitelist) is True

    def test_domain_wildcard_rejects_other_domains(self):
        """Test that @domain.com wildcard rejects emails from other domains."""
        from synth_lab.infrastructure.auth.whitelist import is_whitelisted

        whitelist = ["@company.com"]
        assert is_whitelisted("alice@example.com", whitelist) is False

    def test_case_insensitive_domain_matching(self):
        """Test that domain matching is case-insensitive."""
        from synth_lab.infrastructure.auth.whitelist import is_whitelisted

        whitelist = ["@Company.COM"]
        assert is_whitelisted("alice@company.com", whitelist) is True

    def test_subdomain_not_matched_by_parent_domain(self):
        """Test that @company.com does NOT match @mail.company.com."""
        from synth_lab.infrastructure.auth.whitelist import is_whitelisted

        whitelist = ["@company.com"]
        # alice@sub.company.com should NOT match @company.com
        assert is_whitelisted("alice@sub.company.com", whitelist) is False

    def test_mixed_email_and_domain_whitelist(self):
        """Test whitelist with both individual emails and domain wildcards."""
        from synth_lab.infrastructure.auth.whitelist import is_whitelisted

        whitelist = ["alice@example.com", "@company.com"]
        # Individual email match
        assert is_whitelisted("alice@example.com", whitelist) is True
        # Domain wildcard match
        assert is_whitelisted("bob@company.com", whitelist) is True
        # No match
        assert is_whitelisted("eve@hacker.com", whitelist) is False

    def test_whitespace_in_domain_is_stripped(self):
        """Test that whitespace in domain wildcards is properly handled."""
        from synth_lab.infrastructure.auth.whitelist import is_whitelisted

        whitelist = [" @company.com "]
        assert is_whitelisted("alice@company.com", whitelist) is True

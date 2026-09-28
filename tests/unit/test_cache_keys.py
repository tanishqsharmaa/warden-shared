"""Unit tests for cache key generation and query normalization."""
import pytest

from warden_shared.cache.keys import (
    format_lock_key,
    format_pubsub_channel,
    format_query_cache_key,
    normalize_query,
)


def test_query_normalization_whitespace_and_casing():
    q1 = "   How many PTO days?  \n"
    q2 = "how many pto days?"
    assert normalize_query(q1) == normalize_query(q2)
    assert normalize_query(q1) == "how many pto days?"

def test_query_normalization_unicode():
    q_unicode = "caf\u00e9 policy"
    q_decomposed = "cafe\u0301 policy"
    assert normalize_query(q_unicode) == normalize_query(q_decomposed)

def test_format_query_cache_key_deterministic():
    k1 = format_query_cache_key("Employee", "   How many PTO days?  \n")
    k2 = format_query_cache_key("Employee", "how many pto days?")
    assert k1 == k2
    assert k1.startswith("cache:query:Employee:")
    # 64 char hex sha256
    hash_part = k1.split(":")[-1]
    assert len(hash_part) == 64

def test_role_partitioning_isolation():
    k_emp = format_query_cache_key("Employee", "PTO policy")
    k_mgr = format_query_cache_key("Manager", "PTO policy")
    k_hr = format_query_cache_key("HR-Admin", "PTO policy")
    assert k_emp != k_mgr
    assert k_mgr != k_hr
    assert k_emp.startswith("cache:query:Employee:")
    assert k_mgr.startswith("cache:query:Manager:")
    assert k_hr.startswith("cache:query:HR-Admin:")

def test_format_lock_key():
    lock_key = format_lock_key("Manager", "Annual bonus eligibility")
    assert lock_key.startswith("lock:query:Manager:")
    assert len(lock_key.split(":")[-1]) == 64

def test_format_pubsub_channel():
    chan = format_pubsub_channel("HR-Admin", "Executive severance")
    assert chan.startswith("channel:query:HR-Admin:")
    assert len(chan.split(":")[-1]) == 64

def test_invalid_role_tier_raises():
    with pytest.raises(ValueError, match="Invalid role_tier"):
        format_query_cache_key("Contractor", "query")

    with pytest.raises(ValueError, match="Invalid role_tier"):
        format_lock_key("Guest", "query")

    with pytest.raises(ValueError, match="Invalid role_tier"):
        format_pubsub_channel("Anonymous", "query")

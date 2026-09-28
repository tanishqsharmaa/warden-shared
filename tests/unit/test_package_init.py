"""Unit test asserting package metadata and basic importability."""

def test_package_metadata():
    import warden_shared

    assert hasattr(warden_shared, "__version__")
    assert warden_shared.__version__ == "1.0.0"

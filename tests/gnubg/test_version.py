import pytest
import gnubg

VERSION_PATTERN = r"^(\d+!)?(\d+)(\.\d+)+([\.\-\_])?((a(lpha)?|b(eta)?|c|r(c|ev)?|pre(view)?)\d*)?(\.?(post|dev)\d*)?$"

@pytest.fixture
def version_module():
    # Import the version module from within gnubg package
    import gnubg.__version__ as version
    return version

def test_version_attributes(version_module):
    assert hasattr(version_module, "version"), "version attribute is missing"
    assert hasattr(version_module, "__version__"), "__version__ attribute is missing"
    assert hasattr(version_module, "full_version"), "full_version attribute is missing"
    assert hasattr(version_module, "git_revision"), "git_revision attribute is missing"
    assert hasattr(version_module, "release"), "release attribute is missing"
    assert hasattr(version_module, "short_version"), "short_version attribute is missing"

def test_version_format(version_module):
    import re
    assert re.match(VERSION_PATTERN, version_module.short_version), (
        f"Version '{version_module.short_version}' does not match expected format"
    )

def test_git_revision(version_module):
    git_rev = version_module.git_revision
    assert len(git_rev) == 40 or len(git_rev) == 0, "git_revision must be full hash or empty"
    if git_rev:
        assert all(c in '0123456789abcdef' for c in git_rev), "git_revision must be hexadecimal"

def test_version_values_match():
    import gnubg
    import gnubg.__version__ as v

    assert v.version
    assert v.__version__
    assert v.full_version
    assert v.git_revision
    assert v.short_version


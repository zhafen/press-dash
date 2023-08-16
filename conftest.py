import pytest

def pytest_addoption(parser):
    parser.addoption(
        "--skip-nbconvert", action="store_true", default=False, help="skip nbconvert tests"
    )

def pytest_configure(config):
    config.addinivalue_line("markers", "nbconvert: mark as employing nbconvert")

def pytest_collection_modifyitems(config, items):
    if config.getoption("--skip-nbconvert"):
        skip_nbconvert = pytest.mark.skip(reason="will not run if marked")
        for item in items:
            if "nbconvert" in item.keywords:
                item.add_marker(skip_nbconvert)
    else:
        return

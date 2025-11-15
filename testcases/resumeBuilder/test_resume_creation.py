# def test_resume_creation_success():
#     assert True
import time

# def test_resume_creation_failure():
#     assert False, "Failed to create resume due to missing field"
#
# def test_resume_creation_skipped():
#     import pytest
#     pytest.skip("Skipping for now")
#
# def test_resume_creation_long_name():
#     assert True



import pytest

@pytest.mark.smoke
def test_resume_creation_success():
    assert True

@pytest.mark.smoke
def test_resume_creation_failure():
    time.sleep(4)
    assert False, "Failed to create resume due to missing field"

@pytest.mark.positive
def test_resume_creation_skipped():
    pytest.skip("Skipping for now")

# @pytest.mark.positive
# def test_resume_creation_long_name():
#     assert True
#
# @pytest.mark.negative
# def test_resume_creation_invalid_char():
#     assert True
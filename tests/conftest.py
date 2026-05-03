import pytest
from jeans_pattern.measurements import Measurements

@pytest.fixture
def default_measurements():
    """Default sample from the Excel calculator (jeans size ~34)."""
    return Measurements.from_inches(
        waist=34.5, seat=44.0, rise=9.75,
        knee=10.375, bottom=9.75, length=34.0,
    )

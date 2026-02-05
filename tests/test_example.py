from example import calc

def test_calc():
    assert calc(5, 3) == 2  # Path where a > b
    assert calc(3, 5) == 2  # Path where b >= a
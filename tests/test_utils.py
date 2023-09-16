import pytest
from tabpy.utils import *

def test_year_init():
    with pytest.raises(ValueError):
        Year(1939)
    with pytest.raises(ValueError):
        Year(2040)

    Year(1940)
    Year(2039)

def test_year_as_2digit_int():
    assert(Year(1940).as_2digit_int == 40)
    assert(Year(2000).as_2digit_int == 0)
    assert(Year(2039).as_2digit_int == 39)

def test_year_as_2digit_str():
    assert(Year(1940).as_2digit_str == "40")
    assert(Year(2000).as_2digit_str == "00")
    assert(Year(2039).as_2digit_str == "39")

def test_parse_date_aa():
    assert(parse_date_aa("00") == 2000)
    assert(parse_date_aa("39") == 2039)
    assert(parse_date_aa("40") == 1940)

def test_parse_date_aamm():
    assert(parse_date_aamm("0001") == (2000, Month.January))
    assert(parse_date_aamm("3901") == (2039, Month.January))
    assert(parse_date_aamm("4001") == (1940, Month.January))
    assert(parse_date_aamm("0012") == (2000, Month.December))
    assert(parse_date_aamm("3912") == (2039, Month.December))
    assert(parse_date_aamm("4012") == (1940, Month.December))

def test_month_str():
    assert(Month.January.as_2digit_str == "01")
    assert(Month.September.as_2digit_str == "09")
    assert(Month.December.as_2digit_str == "12")
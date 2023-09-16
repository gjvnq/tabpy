from __future__ import annotations
from enum import IntEnum
from typing import NewType, Tuple

# We do this weird thing so that the end user can configure and change the cut off year at runtime
MAX_XXI_CENTURY_YEAR = 39
def MINIMUM_YEAR() -> int:
    return 1900+MAX_XXI_CENTURY_YEAR+1
def MAXIMUM_YEAR() -> int:
    return 2000+MAX_XXI_CENTURY_YEAR

class OutOfRangeError(ValueError):
    pass

class Month(IntEnum):
    January = 1
    February = 2
    March = 3
    April = 4
    May = 5
    June = 6
    July = 7
    August = 8
    September = 9
    October = 10
    November = 11
    December = 12

    @property
    def as_pt_short_name(self) -> str:
        return {1: "jan", 2: "fev", 3: "mar", 4: "abr", 5: "abr", 6: "jun", 7: "jul", 8: "ago", 9: "set", 10: "out", 11: "nov", 12: "dez"}[self]

    @property
    def as_pt_full_name(self) -> str:
        return {1: "janeiro", 2: "fevereiro", 3: "março", 4: "abril", 5: "abril", 6: "junho", 7: "julho", 8: "agosto", 9: "setembro", 10: "outubro", 11: "novembro", 12: "dezembro"}[self]

    @property
    def as_en_short_name(self) -> str:
        return {1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun", 7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"}[self]

    @property
    def as_en_full_name(self) -> str:
        return {1: "January", 2: "February", 3: "March", 4: "April", 5: "May", 6: "June", 7: "July", 8: "August", 9: "September", 10: "October", 11: "November", 12: "December"}[self]

    @property
    def as_2digit_str(self) -> str:
        """Returns the month as a two digit string"""
        return f"{self:02d}"

class Year(int):
    """A two digit year code representing a year in between 1940 and 2039."""

    def __init__(self, val: int):
        if not (MINIMUM_YEAR() <= self <= MAXIMUM_YEAR()):
            raise OutOfRangeError(f"Year must be between {MINIMUM_YEAR()} and {MAXIMUM_YEAR()}")

    def __str__(self):
        return f"{self:04d}"

    @staticmethod
    def from_2digits(val: int|str) -> Year:
        if not isinstance(val, int):
            val = int(val)
        if 0 <= val <= MAX_XXI_CENTURY_YEAR:
            return Year(2000+val)
        elif MAX_XXI_CENTURY_YEAR+1 <= val <= 99:
            return Year(1900+val)
        raise OutOfRangeError("Year in 2 digits must be between 00 and 99")

    @property
    def as_2digit_int(self) -> int:
        """Returns the year as a two digit number"""
        if 2000 <= self <= MAXIMUM_YEAR():
            return self-2000
        elif MINIMUM_YEAR() <= self <= 1999:
            return self-1900
        raise OutOfRangeError(f"Year must be between {MINIMUM_YEAR()} and {MAXIMUM_YEAR()}")

    @property
    def as_2digit_str(self) -> str:
        """Returns the year as a two digit string"""
        return f"{self.as_2digit_int:02d}"

def parse_date_aa(val: str) -> Year:
    assert len(val) == 2, "aa date format must be exactly 2 characters long"
    return Year.from_2digits(val)

def parse_date_aamm(val: str) -> Tuple[Year, Month]:
    assert len(val) == 4, "aamm date format must be exactly 4 characters long"
    aa, mm = val[0:2], val[2:4]
    return Year.from_2digits(aa), Month(int(mm))
from __future__ import annotations
from collections import defaultdict
from dataclasses import FrozenInstanceError, InitVar, dataclass, field, replace
from functools import reduce
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Set, Tuple

def try_str2int(val: str) -> str|int:
    try:
        return int(val)
    except:
        return val

def int_or_none(val: str) -> Optional[int]:
    val = val.strip()
    if val == "":
        return None
    else:
        return int(val)

IntCodeRegex = re.compile(r"^\d+$")
IntRangeRegex = re.compile(r"^(\d+)-(\d+)$")

@dataclass(frozen=True)
class IntRange:
    start: int
    end: int

    def __contains__(self, item: int) -> bool:
        return self.start <= item <= self.end

    def __repr__(self) -> str:
        return "%s(%r, %r)" % (self.__class__.__name__, self.start, self.end)

StrCodeRegex = re.compile(r"^([^-,]+)$")
StrRangeRegex = re.compile(r"^([^-,]+)-([^-,]+)$")

@dataclass(frozen=True)
class StrRange:
    start: str
    end: str

    def __contains__(self, item: str) -> bool:
        min_len = min(len(self.start), len(self.end))
        max_len = max(len(self.start), len(self.end))
        return min_len <= len(item) <= max_len and self.start <= item <= self.end

    def __repr__(self) -> str:
        return "%s(%r, %r)" % (self.__class__.__name__, self.start, self.end)

class InvalidCnvFirstLine(ValueError): pass

Code = int|str
CodeRange = IntRange|StrRange

@dataclass(frozen=True)
class CategorySet:
    code_length: int
    letter_codes: bool
    categories: Set[int, Category]

    def __len__(self):
        return len(self.categories)

    def get_root(self, item: Code) -> Optional[Category]:
        for cat in self.categories.values():
            if ans := cat.get_root(item):
                return ans
        return None

    def get_leaf(self, item: Code) -> Optional[Category]:
        for cat in self.categories.values():
            if ans := cat.get_leaf(item):
                return ans
        return None

    def get_path(self, item: Code) -> Optional[List[Category]]:
        for cat in self.categories.values():
            if ans := cat.get_path(item):
                return ans
        return None

    def __getitem__(self, item: Code) -> Category:
        ans = self.get_leaf(item)
        if ans is not None:
            return ans
        else:
            raise KeyError(item)

    @staticmethod
    def from_cnv_file(contents: str) -> CategorySet:
        """Creates a new CategorySet from the contents of a CNV file."""
        lines = contents.split("\n")
        reFirstLine = re.compile(r"\s*(\d+)\s+(\d+)(?:\s(L))?")
        m = reFirstLine.match(lines[0])
        if m is None:
            raise InvalidCnvFirstLine(lines[0])

        n_categories, code_length, letter_codes = int(m.group(1)), int(m.group(2)), m.group(3)
        if letter_codes is None:
            letter_codes = False
        elif letter_codes == 'L':
            letter_codes = True
        else:
            raise InvalidCnvFirstLine(lines[0])


        # Parse each line
        raw_categories: Dict[int, List[RawCategoryLine]] = defaultdict(list)
        for line in lines[1:]:
            # skip comments
            if line.lstrip().startswith(";"):
                continue

            parsed_line = RawCategoryLine.from_cnv_line(line, letter_codes)
            raw_categories[parsed_line.idx].append(parsed_line)

        # Actually create the categories
        categories: Dict[int, Category] = {}
        parents: Dict[int, int] = {}
        children = defaultdict(list)
        for cat_raw_lines in raw_categories.values():
            cat_raw = cat_raw_lines[0]

            # Join the multiple lines of the category
            if len(cat_raw_lines) == 1:
                codes = cat_raw_lines[0].codes
                code_ranges = cat_raw_lines[0].code_ranges
            else:
                codes = reduce(lambda a, b: a.codes + b.codes, cat_raw_lines)
                code_ranges = reduce(lambda a, b: a.code_ranges + b.code_ranges, cat_raw_lines)

            # Create the object and save relations for latter
            categories[cat_raw.idx] = Category(cat_raw.idx, cat_raw.name, codes, code_ranges)
            if parent_idx := cat_raw.parent_idx is not None:
                parents[cat_raw.idx] = parent_idx
                children[parent_idx].append(cat_raw.idx)

        # Add the children and parents
        for cat in categories.values():
            if parent_idx := parents.get(cat.idx):
                cat.__dict__['parent'] = categories[parent_idx]
                categories[parent_idx].children.append(cat)

        # Possible TODO: check for data validity and loops in the category tree

        # Finish
        return CategorySet(code_length, letter_codes, categories)

    @staticmethod
    def from_cnv_path(file_path: str|Path, encoding: str = 'iso-8859-1') -> CategorySet:
        """Creates a new CategorySet from a path to a CNV file. By default, the file will be read with the ISO-8859-1 (aka Latin-1) encoding as this is what SUS uses on its FTP server."""
        with open(file_path, 'r', encoding=encoding) as f:
            return CategorySet.from_cnv_file(f.read())

@dataclass(frozen=True)
class RawCategoryLine:
    idx: int
    parent_idx: Optional[int]
    name: str
    codes_spec: List[str]
    codes: List[Code]
    code_ranges: List[CodeRange]

    @staticmethod
    def from_cnv_line(line: str, only_strings: bool) -> RawCategoryLine:
        """Creates a new Category from a line of a CNV file."""
        line += " "*70 # ensure the line is long enough
        parent = int_or_none(line[0:3])
        idx = int(line[3:7])
        name = line[9:59].strip()
        codes_spec = line[60:].rstrip()
        codes, code_ranges = parse_category_codes(codes_spec, only_strings)
        return RawCategoryLine(idx, parent, name, codes_spec, codes, code_ranges)


def parse_category_code(item: str, only_strings: bool) -> Code|CodeRange:
    if not only_strings:
        if IntCodeRegex.match(item):
            return int(item)
        if m := IntRangeRegex.match(item):
            start, end = m.group(1), m.group(2)
            return IntRange(int(start), int(end))

    if StrCodeRegex.match(item):
        return str(item)

    if m := StrRangeRegex.match(item):
        start, end = m.group(1), m.group(2)
        return StrRange(start, end)

    raise ValueError(item)

def parse_category_codes(itens: str, only_strings: bool) -> Tuple[List[Code], List[CodeRange]]:
    itens = itens.split(",")
    codes_and_ranges = list(map(lambda x: parse_category_code(x, only_strings), itens))
    codes = list(filter(lambda x: isinstance(x, Code), codes_and_ranges))
    ranges = list(filter(lambda x: isinstance(x, CodeRange), codes_and_ranges))
    return codes, ranges

@dataclass(frozen=True)
class Category:
    idx: int
    name: str
    codes: Set[Code]
    ranges: Set[CodeRange]
    parent: Optional[Category] = None
    children: Dict[int, Category] = field(default_factory=dict)

    @property
    def is_leaf(self) -> bool:
        return len(self.children) == 0

    def __contains__(self, item: Code) -> bool:
        return item in self.codes or any([item in x for x in self.ranges])

    def get_root(self, item: Code) -> Optional[Category]:
        """Returns the root category associated with the requested code."""
        if self.parent is None:
            return self if item in self else None
        else:
            return self.parent.get_root(item)

    def get_leaf(self, item: Code) -> Optional[Category]:
        """Returns the leaf category associated with the requested code."""
        if self.is_leaf:
            return self if item in self else None
        else:
            for child in self.children:
                if ans := child.get(item):
                    return ans
        return None

    def get_path(self, item: Code) -> Optional[List[Category]]:
        if self.is_leaf:
            return [self] if item in self else None

        if item in self:
            for child in self.children.values():
                if ans := child.get_path(item):
                    return [self]+ans
        return None

    def __getitem__(self, item: Code) -> Category:
        ans = self.get_leaf(item)
        if ans is not None:
            return ans
        else:
            raise KeyError(item)

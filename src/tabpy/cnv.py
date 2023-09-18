from __future__ import annotations
from collections import defaultdict
from dataclasses import FrozenInstanceError, InitVar, dataclass, field, replace
from functools import reduce
from pathlib import Path
import re
from typing import Any, Dict, FrozenSet, List, Optional, Set, Tuple

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
    categories: FrozenSet[Category]

    def __len__(self):
        return len(self.categories)

    def get_root(self, item: Code) -> Optional[Category]:
        for cat in self.categories:
            if item in cat:
                return cat
        return None

    def get_leaf(self, item: Code) -> Optional[Category]:
        for cat in self.categories:
            if ans := cat.get_leaf(item):
                return ans
        return None

    def get_path(self, item: Code) -> Optional[List[Category]]:
        for cat in self.categories:
            if ans := cat.get_path(item):
                return ans
        return None

    def __getitem__(self, item: Code) -> Category:
        ans = self.get_leaf(item)
        if ans is not None:
            return ans
        else:
            raise KeyError(item)

    @property
    def flat_categories(self) -> Dict[int, Category]:
        def flatten(cat: Category):
            yield cat
            for child in cat.children:
                flatten(child)

        ans: Dict[int, Category] = {}
        for cat in self.categories:
            for item in flatten(cat):
                ans[item.idx] = item
        ans: List[Category] = list(ans.values())
        ans.sort(key=lambda x: x.idx)
        ans = { item.idx: item for item in ans }
        return ans

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
        raw_category_lines: Dict[int, List[RawCategoryLine]] = defaultdict(list)
        for line in lines[1:]:
            if parsed_line := RawCategoryLine.from_cnv_line(line, letter_codes):
                raw_category_lines[parsed_line.idx].append(parsed_line)

        # Join lines
        raw_categories: Dict[int, RawCategoryLine] = {}
        for raw_cat_lines in raw_category_lines.values():
            # Join the multiple lines of the category if needed
            if len(raw_cat_lines) == 1:
                cat_raw = raw_cat_lines[0]
                raw_categories[cat_raw.idx] = cat_raw
            else:
                cat_raw = raw_cat_lines[0]
                codes = reduce(lambda a, b: a.codes + b.codes, raw_cat_lines)
                code_ranges = reduce(lambda a, b: a.code_ranges + b.code_ranges, raw_cat_lines)
                raw_categories[cat_raw.idx] = replace(cat_raw, codes=codes, code_ranges=code_ranges)

        # Compute children
        direct_children: Dict[int, List[int]] = defaultdict(list)
        roots: Set[int] = set()
        for raw_cat in raw_categories.values():
            if raw_cat.parent_idx is None:
                roots.add(raw_cat.idx)
            else:
                direct_children[raw_cat.parent_idx].append(raw_cat.idx)

        # Make categories
        def make_category(cat_idx: int) -> Category:
            children = []
            for child_idx in direct_children[cat_idx]:
                children.append(make_category(child_idx))
            raw_cat = raw_categories[cat_idx]
            return Category(raw_cat.idx, raw_cat.name, raw_cat.codes, raw_cat.code_ranges, raw_cat.parent_idx, frozenset(children))
        categories: List[Category] = []
        for cat_idx in roots:
            categories.append(make_category(cat_idx))

        # Finish
        return CategorySet(code_length, letter_codes, frozenset(categories))

    @staticmethod
    def from_cnv_path(file_path: str|Path, encoding: str = 'iso-8859-1') -> CategorySet:
        """Creates a new CategorySet from a path to a CNV file. By default, the file will be read with the ISO-8859-1 (aka Latin-1) encoding as this is what SUS uses on its FTP server."""
        with open(file_path, 'r', encoding=encoding) as f:
            return CategorySet.from_cnv_file(f.read())

@dataclass(frozen=True)
class Category:
    idx: int
    name: str
    codes: FrozenSet[Code] = field(default_factory=frozenset)
    ranges: FrozenSet[CodeRange] = field(default_factory=frozenset)
    parent_idx: Optional[int] = None
    children: FrozenSet[Category] = field(default_factory=frozenset)
    _all_codes: InitVar[FrozenSet[Code]] = None
    _all_ranges: InitVar[FrozenSet[CodeRange]] = None

    @property
    def is_leaf(self) -> bool:
        return len(self.children) == 0

    def __contains__(self, item: Code) -> bool:
        return item in self._all_codes or any([item in x for x in self._all_ranges])

    def __post_init__(self, *args):
        self.__dict__['codes'] = frozenset(self.codes)
        self.__dict__['ranges'] = frozenset(self.ranges)
        self.__dict__['children'] = frozenset(self.children)

        all_codes: Set[Code] = set(self.codes)
        all_ranges: Set[CodeRange] = set(self.ranges)
        for child in self.children:
            all_codes = all_codes.union(child._all_codes)
            all_ranges = all_ranges.union(child._all_ranges)
        self.__dict__['_all_codes'] = all_codes
        self.__dict__['_all_ranges'] = all_ranges

    def get_leaf(self, item: Code) -> Optional[Category]:
        for cat in self.children:
            if ans := cat.get_leaf(item):
                return ans
        return self if item in self else None

    def get_path(self, item: Code) -> Optional[List[Category]]:
        for cat in self.children:
            if ans := cat.get_path(item):
                return [self]+ans
        return [self] if item in self else None

@dataclass(frozen=True)
class RawCategoryLine:
    idx: int
    parent_idx: Optional[int]
    name: str
    codes_spec: List[str]
    codes: List[Code]
    code_ranges: List[CodeRange]

    @staticmethod
    def from_cnv_line(line: str, only_strings: bool) -> Optional[RawCategoryLine]:
        """Creates a new Category from a line of a CNV file."""
        if line.strip() == "":
            return None
        if line.lstrip().startswith(";"):
            return None

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

import pytest
from tabpy.cnv import *


regions_cnv = """
      5 2 L
 ; Regiões do Brasil a partir das siglas das UFs
      1  Norte                                              AM,PA,AC,RO,RR,AP
      1  Norte                                              TO
      2  Nordeste                                           MA,PI,CE,RN,PB,AL
      2  Nordeste                                           PE,SE,BA
      3  Centro-Oeste                                       GO,MT,MS,DF
      4  Sudeste                                            MG,SP,RJ,ES
      5  Sul                                                RS,PR,SC
""".strip()

uf_cnv = """
     28  2
     28  00 Ignorado/exterior                                 ,00-99
      1  11 Rondônia                                        11
      2  12 Acre                                            12
      3  13 Amazonas                                        13
      4  14 Roraima                                         14
      5  15 Pará                                            15
      6  16 Amapá                                           16
      7  17 Tocantins                                       17
      8  21 Maranhão                                        21
      9  22 Piauí                                           22
     10  23 Ceará                                           23
     11  24 Rio Grande do Norte                             24
     12  25 Paraíba                                         25
     13  26 Pernambuco                                      26,20
     14  27 Alagoas                                         27
     15  28 Sergipe                                         28
     16  29 Bahia                                           29
     17  31 Minas Gerais                                    31
     18  32 Espírito Santo                                  32
     19  33 Rio de Janeiro                                  33
     20  35 São Paulo                                       35
     21  41 Paraná                                          41
     22  42 Santa Catarina                                  42
     23  43 Rio Grande do Sul                               43
     24  50 Mato Grosso do Sul                              50
     25  51 Mato Grosso                                     51
     26  52 Goiás                                           52
     27  53 Distrito Federal                                53
""".strip()

sex_cnv = """
3 1
      1  Masculino                                          1
      2  Feminino                                           2
      3  Ignorado                                           0,3-9
""".strip()

def test_IntRange_in():
    r = IntRange(1, 7)
    assert(0 not in r)
    assert(1 in r)
    assert(7 in r)
    assert(8 not in r)

def test_StrRange_in():
    r = StrRange("A01", "A98")
    assert("A00" not in r)
    assert("A01" in r)
    assert("B01" not in r)
    assert("A10" in r)
    assert("A98" in r)
    assert("A99" not in r)
    assert("A100" not in r)

def test_parse_category_code_1():
    code = parse_category_code("0", False)
    assert(code == 0)
    code = parse_category_code("A", False)
    assert(code == "A")
    code = parse_category_code("0-9", False)
    assert(code == IntRange(0, 9))
    code = parse_category_code("0-9", True)
    assert(code == StrRange("0", "9"))
    code = parse_category_code("A0-A9", False)
    assert(code == StrRange("A0", "A9"))

def test_RawCategoryLine_from_cnv_line_1():
    raw = RawCategoryLine.from_cnv_line("      3  Ignorado                                           0,3-9", False)
    assert(raw.idx == 3)
    assert(raw.parent_idx is None)
    assert(raw.name == "Ignorado")
    assert(raw.codes_spec == "0,3-9")
    assert(raw.codes == [0])
    assert(raw.code_ranges == [IntRange(3, 9)])

def test_RawCategoryLine_from_cnv_line_2():
    raw = RawCategoryLine.from_cnv_line("     28  00 Ignorado/exterior                                 ,00-99", False)
    assert(raw.idx == 28)
    assert(raw.parent_idx is None)
    assert(raw.name == "00 Ignorado/exterior")
    assert(raw.codes_spec == "  ,00-99")
    assert(raw.codes == ["  "])
    assert(raw.code_ranges == [IntRange(00, 99)])

def test_RawCategoryLine_from_cnv_line_3():
    raw = RawCategoryLine.from_cnv_line("     28  00 Ignorado/exterior                                 ,00-99", True)
    assert(raw.idx == 28)
    assert(raw.parent_idx is None)
    assert(raw.name == "00 Ignorado/exterior")
    assert(raw.codes_spec == "  ,00-99")
    assert(raw.codes == ["  "])
    assert(raw.code_ranges == [StrRange("00", "99")])

def test_CategorySet_from_cnv_file_1():
    cats = CategorySet.from_cnv_file(sex_cnv)
    assert(len(cats) == 3)
    assert(cats[0] == Category(3, 'Ignorado', [0], [IntRange(3, 9)], None, {}))
    assert(cats[1] == Category(1, 'Masculino', [1], [], None, {}))
    assert(cats[2] == Category(2, 'Feminino', [2], [], None, {}))
    assert(cats[9] == Category(3, 'Ignorado', [0], [IntRange(3, 9)], None, {}))
    assert(cats[9] == cats[0])
    assert(cats[0] == cats.get_leaf(0))
    assert(cats[4] == cats.get_leaf(4))
    assert(cats.get_path(1) == [Category(1, 'Masculino', [1], [], None, {})])

def test_CategorySet_from_cnv_file_2():
    cats = CategorySet.from_cnv_file(regions_cnv)
    assert(len(cats) == 5)
    assert(cats["SP"] == Category(4, 'Sudeste', ['MG', 'SP', 'RJ', 'ES'], [], None, {}))
    print(cats)
    with pytest.raises(KeyError):
        cats["UF"]
    with pytest.raises(KeyError):
        cats["sp"]

# TODO: hierarchal examples
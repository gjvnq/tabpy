from enum import StrEnum

class DefFileLineType(StrEnum):
    COMMENT = ";" # título ou comentário
    HTML_BEFORE = "H" #texto em HTML a ser incluído antes do questionário e do resultado da tabulação
    HTML_AFTER = "F" # texto em HTML a ser incluído após o questionário e do resultado da tabulação
    FILE_PATTERN = "A" # especificação de nomes para os arquivos de dados
    SELECTION_VAR_DEF = "S" # definição de variável de seleção
    LINE_VAR_DEF = "L" # definição de variável de linha
    COLUMN_VAR_DEF = "C" # definição de variável de coluna
    DOUBLE_VAR_DEF = "D" # definição dupla (variável de linha e de quadro)
    TRIPLE_VAR_DEF = "T" # definição tripla (variável de linha, de coluna e de quadro)
    INCREMENT_VAR_DEF = "I" # definição de variável de conteúdo para movimento ou fluxo (incremento ou indicador)
    ACCUMULATOR_VAR_DEF = "E" # definição de variável de conteúdo para estoque ou saldo (incremento)
    PROPORTION_RESULT = "%" # resultado da tabulação na forma de proporção
    FORMATTING_OPTIONS = "O" # opções de formatação do formulário e do resultado
    FORMATTING_OPTIONS = "X" # ???
    FORMATTING_OPTIONS = "N" # ???
    FORMATTING_OPTIONS = "R" # ???
    FORMATTING_OPTIONS = "G" # ???

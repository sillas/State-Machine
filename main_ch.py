import re
from logging_config import _i


def t():
    condition = "[5, 10, 20] contains $.age"

    # Padrão que captura qualquer coisa antes e depois de 'contains'
    # Captura: listas [], dicts {}, strings com aspas, json paths $., números, etc.
    pattern = r'(.+?)\s+contains\s+(.+)'

    match = re.match(pattern, condition.strip())
    if match:
        term_1 = match.group(1).strip()
        term_2 = match.group(2).strip()
        # Troca os termos e substitui 'contains' por 'in'
        text = f"{term_2} in {term_1}"
    else:
        # Se não reconhecer o padrão, retorna a mesma string
        text = condition

    _i(text)


if __name__ == "__main__":
    t()

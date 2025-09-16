# Testes do Sistema de State Machine

Este módulo contém testes unitários para as classes principais do sistema de State Machine, incluindo:
- `StateMachine` (localizada em `core/state_machine.py`)
- `StatementEvaluator` (localizada em `core/statement_evaluator.py`)
- `StatementBuilder` e operadores (localizados em `core/statement_models.py`)

## Funcionalidades Testadas

### 1. Classe StateMachine
- **Inicialização da StateMachine**
  - Validação de parâmetros
  - Cálculo correto de timeout
  - Verificação de machine_tree vazio

- **Execução bem-sucedida**
  - Fluxo de execução correta entre estados
  - Passagem de eventos/contexto entre estados
  - Retorno do resultado final

- **Condições de Erro**
  - Erro quando um estado não é encontrado
  - Erro quando a execução de um estado falha
  - Timeout da máquina de estados
  - Timeout de um estado individual

### 2. Classe StatementEvaluator
- Avaliação correta de statements com diferentes condições
- Processamento de contextos complexos usando JSONPath
- Manipulação de operadores lógicos (AND, OR)
- Avaliação de diferentes tipos de operadores de comparação

### 3. Classe StatementBuilder e Operadores
- Funcionalidade dos métodos `when`, `and_when` e `or_when`
- Construção de statements com múltiplas condições
- Uso dos diferentes operadores de comparação
- Validação da estrutura dos statements gerados

## Como Executar

Para executar todos os testes:
```bash
# 1. Ativar o ambiente virtual
source .venv/bin/activate

# 2. Executar todos os testes
pytest
```

Para executar testes específicos:
```bash
# Executar apenas os testes da StateMachine
pytest tests/core/test_state_machine.py

# Executar apenas os testes do StatementEvaluator
pytest tests/core/test_statement_evaluator.py

# Executar apenas os testes dos operadores do StatementBuilder
pytest tests/core/test_statement_builder_operators.py
```

## Requisitos

- Python 3.10 ou superior
- Ambiente virtual Python ativado
- Dependências instaladas conforme o arquivo `requirements.txt` ou usar `uv`

## Observações

- Os testes da `StateMachine` simulam o comportamento usando mocks para os objetos `Lambda`, permitindo o controle preciso do fluxo de execução e a simulação de condições de erro.
- Os testes do `StatementEvaluator` utilizam exemplos comuns encontrados no arquivo `common_statements.py`.
- Os testes do `StatementBuilder` focam especificamente na construção de statements com múltiplos operadores lógicos.
# JSONPath Cache Wrapper - Documentação

## Visão Geral

A funcionalidade de JSONPath Cache Wrapper permite que você use funções cached de forma muito mais intuitiva, passando dados brutos e deixando o sistema extrair automaticamente os valores necessários usando JSONPath.

## Como Funciona

### 1. Geração do Cache
Quando uma função é gerada e cacheada, o sistema agora:
- Salva o código da função (como antes)
- **NOVO**: Salva nos metadados o mapeamento entre parâmetros da função e os JSONPath originais

### 2. Carregamento do Cache
Quando você carrega uma função do cache, você pode:
- **Método Antigo**: Carregar a função diretamente e passar parâmetros específicos
- **Método Novo**: Usar o wrapper JSONPath que aceita dados brutos

## Uso Prático

### Exemplo Básico

```python
from parser import parse_cond
from demo_usage import load_cached_function_with_jsonpath

# Definir condições com JSONPath
conditions = [
    "when $.user.age gte 18 and $.user.status eq 'active' then #adult-active",
    "when $.user.age lt 18 then #minor",
    "#default"
]

states = {
    "adult-active": {"name": "adult_active_state"},
    "minor": {"name": "minor_state"},
    "default": {"name": "default_state"}
}

# Gerar cache
parse_cond("user-evaluation", conditions, states)

# Carregar com wrapper JSONPath
wrapper = load_cached_function_with_jsonpath("user-evaluation")

# Usar com dados brutos - muito mais intuitivo!
result = wrapper({
    "user": {
        "age": 25,
        "status": "active"
    }
})
# resultado: "adult_active_state"
```

### Comparação: Antes vs Depois

#### Método Antigo (ainda funciona)
```python
cached_function = load_cached_function(cache_file_path, function_name)
result = cached_function(25, "active")  # Precisa saber a ordem exata dos parâmetros
```

#### Método Novo (recomendado)
```python
wrapper = load_cached_function_with_jsonpath("user-evaluation")
result = wrapper({
    "user": {"age": 25, "status": "active"}
})  # Dados naturais, extração automática
```

## Vantagens do Novo Método

1. **Mais Intuitivo**: Você passa os dados como eles existem naturalmente
2. **Menos Propenso a Erros**: Não precisa se preocupar com ordem de parâmetros
3. **Mais Flexível**: Funciona com estruturas de dados complexas e aninhadas
4. **Manutenível**: Mudanças nos JSONPath são transparentes para o código cliente

## Estrutura dos Metadados

O arquivo de metadados agora inclui:

```json
{
  "hash": "6c1f3b6f...",
  "choice_name": "user-evaluation",
  "cache_file": "/path/to/cached/function.py",
  "created_at": "...",
  "jsonpath_params": {
    "_user_age": "$.user.age",
    "_user_status": "$.user.status"
  }
}
```

## Exemplo Avançado

```python
# Condições complexas
conditions = [
    "when $.customer.profile.age gte 25 and $.order.total gt 100 and $.customer.tier eq 'premium' then #premium-discount",
    "when $.order.items contains 'electronics' then #electronics-promo",
    "#no-discount"
]

# Uso com dados complexos
data = {
    "customer": {
        "profile": {"age": 30},
        "tier": "premium"
    },
    "order": {
        "total": 150,
        "items": ["laptop", "mouse"]
    }
}

result = wrapper(data)  # "premium_discount_applied"
```

## API Reference

### `load_cached_function_with_jsonpath(choice_name: str)`
Carrega uma função cached e retorna um wrapper que aceita dados brutos.

**Parâmetros:**
- `choice_name`: Nome da escolha/função a ser carregada

**Retorna:**
- Função wrapper que aceita `data: dict` e retorna o resultado da função cached

**Exceções:**
- `ValueError`: Se não encontrar metadados ou arquivo de cache
- `ImportError`: Se não conseguir carregar o módulo cached

### `create_jsonpath_wrapper(cached_function, jsonpath_params: dict)`
Cria um wrapper JSONPath para uma função cached.

**Parâmetros:**
- `cached_function`: Função cached carregada
- `jsonpath_params`: Mapeamento parâmetro -> JSONPath

**Retorna:**
- Função wrapper

## Tratamento de Erros

O wrapper trata automaticamente:
- **JSONPath não encontrado**: Log de warning, parâmetro recebe `None`
- **Dados malformados**: Exceptions do jsonpath_query são propagadas
- **Parâmetros faltando**: Python levanta TypeError normalmente

## Compatibilidade

- ✅ **Backward Compatible**: Funções antigas continuam funcionando
- ✅ **Cache Existente**: Cache antigo é automaticamente invalidado e regenerado
- ✅ **Múltiplas Versões**: Sistema de hash detecta mudanças e regenera quando necessário
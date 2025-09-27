# Sistema de Cache para Parser de Condições

Este sistema implementa um cache baseado em hash para otimizar o processamento de condições no parser.

## Características

### Hash-Based Cache Invalidation
- Gera um hash SHA256 das condições, nome da escolha e estados
- Detecta automaticamente mudanças nas configurações
- Evita reprocessamento desnecessário

### Armazenamento em Arquivos
- Salva funções geradas em arquivos Python no diretório `conditions_cache/`
- Mantém metadados em arquivos JSON para controle do cache
- Limpa automaticamente versões antigas quando há mudanças

### Vantagens
- **Performance**: Evita reprocessamento de condições já compiladas
- **Persistência**: Cache sobrevive entre execuções do programa
- **Invalidação Inteligente**: Detecta mudanças automaticamente
- **Limpeza Automática**: Remove arquivos de cache obsoletos

## Estrutura do Cache

```
conditions_cache/
├── __init__.py                     # Torna o diretório um pacote Python
├── {choice_name}_{hash}.py         # Função cached gerada
└── {choice_name}_metadata.json     # Metadados do cache
```

## Uso

### Função Principal
```python
from parser import parse_cond

# Primeira chamada - gera e salva no cache
cache_path = parse_cond(choice_name, conditions, states)

# Segunda chamada com mesmas condições - usa cache
cache_path = parse_cond(choice_name, conditions, states)  # Usa cache!

# Chamada com condições diferentes - gera nova função
cache_path = parse_cond(choice_name, modified_conditions, states)  # Nova geração
```

### Carregamento de Funções Cached
```python
import importlib.util

def load_cached_function(cache_file_path: str, function_name: str):
    spec = importlib.util.spec_from_file_location("cached_module", cache_file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load spec from {cache_file_path}")
    
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    return getattr(module, function_name)

# Usar a função cached
cached_func = load_cached_function(cache_path, "choice_name")
result = cached_func(param1, param2)
```

## Exemplo de Uso

Veja `test_cache.py` e `demo_usage.py` para exemplos completos de como usar o sistema.

## Arquivos de Teste

- `test_cache.py`: Demonstra o funcionamento do cache invalidation
- `demo_usage.py`: Mostra como carregar e usar funções cached
- `parser.py`: Implementação principal com sistema de cache

## Melhorias Implementadas

1. **Cache baseado em hash**: Detecta mudanças automaticamente
2. **Persistência**: Cache mantido entre execuções
3. **Limpeza automática**: Remove arquivos obsoletos
4. **Metadados**: Rastreamento de informações do cache
5. **Logs informativos**: Mostra quando cache é usado ou quando nova função é gerada
# Referência da API - Parser YAML

Este documento descreve a API do parser YAML para carregar e executar máquinas de estado definidas em arquivos YAML.

## StateMachineParser

Classe principal para carregar e converter definições YAML em objetos `StateMachine` executáveis.

### Construtor

```python
from core.parser_machine import StateMachineParser

parser = StateMachineParser(machine_definitions_file: str)
```

**Parâmetros:**
- `machine_definitions_file`: Caminho para o arquivo YAML com as definições

**Exemplo:**
```python
parser = StateMachineParser('machines/sm_description.yml')
```

### Métodos

#### `parse() -> StateMachine`

Converte as definições YAML carregadas em um objeto `StateMachine` executável.

**Retorno:** Instância de `StateMachine` pronta para execução

**Exemplo:**
```python
parser = StateMachineParser('machines/sm_description.yml')
machine = parser.parse()

if machine:
    result = machine.run({"value": 50})
    print(result)
```

#### `parse_machine(machine_config: dict) -> StateMachine`

Converte uma configuração específica de máquina em objeto `StateMachine`. Usado internamente e para parsing de sub-máquinas em estados paralelos.

Para uso direto, analise o exemplo em `machines/example_machine.py`

**Parâmetros:**
- `machine_config`: Dicionário com configuração da máquina

**Retorno:** Instância de `StateMachine`

## StateConfigurationProcessor

Classe interna que processa configurações de estados e constrói blocos de execução.

### Tipos de Estado Suportados

#### 1. Estado Lambda

Executa uma função lambda externa:

```yaml
states:
  meu-estado:
    name: nome_da_funcao
    type: lambda
    timeout: 30  # opcional
```

**Processamento:**
- Verifica se o arquivo lambda existe em `{lambda_dir}/{name}/main.py`
- Cria instância de `Lambda` com configurações apropriadas
- Aplica timeout se especificado

#### 2. Estado Choice

Executa lógica condicional:

```yaml
states:
  decisao:
    name: nome_da_decisao
    type: choice
```

**Processamento:**
- Resolve variáveis de condição
- Substitui referências de hash (`#estado`) por nomes reais
- Cria instância de `Choice` com condições processadas

#### 3. Estado Parallel

Executa múltiplos workflows simultaneamente:

```yaml
states:
  paralelo:
    name: execucao_paralela
    type: parallel
    workflows:
      - workflow-1
      - workflow-2
```

**Processamento:**
- Cria `StateMachine` para cada workflow listado
- Configura execução paralela via `Parallel`

## Exemplo de Uso Completo

```python
from core.parser_machine import StateMachineParser
import logging

# Configurar logging para ver o progresso
logging.basicConfig(level=logging.INFO)

def executar_workflow_yaml():
    try:
        # Carregar definições do arquivo YAML
        parser = StateMachineParser('machines/sm_description.yml')
        
        # Converter para StateMachine executável
        machine = parser.parse()
        
        if not machine:
            print("Erro: não foi possível carregar a máquina")
            return
        
        # Preparar dados de entrada
        event = {
            "value": 25,
            "usuario": {"nome": "João", "idade": 30}
        }
        
        # Executar o workflow
        resultado = machine.run(event)
        
        print(f"Resultado final: {resultado}")
        
    except FileNotFoundError:
        print("Arquivo YAML não encontrado")
    except Exception as e:
        print(f"Erro durante execução: {e}")

# Executar
executar_workflow_yaml()
```

## Validação e Tratamento de Erros

O parser inclui validação robusta:

### Erros Comuns

1. **Arquivo não encontrado:**
```python
FileNotFoundError: Error: machines/arquivo.yml not found.
```

2. **YAML inválido:**
```python
yaml.YAMLError: Error parsing YAML: ...
```

3. **Estado não encontrado:**
```python
KeyError: State key not found: nome-do-estado
```

4. **Lambda não encontrado:**
```python
ModuleNotFoundError: Lambda lambdas/exemplo/funcao/main.py not found.
```

5. **Variável de condição não encontrada:**
```python
ValueError: Conditions for choice nome_choice do not exist!
```

### Estratégias de Debug

```python
import logging

# Ativar logs detalhados
logging.basicConfig(level=logging.DEBUG)

# Criar parser com logs
parser = StateMachineParser('machines/problema.yml')

try:
    machine = parser.parse()
    result = machine.run({"test": True})
except Exception as e:
    logging.error(f"Erro detalhado: {e}")
    # Analisar logs para identificar o problema
```

## Integração com Código Python

### Usando junto com definição programática:

```python
from core.parser_machine import StateMachineParser
from core.state_machine import StateMachine
from core.handlers.lambda_handler import Lambda

def workflow_hibrido():
    # Carregar parte do workflow do YAML
    parser = StateMachineParser('machines/parte1.yml')
    parte1 = parser.parse()
    
    # Criar parte adicional programaticamente  
    parte2 = StateMachine("parte2", [
        Lambda("processar_resultado", None, "lambdas/custom")
    ])
    
    # Combinar ou executar sequencialmente
    resultado1 = parte1.run({"input": "dados"})
    resultado_final = parte2.run(resultado1)
    
    return resultado_final
```

### Criando Parser Customizado:

```python
from core.parser_machine import StateMachineParser

class MeuParser(StateMachineParser):
    def __init__(self, arquivo_yaml, configuracoes_extras=None):
        super().__init__(arquivo_yaml)
        self.configuracoes_extras = configuracoes_extras or {}
    
    def parse(self):
        machine = super().parse()
        # Aplicar configurações extras
        if self.configuracoes_extras.get('timeout_global'):
            # Aplicar timeout global
            pass
        return machine
```

## Performance e Otimização

### Cache de Parsing

```python
import functools
from core.parser_machine import StateMachineParser

@functools.lru_cache(maxsize=10)
def get_cached_machine(arquivo_yaml):
    parser = StateMachineParser(arquivo_yaml)
    return parser.parse()

# Uso com cache
machine = get_cached_machine('machines/frequente.yml')
```

### Validação Prévia

```python
def validar_yaml_antes_execucao(arquivo_yaml):
    try:
        parser = StateMachineParser(arquivo_yaml)
        machine = parser.parse()
        return True, "YAML válido"
    except Exception as e:
        return False, f"Erro de validação: {e}"

# Validar antes de usar em produção
valido, mensagem = validar_yaml_antes_execucao('machines/producao.yml')
if valido:
    # Prosseguir com execução
    pass
```

## Limitações Conhecidas

1. **Referências circulares**: O parser ainda não detecta loops infinitos em workflows
2. **Validação de schema**: Ainda não há validação formal do schema YAML
3. **Substituição de variáveis**: Limitada aos padrões `$variavel` (choice) e `#estado` (estados)
4. **Aninhamento**: Não suporta definições de máquina aninhadas (sequênciais) no mesmo arquivo yml

## Próximos Passos

- Consulte [Configuração YAML](yaml-configuration.md) para sintaxe detalhada
- Veja [Exemplos YAML](yaml-examples.md) para casos de uso práticos
- Examine os arquivos de exemplo em `machines/` para referência
# Exemplos YAML do State Machine

Este documento apresenta exemplos práticos de configuração YAML para diferentes cenários de uso.

## Exemplo 1: Máquina Sequencial Simples

**Arquivo**: `machines/sm_description.yml`

```yaml
entry: example-machine

example-machine:
  name: 'example machine'
  lambda_dir: lambdas/example

  tree:
    center-state: in-or-out
    in-or-out: $ioo-statements
    outer-state: null
  
  states:
    center-state:
      name: center_state
      type: lambda
    
    in-or-out:
      name: in_or_out
      type: choice
    
    outer-state:
      name: outer_state
      type: lambda
  
  vars:
    $ioo-statements:
      - "when ($.value gt 10) and ($.value lt 53) then #center-state else #outer-state"
```

### Como Funciona

1. **Entrada**: Executa `center_state` lambda
2. **Decisão**: Avalia se `value` está entre 10 e 53
3. **Saída**:
   - Se `value` ∈ [11, 52] → volta para `center_state`
   - Caso contrário → vai para `outer_state` (final)

### Estrutura de Arquivos Necessária

```
lambdas/example/
├── center_state/
│   └── main.py
└── outer_state/
    └── main.py
```

### Exemplo de Lambda

```python
# lambdas/example/center_state/main.py
def lambda_handler(event, context):
    event["value"] += 1
    return event
```

## Exemplo 2: Execução Paralela

**Arquivo**: `machines/sm_p_description.yml`

```yaml
entry: example-machine

# Primeira máquina para execução paralela
mc_01:
  name: machine_01
  lambda_dir: lambdas/example

  tree:
    center-state: null
  
  states:
    center-state:
      name: center_state
      type: lambda 

# Segunda máquina para execução paralela
mc_02:
  name: machine_02
  lambda_dir: lambdas/example

  tree:
    outer-state: null
  
  states:
    outer-state:
      name: outer_state
      type: lambda 

# Máquina principal que orquestra a execução paralela
example-machine:
  name: 'example machine'
  lambda_dir: lambdas/example

  tree:
    run-state: null # Neste caso, não temos mais estados.
  
  states:
    run-state:
      name: unique_state
      type: parallel
      workflows:
        - mc_01
        - mc_02
```

### Como Funciona

1. **Entrada**: Executa estado paralelo `unique_state`
2. **Paralelo**: Executa simultaneamente um ou mais máquinas:
   - `mc_01`: executa `center_state`
   - `mc_02`: executa `outer_state`
   # Use para fluxos complexos ou para execução paralela de estados.
3. **Resultado**: Retorna dados de ambos workflows

### Resultado Esperado

```python
{
    'machine_01': resultado_do_center_state,
    'machine_02': resultado_do_outer_state
}
```

## Exemplo 3: Decisões Complexas

```yaml
entry: workflow-complexo

workflow-complexo:
  name: 'Workflow com Múltiplas Decisões'
  lambda_dir: lambdas/business

  tree:
    validar-usuario: decisao-idade
    decisao-idade: $condicoes-idade
    processar-adulto: decisao-premium
    processar-menor: notificar-responsavel
    decisao-premium: $condicoes-premium
    upgrade-premium: null
    manter-basico: null
    notificar-responsavel: null
  
  states:
    validar-usuario:
      name: validar_usuario
      type: lambda
    
    decisao-idade:
      name: verificar_idade
      type: choice
    
    processar-adulto:
      name: processar_adulto
      type: lambda
    
    processar-menor:
      name: processar_menor
      type: lambda
      
    decisao-premium:
      name: verificar_premium
      type: choice
      
    upgrade-premium:
      name: upgrade_premium
      type: lambda
      
    manter-basico:
      name: manter_basico
      type: lambda
      
    notificar-responsavel:
      name: notificar_responsavel
      type: lambda
  
  vars:
    $condicoes-idade:
      - "when $.usuario.idade gte 18 then #processar-adulto else #processar-menor"
      
    $condicoes-premium:
      - "when ($.usuario.pontos gt 1000) and ($.usuario.ativo eq true) then #upgrade-premium"
      - "#manter-basico"
```

### Fluxo de Execução

```
validar-usuario
       ↓
  decisao-idade
    ↓        ↓
adulto      menor
   ↓          ↓
decisao    notificar
premium   responsavel
 ↓    ↓
up   basico
grade
```

## Exemplo 4: Timeout e Configurações Avançadas

```yaml
entry: workflow-robusto

workflow-robusto:
  name: 'Workflow com Timeouts'
  lambda_dir: lambdas/robusto

  tree:
    processar-dados: validar-resultado
    validar-resultado: $validacao
    retry-processamento: null
    finalizar-sucesso: null
  
  states:
    processar-dados:
      name: processar_dados_complexos
      type: lambda
      timeout: 300  # 5 minutos
    
    validar-resultado:
      name: validar_resultado
      type: choice
    
    retry-processamento:
      name: retry_processamento
      type: lambda
      timeout: 180  # 3 minutos
      
    finalizar-sucesso:
      name: finalizar_sucesso
      type: lambda
  
  vars:
    $validacao:
      - "when $.resultado.status eq 'success' then #finalizar-sucesso"
      - "when $.tentativas lt 3 then #retry-processamento"
      - "#finalizar-sucesso"  # fallback
```

## Exemplo 5: Múltiplas Condições

```yaml
entry: classificador

classificador:
  name: 'Sistema de Classificação'
  lambda_dir: lambdas/classificador

  tree:
    analisar-input: classificar
    classificar: $regras-classificacao
    categoria-a: null
    categoria-b: null
    categoria-c: null
    categoria-default: null
  
  states:
    analisar-input:
      name: analisar_input
      type: lambda
    
    classificar:
      name: aplicar_regras
      type: choice
      
    categoria-a:
      name: processar_categoria_a
      type: lambda
      
    categoria-b:
      name: processar_categoria_b
      type: lambda
      
    categoria-c:
      name: processar_categoria_c
      type: lambda
      
    categoria-default:
      name: processar_default
      type: lambda
  
  vars:
    $regras-classificacao:
      - "when ($.score gt 0.8) and ($.tipo eq 'premium') then #categoria-a"
      - "when ($.score gt 0.6) and ($.usuario.verificado eq true) then #categoria-b"
      - "when $.score gt 0.4 then #categoria-c"
      - "#categoria-default"  # caso padrão
```

## Padrões Comuns

### 1. Estado Final

Estados que não têm próximo estado:

```yaml
tree:
  ultimo-estado: null
```

### 2. Loop Condicional

Estados que podem voltar para si mesmos:

```yaml
vars:
  $loop-condicional:
    - "when $.continuar eq true then #mesmo-estado else #proximo-estado"
```

### 3. Fallback Padrão

Sempre inclua um caso padrão em choices:

```yaml
vars:
  $condicoes_1: # usando condição padrão
    - "when $.condicao1 then #estado1"
    - "when $.condicao2 then #estado2"
    - "#estado-padrao"
  $condicoes_2: # usando else
    - "when $.condicao1 then #estado1 else #estado-padrao"
```

## Dicas de Boas Práticas

1. **Nomes Descritivos**: Use nomes claros para estados e máquinas
2. **Timeouts**: Defina timeouts para operações longas
3. **Fallbacks**: Sempre tenha um caso padrão em choices
4. **Modularidade**: Separe workflows complexos em máquinas menores
5. **Documentação**: Comente configurações complexas

## Validação

Para validar sua configuração:

```python
from core.parser_machine import StateMachineParser

parser = StateMachineParser('seu-arquivo.yml')
machine = parser.parse()

if machine:
    result = machine.run({"test": "data"})
```

## Próximos Passos

- Consulte [Configuração YAML](yaml-configuration.md) para detalhes técnicos
- Veja [Referência da API](api-reference.md) para integração programática
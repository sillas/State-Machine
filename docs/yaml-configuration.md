# Configuração YAML para State Machine

Este documento descreve como definir máquinas de estado usando arquivos YAML no projeto State Machine.

## Estrutura Básica

Um arquivo YAML de configuração de máquina de estado possui a seguinte estrutura:

```yaml
entry: nome-da-maquina-principal

maquina-1:
  name: 'Nome da Máquina'
  lambda_dir: diretorio/das/lambdas # Diretório raiz dos lambdas
  tree:
    estado-1: proximo-estado
    estado-2: null
  states:
    estado-1:
      name: nome_real_do_estado # Diretório do lambda dentro de "lambda_dir"
      type: lambda|choice|parallel
  vars: # usado para as definições dos estados "Choice"
    $variavel: valor
```

## Elementos Principais

### 1. Entry Point (`entry`)

Define qual máquina será executada como ponto de entrada:

```yaml
entry: example-machine
```

### 2. Definição de Máquina

Cada máquina possui:

- **name**: Nome descritivo da máquina
- **lambda_dir**: Diretório onde estão as funções lambda
- **tree**: Fluxo de execução entre estados
- **states**: Definições detalhadas dos estados
- **vars**: Variáveis reutilizáveis (opcional)

### 3. Tree (Árvore de Execução)

Define o fluxo entre estados:

```yaml
tree:
  primeiro-estado: segundo-estado    # primeiro-estado → segundo-estado
  segundo-estado: terceiro-estado    # segundo-estado → terceiro-estado
  terceiro-estado: null              # terceiro-estado (final)
```

### 4. States (Definições de Estados)

#### Estado Lambda

Executa uma função lambda:

```yaml
states:
  meu-estado:
    name: nome_da_funcao_lambda
    type: lambda
    timeout: 30  # opcional, em segundos (default: 60s para tipo lambda)
```

A função lambda deve estar em: `{lambda_dir}/{name}/main.py`
E possuir o método de entrada `lambda_handler(event: Any, context: dict[str, Any])`

#### Estado Choice

Executa lógica condicional:

```yaml
states:
  decisao:
    name: nome_da_decisao
    type: choice
```

Requer variáveis com as condições:

```yaml
vars:
  $condicoes: # lista
    - "when $.valor gt 10 then #estado-a else #estado-b"
```

#### Estado Parallel

Executa múltiplos workflows em paralelo:

```yaml
states:
  paralelo:
    name: execucao_paralela
    type: parallel
    workflows:
      - workflow-1
      - workflow-2
```

### 5. Variables (Variáveis)

Permitem reutilização de valores complexos no Choice:

```yaml
vars:
  $minhas-condicoes:
    - "when ($.value gt 10) and ($.value lt 53) then #center-state else #outer-state"
```

Uso no tree:
```yaml
tree:
  estado-choice: $minhas-condicoes
```

## Referências de Estado

### Referência por Hash (#)

Dentro de condições, use `#` para referenciar estados definidos:

```yaml
vars:
  $condicoes:
    - "when $.valor gt 100 then #estado-caro else #estado-barato"
```

Isso será convertido automaticamente para os nomes reais dos estados.
Você pode usar os nomes reais (em name) entre aspas simples, se preferir.

## Sintaxe de Condições

As condições seguem a sintaxe natural:

```yaml
# Condição simples
"when $.idade gt 18 then #adulto else #menor"

# Condições complexas
"when ($.idade gt 18) and ($.nome starts_with 'João') then #valido"
# ou
"when $.idade gt 18 and $.nome starts_with 'João' then #valido"

# Condições aninhadas
"when $.preco gt 100 then #caro else when $.preco gt 50 then #medio else #barato"

# Condições complexas (lista)
- "when exist $.error then #error-handler-state"
- "when $.result eq 'emal' then #send-email-state"
- "when $.result eq 'whatsapp' then #send-wa-state"
- "#default-state" #TODO
```

### Operadores Suportados

- **Comparação**: `gt`, `lt`, `eq`, `neq`, `gte`, `lte`
- **String**: `contains`, `starts_with`, `ends_with`
- **Listas**: `contains`
- **Estrutura**: `exist` #TODO
- **Lógicos**: `and`, `or`, `not`
- **Agrupamento**: `(condição)`

## Exemplos de uso:
- **Comparação**: `term op term`
- **String**: `term op literal`

## Literal:
- String: `'string', '10'` # Aspas simples
- Number: 10, 15.7 # inteiro e ponto flutuate
- Lista Vazia: `[]` #TODO
- Dicionário Vazio: `{}` #TODO
**Obs.:** Não é permitido listas ou dicionários "literais", apenas via JSONPath.

### JSONPath

Use JSONPath para acessar dados:

```yaml
"when $.usuario.idade gt 25 then #senior"
"when $.itens[0] eq 'premium' then #vip"
"when $.lista eq [] then #vazia"
```

## Exemplo Completo

Veja `machines/sm_description.yml` para um exemplo funcional completo.

## Próximos Passos

- Consulte [Exemplos YAML](yaml-examples.md) para casos de uso práticos
- Veja [Referência da API](api-reference.md) para detalhes técnicos
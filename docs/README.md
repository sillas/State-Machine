# Documentação do State Machine

Esta pasta contém a documentação detalhada para o projeto State Machine.

## Conteúdo

- [Definição via YAML](yaml-configuration.md) - Como definir máquinas de estado usando arquivos YAML
- [Exemplos YAML](yaml-examples.md) - Exemplos práticos e casos de uso
- [Referência da API](api-reference.md) - Documentação técnica da API

## Visão Geral

O State Machine suporta duas formas de definição:

1. **Programática** - Definindo máquinas diretamente em Python
2. **Declarativa** - Usando arquivos YAML para configuração

A documentação nesta pasta foca na abordagem declarativa usando YAML, que oferece:

- Separação clara entre lógica e configuração
- Reutilização de componentes
- Facilidade de manutenção
- Versionamento de workflows

## Como Usar

1. Defina sua máquina de estado em um arquivo YAML
2. Use o `StateMachineParser` para carregar
3. Implemente as funções lambda necessárias
4. Execute usado [sua_máquina].run(input_data)

Consulte os documentos específicos para detalhes completos.
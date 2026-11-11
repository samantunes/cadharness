# UC-NNN — <Verbo no infinitivo + objeto>

| Campo | Valor |
|---|---|
| Release | R<n> |
| Situação | Planejado \| Parcial \| Implementado. Diga o que já existe e o que falta implementar |
| Origem | <requisitos, histórias ou conversas que originaram este caso de uso> |
| Regras da release | <IDs das regras globais da release que se aplicam> |
| Módulos | `src/modules/<modulo>` (um ou mais) |
| Telas | <telas afetadas, ou "Nenhuma"> |
| Endpoints | <endpoints HTTP ou ferramentas MCP criadas/alteradas, ou "Nenhum" com o motivo> |
| Documentação visual | <links para diagramas, PDFs, protótipos> |
| Pendências | PEND-NN (ver `../pendencias.md`) |

## Objetivo

<Um ou dois parágrafos: o que este caso de uso entrega, para quem e com que meta mensurável.
Diga também o que fica para outro caso de uso.>

## Atores

| Ator | Papel neste caso de uso |
|---|---|
| <pessoa, sistema ou script> | <o que faz aqui> |

## Pré-condições

1. <estado que precisa ser verdadeiro antes de começar>

## Fluxo principal

1. <passo observável>
2. <passo observável>

## Fluxos alternativos e exceções

| ID | Condição | Comportamento esperado |
|---|---|---|
| FA-01 | <condição alternativa válida> | <o que acontece> |
| EX-01 | <condição inválida> | <bloqueio / recusa / mensagem> |

## Regras de negócio

| ID | Regra | Origem |
|---|---|---|
| RN-001 | <regra com DEVE / NÃO DEVE, verificável> | <origem> |

## Dados e contratos de referência

| Elemento | Definição | Situação |
|---|---|---|
| <contrato ou dado> | <campos principais, ou link para `src/modules/<m>/contracts.py`> | EXISTE \| DEFINIDO \| PROPOSTA |

## Pós-condições

- <estado garantido ao final>

## Critérios de aceitação

### CA-01 — <nome curto>

- **Dado** <contexto com valores concretos>
- **Quando** <ação>
- **Então** <resultado verificável com números>

## Dependências

| Tipo | Item | Por quê |
|---|---|---|
| Decisão \| Existente \| Insumo \| Caso de uso | <item> | <motivo> |

**Usado por** (vêm depois na ordem de desenvolvimento): <UC-NNN: motivo>

## Fora do escopo

- <o que explicitamente não será feito aqui, e onde será>

## Pendências

- **PEND-NN** — <decisão em aberto e o que ela bloqueia>

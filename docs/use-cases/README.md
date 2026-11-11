# Casos de uso

Cada caso de uso especifica **o que deve ser entregue**. É o documento de produto; as mudanças
OpenSpec (`openspec/changes/`) são as unidades de trabalho que o implementam.

## Regras

- Arquivo: `UC-NNN-<slug-em-kebab-case>.md`, numeração sequencial, nunca reutilizada.
- Estrutura: exatamente a de [`_TEMPLATE.md`](_TEMPLATE.md). Não remova seções; use "Nenhum" quando não se aplica.
- Nasce ao final do `/opsx:explore` (ver `CLAUDE.md`).
- IDs locais ao UC: `FA-NN`, `EX-NN`, `RN-NNN`, `CA-NN`. IDs globais: `PEND-NN` em [`../pendencias.md`](../pendencias.md).
- Cada `CA-NN` vira um ou mais cenários OpenSpec e, portanto, testes.
- A linha **Módulos** define o escopo de edição do Claude Code (ver `/escopo`).
- **Situação**: `Planejado` → `Parcial` (diga o que falta) → `Implementado` (todos os CA com teste verde).

## Índice

| UC | Título | Release | Situação | Módulos |
|---|---|---|---|---|
| — | — | — | — | — |

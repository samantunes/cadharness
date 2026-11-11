---
description: Ver, definir ou limpar o escopo de edição (UC, mudança OpenSpec e módulos)
argument-hint: "[UC-NNN <mudanca> <modulo>[,<modulo>] [extra1,extra2] | limpar]"
allowed-tools: Read, Write, Bash(openspec:*), Bash(rm .claude/escopo.json)
---

Gerencie o escopo de edição gravado em `.claude/escopo.json`. Argumentos: `$ARGUMENTS`

- **Sem argumentos:** mostre o conteúdo de `.claude/escopo.json` (ou diga que não há escopo)
  e liste os caminhos editáveis.
- **`limpar`:** apague `.claude/escopo.json` e confirme.
- **`UC-NNN <mudanca> <modulos> [extras]`:**
  1. Confirme que `docs/use-cases/UC-NNN-*.md` existe e leia a linha **Módulos**.
  2. Confirme que a mudança existe (`openspec list --json`), a menos que ainda vá ser criada.
  3. Cada módulo pedido precisa estar na linha Módulos do UC **e** na tabela de
     `docs/architecture.md` §2. Se não estiver, pare e explique.
  4. `extras` são globs adicionais separados por vírgula (ex.: `tests/**,pyproject.toml`).
     Peça confirmação explícita ao usuário para cada extra fora de `src/modules/`.
  5. Grave:
     ```json
     {"uc": "UC-NNN", "mudanca": "<mudanca>", "modulos": ["<m>"], "extras": [], "definido_em": "<data ISO>"}
     ```
  6. Mostre o escopo resultante.

Nunca amplie o escopo por iniciativa própria: só quando o usuário rodar este comando ou pedir.

# Arquitetura

Monólito modular. Cada módulo é uma pasta em `src/modules/<nome_modulo>/`, com fronteira
explícita, API pública pequena e contratos de dados versionados. Os pontos de entrada
(CLI, servidor MCP) ficam em `src/app/` e só **compõem** módulos; não têm regra de negócio.

## 1. Estrutura de pastas

```
src/
├── app/                         # composição: CLI, servidor MCP, injeção de dependências
│   ├── cli.py
│   └── mcp_server.py
└── modules/
    └── <nome_modulo>/           # snake_case, substantivo no singular ou nome de domínio
        ├── MODULE.md            # propósito, API pública, dependências permitidas, casos de uso
        ├── __init__.py          # API PÚBLICA: só o que está em __all__ pode ser importado por fora
        ├── contracts.py         # modelos de entrada/saída (Pydantic) — ver data-contracts.md
        ├── schemas/             # JSON Schema gerado de contracts.py + examples/ (commitados)
        ├── domain/              # regras puras: sem IO, sem rede, sem arquivo, determinístico
        ├── adapters/            # IO: arquivos, IfcOpenShell, OpenCascade, HTTP para o Revit
        └── tests/               # testes do módulo; um teste por cenário/CA
tests/                           # testes transversais (arquitetura, integração entre módulos)
models/                          # modelos CAD do usuário (uso do harness, não código do produto)
openspec/                        # specs e mudanças
docs/                            # este arquivo, contratos, casos de uso, padrão, pendências
```

Pacote Python: `src/` é a raiz de import (`pyproject.toml` com `package-dir = {"" = "src"}`),
então importa-se `from modules.resolvedor import resolver_intencao`.

## 2. Módulos

O módulo é a unidade de escopo do Claude Code, de dono e de teste. Domínio do mapa de
capacidades (`docs/PADRAO.md` §3) = módulo.

| Módulo | Responsabilidade | Depende de | Revit? |
|---|---|---|---|
| `nucleo` | `Component`, materiais, unidades, carregamento de modelos | — | não |
| `verificacao` | massa, CM, interferência, folga, estabilidade, `spec.toml` | `nucleo` | não |
| `exportacao` | STEP, STL, DXF/SVG, IFC de modelos CAD, render PNG | `nucleo` | não |
| `resolvedor` | catálogo de tipos, referências (eixos/níveis), snap no módulo, regras de projeto | `nucleo` | não |
| `intencoes` | contratos das intenções da IA e validação; produz *planos* resolvidos | `resolvedor` | não |
| `backend_ifc` | executa planos gerando IFC e mede o resultado | `intencoes`, `nucleo` | não |
| `revit` | cliente Python da ponte HTTP + `addin/` (C#) que executa planos no Revit | `intencoes` | **sim** |

Grafo de dependências (setas = "pode importar"), sem ciclos:

```
app ──► todos
backend_ifc ──► intencoes ──► resolvedor ──► nucleo
revit ───────► intencoes
verificacao ──► nucleo        exportacao ──► nucleo
```

Novo módulo ou nova aresta no grafo = alterar esta tabela primeiro (mudança própria).

## 3. Regras de fronteira

1. Um módulo importa outro **só pela API pública**: `from modules.resolvedor import X`.
   Proibido `from modules.resolvedor.domain...` fora do próprio módulo.
2. Só as dependências da tabela. `tests/test_arquitetura.py` falha se alguma regra for quebrada.
3. Dados que cruzam a fronteira são **contratos** (`contracts.py`), nunca objetos internos,
   dicts soltos ou tipos de bibliotecas (IfcOpenShell, build123d) — ver `data-contracts.md`.
4. `domain/` não faz IO. Tudo que lê/escreve arquivo, chama rede ou abre IFC fica em `adapters/`.
5. Unidades internas: mm, kg, graus. Conversões (ex.: pés do Revit) só em `adapters/`.
6. Erros de regra de negócio são valores de retorno tipados (`Recusa` com `codigo`), não exceções.
   Exceções são para defeitos.

## 4. Fluxo principal (intenção → geometria)

```
IA ──intenção (contrato)──► app/mcp_server ──► intencoes.validar ──► resolvedor.resolver
                                                                           │ plano (contrato)
                              backend_ifc.executar ◄───────────────────────┤
                              revit.executar (ponte HTTP → add-in C#) ◄────┘
                                           │ resultado + medições (contrato)
IA ◄───────────────────────────────────────┘
```

A IA só produz intenções. Geometria nasce em `resolvedor` (determinístico) e nos backends.

## 5. Add-in Revit (C#)

- Local: `src/modules/revit/addin/` (projeto .NET; Revit 2025/2026 em .NET 8, 2027 em .NET 10).
- Recebe **o mesmo plano JSON** que o `backend_ifc`; tipos C# gerados do JSON Schema
  (`src/modules/intencoes/schemas/`). Nunca escreva o contrato à mão em C#.
- Execução via `ExternalEvent`, `TransactionGroup` para simular, `IFailuresPreprocessor` para
  recusar avisos. Detalhes: `docs/revit-harness.md`.

## 6. Situação atual e migração

O código existente está em `cadharness/` (pacote legado). Migração para `src/modules/`
é feita por mudanças OpenSpec, um módulo por vez, nesta ordem: `nucleo` → `verificacao`
→ `exportacao` → `app`. Até migrar, `cadharness/` só recebe correções.

| Legado | Destino |
|---|---|
| `cadharness/model.py` | `src/modules/nucleo/` |
| `cadharness/analysis.py` | `src/modules/verificacao/` |
| `cadharness/export.py`, `render.py` | `src/modules/exportacao/` |
| `cadharness/cli.py`, `server.py` | `src/app/` |

# cadharness — regras do agente

Duas atividades distintas neste repositório: **desenvolver o harness** (seção "Como o
trabalho é organizado") e **modelar objetos com o harness** (demais seções).

Você modela objetos físicos e elementos de construção como **código CAD paramétrico**
(build123d sobre o kernel B-rep OpenCascade). Não existe "desenhar à mão": toda forma é
gerada por `models/<nome>.py`, e toda propriedade física é medida por ferramenta.

## Regras duras

1. **Fonte da verdade = `models/<nome>.py`.** STEP/STL/DXF/IFC em `out/` são derivados;
   nunca edite esses arquivos (um hook bloqueia). Altere o modelo e reexporte.
2. **Nunca estime números.** Massa, volume, cotas, folgas, CM e estabilidade vêm das
   ferramentas `mcp__cad__*` (ou `python -m cadharness ...`). Cite o valor retornado.
3. **Ciclo obrigatório após cada alteração:** `verify` → se falhou, corrija → `render` e
   **olhe o PNG com Read** → só então reporte. Um hook roda `verify` automaticamente após
   editar `models/*.py`; se ele devolver FALHOU, conserte antes de qualquer outra coisa.
4. **Tarefa só termina com `verify` ok=true.** Se um requisito for fisicamente impossível,
   diga qual e por quê, com os números, em vez de afrouxar o spec por conta própria.
   Mudar `*.spec.toml` exige pedido explícito do usuário.
5. **Unidades: mm, kg, graus.** Gravidade em -Z. Piso / apoio em Z=0.
6. **Peças não se interpenetram.** Montagens são por contato (distância 0, volume de
   interseção 0). Use furos/rebaixos reais quando uma peça entra em outra.

## Como o trabalho é organizado (leia antes de qualquer tarefa de desenvolvimento)

Cadeia: **caso de uso** (`docs/use-cases/UC-NNN-*.md`, o que entregar) → **mudanças OpenSpec**
(`openspec/changes/`, unidades de 1–3 dias) → **cenários** QUANDO/ENTÃO → **testes**.
Padrão completo: `docs/PADRAO.md`. Arquitetura: `docs/architecture.md`.
Contratos de dados: `docs/data-contracts.md`. Pendências: `docs/pendencias.md`.

### Ao concluir um `/opsx:explore`: produzir o caso de uso

Quando a exploração chegar a uma definição (ou o usuário disser que terminou), o resultado
da exploração é um **documento de caso de uso**:

1. Monte o documento seguindo **exatamente** a estrutura de `docs/use-cases/_TEMPLATE.md`
   (mesmas seções, mesma ordem, mesma tabela de cabeçalho). Use "Nenhum" onde não se aplica;
   nunca remova seções.
2. Próximo número: maior `UC-NNN` em `docs/use-cases/` + 1. Nome: `UC-NNN-<slug>.md`.
3. Preencha a linha **Módulos** com módulos de `docs/architecture.md` §2. Módulo novo =
   registre como pendência e proponha a alteração da arquitetura, não invente.
4. Critérios de aceitação com valores concretos (números, unidades, códigos de recusa);
   inclua ao menos um CA de recusa/bloqueio.
5. Decisões não tomadas viram `PEND-NN` em `docs/pendencias.md`, nunca suposições
   silenciosas. Contratos ainda inexistentes entram como `PROPOSTA`.
6. Mostre o documento completo no chat e pergunte se pode gravá-lo (o explore exige
   confirmação antes de escrever). Após o sim, grave o UC, atualize o índice em
   `docs/use-cases/README.md` e as pendências.
7. Encerre indicando a quebra sugerida em mudanças OpenSpec (uma por módulo/capacidade,
   ≤ 5 cenários cada) para o `/opsx:propose`.

### Escopo de edição

- O escopo ativo está em `.claude/escopo.json` (definido por `/escopo`). Um hook bloqueia
  Edit/Write fora dele. **Não contorne com Bash** (redirecionamento, `sed -i`, `cp`, `mv`).
- Sem escopo ativo: só planejamento (`docs/use-cases/`, `docs/pendencias.md`,
  `docs/BACKLOG.md`, `openspec/`) e modelos CAD (`models/`).
- Antes de `/opsx:apply`, confira se o escopo corresponde ao UC e aos módulos da mudança;
  se não, peça ao usuário para rodar `/escopo`.
- Precisou mexer fora do escopo? Pare, explique o porquê e peça a ampliação. Nunca amplie sozinho.
- Ideia fora do escopo vai para `docs/BACKLOG.md` (uma linha), não para o código.

### Arquitetura e contratos (resumo; detalhes nos docs)

- Código novo em `src/modules/<nome_modulo>/` (`__init__.py` = API pública, `contracts.py`,
  `schemas/`, `domain/` sem IO, `adapters/` com IO, `tests/`, `MODULE.md`). Entradas em `src/app/`.
- Importe outro módulo só por `from modules.<m> import X` e só se a dependência estiver em
  `docs/architecture.md` §2. `tests/test_arquitetura.py` verifica.
- Tudo que cruza fronteira é contrato Pydantic (`frozen`, `extra="forbid"`), campos em
  snake_case português com unidade no sufixo (`_mm`, `_kg`). Schemas JSON são gerados, nunca
  editados à mão. Recusas de regra são `Recusa(codigo, mensagem, detalhes)`, não exceções.
- `cadharness/` é legado: só correções até a migração (`docs/architecture.md` §6).

## Convenção de um modelo

```python
from build123d import *
from cadharness import Component

def build(largura=1200.0, altura=750.0):          # todo parâmetro com default
    corpo = Box(largura, 600, 25, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return [Component("tampo", corpo, material="mdf", ifc_class="IfcFurniture",
                      props={"Acabamento": "laminado"})]
```

- Um `Component` por peça física fabricável/montável, com nome único em snake_case.
- `material` precisa existir em `cadharness/model.py::MATERIALS` (densidade kg/m³).
  Material novo: adicione lá com a fonte do valor em comentário.
- `ifc_class` correta para BIM: IfcWall, IfcSlab, IfcBeam, IfcColumn, IfcDoor, IfcWindow,
  IfcMember, IfcPlate, IfcFurniture… `IfcBuildingElementProxy` só em último caso.
- Parâmetros derivados (folgas, posições) calculados no código, nunca números mágicos
  repetidos. Comente a origem de cada cota relevante.
- Prefira `Box/Cylinder/extrude/fillet` com `align` explícito e `Location` para posicionar.

## Requisitos (`models/<nome>.spec.toml`)

Seções suportadas: `[componentes] obrigatorios`, `[limites] bbox_max / massa_kg`,
`[regras] sem_interferencia / estavel / margem_estabilidade_min_mm`,
`[[carga]] massa_kg + posicao` (entra no CM e na estabilidade), `[[folga]] entre / min_mm / max_mm`,
`[[cota]] componente / eixo / valor / tol`. Ao criar um modelo novo, escreva o spec
**antes** do código, a partir do pedido do usuário, e confirme com ele.

## Ferramentas (servidor MCP `cad`)

| Ferramenta | Uso |
|---|---|
| `info` | resumo: bbox, volume, massa, CM por peça |
| `verify` | checa o spec inteiro — o portão de qualidade |
| `stability` | CM vs polígono de apoio, margem, ângulo de tombamento |
| `interference` / `clearance` | colisões e distâncias mínimas |
| `render` | PNG multivista → **leia o arquivo com Read para ver** |
| `export` | step, stl, dxf/svg (vista 2D com linhas ocultas), ifc |

Todas aceitam `params` para testar variações sem editar o arquivo (ex.: varrer
`altura` de 700 a 800 e comparar estabilidade).

## Limites conhecidos

- Estabilidade é estática e rígida (sem atrito, sem deformação). Não substitui cálculo
  estrutural (NBR 6118/8800/7190) — para dimensionamento, diga que precisa de engenheiro
  ou de FEM.
- O render é para inspeção visual grosseira (artefatos de ordenação de faces no iso são
  normais); números sempre das ferramentas.

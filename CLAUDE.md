# cadharness — regras do agente de modelagem

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

# cadharness

Harness para o **Claude Code** modelar objetos físicos e elementos de construção como
**CAD paramétrico em código**, com verificação física automática e exportação para
STEP, STL, DXF/SVG e **IFC (BIM)**.

> Ideia central: o LLM não "desenha". Ele escreve um programa que gera sólidos B-rep
> exatos (build123d / OpenCascade, o mesmo kernel do FreeCAD), e toda medida — massa,
> centro de massa, folgas, colisões, estabilidade — é calculada por ferramenta e checada
> contra um arquivo de requisitos. O agente só conclui quando `verify` passa.

```
Usuário ──► Claude Code
             ├── CLAUDE.md                → regras duras (fonte da verdade, unidades, ciclo)
             ├── .claude/skills/          → modelar-peca · verificacao-fisica · exportar-bim
             ├── .claude/hooks/           → verify automático após editar; bloqueia editar derivados
             └── MCP "cad" (cadharness)   → info · verify · stability · interference
                                            clearance · render (PNG) · export
                       │
                       ▼
             models/<nome>.py  ──build123d──►  sólidos B-rep  ──►  out/ (STEP, STL, DXF, IFC, PNG)
             models/<nome>.spec.toml  (requisitos verificáveis)
```

## Por que código-CAD (e não Blender/Revit via MCP)

| Opção | Controle físico/dimensional | Verificável por máquina | Esforço p/ harness | Observação |
|---|---|---|---|---|
| **build123d / CadQuery (este repo)** | Exato (B-rep, tolerância ~1e-7 mm) | Total: volume, inércia, distância, booleanas | Baixo | LLMs escrevem Python muito bem; diff em git; parâmetros |
| FreeCAD via MCP | Exato (mesmo kernel) | Bom, via API Python | Médio | GUI pesada; bom para quem já usa FreeCAD/Arch |
| Blender + Bonsai (IFC) via MCP | Malha / IFC nativo | Médio | Médio | Ótimo p/ BIM visual; física de malha, não sólido exato |
| Onshape / Fusion via API | Exato | Bom | Alto | Proprietário, rede, cotas por API REST |
| Revit / Archicad via MCP | Exato no próprio software | Limitado | Alto | Windows + licença; útil só se o fluxo já é lá |

Para "mais controle físico", o caminho com melhor custo-benefício é **código paramétrico +
ferramentas de medição**: cada número é reproduzível, o modelo é versionável e o agente
consegue iterar sozinho (alterar → verificar → ver → corrigir).

## Instalação

```bash
pip install -e ".[dev]"
```

```bash
python -m pytest
```

Abra a pasta no Claude Code: o `.mcp.json` registra o servidor `cad`, e o
`.claude/settings.json` libera as ferramentas e ativa os hooks.

## Uso pela linha de comando (o mesmo que o agente usa)

```bash
python -m cadharness verify models/mesa.py
```

```bash
python -m cadharness verify models/mesa.py -p recuo_perna=120
```

```bash
python -m cadharness render models/mesa.py
```

```bash
python -m cadharness export models/parede_porta.py --format ifc
```

```bash
python -m cadharness export models/parede_porta.py --format dxf --view topo
```

Saída sempre em JSON. Comandos: `info`, `verify`, `stability`, `interference`,
`clearance --a X --b Y`, `render [--view iso|frente|topo|direita]`,
`export --format step|stl|dxf|svg|ifc`.

## Exemplos incluídos

- `models/mesa.py` — tampo MDF, 4 pernas e saias de pinus. O spec exige estabilidade com
  uma pessoa de 50 kg apoiada na quina. Com `recuo_perna=120` a mesa **tomba** (margem
  −37,6 mm) e o `verify` falha — exatamente o tipo de erro físico que o harness pega.
- `models/parede_porta.py` — laje + parede de blocos com vão + porta, exportados como
  IfcSlab / IfcWall / IfcDoor, com material, pavimento e `Pset_CadHarness` (volume, massa).

## Arquivo de requisitos (`*.spec.toml`)

```toml
[componentes]
obrigatorios = ["tampo", "perna_1"]

[limites]
bbox_max = [1250, 650, 760]   # mm
massa_kg = [15, 40]

[regras]
sem_interferencia = true
estavel = true
margem_estabilidade_min_mm = 30

[[carga]]                      # entra no CM e na estabilidade
massa_kg = 50
posicao = [600, 300, 750]

[[folga]]
entre = ["porta_P1", "parede_eixo_A"]
min_mm = 3
max_mm = 10

[[cota]]
componente = "tampo"
eixo = "z"
valor = 25
tol = 0.1
```

## Complexidade e próximos passos

| Etapa | Situação | Esforço |
|---|---|---|
| Modelagem paramétrica + verificação (massa, CM, colisão, folga, estabilidade) | **feito** | — |
| Export STEP/STL/DXF/IFC + render para o agente ver | **feito** | — |
| Aberturas IFC reais (IfcOpeningElement), IfcWallType, camadas de material | próximo | 1–2 semanas |
| Validação IDS (IfcTester) do IFC exportado | próximo | dias |
| Análise estrutural simples (FEM linear com gmsh + scikit-fem / CalculiX) | depois | 1–2 meses |
| Restrições de montagem (joints build123d) e cinemática / alcance | depois | 1 mês |
| Avaliação: banco de pedidos com respostas conhecidas (ex.: "mesa p/ 6 pessoas, ≤ 30 kg") | contínuo | — |

Limites atuais: estabilidade estática de corpo rígido (sem atrito/deformação); não
substitui cálculo estrutural. O IFC usa geometria tesselada (bom para coordenação, não
para edição paramétrica no Revit).

# Harness do Revit: a IA modela, a aplicação controla a geometria

> Estudo de arquitetura e catálogo de ferramentas. Base: Revit API 2025–2027
> (Revit 2025/2026 rodam em .NET 8, com migração anunciada para .NET 10; o Revit 2027 já usa .NET 10).

## 1. Princípio

A IA **nunca escreve coordenadas livres nem geometria**. Ela declara **intenção** em termos do
projeto ("parede tipo ALV-14 entre os eixos A1 e A3 no Térreo", "porta P90 na parede W12, a
15 cm do canto"). A aplicação **resolve** a intenção em geometria segundo regras determinísticas,
e o **Revit gera a geometria com o próprio motor paramétrico** (tipos, famílias, hospedeiros,
uniões, restrições). Depois a aplicação **mede** o resultado e só confirma se as regras passarem.

```
 IA (Claude)                 Aplicação (Python, fora do Revit)             Revit (add-in C#)
 ───────────                 ─────────────────────────────────            ─────────────────
 intenção em JSON   ──►  1. valida contra catálogo e regras        ──►  4. executa em Transaction
 (referências,           2. resolve referências → coordenadas            (Wall.Create, NewFamilyInstance…)
  tipos, parâmetros)         com snap em eixos/módulo                  5. FailuresPreprocessor captura avisos
                          3. pede simulação (dry-run)              ◄──  6. mede o resultado, RollBack ou Commit
 decide / corrige   ◄──  7. relatório: o que mudou, medidas, falhas     7. IUpdater mantém as invariantes
                                                                           mesmo após edição manual
```

Divisão de responsabilidades:

| Quem | Controla | Não controla |
|---|---|---|
| IA | escolha de tipos do catálogo, topologia (o que liga a quê), parâmetros dentro de faixas, sequência de operações | coordenadas brutas, geometria de família, uniões, cortes de vão |
| Aplicação | snap, módulos, folgas mínimas, tolerâncias, unidades, permissões por nível, aprovação | estética e decisões de projeto |
| Revit | geometria real: uniões de paredes, vãos hospedados, perfis de laje, regeneração paramétrica | regras de projeto (elas vêm da aplicação) |

## 2. O que a Revit API oferece para esse controle

| Necessidade | Mecanismo da API | Como usamos |
|---|---|---|
| Referencial do projeto | `Level.Create`, `Grid.Create`, `ReferencePlane` | Toda posição é relativa a nível e eixo. A IA cita `"A/1"`, não `(3.2, 0)` |
| Geometria governada por tipo | `WallType`, `FloorType`, `FamilySymbol`, `CompoundStructure` | A IA só escolhe tipos de uma lista permitida; espessura e camadas vêm do tipo |
| Criação com motor paramétrico | `Wall.Create`, `Floor.Create(doc, CurveLoops, typeId, levelId)`, `Document.Create.NewFamilyInstance(...)` com hospedeiro | Portas e janelas cortam a parede sozinhas; o Revit faz as uniões |
| Restrições | `Document.Create.NewDimension` + `Dimension.IsLocked`, `NewAlignment`, base e topo de parede presos a níveis | Prende medidas que a IA não pode alterar depois |
| Parâmetros | `Element.LookupParameter`, `BuiltInParameter`, `FamilyManager` (fórmulas) | A IA altera parâmetros com faixa validada; fórmulas da família garantem coerência |
| Simulação (dry-run) | `TransactionGroup` com `Start` … `RollBack`, `SubTransaction` | Executa, mede e desfaz, entregando uma prévia sem sujar o modelo |
| Captura de erros | `FailureHandlingOptions.SetFailuresPreprocessor(IFailuresPreprocessor)` | Avisos como "paredes sobrepostas" ou "ambiente não fechado" viram erro estruturado para a IA, com rollback |
| Invariantes permanentes | Dynamic Model Update: `IUpdater` + `UpdaterRegistry` com gatilhos | Reaplica regras após qualquer edição (ex.: porta a pelo menos 10 cm do canto) |
| Comunicação externa | `ExternalEvent` + `IExternalEventHandler` | Um servidor HTTP local recebe o pedido, e o handler executa na thread do Revit |
| Rastreabilidade | `ExtensibleStorage` (`Schema`, `Entity`) | Cada elemento guarda o id da operação e a intenção JSON que o gerou |
| Medição e verificação | `ElementIntersectsElementFilter`, `ElementIntersectsSolidFilter`, `BoundingBoxIntersectsFilter`, `get_Geometry`, `SpatialElementGeometryCalculator`, `Room.IsPointInRoom` | Colisões, áreas, volumes, folgas e ambientes calculados pelo próprio Revit |
| Visão para a IA | `Document.ExportImage(ImageExportOptions)` | PNG de vistas para o Claude conferir visualmente |
| Ponte com o cadharness | `Document.Export(folder, name, IFCExportOptions)` | Reaproveita as verificações do IfcOpenShell |

**Cuidado com as unidades:** internamente o Revit trabalha em **pés decimais**. A conversão
(`UnitUtils.ConvertToInternalUnits(valor, UnitTypeId.Millimeters)`) fica só na aplicação,
nunca com a IA.

**O que fica proibido para a IA:** `DirectShape` (geometria livre), `ElementTransformUtils.MoveElement`
com vetor arbitrário, edição de família sem template e qualquer coordenada fora do snap.

## 3. Catálogo de ferramentas do servidor MCP `revit`

### Leitura de contexto (nível 0, sempre liberado)
| Ferramenta | Retorna | API |
|---|---|---|
| `projeto_resumo` | níveis, eixos, fases, contagem por categoria, unidades | `FilteredElementCollector` |
| `catalogo_tipos(categoria)` | tipos permitidos com parâmetros-chave (espessura, largura do vão) | `WallType`, `FamilySymbol` |
| `listar_elementos(categoria, nivel, filtro)` | id, tipo, referências (eixos e hospedeiro), parâmetros, com paginação | coletores + parâmetros |
| `topologia(elemento)` | uniões, hospedeiro, elementos hospedados, ambientes vizinhos | `WallUtils`, `JoinGeometryUtils`, `FamilyInstance.Host` |
| `ambientes(nivel)` | ambientes com área, perímetro e fronteiras | `Room`, `SpatialElementBoundaryOptions` |
| `render_vista(vista)` | PNG para a IA ver | `ExportImage` |

### Intenção, simulação e execução (o coração do harness)
| Ferramenta | A IA informa | O sistema decide |
|---|---|---|
| `planejar(intencoes[])` | lista de intenções JSON | valida catálogo e regras, resolve referências, devolve o plano com coordenadas resolvidas e cada regra aplicada |
| `simular(plano)` | o id do plano | executa num `TransactionGroup`, mede, faz `RollBack` e devolve diferenças, avisos e medidas |
| `aplicar(plano)` | o id do plano já simulado (e aprovado pelo usuário) | executa de novo, faz `Commit`, grava a intenção em ExtensibleStorage |
| `desfazer(operacao)` | o id da operação | remove ou reverte os elementos daquela operação |

Intenções de alto nível que o `planejar` aceita:

| Intenção | Exemplo | Resolução determinística |
|---|---|---|
| `parede_entre_eixos` | `{tipo:"ALV-14", de:"A/1", ate:"A/3", nivel:"Terreo", topo:"Cobertura", alinhamento:"eixo"}` | interseção dos eixos, linha de locação, topo preso ao nível |
| `ambiente_retangular` | `{nome:"Sala", origem:"B/2", largura_mm:4000, profundidade_mm:5000, tipo_parede:"ALV-14"}` | snap no módulo, 4 paredes unidas, Room colocado e verificado |
| `inserir_vao` | `{familia:"P90", parede:"W12", ancora:"inicio", distancia_mm:150}` | ponto sobre a linha da parede, hospedado, com checagem de folga e de colisão com outras aberturas |
| `laje_por_contorno` | `{tipo:"LJ-12", contorno:"paredes_do_ambiente:Sala", nivel:"Terreo"}` | `CurveLoop` derivado das faces das paredes |
| `ajustar_parametro` | `{elemento:123, parametro:"Altura do peitoril", valor_mm:1100}` | confere a faixa permitida e simula |
| `trocar_tipo` | `{elementos:[...], novo_tipo:"ALV-19"}` | checa a compatibilidade dos hospedados |

### Verificação (o portão de qualidade)
| Ferramenta | Verifica |
|---|---|
| `verificar(regras)` | arquivo de regras do projeto (como o `.spec.toml` do cadharness): folgas, áreas mínimas por ambiente, vão mínimo de porta (acessibilidade, NBR 9050), sobreposições, ambientes fechados |
| `colisoes(catA, catB)` | interferência sólida pelo Revit |
| `medir(a, b)` | distância mínima entre elementos ou referências |
| `exportar_ifc` + verificações do cadharness/IfcTester | validação independente do Revit |

### Guardas (rodam dentro do Revit, sem a IA)
- `IUpdater` para invariantes: paredes sobre eixo continuam sobre eixo, vãos respeitam folga,
  elemento marcado como "travado pela aplicação" não muda de tipo.
- `IFailuresPreprocessor` em toda transação vinda da IA: qualquer aviso derruba a transação e
  volta como erro explicado.
- Cotas travadas (`IsLocked`) nas medidas declaradas como requisito.

## 4. Graus de liberdade da IA (liberação gradual)

| Nível | A IA pode | Exemplo |
|---|---|---|
| N0 | só ler e verificar | "quais portas têm menos de 80 cm?" |
| N1 | ajustar parâmetros de elementos existentes dentro de faixas | altura de peitoril, tipo de acabamento |
| N2 | inserir elementos do catálogo em referências (eixo, nível, hospedeiro) | portas, janelas, pilares em interseções de eixos |
| N3 | traçar layout com snap no módulo | paredes e ambientes a partir de um programa de necessidades |
| N4 | gerar famílias a partir de templates com parâmetros | uma janela nova: a IA define os parâmetros e o template gera a geometria |

Cada nível exige que o anterior passe na bateria de testes (seção 7).

## 5. Exemplo ponta a ponta

Pedido: *"Crie uma sala de 4 × 5 m a partir do eixo B/2, com porta de 90 cm e duas janelas."*

1. A IA chama `catalogo_tipos` e escolhe `ALV-14`, `P90` e `J120x120`.
2. Monta as intenções `ambiente_retangular`, `inserir_vao` (porta) e 2× `inserir_vao` (janelas).
3. `planejar` arredonda para o módulo de 50 mm, verifica que a porta cabe (900 + 2×100 de folga
   ≤ 4000) e resolve as coordenadas.
4. `simular` cria tudo, mede (área do Room = 20,00 m², ambiente fechado, sem avisos) e faz rollback.
5. A IA mostra o relatório e o PNG ao usuário, que aprova.
6. `aplicar` confirma. Cada elemento guarda a intenção, e o `IUpdater` protege as invariantes.

## 6. Reaproveitar o cadharness: desenvolver sem licença

A camada de intenção e resolução é **independente do Revit**. Por isso propomos dois *backends*
para o mesmo JSON:

```
intenção ─► resolvedor (Python, testável) ─┬─► backend IFC (cadharness + IfcOpenShell) → sem licença
                                           └─► backend Revit (add-in C#)                → mês de licença
```

- O resolvedor, as regras, o catálogo e os testes são escritos e validados agora, com o
  backend IFC gerando IfcWall, IfcDoor e IfcSlab (o cadharness já faz isso).
- Quando a licença estiver ativa, só o backend Revit é testado, e as mesmas perguntas de teste
  rodam nos dois para comparar os resultados.

## 7. Avaliação

Uma bateria de pedidos com respostas conhecidas, rodada a cada mudança:
- "sala 4×5 + porta 90": área do Room = 20,00 m², 4 paredes unidas, porta hospedada, 0 avisos.
- "porta a 5 cm do canto": precisa ser **recusada** pelo resolvedor (folga mínima).
- "parede sobre parede existente": precisa ser recusada pela simulação (aviso do Revit).
- Medida: taxa de acerto na 1ª tentativa, nº de rollbacks, nº de intenções inválidas.

## 8. O que já existe e onde nos diferenciamos

- **mcp-servers-for-revit**: servidor MCP em TypeScript conversando por localhost com um plugin
  C# dentro do Revit, mais uma variante em Python baseada no pyRevit. Expõe CRUD de elementos.
  É uma boa referência para a ponte de comunicação, mas lá **a IA controla a geometria
  diretamente** (cria e move com coordenadas).
- **Nossa proposta:** intenção → resolução determinística → simulação com rollback →
  invariantes no Revit. É o que garante o controle geométrico pela aplicação.

## 9. Limites e riscos

- A Revit API só roda **dentro do Revit aberto**, em thread única, e exige licença completa
  (o Revit LT não tem API). Para rodar sem interface existe o Design Automation for Revit,
  na nuvem da Autodesk, pago por uso (verificar o preço antes).
- `IUpdater` mal escrito pode criar laços e transações estranhas. Mantenha cada updater
  pequeno e idempotente.
- Famílias de terceiros podem não ter parâmetros coerentes. Por isso o catálogo é curado.
- Mudança de .NET entre versões (8 → 10) exige recompilar o add-in.

## 10. Roteiro

| Fase | Entrega | Precisa de Revit? |
|---|---|---|
| 0 | esquema JSON das intenções, resolvedor com snap e regras, backend IFC no cadharness, testes | não |
| 1 | add-in C#: servidor HTTP + `ExternalEvent`, ferramentas de leitura | só para testar (trial) |
| 2 | `simular`/`aplicar` com `TransactionGroup` e `IFailuresPreprocessor`, intenções N2 | sim (1 mês) |
| 3 | `IUpdater` com invariantes, ExtensibleStorage, intenções N3 | sim |
| 4 | famílias por template (N4) | sim |

## Fontes

- Referência da API Revit 2026: `Floor.Create`, `Toposolid.Create`, `IUpdater`, `UpdaterRegistry.RegisterUpdater` (help.autodesk.com/cloudhelp/2026/ENU/Revit-API-MainReference)
- Blog da Autodesk: Revit 2027 SDK (.NET 10) e plano de migração do 2025/2026 para .NET 10
- Fórum Revit API: migração do Revit 2025/2026 para .NET 10
- github.com/mcp-servers-for-revit

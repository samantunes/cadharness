# Padrão de desenvolvimento

Objetivo: saber **sempre** o que está sendo feito, o que vem depois e o que está pronto,
sem depender de memória. Ferramenta: OpenSpec + Claude Code + git.

## 1. Quatro níveis (e só quatro)

| Nível | O que é | Vida útil | Onde fica | Exemplo |
|---|---|---|---|---|
| **Produto** | um repositório | anos | GitHub | `cadharness` |
| **Capacidade** | algo que o sistema *sabe fazer*; substantivo | permanente | `openspec/specs/<dominio>/<capacidade>/spec.md` | `intencoes/inserir-vao` |
| **Mudança** | uma unidade de trabalho; verbo + substantivo | 1 a 3 dias | `openspec/changes/<nome>/` → depois `archive/` | `add-recusa-folga-minima-vao` |
| **Cenário** | um comportamento verificável QUANDO/ENTÃO | permanente | dentro da spec **e** como teste em `tests/` | "porta a 50 mm do canto é recusada" |

Regra de ouro: **cenário = teste**. Se não dá para escrever o teste, o cenário está vago.

## 2. Como cortar uma funcionalidade

Pergunte nesta ordem:

1. **Qual capacidade do mapa (seção 3) ela altera?** Se forem duas, são duas mudanças.
2. **Corte vertical:** a mudança entrega um comportamento de ponta a ponta (esquema →
   resolvedor → backend → teste). Nunca "fazer todo o resolvedor" ou "só a camada X".
3. **Tamanho:** no máximo 5 cenários, 10 tarefas e 3 dias. Passou disso → divida.
4. **Precisa de Revit?** Se não, tem que rodar só com o backend IFC. Mudanças que precisam
   de Revit recebem o prefixo `revit-` e entram na fila do mês de licença.
5. **Recusa primeiro:** o primeiro cenário de uma intenção nova costuma ser o que ela
   deve **recusar**. É o que garante o controle geométrico.

Exemplo de quebra da intenção "inserir vão":

| Mudança | Cenários | Revit? |
|---|---|---|
| `add-intencao-inserir-vao` | porta P90 a 150 mm do início da parede de 4 m → vão no lugar certo | não |
| `add-recusa-folga-minima-vao` | porta a 50 mm do canto → recusada com `folga_minima` | não |
| `add-recusa-vao-sobreposto` | segunda porta sobre a primeira → recusada | não |
| `revit-inserir-vao-hospedado` | mesmos cenários executados no Revit, mesmas medidas | sim |

## 3. Mapa de capacidades

Toda mudança aponta para uma linha daqui. Capacidade nova = primeiro altere este mapa.

| Domínio | Capacidades | Revit? |
|---|---|---|
| `nucleo` | `modelo-componentes`, `materiais`, `unidades` | não |
| `verificacao` | `spec-requisitos`, `massa-cm`, `interferencia`, `folga`, `estabilidade` | não |
| `export` | `step-stl`, `desenho-2d`, `ifc` | não |
| `resolvedor` | `catalogo-tipos`, `referencias` (eixos/níveis), `snap-modulo`, `regras-projeto` | não |
| `intencoes` | `parede-entre-eixos`, `ambiente-retangular`, `inserir-vao`, `laje-contorno`, `ajustar-parametro`, `trocar-tipo` | não (backend IFC) |
| `backend-ifc` | `executor-ifc`, `medicao-ifc` | não |
| `revit` | `ponte-http`, `leitura`, `simular-aplicar`, `falhas`, `guardas-iupdater`, `rastreio` | **sim** |
| `agente` | `regras-claude`, `skills`, `hooks`, `avaliacao` | não |

## 4. Fluxo de uma mudança

```
/opsx:explore   (opcional, ideia ainda nebulosa)
/opsx:propose   → proposal.md, specs (delta), design.md, tasks.md
      │  você revisa: escopo? cenários com números? cabe em 3 dias?
/opsx:apply     → código + um teste por cenário
      │  python -m pytest verde
/opsx:archive   → spec principal atualizada, mudança vai para archive/
```

Git: uma branch por mudança (`mudanca/<nome>`), um PR por mudança, merge só após o archive.

## 5. Limite de trabalho em andamento (o que resolve o "não consigo controlar")

- **No máximo 2 mudanças ativas** em `openspec/changes/` (fora `archive/`).
- Para ver o estado de tudo: `openspec list` (mudanças) e `openspec list --specs` (capacidades).
- Ideia nova no meio do caminho → anote em `docs/BACKLOG.md` (uma linha), não abra mudança.
- Mudança parada há mais de 5 dias → divida, arquive o que estiver pronto ou apague.

## 6. Checklist de pronto

- [ ] Todos os cenários da spec têm teste com o nome do cenário no docstring
- [ ] `python -m pytest` verde
- [ ] Nenhum número no código sem origem comentada (regra, norma ou parâmetro)
- [ ] Se mudou ferramenta/MCP: `CLAUDE.md` e skills atualizados
- [ ] `/opsx:archive` executado

## 7. Ritmo semanal

| Quando | O quê | Tempo |
|---|---|---|
| Segunda | ler `docs/BACKLOG.md`, escolher até 2 mudanças, `/opsx:propose` | 30 min |
| Dias úteis | `/opsx:apply`, revisar, testar | — |
| Sexta | arquivar o que terminou, rodar a avaliação do agente, podar o backlog | 30 min |

## 8. Vários produtos

Cada repositório segue o mesmo padrão (copie `openspec/config.yaml` e este arquivo).
O limite de 2 mudanças ativas vale **somando todos os repositórios**: é o que mantém o
controle quando há muitos projetos.

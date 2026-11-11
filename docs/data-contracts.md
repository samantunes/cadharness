# Contratos de dados e schemas

Contrato = estrutura de dados que **cruza uma fronteira**: entre módulos, entre Python e o
add-in C#, entre a IA (ferramentas MCP) e o sistema, ou gravada em arquivo. Tudo que cruza
fronteira tem contrato; nada de dicts soltos.

## 1. Fonte da verdade

| O quê | Onde | Quem escreve |
|---|---|---|
| Definição | `src/modules/<m>/contracts.py` (Pydantic v2) | pessoa / Claude, via mudança OpenSpec |
| JSON Schema | `src/modules/<m>/schemas/<Contrato>.v<MAJOR>.schema.json` | **gerado**, nunca editado à mão |
| Exemplos | `src/modules/<m>/schemas/examples/<Contrato>/*.json` | pessoa / Claude; válidos e inválidos |
| Tipos C# | `src/modules/revit/addin/Contracts/` | **gerados** do JSON Schema |
| Referência no UC | tabela "Dados e contratos de referência" | link para `contracts.py` |

Fluxo: `contracts.py` → gerar schema → testes validam exemplos → C# gerado do schema.

## 2. Regras de modelagem

1. **Nome do contrato**: substantivo em PascalCase, português (`IntencaoInserirVao`, `PlanoResolvido`, `Recusa`).
2. **Campos**: `snake_case`, português, **unidade no sufixo** quando houver grandeza física:
   `distancia_mm`, `massa_kg`, `angulo_graus`, `area_m2`. Sem unidade implícita, nunca.
3. **Identificadores**: `id` como string estável (`"W12"`, GlobalId IFC, `ElementId` do Revit
   como string). Referências a outro objeto terminam em `_id` / `_ref`.
4. **Enumerações** fechadas com `Literal[...]` ou `Enum`; nada de string livre para estado.
5. **Obrigatório por padrão.** Campo opcional precisa de motivo e de default explícito.
6. **Validação no contrato**: faixas (`Field(ge=0, le=10000)`), padrões (`pattern=`) e
   regras de um único objeto. Regras que dependem do projeto (catálogo, folgas) ficam no
   `domain/` e retornam `Recusa`.
7. **Imutável**: `model_config = ConfigDict(frozen=True, extra="forbid")`. Campo desconhecido é erro.
8. **Discriminador** para uniões: campo `tipo: Literal["inserir_vao"]` em cada intenção.
9. **Todo contrato tem `versao_contrato: Literal["1"]`** (major) quando gravado em disco ou
   enviado ao add-in.
10. **Dados pessoais/sensíveis**: marcar o campo com `json_schema_extra={"sensivel": True}`;
    nunca logar; mascarar em exportações.

## 3. Contratos padrão do sistema

| Contrato | Uso | Campos essenciais |
|---|---|---|
| `Intencao*` | o que a IA pede | `tipo`, parâmetros com unidade, referências (`eixo`, `nivel`, `parede_id`) — **nunca XYZ** |
| `PlanoResolvido` | saída do `resolvedor` | `plano_id`, `operacoes[]` com coordenadas em mm, `regras_aplicadas[]` |
| `ResultadoExecucao` | saída de um backend | `plano_id`, `backend` (`ifc`\|`revit`), `elementos[]`, `medicoes`, `avisos[]` |
| `Recusa` | regra violada | `codigo` (ex.: `folga_minima`), `mensagem`, `detalhes` com valores atual/limite |

`codigo` de `Recusa` é estável e documentado no `MODULE.md` do módulo que o emite; a IA
decide o que fazer com base nele.

## 4. Versionamento

- **Compatível** (campo opcional novo, novo valor de enum tolerado): mesma major, regenera schema.
- **Incompatível** (remover/renomear campo, mudar unidade ou tipo, tornar obrigatório):
  nova major (`.v2.schema.json`), a anterior continua até todos os consumidores migrarem.
- Mudança de contrato é sempre uma mudança OpenSpec própria, com o UC atualizado
  (coluna Situação: `PROPOSTA` → `DEFINIDO` → `EXISTE`).

## 5. Testes de contrato (obrigatórios)

Em `src/modules/<m>/tests/test_contratos.py`:
1. Todo exemplo em `examples/<Contrato>/valido_*.json` valida; todo `invalido_*.json` falha.
2. O schema commitado é igual ao gerado agora (impede schema desatualizado).
3. Ida e volta: `Modelo.model_validate_json(x.model_dump_json()) == x`.
4. Quando o add-in existir: os mesmos exemplos são desserializados no C# (xUnit).

## 6. Situação no UC

| Situação | Significado |
|---|---|
| `PROPOSTA` | descrito no UC, ainda sem código |
| `DEFINIDO` | existe em `contracts.py` com schema e exemplos, sem consumidor completo |
| `EXISTE` | em uso, com testes de contrato verdes |

---
name: verificacao-fisica
description: Auditar um modelo existente quanto a massa, centro de massa, estabilidade com cargas, interferências e folgas, e propor correções paramétricas. Use quando o usuário perguntar se algo tomba, aguenta, encaixa, colide ou cabe.
---

# Verificação física

1. `mcp__cad__info` → registre massa total, CM e bbox.
2. `mcp__cad__interference` → toda interpenetração é erro de modelagem; liste par e volume.
3. `mcp__cad__stability` sem e com as cargas do spec. Reporte margem (mm) e ângulo de
   tombamento (°). Margem < 0 = tomba.
4. Para cada risco, encontre o parâmetro que mais influencia e **varra-o** com `params`
   (3–5 valores). Mostre a tabela e recomende o menor ajuste que passa no `verify`.
5. Deixe explícito o que a análise NÃO cobre: resistência dos materiais, flambagem,
   fadiga, ligações, dinâmica. Recomende FEM/engenheiro quando a pergunta for essa.

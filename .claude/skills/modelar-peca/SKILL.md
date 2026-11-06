---
name: modelar-peca
description: Criar ou alterar um modelo CAD paramétrico (móvel, peça, elemento construtivo) em models/*.py com requisitos verificáveis. Use quando o usuário pedir para desenhar, modelar, projetar ou modificar um objeto físico.
---

# Modelar peça

1. **Requisitos primeiro.** Extraia do pedido: dimensões máximas, materiais, cargas de uso,
   folgas funcionais, cotas críticas. Escreva `models/<nome>.spec.toml`. Se faltar
   informação crítica (ex.: carga), pergunte; se for secundária, assuma e declare.
2. **Esqueleto paramétrico.** Crie `models/<nome>.py` com `build(**params)`; todas as cotas
   principais como parâmetros com default. Origem e eixos documentados no docstring.
3. **Construa de fora para dentro:** envoltória → peças estruturais → ligações → detalhes
   (furos, chanfros, fillets por último — são os que mais quebram o B-rep).
4. **Verifique.** O hook roda `verify` sozinho; leia o resultado. Falhou → corrija a
   geometria, não o spec.
5. **Olhe.** `mcp__cad__render` e `Read` no PNG. Confira se cada peça está onde o nome diz.
6. **Explore variações** com `params` (sem editar o arquivo) quando houver trade-off, e
   apresente uma tabela parâmetro → massa / margem de estabilidade / ok.
7. **Entregue:** resumo com números de `info`/`verify`, caminho do PNG e exports pedidos.

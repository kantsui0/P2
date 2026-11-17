# Etapa 6 — Painel, selos e Todos os pedidos

**Aprovada no escopo solicitado**, após verificação com servidor real em base isolada.

## Entrega

- Funções puras em `src/utils/metrics.ts` reutilizam `orderTotal`: total por cliente, selo, Top 3, indicadores e filtros/ordenação. map/filter/reduce/sort operam sobre novas coleções; arrays do estado não são ordenados diretamente.
- Pedidos abertos e pagos compõem total vendido, ticket médio, total por cliente, selo e Top 3. Cancelados permanecem no indicador do próprio status e na tela Todos os pedidos. Média = soma / quantidade de pedidos válidos; zero válidos resulta em zero. Pedido válido de total zero participa do denominador e gera Regular, não Sem compras.
- Painel: total de clientes, vendido, ticket médio, quantidade/soma para cada status, Top 3 com nome/valor e atalho Novo cliente. Empates do ranking são resolvidos por ID crescente.
- VIP >= 2000; Sem compras somente na ausência de pedidos válidos; Regular nos demais casos. Lista e detalhe usam a mesma função. Alterações de pedido recarregam o selo do detalhe imediatamente.
- Todos os pedidos associa nomes por ID, inclui cancelados e abre o cliente pelo link. Filtros simultâneos de status e faixa inclusiva; preço vazio significa limite ausente, zero é limite válido. Faixa negativa/invertida mostra erro. Ordenação por data ou total, crescente/decrescente, sem mutar pedidos.
- Nomes via GET /clientes?limit=100&skip=0 e páginas seguintes conforme total, avançando pela quantidade realmente recebida. Página vazia antes do total gera erro em vez de laço infinito.
- Ao entrar/revisitar Painel, lista, detalhe e Todos os pedidos, novas leituras consultam a API. Sem cache persistente de recursos. Leitura cancelada/resposta obsoleta não altera a tela desmontada; loading/erro/retry preservados.

## Verificações e evidências

| Comando | Resultado | Evidência |
| --- | --- | --- |
| npm run build | Passou | evidence/stage6-build.txt |
| npm run lint | Passou, sem avisos | evidence/stage6-lint.txt |
| node tests/orders_unit.mjs | Passou | evidence/stage6-orders-unit.txt |
| node tests/metrics_unit.mjs | Passou: entradas congeladas, totais, limite VIP, zero, média, ranking/filtros | evidence/metrics-unit.txt |
| python tests/metrics_real.py | Passou, API real isolada, sem respostas simuladas | evidence/metrics-real-tests.txt e metrics-real.json |
| python tests/session_browser.py | Regressão passou, respostas simuladas | evidence/metrics-session-regression.txt |
| python tests/clients_browser.py | Regressão passou, respostas simuladas | evidence/metrics-clients-regression.txt |

O teste isolado copia literalmente `servidor-crm/server.js` para uma pasta temporária sob /workspace/work, reutiliza dependências e usuários, mas inicia as três coleções de negócio vazias. API em 3334; Vite em 5174 recebe VITE_API_URL pelo ambiente do processo. O `.env` do projeto e os hashes dos JSON do servidor original são comparados ao final e permanecem inalterados. Processos isolados encerrados ao concluir. Não executar dois testes isolados simultaneamente nas mesmas portas.

### Aceite observado

1. Vazio e apenas cancelados: ticket zero, Sem compras.
2. Cliente Alfa: aberto 1500 + pago 500 + cancelado 9000 → vendido 2000, ticket 1000, VIP lista/detalhe. Grupos: aberto 1/1500, pago 1/500, cancelado 1/9000.
3. Cancelar aberto pelo front → vendido 500, ticket 500, selo Regular no detalhe imediatamente e na lista ao revisitar.
4. Criar/editar/excluir pedido pelo front → vendido 2500 → 600 → 500, selos atualizados.
5. Pedido válido zero → Regular; só cancelados → Sem compras, nas duas telas.
6. Top 3: Maior 3000, Medio 1000, Alfa 500; valores cancelados excluídos.
7. Base com 105 clientes: requisições limit=100/skip=0 e limit=100/skip=100 observadas; pedido do cliente da última página exibe o nome correto.
8. Status cancelado + faixa 9000–9500 seleciona somente 9000; pago + faixa 100–500 seleciona 100 e 500. Quatro ordenações conferidas; faixa inválida exibe mensagem. Link abre o ID correto.
9. Renomear cliente atualiza nome em Todos os pedidos. Excluir cliente com um pedido atualiza total de clientes para 104, vendido para 4500 e remove o pedido ao revisitar.
10. Sem erros JS não tratados; Painel, Pedidos, lista e detalhe sem overflow a 375px/1280px.

Capturas: `evidence/metrics-initial.png` e `evidence/metrics-orders-mobile.png`.

Sem pendências funcionais desta etapa. Publicação GitHub, empacotamento/entrega e eventual revisão final permanecem fora deste escopo.

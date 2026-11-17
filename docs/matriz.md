> Atualização de entrega: repositório público definido em https://github.com/kantsui0/P2; consulte docs/entrega.md e o relatório externo validacao-entrega.json para a validação do pacote publicado. Os bloqueios abaixo refletem a data da revisão funcional. Submissão ao AVA continua não confirmada.

# Matriz final de requisitos — revisão do PDF completo

PDF reaberto integralmente (2 páginas) em 17/11/2026. Os 31 itens originais da etapa 1 estão preservados abaixo. Resultado: **29 passou, 0 falhou, 2 bloqueado**. Revisão funcional aprovada; entrega completa da prova permanece pendente dos itens 30–31.

## Evidências desta rodada

Todos os logs abaixo estão em `evidence/final-review/`:

- **R**: `real-integration.txt` — API real, cliente temporário identificável, reinício real da API, persistência e limpeza.
- **D**: `details.txt` — pedidos/histórico reais com cliente temporário identificável.
- **M**: `metrics.txt` — cópia isolada do servidor fornecido e base de teste, sem mocks.
- **S**: `session.txt` — respostas simuladas para testar sessão/mensagens da interface.
- **C**: `clients.txt` — respostas simuladas para concorrência, erros e regressão de clientes.
- **U**: `supplement.txt`, `supplement.json` e PNGs — controles auxiliares, 375px, console, API real com falhas explicitamente simuladas.
- **P**: `orders-unit.txt` e `metrics-unit.txt` — funções puras, incluindo entradas congeladas.
- **B**: `build.txt` e `lint.txt` — build e lint atuais.

## Matriz preenchida

| # | Requisito original | Resultado | Evidência curta |
| --- | --- | --- | --- |
| 1 | Projeto novo, Vite + React + TypeScript, rotas, Context onde fizer sentido, serviço API e URL em `.env` | passou | Build + inspeção; Vite isolado em 5174 usou API 3334 por variável de ambiente. [M,B] |
| 2 | Login com username/password, accessToken, Bearer, nome via `/auth/me` | passou | Login/Bearer/me reais; nome no menu. Token real é UUID, não JWT: contrato do servidor prevalece. [R] |
| 3 | Só Login público, redirecionamento de volta, Sair e sessão expirada | passou | Guarda, retorno com query/hash, logout e reinício real: 401 limpa sessão. [R,S] |
| 4 | Login inválido | passou | Senha errada real devolve 400; mensagem no formulário e loading encerra. [R] |
| 5 | Menu Painel, Clientes, Pedidos, Novo cliente e Sair | passou | Menu completo, marca CRM, atalhos, link Top 3, cancelar/voltar e Sair exercitados. [R,M,U] |
| 6 | Clientes: busca por nome/e-mail, paginação de 5 (`limit`, `skip`), detalhe ao clicar | passou | Cliente 12 localizado por nome/e-mail; páginas 5/5/2. Corrida de respostas com atraso controlado. [R,C] |
| 7 | Clientes: estados carregando, vazio e erro | passou | Loading com atraso artificial; vazio por busca real; 500 simulado e retry recupera. [C,U] |
| 8 | Cliente: criar/editar; nome e e-mail válido; ao menos 2 de telefone/empresa/cidade | passou | Criar/editar reais; nome/e-mail validados; telefone/empresa/cidade presentes; retorno e reload. [R] |
| 9 | Detalhe: dados, selo, editar, excluir, pedidos e histórico | passou | Dados, selo e ambas as seções testadas; editar/excluir e voltar funcionam. [R,D,M,U] |
| 10 | Excluir cliente com confirmação e contagem dos pedidos/atendimentos apagados | passou | Cliente de teste: 2 pedidos/3 atendimentos; cancelar preserva, confirmar remove cascata/lista. [R] |
| 11 | Pedidos: data, status e total calculado por soma de preço × quantidade | passou | Vários itens: total 25,00; edição resulta 37,50; datas/status exibidos. [D] |
| 12 | Criar pedido com ao menos 1 item, título, preço >= 0, quantidade inteira >= 1 | passou | Lista/título/preço vazio/negativo e quantidade fracionária/zero rejeitados; preço zero aceito. [D] |
| 13 | Editar itens somente em aberto | passou | PATCH itens em aberto; botão ausente em pago/cancelado, inclusive após reload. [D] |
| 14 | Transições aberto → pago/cancelado; pago → cancelado; cancelado terminal | passou | As três transições executadas; cancelado sem botões de edição/status. [D] |
| 15 | Excluir pedido com confirmação; atualizar lista, selo e Painel após toda mutação | passou | Cancelar/confirmar exclusão; lista/selo/Painel atualizados após criar/editar/status/excluir. [D,M] |
| 16 | Histórico: título, texto, canal, data, ordem decrescente | passou | Título/texto/canal/data conferidos; data desc e id desc em empate, registro antigo com id maior no fim. [D] |
| 17 | Histórico: filtro telefone/e-mail/WhatsApp/presencial/todos e contador | passou | Todos e quatro canais; 5 registros: contadores 5/2/1/1/1; filtros vazios exibidos. [D] |
| 18 | Histórico: criar, editar e excluir | passou | CRUD real; edição de canal com filtro ativo, contador mantido e persistência após reload. [D] |
| 19 | Selo na lista/detalhe: VIP >= R$ 2.000; Sem compras sem pedido válido; Regular nos demais | passou | VIP=2000; 1999,99=Regular (unitário); zero válido=Regular; só cancelados/sem pedidos=Sem compras. [M,P] |
| 20 | Painel: total de clientes, vendido e ticket médio sem cancelados | passou | 1500 aberto+500 pago+9000 cancelado: vendido2000/ticket1000; zero válidos=0. [M] |
| 21 | Painel: quantidade e valor por aberto/pago/cancelado | passou | Grupos 1/1500, 1/500 e 1/9000; cancelados incluídos somente no grupo próprio. [M] |
| 22 | Top 3 por valor comprado, sem cancelados; atalho Novo cliente | passou | Top3 3000/1000/500, decrescente; base com menos de 3 e atalho Novo cliente. [M,U] |
| 23 | Todos os pedidos com nome, filtros de status/faixa de valor, ordenação data/total, link ao cliente | passou | Filtros combinados inclusivos; quatro ordenações; cancelados visíveis; nome/link corretos. [M] |
| 24 | Obter clientes para nomes (PDF sugere `limit=100`, padrão 30) | passou | 105 clientes: limit100/skip0 e skip100 observados; nome do último cliente correto. [M] |
| 25 | Rota /xyz e /clientes/999 | passou | /xyz com link Painel; /clientes/999 e edição exibem mensagem; retry/voltar funcionam. [R,U] |
| 26 | Toda chamada: try/catch/finally, finalização do loading, status e mensagem visível | passou | Status/try-catch-finally inspecionados; erros reais e simulados, loading/retry/formulários conferidos. [R,S,C,U] |
| 27 | E-mail repetido (409) e persistência JSON | passou | 409 real na criação/edição; clientes/pedidos/atendimentos persistem nos JSON e após reload. [R,D] |
| 28 | Funções puras para total, total comprado, selo e Top 3; map/filter/reduce/sort sem mutação | passou | Entradas congeladas; totais, limite VIP, média, Top3 e filtros sem mutação. [P] |
| 29 | Celular 375px, sem rolagem lateral, console sem erro | passou | 375px em todas as telas/formulários/diálogos; 24 checkpoints extras; zero console inesperado/pageerror. [U,M,D] |
| 30 | README de execução, build, commits GitHub, link, ZIP sem node_modules | bloqueado | README de execução e build passaram; sem commits/remoto/link GitHub e sem ZIP final do app. Publicação/empacotamento não executados nesta revisão. |
| 31 | Entrega AVA até 22:10 de 17/11/2026, ZIP e link GitHub | bloqueado | Sem comprovante de envio ao AVA nem link/ZIP final. A revisão não publica nem envia a prova. |

## Erros: real versus simulado

| Caso | Origem da falha | Verificação na tela |
| --- | --- | --- |
| 400 | Real: senha errada. Simulado: gravação de pedido/dados inválidos e restauração de sessão | Mensagem, loading finalizado e possibilidade de tentar novamente |
| 401 | Real: servidor parado/reiniciado invalida o token. Também simulado nas regressões | Sessão removida, mensagem de expiração, Login e reautenticação |
| 404 | Real: cliente 999 e sua edição. Simulado adicional em gravação/restauração | Cliente não encontrado / recurso não encontrado; retry/voltar |
| 409 | Real: e-mail duplicado ao criar/editar cliente. Simulado adicional no formulário | Mensagem visível, dados do formulário preservados |
| 500 | Resposta real da rota /http/500 encaminhada pelo teste; também respostas simuladas em relatórios, selo, pedidos, atendimentos e gravação | Mensagem, retry ou novo envio recupera |
| Rede | Real: API parada. Simulado adicional: route.abort no envio | Mensagem de conexão; loading finalizado |
| Lentidão | Atraso artificial, mantendo conteúdo real da resposta | Loading de Painel, clientes, pedidos, atendimentos e selo |

Os erros HTTP/rede provocados produzem mensagens de recurso no console do Chromium. Foram classificados como esperados, não ocultados. `supplement.json` registra as mensagens, com **0 erros inesperados e 0 exceções JavaScript não tratadas**. Nenhum erro inesperado reproduzível exigiu correção do app; foram ampliados os testes e atualizada a documentação.

## Preservação e limites

Testes de integração usam cliente identificável e removem apenas esse cliente/vínculos. Métricas usam cópia isolada. Ao final, código do servidor e conteúdo lógico dos quatro JSON originais foram comparados ao ZIP fornecido: preservados. O token não foi gravado nos relatórios.

O PDF menciona JWT, mas o servidor fornecido usa UUID opaco com sessões em memória. O app usa accessToken/Bearer conforme o contrato real; o servidor não foi modificado para inventar JWT.

Não há remote nem commits no repositório local, link GitHub no README, ZIP final do app ou comprovante AVA. Esses itens não são presumidos aprovados pelas etapas funcionais anteriores. A revisão solicitada não autoriza publicar em um destino ainda não informado nem enviar ao AVA.

# Etapas 4 e 5 — pedidos e histórico

## Entregue

Pedidos integrados ao detalhe, com data/status/itens/total. Função pura orderTotal em src/utils/orders.ts. Cadastro e edição validam lista não vazia, título, preço preenchido/finito >=0 e quantidade inteira >=1. Preço vazio é rejeitado e zero aceito. Edição de itens só em aberto, com PATCH itens. Status usa PATCH status e apenas as três transições autorizadas. Cancelado mantém só exclusão, com confirmação. Cada mutação bem-sucedida consulta novamente a coleção.

Histórico mostra título/texto/canal/data e ordena por data desc e id desc. Todos/Telefone/E-mail/WhatsApp/Presencial usam os valores do servidor. Contador deriva da lista filtrada. Criação, edição e exclusão consultam novamente os dados e mantêm o filtro selecionado. Recarregar a página inicia o filtro em Todos; os registros permanecem no servidor.

Loading/erro/vazio/retry nas duas seções. Erros de gravação são exibidos no formulário ou confirmação. Loading encerra em finally. Token/401 vêm do serviço centralizado.

## Verificação real — aprovada para o escopo solicitado

- node tests/orders_unit.mjs: passou; soma de vários itens, zero, lista vazia, entradas congeladas sem mutação e transições permitidas.
- python tests/details_real.py: passou no servidor fornecido, sem interceptação de respostas. Evidências: details-real.json e details-real-tests.txt.
- Pedidos: validações impedem requests inválidos; total manual de 25,00 com dois itens (incluindo zero), edição para 37,50; edição ausente após pagamento e cancelamento; três transições; exclusão cancelada/confirmada; recarga e arquivos JSON conferidos.
- Atendimentos: todos os canais criados pelo formulário; datas e empate por id conferidos, com registro antigo criado depois para detectar ordenação incorreta; todos os filtros/contadores; canal editado com filtro ativo; criação em outro canal preserva filtro; exclusão cancelada/confirmada; persistência após reload.
- Captura: evidence/real-orders-contacts-mobile.png. Sem overflow a 375/1280px; sem erros JS não tratados.
- Cliente e vínculos de teste removidos pela API; dados anteriores comparados e preservados.

O servidor permanece fornecido sem alterações. Ele não aplica as restrições de estado de pedidos; essa responsabilidade foi implementada no front conforme a prova. Selo, métricas de Painel e tela Todos os pedidos foram concluídos na [etapa 6](etapa-6.md).

# Contrato confirmado — servidor-crm fornecido

Fontes lidas integralmente: README.md e server.js do ZIP recebido. Chamadas reais registradas em evidence/real-integration.json. Não houve mudança no código do servidor.

## Autenticação e erros

- Base: http://localhost:3333, via VITE_API_URL no .env do front. CORS liberado pelo middleware cors().
- POST /auth/login: `{username,password}`. Conta documentada emilys/emilyspass. 200 `{accessToken,id,username,nome}`. O token é UUID gerado por crypto.randomUUID(), mantido em Map, **não JWT**, apesar do termo usado no PDF. Não interpretar o token; usar Bearer.
- Senha incorreta ou campos ausentes: **400**, `{message}`. O formulário foi corrigido para mostrar erro de credenciais nesse status.
- GET /auth/me: 200 `{id,username,nome}`; menu lê `nome` dessa rota.
- Demais rotas abaixo requerem `Authorization: Bearer <accessToken>`. Reinício invalida todos os tokens: 401 `{message:"Sessão inválida ou expirada"}`.
- Exceção pública para treino: GET /http/:codigo/:mensagem? devolve o código informado (200–599) e `{message}`. Usada para teste real de 500, sem alterar servidor.
- Erros: 400 validação/JSON inválido/credenciais; 401 sessão; 404 recurso/rota; 409 e-mail duplicado (case-insensitive); 500 interno. Todos usam `{message}`. Rede indisponível não tem status HTTP. O serviço lê ok/status e apresenta mensagens locais compreensíveis.

## Clientes e paginação

- GET /clientes?q=&limit=&skip=: `{clientes:[...],total,skip,limit}`. Busca por substring em nome/e-mail, aparada e sem distinguir maiúsculas. `total` é o total após filtro, antes da página.
- Padrão limit=30 e skip=0. **Não existe máximo de limit**. `limit<=0` ou NaN vira 30; skip negativo/NaN vira 0. Frações não são rejeitadas: metadados podem ser fracionários e Array.slice converte os índices. O front envia apenas inteiros (limit=5, skip=0/5/10…).
- Observado: limit=1000 retorna os 12 clientes originais e limit=1000; limit=0/-5/abc retorna limit=30; limit=2.5&skip=1.5 retorna 3 registros, limit=2.5 e skip=1.5.
- GET /clientes/:id: objeto direto `{id,nome,email,telefone?,empresa?,cidade?}`.
- POST /clientes: nome não vazio/e-mail válido obrigatórios; opcionais telefone, empresa, cidade. 201 com objeto criado.
- PATCH /clientes/:id: campos alterados; 200 objeto atualizado. Front envia apenas diferenças.
- DELETE /clientes/:id: 200 objeto excluído, não 204; remove também pedidos e atendimentos do cliente.

## Pedidos

- GET /pedidos e GET /clientes/:id/pedidos: `{pedidos:[...],total}`; coleção inteira, sem paginação.
- Pedido: `{id,clienteId,data,status,itens:[{id,titulo,preco,quantidade}]}`; sem total calculado.
- POST /clientes/:id/pedidos: `{itens:[{titulo,preco,quantidade}],data?,status?}`; 201 objeto. Pelo menos um item; título não vazio; preço number >=0; quantidade inteira >=1. Itens recebem id 1..N e título aparado.
- PATCH /pedidos/:id: `itens`, `status` ou `data`; 200 objeto atualizado. Front separa PATCH de itens e PATCH de status.
- DELETE /pedidos/:id: 200 objeto excluído.
- Enum: aberto/pago/cancelado; default aberto. **Servidor não restringe transições ou edição de itens por status**; front aplica aberto→pago/cancelado, pago→cancelado, cancelado terminal e edição apenas em aberto.

## Atendimentos

- GET /clientes/:id/atendimentos: `{atendimentos:[...],total}`, coleção inteira, data decrescente e id decrescente em empate.
- Atendimento: `{id,clienteId,titulo,texto,canal,data}`.
- POST /clientes/:id/atendimentos: título/texto não vazios; canal opcional, default telefone; data opcional. 201 objeto, título/texto aparados.
- PATCH /atendimentos/:id: titulo/texto/canal/data; 200 objeto atualizado.
- DELETE /atendimentos/:id: 200 objeto excluído.
- Valores literais: `telefone`, `email`, `whatsapp`, `presencial`. Rótulos do front: Telefone, E-mail, WhatsApp e Presencial; Todos é apenas filtro local.

## IDs, datas e contagens

IDs e clienteId são números. Novo id = maior id da coleção + 1 (pode reutilizar o maior excluído). Parâmetros de rota são convertidos com Number(). IDs de itens são locais ao pedido e renumerados na edição.

Pedidos/atendimentos usam campo `data`, default `new Date().toISOString().slice(0,10)` (dia UTC, YYYY-MM-DD). Não há validação cronológica de datas customizadas; PATCH aceita valor enviado. Clientes não têm datas automáticas. Front exibe YYYY-MM-DD como DD/MM/YYYY sem conversão de fuso.

Contagens de exclusão vêm de total das duas coleções completas. Adaptadores foram fixados nesse envelope; resposta incoerente bloqueia confirmação. A contagem é um retrato imediatamente anterior ao diálogo, não um bloqueio transacional contra alterações concorrentes.

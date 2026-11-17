> Atualização: integração real concluída; veja [relatório atual](integracao-real.md). O bloqueio descrito abaixo é histórico.

# Etapa 2 — API, sessão e proteção de rotas

## Implementado

- Serviço `src/services/api.ts`: base exclusivamente via VITE_API_URL; login público; chamadas protegidas com token explícito e Bearer; leitura de `response.ok/status`; erros 400/401/404/409/500 e rede; resposta 204; validação de JSON e accessToken.
- Context de sessão com token em sessionStorage (por aba), usuário obtido por /auth/me, restauração na recarga e logout. Senha não persistida. Nome não é extraído do login nem do token.
- Somente /login público. Guard conserva pathname + search + hash no estado do histórico e restaura após login. Login sem destino retorna a /painel. Destinos externos são recusados.
- 401 público permanece no formulário; 401 protegido invalida a sessão correspondente, limpa token/usuário e mostra mensagem no Login. Respostas antigas não invalidam token de uma sessão nova.
- Falhas não-401 na restauração aparecem na tela com Tentar novamente/Sair. Loading finalizado em finally nos consumidores assíncronos; formulário controla seu próprio estado.
- Menu com nome, links e Sair. /xyz protegido mostra página inexistente com link para Painel após autenticação.
- Painel, Clientes, Pedidos e formulários são apenas destinos identificados para navegação nesta etapa; funcionalidades de negócio continuam pendentes.

## Contrato provisório

Servidor ainda ausente. O PDF confirma login com username/password, accessToken, Bearer e /auth/me, mas não define o campo do nome. O adaptador lê nome, name, firstName/lastName ou username; todos vêm de /auth/me. Essa compatibilidade provisória NÃO confirma o schema real. Respostas sem nome geram mensagem visível. Os tipos dos recursos de negócio não foram inventados; o serviço genérico retorna unknown até confirmação de contrato.

## Testes reproduzíveis

Com Vite ativo e Python Playwright/Chromium disponíveis:

```sh
npm run build
npm run lint
python tests/session_browser.py
```

O script intercepta a API no navegador, sem iniciar servidor substituto. Exercita senha errada; proteção e retorno com query/hash após recarga do Login; nome e Bearer; logout; /xyz; destino padrão; erros 400/404/409/500/rede no formulário e na restauração, com recuperação; 401 protegido e reautenticação; layout 375px. Respostas simuladas não contam como integração real.

Resultados: evidence/session-browser.json, evidence/session-tests.txt, capturas session-expired-mobile.png e session-menu-mobile.png. Falhas HTTP e de rede provocadas nos testes podem gerar mensagens de recurso no console; nenhum erro JavaScript não tratado é aceito.

## Bloqueio

Nenhuma pasta servidor-crm encontrada em /workspace, /tmp ou /opt. GET real http://localhost:3333/auth/me falhou por conexão recusada. Não foi possível conferir README/rotas nem iniciar/reiniciar a API. Teste real de senha incorreta, login, nome e expiração após reinício permanece BLOQUEADO. Etapa NÃO APROVADA.

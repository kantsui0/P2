> Atualização: integração real concluída; veja [relatório atual](integracao-real.md). O bloqueio descrito abaixo é histórico.

# Etapa 3 — clientes

Status: implementada com testes simulados; NÃO APROVADA sem integração real.

## Entrega

- Lista consulta q, limit=5, skip; usa total retornado; busca reinicia página. AbortController, revisão de requisição e guarda de efeito invalidam respostas antigas, inclusive erro/finally atrasados.
- Carregando/vazio/erro e retry; links para detalhe/cadastro; botões de paginação conforme total.
- Detalhe, cadastro e edição com nome/e-mail obrigatórios e telefone, empresa e cidade opcionais. Validação local de nome aparado e formato de e-mail antes de enviar.
- POST/PATCH via serviço centralizado; após criar volta à lista com nova consulta; após editar volta ao detalhe com nova consulta. Sem cache de clientes desatualizado.
- Exclusão consulta pedidos e atendimentos antes de abrir confirmação modal. Contagem vem das respostas da API, nunca de fixtures no produto. Usa total quando há envelope paginado; usa tamanho quando a resposta é array. Se formato/consulta falhar, não oferece confirmação. Cancelar não faz DELETE; confirmar executa DELETE e retorna à lista recarregada. Erros aparecem na própria confirmação.
- 404 de detalhe/edição: “Cliente não encontrado”. Selo não implementado, reservado à etapa 6.

## Contrato ainda provisório

Servidor não anexado no momento dos testes. Adaptadores isolados em src/services/clients.ts assumem clientes com id string/número, nome, email e opcionais telefone/empresa/cidade; detalhe como objeto direto; lista como {clientes,total}; vínculos como arrays completos ou {pedidos,total}/{atendimentos,total}. Arrays só poderão comprovar contagem integral quando o contrato real confirmar ausência de paginação implícita. Não é possível confirmar esses formatos sem README/rotas do ZIP da professora.

As contagens são uma consulta imediatamente anterior à confirmação, não uma transação bloqueando mudanças concorrentes no servidor.

## Comandos e resultados

- npm run build: passou (evidence/clients-build.txt).
- npm run lint: passou sem avisos (evidence/clients-lint.txt).
- python tests/clients_browser.py: passou (evidence/clients-tests.txt e clients-browser.json).
- python tests/session_browser.py: regressão passou (evidence/session-regression-clients.txt); fixture de detalhe adicionada para a nova tela sem retirar verificações anteriores.
- curl -sS --max-time 3 http://localhost:3333/auth/me: conexão recusada, exit 7. Servidor não disponível.

Testes de clientes: 12 registros simulados, páginas 5/5/2; busca nome/e-mail do registro 12; reset de página; resposta lenta descartada; estados loading/vazio/erro/retry; validação sem request inválido; criação; 409 na criação/edição; edição e reload; confirmação com 2 pedidos e 3 atendimentos (envelope com total maior que a página); falha nas contagens; cancelamento sem DELETE; erro de exclusão com retry; exclusão e lista atualizada; 404 detalhe/edição; 375px sem overflow/erros JS não tratados.

Captura da confirmação: evidence/clients-delete-mobile.png. Todos os dados desses testes foram interceptados pelo Playwright; não comprovam integração ou persistência do servidor real.

## Pendente

O usuário informou possuir o ZIP fornecido pela professora. Aguardar anexo; ler README/rotas, revisar adaptadores, iniciar servidor e executar os critérios com um cliente de teste real, incluindo pedidos/atendimentos e contagens em cascata. Não alterar/excluir clientes preexistentes para os testes. Etapas 1 e 2 também mantêm pendências de integração.

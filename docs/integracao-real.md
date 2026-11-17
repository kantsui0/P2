# Integração real — etapas 1 a 3

O ZIP da professora foi extraído em /workspace/servidor-crm. README e server.js lidos integralmente; npm ci instalou dependências e npm start iniciou a API em 3333. Código e dados originais preservados. O contrato confirmado substitui hipóteses anteriores (docs/contrato-api.md).

Correções: login inválido retorna 400 (mensagem de credenciais no formulário); nome vem de nome em /auth/me; token UUID opaco, não JWT; IDs numéricos; coleções de vínculos com envelope/total, completas; PATCH de cliente envia diferenças.

## Resultado

Critérios das etapas 1–3 aprovados para o escopo solicitado, com integração real executada. Registros anteriores de bloqueio em docs/etapa-2.md, docs/etapa-3.md e evidence/verificacoes.md são históricos e foram superados por este relatório.

`python tests/real_integration.py` executa contra a API fornecida e registra evidence/real-integration.json e real-tests.txt:

- Login retorna accessToken; /auth/me aceita Bearer e retorna nome. Token omitido das evidências.
- Leituras reais de clientes, pedidos e atendimentos; envelopes/IDs/datas/canais registrados; limites da paginação inspecionados no código e chamadas.
- Senha errada, guarda de rota, retorno com query/hash, menu, logout, /xyz e link Painel.
- Cliente fora da primeira página encontrado por nome/e-mail; páginas 5/5/2.
- Cadastro, edição, 409 em ambos, validação local, detalhe atualizado e persistência JSON após reload.
- Cliente de teste com 2 pedidos/3 atendimentos: contagens reais, cancelar preserva, confirmar exclui em cascata e atualiza lista.
- Cliente inexistente mostra mensagem correta.
- 500 vem da rota real /http/500, encaminhado pelo Playwright para a chamada de sessão, com mensagem e retry na tela. Trata-se de indução controlada de erro, não falha natural de /auth/me.
- API parada de verdade: falha de rede visível. API reiniciada de verdade: 401 limpa sessão e novo login funciona.
- Comparação dos JSON confirma preservação dos dados originais. Sem erros JS não tratados.

Testes simulados de concorrência/erros permanecem complementares em tests/session_browser.py e tests/clients_browser.py, agora com fixtures conforme contrato. A corrida de respostas foi verificada por resposta atrasada controlada, sem alegar latência natural do servidor.

Na primeira tentativa o Vite não estava ativo; npm run dev foi reiniciado e a execução repetida com sucesso. Não foi necessário alterar o servidor nem executar reset.

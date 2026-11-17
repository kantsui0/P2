# Evidências — etapa 1

Data: 17/11/2026. Resultado: parcialmente entregue, NÃO APROVADA; integração bloqueada.

| Comando/verificação | Resultado |
| --- | --- |
| pdftotext -layout do PDF, leitura integral | 2 páginas lidas; texto intermediário em /workspace/work/prova.txt |
| Busca por servidor-crm em /workspace, /codex, /opt, /tmp | Nenhuma pasta encontrada; README/rotas ausentes |
| npm create vite@latest crm-front -- --template react-ts | Primeira tentativa falhou no cache padrão; corrigida com --cache /workspace/work/npm-cache, sucesso |
| npm --cache /workspace/work/npm-cache install | Sucesso, 28 pacotes; package-lock.json gerado |
| git init -b main | Repositório novo inicializado em /workspace/crm-front/.git |
| npm run build | Sucesso: TypeScript + Vite; saída em build.txt |
| npm run lint | Sucesso; saída em lint.txt |
| npm run dev -- --host 0.0.0.0 | Servidor Vite iniciado em http://localhost:5173 |
| curl -I http://localhost:5173 | HTTP 200 |
| python /workspace/work/check_front.py | Chromium real, página renderizada a 1280 e 375 px; URL do .env exibida; sem overflow ou erros de console/pageerror |
| Playwright: tentativa inicial | Binário empacotado ausente; corrigido usando Chromium instalado em /usr/bin/chromium |
| curl -sS --max-time 3 http://localhost:3333/auth/me | Exit 7, conexão recusada, nenhum status/corpo HTTP observado; NÃO testa autenticação |
| Login → accessToken → /auth/me | BLOQUEADO: servidor ausente |
| Leituras reais clientes, pedidos, atendimentos | BLOQUEADAS: servidor ausente; nenhum formato observado |

Capturas: front-1280.png e front-375.png. Resultado legível por máquina: browser.json.

O front desta etapa é uma tela de preparação com bloqueio explícito. Nenhuma funcionalidade futura foi marcada como concluída. A matriz é plano de testes de toda a prova, não evidência de implementação.

Pendente: disponibilizar a pasta servidor-crm com README, rotas e dados; confirmar contrato; iniciar o servidor e registrar os testes reais solicitados. GitHub/entrega AVA ficam para etapa própria.

Os arquivos estão em /workspace/crm-front. A pasta de saídas sugerida pelo ambiente (/codex/browser/projectless/0002-files-mentioned-by-the-user-uploaded-file-pointe/output) não pôde ser criada porque /codex é somente leitura; os arquivos foram preservados no workspace.

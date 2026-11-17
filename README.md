# CRM de clientes — Prova P2

Aplicação Vite + React + TypeScript com autenticação, clientes, pedidos, histórico de atendimento, Painel, selos e filtros. Usa o `servidor-crm` fornecido pela professora, sem modificar seu código. A API é necessária para login e dados; o build do front não exige a API ligada.

## Repositório GitHub

**Repositório:** https://github.com/kantsui0/P2

**Histórico de commits:** https://github.com/kantsui0/P2/commits/main/

O repositório é público para acesso da professora. Para obter o código com histórico:

```sh
git clone https://github.com/kantsui0/P2.git crm-front
```

O ZIP do front contém os mesmos arquivos versionados, sem `.git` ou dependências instaladas.

## Requisitos

- Node.js **24 LTS**, com npm (versões usadas na validação: Node 24.22.1 e npm 11.9.0).
- Acesso ao registro npm para instalar dependências.
- O ZIP `servidor-crm.zip` da professora, separado do ZIP do front.
- Dois terminais para executar API e front simultaneamente.

Extraia os arquivos nesta estrutura:

```text
pasta-do-projeto/
  servidor-crm/       # extraído do ZIP da professora
    package.json
    server.js
    data/
  crm-front/          # extraído do ZIP desta entrega
    package.json
    package-lock.json
    .env.example
    README.md
    src/
```

O ZIP do front não inclui `node_modules`, `.git`, `.env` local ou `dist`.

## 1. Iniciar a API

No primeiro terminal, a partir de `pasta-do-projeto`:

```sh
cd servidor-crm
npm ci
npm start
```

Mantenha o terminal aberto. A API atende em **http://localhost:3333** e grava em `servidor-crm/data/*.json`. Não execute `npm run reset` para iniciar: esse comando restaura a base e apaga alterações.

## 2. Configurar e iniciar o front

No segundo terminal, a partir de `pasta-do-projeto`:

```sh
cd crm-front
npm ci
```

Copie `.env.example` para `.env`. No Linux/macOS/Git Bash:

```sh
cp .env.example .env
```

No PowerShell do Windows:

```powershell
Copy-Item .env.example .env
```

O conteúdo deve ser:

```dotenv
VITE_API_URL=http://localhost:3333
```

O serviço lê `import.meta.env.VITE_API_URL`. Se a porta/endereço da API mudar, edite `.env` e reinicie o Vite. Variáveis `VITE_` são públicas no navegador; não coloque senhas ou tokens nelas.

Inicie:

```sh
npm run dev
```

Abra **http://localhost:5173** (ou a URL mostrada pelo Vite caso essa porta esteja ocupada).

Conta de teste documentada pelo servidor:

- Usuário: `emilys`
- Senha: `emilyspass`

O nome do menu vem de `/auth/me`. O token fica no `sessionStorage` da aba. Reiniciar a API invalida a sessão: o app mostra a mensagem e volta ao Login. Se aparecer erro de conexão, confira o primeiro terminal e `VITE_API_URL`.

## 3. Gerar e conferir o build

Na pasta `crm-front`, após `npm ci` e a criação do `.env`:

```sh
npm run build
npm run lint
```

O build executa TypeScript e Vite e gera `dist/`. Para visualizar a versão compilada:

```sh
npm run preview
```

Abra **http://localhost:4173** (ou a URL informada). Para entrar e usar os dados, mantenha a API ligada. A variável de API é incorporada no build; depois de alterá-la, gere o build novamente.

## Testes e evidências

Testes unitários, sem dependências adicionais:

```sh
node tests/orders_unit.mjs
node tests/metrics_unit.mjs
```

A [matriz final](docs/matriz.md) registra cada requisito e distingue API real de falhas simuladas. Logs e capturas estão em `evidence/`; a revisão final está em `evidence/final-review/`.

Os testes de navegador são opcionais para instalar/compilar o app. Usam Python, Playwright e Chromium; os scripts desta revisão referenciam `/usr/bin/chromium`. Em outro sistema, ajuste `executable_path` antes de executar. Eles não são necessários para o `npm run build`.

- `tests/session_browser.py` e `tests/clients_browser.py`: respostas simuladas; front ativo em 5173.
- `tests/details_real.py` e `tests/final_review.py`: API em 3333 e front em 5173; criam cliente de teste identificável e removem somente seus vínculos ao terminar.
- `tests/real_integration.py`: requer 3333 livre e front ativo; controla o início/reinício da API, deixando-a ligada ao terminar.
- `tests/metrics_real.py`: copia o servidor para base isolada, inicia API em 3334 e front em 5174, preserva a base original e encerra os processos isolados. Requer as portas livres e a pasta `work` ao lado do front.

Não execute testes reais simultaneamente. Veja também o [contrato confirmado](docs/contrato-api.md).

## Entrega no AVA

A prova deve ser submetida **pelo AVA**, com o **ZIP do front sem node_modules** e o **link GitHub**, até **22h10 de 17/11/2026, horário de Brasília**.

**Submissão não confirmada.** Gerar o ZIP ou publicar o repositório não equivale a enviar a prova. Só registre a entrega como concluída após confirmação do AVA. Use o link do repositório informado acima junto com o ZIP do front.

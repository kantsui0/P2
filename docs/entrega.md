# Preparação da entrega

**Publicação concluída:** a permissão foi liberada e os commits foram enviados para a branch main. O histórico remoto foi conferido pela API do GitHub.

Repositório destinado à entrega: https://github.com/kantsui0/P2 (público).

Histórico: commits locais de implementação e documentação preservados; atualização de publicação acrescentada sem inventar commits retroativos por etapa.

O ZIP crm-front.zip é gerado por git archive a partir do commit publicado, com prefixo crm-front/. Não inclui node_modules, .git, .env local ou dist. Inclui .env.example, package-lock.json, fontes, README, testes e evidências.

A validação do pacote é feita extraindo em pasta limpa, seguindo npm ci, cópia de .env.example, npm run build e npm run lint. O relatório externo validacao-entrega.json contém hash do ZIP e commit correspondente, evitando modificar o pacote depois de validado.

A conta foi conectada ao GitHub pelo usuário; o repositório vazio P2 foi fornecido explicitamente para publicação. O antigo bloqueio de publicação nas matrizes de revisão é histórico e não se refere a esta preparação.

**Envio ao AVA: não confirmado.** Prazo informado: 17/11/2026 às 22h10, horário de Brasília; enviar ZIP e link do repositório pelo AVA. Publicar no GitHub não equivale a submeter a prova.

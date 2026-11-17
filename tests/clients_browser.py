"""Client acceptance scenarios against simulated API, never real integration."""
import asyncio, json
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from playwright.async_api import async_playwright, expect
async def main():
 checks=[]; calls=[]; errors=[]
 clients=[dict(id=i,nome=f'Cliente {i:02}',email=f'cliente{i}@teste.com',telefone='21999999999',empresa='Teste',cidade='Rio') for i in range(1,13)]
 controls={'list_error':False,'counts_error':False,'delete_error':False,'slow_started':asyncio.Event(),'slow_release':asyncio.Event(),'slow_done':asyncio.Event()}
 async with async_playwright() as p:
  browser=await p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
  page=await browser.new_page(viewport={'width':375,'height':850})
  page.on('pageerror',lambda e:errors.append(str(e)))
  await page.add_init_script("sessionStorage.setItem('crm.accessToken','test-token')")
  async def handle(route):
   req=route.request; url=urlparse(req.url); path=url.path; query=parse_qs(url.query,keep_blank_values=True)
   assert req.headers.get('authorization')=='Bearer test-token'
   calls.append({'method':req.method,'path':path,'query':query})
   async def reply(body,status=200): await route.fulfill(status=status,json=body)
   if path=='/pedidos': await reply({'pedidos':[], 'total':0}); return
   if path=='/auth/me': await reply({'nome':'Emily'}); return
   if path=='/clientes' and req.method=='GET':
    assert query['limit']==['5']; q=query['q'][0].lower(); skip=int(query['skip'][0])
    if controls['list_error']: await reply({},500); return
    found=[c.copy() for c in clients if q in c['nome'].lower() or q in c['email'].lower()]
    if q=='cliente 01':
     controls['slow_started'].set(); await controls['slow_release'].wait()
     try: await reply({'clientes':found[skip:skip+5],'total':len(found)})
     finally: controls['slow_done'].set()
    else: await reply({'clientes':found[skip:skip+5],'total':len(found)})
    return
   if path=='/clientes' and req.method=='POST':
    data=req.post_data_json
    if any(c['email']==data['email'] for c in clients): await reply({},409); return
    data['id']=max(c['id'] for c in clients)+1; clients.append(data); await reply(data,201); return
   parts=path.strip('/').split('/'); cid=int(parts[1]); client=next((c for c in clients if c['id']==cid),None)
   if not client: await reply({},404); return
   if len(parts)==3:
    if controls['counts_error']: await reply({},500); return
    # Exact envelopes from supplied server, including full child records.
    await reply({'pedidos':[{'id':i,'clienteId':cid,'data':'2026-11-17','status':'aberto','itens':[{'titulo':'Teste','preco':1,'quantidade':1}]} for i in [1,2]], 'total':2} if parts[2]=='pedidos' else {'atendimentos':[{'id':i,'clienteId':cid,'data':'2026-11-17','titulo':'Teste','texto':'Teste','canal':'telefone'} for i in [1,2,3]], 'total':3}); return
   if req.method=='GET': await reply(client); return
   if req.method=='PATCH':
    data=req.post_data_json
    if any(c['id']!=cid and c['email']==data['email'] for c in clients): await reply({},409); return
    client.update(data); await reply(client); return
   if req.method=='DELETE':
    if controls['delete_error']: await reply({},500); return
    clients.remove(client); await route.fulfill(status=204); return
   raise AssertionError((path,req.method))
  await page.route('http://localhost:3333/**',handle)
  async def heading(text): await expect(page.get_by_role('heading',name=text,exact=True)).to_be_visible()
  async def search(text): await page.get_by_label('Buscar por nome ou e-mail').fill(text)
  async def link(text): await expect(page.get_by_role('link',name=text,exact=True)).to_be_visible()
  await page.goto('http://localhost:5173/clientes'); await heading('Clientes'); await link('Cliente 01')
  await expect(page.get_by_text('12 clientes encontrados',exact=True)).to_be_visible()
  await expect(page.get_by_role('button',name='Anterior',exact=True)).to_be_disabled()
  await page.get_by_role('button',name='Próxima',exact=True).click(); await link('Cliente 06')
  await page.get_by_role('button',name='Próxima',exact=True).click(); await link('Cliente 11')
  await expect(page.get_by_role('button',name='Próxima',exact=True)).to_be_disabled()
  await page.get_by_role('button',name='Anterior',exact=True).click(); await link('Cliente 06')
  checks.append('Paginação 5/5/2 usa total=12, skip=0/5/10 e limites dos botões.')
  for q in ['Cliente 12','cliente12@teste.com']:
   await search(q); await link('Cliente 12')
   await expect(page.get_by_text('Página 1 de 1',exact=True)).to_be_visible()
  checks.append('Nome e e-mail encontram cliente fora da primeira página; busca reinicia skip=0.')
  await search('cliente 01'); await controls['slow_started'].wait()
  await expect(page.get_by_role('status')).to_contain_text('Carregando clientes')
  await search('Cliente 12'); await link('Cliente 12')
  controls['slow_release'].set(); await controls['slow_done'].wait()
  await link('Cliente 12'); await expect(page.get_by_role('link',name='Cliente 01',exact=True)).to_have_count(0)
  checks.append('Resposta atrasada da busca anterior não substitui resultado recente; loading visível.')
  await search('nenhum'); await expect(page.get_by_text('Nenhum cliente encontrado.',exact=True)).to_be_visible()
  controls['list_error']=True; await search('falha'); await expect(page.get_by_role('alert')).to_contain_text('O servidor apresentou um erro.')
  controls['list_error']=False; await page.get_by_role('button',name='Tentar novamente').click()
  await expect(page.get_by_text('Nenhum cliente encontrado.',exact=True)).to_be_visible()
  checks.append('Estados vazio/erro e recuperação por retry.')
  await page.goto('http://localhost:5173/clientes/novo'); await heading('Novo cliente')
  before=len([c for c in calls if c['method']=='POST'])
  await page.get_by_role('button',name='Salvar',exact=True).click(); await expect(page.get_by_role('alert')).to_have_text('Informe o nome do cliente.')
  await page.get_by_label('Nome (obrigatório)',exact=True).fill('Cliente de teste')
  await page.get_by_label('E-mail (obrigatório)',exact=True).fill('invalido')
  await page.get_by_role('button',name='Salvar',exact=True).click(); await expect(page.get_by_role('alert')).to_have_text('Informe um e-mail válido.')
  assert before==len([c for c in calls if c['method']=='POST'])
  await page.get_by_label('E-mail (obrigatório)',exact=True).fill('cliente1@teste.com')
  await page.get_by_role('button',name='Salvar',exact=True).click(); await expect(page.get_by_role('alert')).to_contain_text('Já existe um cliente')
  await expect(page.get_by_role('button',name='Salvar',exact=True)).to_be_enabled()
  await page.get_by_label('E-mail (obrigatório)',exact=True).fill('novo@teste.com')
  for name,value in [('Telefone','12345'),('Empresa','Empresa de teste'),('Cidade','Niterói')]: await page.get_by_label(name,exact=True).fill(value)
  await page.get_by_role('button',name='Salvar',exact=True).click(); await heading('Clientes')
  await search('novo@teste.com'); await page.get_by_role('link',name='Cliente de teste',exact=True).click(); await heading('Cliente de teste')
  await expect(page.get_by_text('Empresa de teste',exact=True)).to_be_visible()
  checks.append('Validação nome/e-mail sem POST inválido; 409 visível; cadastro e retorno à lista atualizada.')
  await page.get_by_role('link',name='Editar',exact=True).click(); await heading('Editar cliente')
  await expect(page.get_by_label('Nome (obrigatório)',exact=True)).to_have_value('Cliente de teste')
  await page.get_by_label('E-mail (obrigatório)',exact=True).fill('cliente1@teste.com')
  await page.get_by_role('button',name='Salvar',exact=True).click(); await expect(page.get_by_role('alert')).to_contain_text('Já existe um cliente')
  await page.get_by_label('E-mail (obrigatório)',exact=True).fill('editado@teste.com')
  await page.get_by_label('Nome (obrigatório)',exact=True).fill('Cliente editado')
  await page.get_by_role('button',name='Salvar',exact=True).click(); await heading('Cliente editado')
  await page.reload(); await heading('Cliente editado')
  await expect(page.get_by_text('editado@teste.com',exact=True)).to_be_visible()
  checks.append('Edição pré-preenchida, 409, PATCH e detalhe atualizado inclusive após reload da página (dados simulados em memória).')
  controls['counts_error']=True
  await page.get_by_role('button',name='Excluir cliente',exact=True).click(); await expect(page.get_by_role('alert')).to_contain_text('O servidor apresentou um erro.')
  await expect(page.get_by_role('button',name='Confirmar exclusão')).to_have_count(0)
  controls['counts_error']=False
  await page.get_by_role('button',name='Excluir cliente',exact=True).click()
  await expect(page.get_by_role('dialog')).to_contain_text('2 pedidos e 3 atendimentos')
  await page.screenshot(path='evidence/clients-delete-mobile.png',full_page=True)
  await page.get_by_role('button',name='Cancelar',exact=True).click(); await expect(page.get_by_role('dialog')).to_have_count(0)
  assert not any(c['method']=='DELETE' for c in calls)
  await page.get_by_role('button',name='Excluir cliente',exact=True).click(); await expect(page.get_by_role('dialog')).to_contain_text('2 pedidos e 3 atendimentos')
  controls['delete_error']=True
  await page.get_by_role('button',name='Confirmar exclusão').click(); await expect(page.get_by_role('dialog').get_by_role('alert')).to_contain_text('O servidor apresentou um erro.')
  controls['delete_error']=False
  await page.get_by_role('button',name='Confirmar exclusão').click(); await heading('Clientes')
  await search('editado@teste.com'); await expect(page.get_by_text('Nenhum cliente encontrado.',exact=True)).to_be_visible()
  checks.append('Contagens consultadas: 2 pedidos/3 atendimentos (envelopes completos confirmados no servidor); falha bloqueia confirmação; cancelar não apaga; erro DELETE visível; confirmar volta à lista atualizada.')
  await page.goto('http://localhost:5173/clientes/999'); await expect(page.get_by_role('alert')).to_have_text('Cliente não encontrado')
  await page.goto('http://localhost:5173/clientes/999/editar'); await expect(page.get_by_role('alert')).to_have_text('Cliente não encontrado')
  checks.append('ID inexistente no detalhe e edição: Cliente não encontrado.')
  assert not await page.evaluate('document.documentElement.scrollWidth > innerWidth')
  assert not errors,errors
  checks.append('Sem erros JS não tratados; layout 375px sem overflow.')
  Path('evidence/clients-browser.json').write_text(json.dumps({'source':'SIMULATED_API_NOT_REAL_INTEGRATION','checks':checks,'calls':calls,'pageErrors':errors},indent=2,ensure_ascii=False))
  print('\n'.join(checks)); await browser.close()
asyncio.run(main())

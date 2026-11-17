"""Orders/history UI acceptance against the provided server, no intercepted responses.
Requires both servers running. Creates and cleans up only a dedicated test client.
"""
import asyncio,json,time
from pathlib import Path
from playwright.async_api import async_playwright,expect
ROOT=Path(__file__).resolve().parents[1]; SERVER=ROOT.parent/'servidor-crm'; E=ROOT/'evidence'
async def main():
 checks=[]; calls=[]; cid=None
 before={name:json.loads((SERVER/'data'/f'{name}.json').read_text()) for name in ['clientes','pedidos','atendimentos']}
 async with async_playwright() as p:
  request=await p.request.new_context()
  response=await request.post('http://localhost:3333/auth/login',data={'username':'emilys','password':'emilyspass'})
  token=(await response.json())['accessToken']
  async def api(method,path,body=None):
   response=await request.fetch('http://localhost:3333'+path,method=method,headers={'Authorization':'Bearer '+token},data=body)
   assert response.ok,(response.status,await response.text())
   return await response.json()
  client=await api('POST','/clientes',{'nome':'Teste pedidos e histórico','email':f'details-{time.time_ns()}@example.test','telefone':'21900000000','empresa':'Teste','cidade':'Niterói'})
  cid=client['id']
  browser=await p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
  page=await browser.new_page(viewport={'width':375,'height':850}); errors=[]
  page.on('pageerror',lambda error:errors.append(str(error)))
  def record(req):
   if ':3333/' in req.url and req.method in ['POST','PATCH','DELETE']:
    calls.append({'method':req.method,'path':req.url.split(':3333')[-1], 'body':req.post_data_json if req.method in ['POST','PATCH'] else None})
  page.on('request',record)
  await page.goto('http://localhost:5173/login')
  await page.evaluate('(token) => sessionStorage.setItem("crm.accessToken",token)',token)
  async def open_detail():
   await page.goto(f'http://localhost:5173/clientes/{cid}')
   await expect(page.get_by_role('heading',name='Teste pedidos e histórico',exact=True)).to_be_visible()
  orders=page.get_by_role('region',name='Pedidos',exact=True)
  contacts=page.get_by_role('region',name='Histórico de atendimento',exact=True)
  async def order_form():
   await orders.get_by_role('button',name='Novo pedido',exact=True).click()
   return orders.get_by_role('form',name='Novo pedido',exact=True)
  async def new_zero(title):
   form=await order_form(); await form.get_by_label('Título',exact=True).fill(title); await form.get_by_label('Preço',exact=True).fill('0')
   await form.get_by_role('button',name='Salvar pedido',exact=True).click()
   data=await api('GET',f'/clientes/{cid}/pedidos'); oid=data['pedidos'][-1]['id']
   article=orders.get_by_role('article',name=f'Pedido {oid}',exact=True)
   await expect(article).to_be_visible(); return article,oid
  try:
   await open_detail()
   await expect(orders.get_by_text('Nenhum pedido.',exact=True)).to_be_visible()
   await expect(contacts.get_by_text('0 atendimentos',exact=True)).to_be_visible()
   form=await order_form()
   await form.get_by_role('button',name='Remover item 1',exact=True).click()
   await form.get_by_role('button',name='Salvar pedido',exact=True).click(); await expect(form.get_by_role('alert')).to_contain_text('pelo menos um item')
   await form.get_by_role('button',name='Adicionar item',exact=True).click()
   await form.get_by_role('button',name='Salvar pedido',exact=True).click(); await expect(form.get_by_role('alert')).to_contain_text('Preencha o título')
   await form.get_by_label('Título',exact=True).fill('Produto principal')
   await form.get_by_role('button',name='Salvar pedido',exact=True).click(); await expect(form.get_by_role('alert')).to_contain_text('Informe um preço')
   await form.get_by_label('Preço',exact=True).fill('-1')
   await form.get_by_role('button',name='Salvar pedido',exact=True).click(); await expect(form.get_by_role('alert')).to_contain_text('Informe um preço')
   await form.get_by_label('Preço',exact=True).fill('12.5'); await form.get_by_label('Quantidade',exact=True).fill('1.5')
   await form.get_by_role('button',name='Salvar pedido',exact=True).click(); await expect(form.get_by_role('alert')).to_contain_text('quantidade deve ser inteira')
   await form.get_by_label('Quantidade',exact=True).fill('0')
   await form.get_by_role('button',name='Salvar pedido',exact=True).click(); await expect(form.get_by_role('alert')).to_contain_text('quantidade deve ser inteira')
   assert not calls
   await form.get_by_label('Quantidade',exact=True).fill('2'); await form.get_by_role('button',name='Adicionar item',exact=True).click()
   await form.get_by_label('Título',exact=True).nth(1).fill('Brinde')
   await form.get_by_label('Preço',exact=True).nth(1).fill('0'); await form.get_by_label('Quantidade',exact=True).nth(1).fill('3')
   await form.get_by_role('button',name='Salvar pedido',exact=True).click()
   await expect(orders.get_by_role('article')).to_have_count(1)
   data=await api('GET',f'/clientes/{cid}/pedidos'); order=data['pedidos'][0]; oid=order['id']
   article=orders.get_by_role('article',name=f'Pedido {oid}',exact=True)
   await expect(article).to_contain_text('25,00'); assert sum(i['preco']*i['quantidade'] for i in order['itens'])==25
   checks.append('Validações reais no front: zero itens/título vazio/preço vazio/negativo/quantidade fracionária e zero bloqueiam requests; preço zero aceito; vários itens totalizam R$ 25,00.')
   await article.get_by_role('button',name='Editar itens',exact=True).click()
   form=orders.get_by_role('form',name='Editar itens',exact=True)
   await form.get_by_label('Quantidade',exact=True).first.fill('3'); await form.get_by_role('button',name='Salvar pedido',exact=True).click()
   await expect(article).to_contain_text('37,50')
   patch=[call for call in calls if call['method']=='PATCH'][-1]; assert set(patch['body'])=={'itens'}
   await article.get_by_role('button',name='Marcar como pago',exact=True).click()
   await expect(article).to_contain_text('Status: pago'); await expect(article.get_by_role('button',name='Editar itens',exact=True)).to_have_count(0)
   patch=[call for call in calls if call['method']=='PATCH'][-1]; assert patch['body']=={'status':'pago'}
   await page.reload(); await expect(article).to_contain_text('Status: pago'); await expect(article).to_contain_text('37,50')
   await expect(article.get_by_role('button',name='Editar itens',exact=True)).to_have_count(0)
   await article.get_by_role('button',name='Cancelar pedido',exact=True).click()
   await expect(article).to_contain_text('Status: cancelado')
   await expect(article.get_by_role('button')).to_have_count(1)
   article2,oid2=await new_zero('Pedido sem custo')
   await expect(article2).to_contain_text('0,00')
   await article2.get_by_role('button',name='Cancelar pedido',exact=True).click(); await expect(article2).to_contain_text('Status: cancelado')
   await expect(article2.get_by_role('button')).to_have_count(1)
   checks.append('Edição de itens apenas em aberto com PATCH itens; aberto→pago, pago→cancelado e aberto→cancelado com PATCH status; pago/cancelado sem editar e cancelado sem ações de status; total 37,50 persiste no reload.')
   await article2.get_by_role('button',name='Excluir pedido',exact=True).click()
   await page.get_by_role('dialog').get_by_role('button',name='Cancelar',exact=True).click()
   assert any(o['id']==oid2 for o in (await api('GET',f'/clientes/{cid}/pedidos'))['pedidos'])
   await article2.get_by_role('button',name='Excluir pedido',exact=True).click()
   await page.get_by_role('dialog').get_by_role('button',name='Confirmar exclusão',exact=True).click()
   await expect(article2).to_have_count(0); await page.reload(); await expect(article2).to_have_count(0)
   await expect(article).to_contain_text('Status: cancelado')
   checks.append('Exclusão de pedido: cancelar preserva, confirmar exclui; lista e status persistem após recarregar.')
   # Seed an older real record to distinguish date ordering from insertion/ID ordering.
   for channel,label in [('telefone','Ligação'),('email','E-mail'),('whatsapp','Conversa WhatsApp'),('presencial','Visita')]:
    await contacts.get_by_role('button',name='Novo atendimento',exact=True).click()
    form=contacts.get_by_role('form',name='Novo atendimento',exact=True)
    if channel=='telefone':
     await form.get_by_role('button',name='Salvar atendimento',exact=True).click(); await expect(form.get_by_role('alert')).to_contain_text('Preencha o título e o texto')
    await form.get_by_label('Título do atendimento',exact=True).fill(label)
    await form.get_by_label('Texto',exact=True).fill('Texto '+label)
    await form.get_by_label('Canal',exact=True).select_option(channel)
    await form.get_by_role('button',name='Salvar atendimento',exact=True).click()
    await expect(contacts.get_by_role('heading',name=label,exact=True)).to_be_visible()
   await api('POST',f'/clientes/{cid}/atendimentos',{'titulo':'Registro antigo','texto':'Histórico antigo','canal':'telefone','data':'2000-01-01'})
   await page.reload(); await expect(contacts.get_by_text('5 atendimentos',exact=True)).to_be_visible()
   titles=await contacts.get_by_role('article').get_by_role('heading').all_text_contents()
   assert titles==['Visita','Conversa WhatsApp','E-mail','Ligação','Registro antigo'],titles
   assert await contacts.get_by_label('Filtrar por canal').locator('option').all_text_contents()==['Todos','Telefone','E-mail','WhatsApp','Presencial']
   for channel,count in [('',5),('telefone',2),('email',1),('whatsapp',1),('presencial',1)]:
    await contacts.get_by_label('Filtrar por canal').select_option(channel)
    await expect(contacts.get_by_text(f'{count} atendimentos',exact=True)).to_be_visible()
    await expect(contacts.get_by_role('article')).to_have_count(count)
   checks.append('Criação real em todos os canais; lista por data desc e id desc no empate, registro antigo com ID maior fica no fim; todos os filtros/contadores conferidos.')
   await contacts.get_by_label('Filtrar por canal').select_option('email')
   await contacts.get_by_role('button',name='Editar atendimento',exact=True).click()
   form=contacts.get_by_role('form',name='Editar atendimento',exact=True)
   await form.get_by_label('Canal',exact=True).select_option('whatsapp')
   await form.get_by_label('Título do atendimento',exact=True).fill('E-mail virou WhatsApp')
   await form.get_by_label('Texto',exact=True).fill('Texto editado')
   await form.get_by_role('button',name='Salvar atendimento',exact=True).click()
   await expect(contacts.get_by_label('Filtrar por canal')).to_have_value('email')
   await expect(contacts.get_by_text('0 atendimentos',exact=True)).to_be_visible()
   # Creating into another channel keeps filter and count.
   await contacts.get_by_role('button',name='Novo atendimento',exact=True).click()
   form=contacts.get_by_role('form',name='Novo atendimento',exact=True)
   await form.get_by_label('Título do atendimento',exact=True).fill('Outro canal')
   await form.get_by_label('Texto',exact=True).fill('Criado com filtro ativo')
   await form.get_by_label('Canal',exact=True).select_option('presencial')
   await form.get_by_role('button',name='Salvar atendimento',exact=True).click()
   await expect(contacts.get_by_label('Filtrar por canal')).to_have_value('email'); await expect(contacts.get_by_text('0 atendimentos',exact=True)).to_be_visible()
   await contacts.get_by_label('Filtrar por canal').select_option('whatsapp'); await expect(contacts.get_by_text('2 atendimentos',exact=True)).to_be_visible()
   edited=contacts.get_by_role('article').filter(has=page.get_by_role('heading',name='E-mail virou WhatsApp',exact=True))
   await expect(edited).to_contain_text('Texto editado')
   await edited.get_by_role('button',name='Excluir atendimento',exact=True).click()
   await page.get_by_role('dialog').get_by_role('button',name='Cancelar',exact=True).click(); await expect(edited).to_be_visible()
   await edited.get_by_role('button',name='Excluir atendimento',exact=True).click()
   await page.get_by_role('dialog').get_by_role('button',name='Confirmar exclusão',exact=True).click()
   await expect(contacts.get_by_label('Filtrar por canal')).to_have_value('whatsapp'); await expect(contacts.get_by_text('1 atendimentos',exact=True)).to_be_visible()
   await page.screenshot(path=str(E/'real-orders-contacts-mobile.png'),full_page=True)
   await page.reload(); await expect(contacts.get_by_text('5 atendimentos',exact=True)).to_be_visible()
   await expect(contacts.get_by_role('heading',name='E-mail virou WhatsApp',exact=True)).to_have_count(0)
   await contacts.get_by_label('Filtrar por canal').select_option('whatsapp'); await expect(contacts.get_by_text('1 atendimentos',exact=True)).to_be_visible()
   checks.append('Filtro mantido após criar/editar/excluir; editar canal remove registro da seleção; cancelamento/confirmar exclusão funcionam; recarga confirma persistência.')
   for width in [375,1280]:
    await page.set_viewport_size({'width':width,'height':850}); assert not await page.evaluate('document.documentElement.scrollWidth > innerWidth')
   assert not errors,errors
   orders_data=await api('GET',f'/clientes/{cid}/pedidos'); contacts_data=await api('GET',f'/clientes/{cid}/atendimentos')
   for kind,data in [('pedidos',orders_data),('atendimentos',contacts_data)]:
    stored=[item for item in json.loads((SERVER/'data'/f'{kind}.json').read_text()) if item['clienteId']==cid]
    assert sorted(stored,key=lambda x:x['id'])==sorted(data[kind],key=lambda x:x['id'])
   checks.append('Persistência nos JSON reais confirmada; desktop/375px sem overflow; nenhum erro JS não tratado.')
   (E/'details-real.json').write_text(json.dumps({'source':'REAL_PROVIDED_SERVER','checks':checks,'mutations':calls,'orders':orders_data,'contacts':contacts_data,'pageErrors':errors},indent=2,ensure_ascii=False))
   print('\n'.join(checks))
  finally:
   if cid:await api('DELETE',f'/clientes/{cid}')
   await browser.close(); await request.dispose()
  for name,data in before.items():assert json.loads((SERVER/'data'/f'{name}.json').read_text())==data,name
  print('Cleanup: cliente e vínculos de teste removidos; dados anteriores preservados.')
asyncio.run(main())

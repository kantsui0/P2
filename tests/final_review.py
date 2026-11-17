"""Supplemental final review: real API + explicitly marked injected failures.
Temporary identifiable client, cleaned via API. Viewport 375px throughout.
"""
import asyncio,json,time,re
from pathlib import Path
from playwright.async_api import async_playwright,expect
ROOT=Path(__file__).resolve().parents[1]; E=ROOT/'evidence/final-review'
async def main():
 evidence=[]; console=[]; unexpected=[]; errors=[]; cid=None
 async with async_playwright() as p:
  req=await p.request.new_context()
  r=await req.post('http://localhost:3333/auth/login',data={'username':'emilys','password':'emilyspass'});token=(await r.json())['accessToken']
  async def api(method,path,body=None):
   r=await req.fetch('http://localhost:3333'+path,method=method,headers={'Authorization':'Bearer '+token},data=body);assert r.ok;return await r.json()
  client=await api('POST','/clientes',{'nome':'Revisao final identificavel','email':f'revisao-{time.time_ns()}@example.test','telefone':'123','empresa':'Teste','cidade':'Teste'});cid=client['id']
  browser=await p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
  page=await browser.new_page(viewport={'width':375,'height':812})
  def capture(msg):
   if msg.type not in ['error','warning']:return
   console.append({'type':msg.type,'text':msg.text})
   if not re.search(r'Failed to load resource:.*(400|401|404|409|500|net::ERR_FAILED)',msg.text):unexpected.append(msg.text)
  page.on('console',capture);page.on('pageerror',lambda e:errors.append(str(e)))
  await page.goto('http://localhost:5173/login');await page.evaluate('(t)=>sessionStorage.setItem("crm.accessToken",t)',token)
  async def checkpoint(label,source='API real'):
   assert not await page.evaluate('document.documentElement.scrollWidth > innerWidth'),label
   assert not await page.evaluate("[...document.querySelectorAll('dialog[open],form')].some(e=>e.scrollWidth>e.clientWidth+1)"),label
   await page.screenshot(path=str(E/(label+'.png')),full_page=True)
   evidence.append({'scenario':label,'source':source,'width':375,'horizontalOverflow':False})
  async def detail():
   await page.goto(f'http://localhost:5173/clientes/{cid}');await expect(page.get_by_role('heading',name=client['nome'],exact=True)).to_be_visible()
  async def inject(path,status,method='GET'):
   async def handler(route):
    if route.request.method!=method:await route.continue_();return
    if status=='network':await route.abort('failed')
    else:await route.fulfill(status=status,json={'message':'Erro controlado na revisão'})
   await page.route('http://localhost:3333'+path,handler)
   return handler
  async def clear(path,handler):await page.unroute('http://localhost:3333'+path,handler)
  try:
   await detail();orders=page.get_by_role('region',name='Pedidos',exact=True);contacts=page.get_by_role('region',name='Histórico de atendimento',exact=True)
   await expect(orders.get_by_text('Nenhum pedido.',exact=True)).to_be_visible();await expect(contacts.get_by_text('0 atendimentos',exact=True)).to_be_visible();await checkpoint('01-empty-detail')
   # Real links, form cancels and responsive forms.
   await page.get_by_role('link',name='Editar',exact=True).click();await expect(page.get_by_role('heading',name='Editar cliente')).to_be_visible();await checkpoint('02-client-edit');await page.get_by_role('link',name='Cancelar',exact=True).click()
   await page.get_by_role('link',name='Voltar para clientes',exact=True).click();await expect(page.get_by_role('heading',name='Clientes',exact=True)).to_be_visible()
   await page.get_by_role('navigation',name='Menu principal').get_by_role('link',name='Novo cliente',exact=True).click();await checkpoint('03-client-create');await page.get_by_role('link',name='Cancelar',exact=True).click()
   await page.get_by_role('link',name='CRM de clientes',exact=True).click();await expect(page.get_by_role('heading',name='Painel',exact=True)).to_be_visible()
   await page.get_by_role('region',name='Top 3 clientes').get_by_role('link').first.click();await expect(page.get_by_role('heading',level=1)).to_be_visible()
   await detail();await orders.get_by_role('button',name='Novo pedido',exact=True).click();form=orders.get_by_role('form',name='Novo pedido',exact=True)
   await checkpoint('04-order-form');await form.get_by_role('button',name='Cancelar pedido',exact=True).click();await expect(form).to_have_count(0)
   await contacts.get_by_role('button',name='Novo atendimento',exact=True).click();form=contacts.get_by_role('form',name='Novo atendimento',exact=True)
   await checkpoint('05-contact-form');await form.get_by_role('button',name='Cancelar atendimento',exact=True).click();await expect(form).to_have_count(0)
   # All HTTP messages and network visible in a mutation form, loading ends.
   await orders.get_by_role('button',name='Novo pedido',exact=True).click();form=orders.get_by_role('form',name='Novo pedido',exact=True)
   await form.get_by_label('Título',exact=True).fill('Revisao item');await form.get_by_label('Preço',exact=True).fill('10')
   for status,text in [(400,'Dados inválidos'),(404,'Recurso não encontrado'),(409,'Já existe um cliente'),(500,'O servidor apresentou um erro'),('network','Não foi possível conectar')]:
    path=f'/clientes/{cid}/pedidos';handler=await inject(path,status,'POST')
    await form.get_by_role('button',name='Salvar pedido',exact=True).click();await expect(form.get_by_role('alert')).to_contain_text(text)
    await expect(form.get_by_role('button',name='Salvar pedido',exact=True)).to_be_enabled()
    await checkpoint('06-order-error-'+str(status),'Falha simulada: '+str(status));await clear(path,handler)
   await form.get_by_role('button',name='Salvar pedido',exact=True).click();await expect(orders.get_by_role('article')).to_have_count(1)
   article=orders.get_by_role('article');await article.get_by_role('button',name='Editar itens',exact=True).click();form=orders.get_by_role('form',name='Editar itens',exact=True);await checkpoint('07-order-edit');await form.get_by_role('button',name='Cancelar pedido',exact=True).click()
   await article.get_by_role('button',name='Excluir pedido',exact=True).click();await checkpoint('08-order-confirm');await page.keyboard.press('Escape');await expect(page.get_by_role('dialog')).to_have_count(0)
   # Real contact, edit cancel, delete dialog cancel via Escape.
   await contacts.get_by_role('button',name='Novo atendimento',exact=True).click();form=contacts.get_by_role('form',name='Novo atendimento',exact=True)
   await form.get_by_label('Título do atendimento',exact=True).fill('Revisao contato');await form.get_by_label('Texto',exact=True).fill('Teste de revisão')
   await form.get_by_role('button',name='Salvar atendimento',exact=True).click();await expect(contacts.get_by_role('article')).to_have_count(1)
   await contacts.get_by_role('button',name='Editar atendimento',exact=True).click();await checkpoint('09-contact-edit');await contacts.get_by_role('button',name='Cancelar atendimento',exact=True).click()
   await contacts.get_by_role('button',name='Excluir atendimento',exact=True).click();await checkpoint('10-contact-confirm');await page.keyboard.press('Escape')
   await page.get_by_role('button',name='Excluir cliente',exact=True).click();await expect(page.get_by_role('dialog')).to_contain_text('1 pedidos e 1 atendimentos');await checkpoint('11-client-confirm');await page.keyboard.press('Escape')
   # Slow real responses for loading on reports and collections; explicit delay only.
   async def slow(route):await asyncio.sleep(.7);await route.continue_()
   await page.route('http://localhost:3333/pedidos',slow);await page.goto('http://localhost:5173/painel');await expect(page.get_by_role('status')).to_contain_text('Carregando painel');await checkpoint('12-dashboard-loading','API real com atraso artificial');await expect(page.get_by_role('region',name='Ticket médio')).to_be_visible();await page.unroute('http://localhost:3333/pedidos',slow)
   for screen in ['/painel','/pedidos']:
    h=await inject('/pedidos',500);await page.goto('http://localhost:5173'+screen);await expect(page.get_by_role('alert')).to_contain_text('O servidor apresentou um erro');await checkpoint('13-report-error-'+screen[1:],'500 simulado');await clear('/pedidos',h);await page.get_by_role('button',name='Tentar novamente').click();await expect(page.get_by_role('alert')).to_have_count(0)
   await page.get_by_label('Valor mínimo').fill('99999999');await expect(page.get_by_text('Nenhum pedido para estes filtros.',exact=True)).to_be_visible();await checkpoint('14-all-orders-empty')
   # Badge and section retry controls; failure applies to real collection path.
   h=await inject(f'/clientes/{cid}/pedidos',500);await detail();await expect(page.get_by_role('button',name='Recarregar selo')).to_be_visible();await expect(orders.get_by_role('alert')).to_contain_text('O servidor apresentou um erro')
   await clear(f'/clientes/{cid}/pedidos',h);await page.get_by_role('button',name='Recarregar selo').click();await orders.get_by_role('button',name='Tentar novamente').click();await expect(page.get_by_label('Selo do cliente')).to_have_text('Regular');await expect(orders.get_by_role('article')).to_have_count(1)
   h=await inject(f'/clientes/{cid}/atendimentos',500);await detail();await expect(contacts.get_by_role('alert')).to_contain_text('O servidor apresentou um erro');await clear(f'/clientes/{cid}/atendimentos',h);await contacts.get_by_role('button',name='Tentar novamente').click();await expect(contacts.get_by_role('article')).to_have_count(1)
   evidence.append({'scenario':'badge/orders/history retries','source':'500 simulado seguido por leitura real'})
   # Slow collection reads cover loading in detail without replacing response content.
   await page.route(f'http://localhost:3333/clientes/{cid}/pedidos',slow);await page.route(f'http://localhost:3333/clientes/{cid}/atendimentos',slow);await detail();await expect(orders.get_by_role('status')).to_contain_text('Carregando pedidos');await expect(contacts.get_by_role('status')).to_contain_text('Carregando atendimentos');await checkpoint('15-detail-loading','API real com atraso artificial');await expect(contacts.get_by_role('article')).to_have_count(1);await page.unroute(f'http://localhost:3333/clientes/{cid}/pedidos',slow);await page.unroute(f'http://localhost:3333/clientes/{cid}/atendimentos',slow)
   await page.reload();await expect(orders.get_by_role('article')).to_have_count(1);await expect(contacts.get_by_role('article')).to_have_count(1);await checkpoint('16-persisted-detail')
   for path in ['/clientes/999','/clientes/999/editar']:
    await page.goto('http://localhost:5173'+path);await expect(page.get_by_role('alert')).to_have_text('Cliente não encontrado')
    await page.get_by_role('button',name='Tentar novamente',exact=True).click();await expect(page.get_by_role('alert')).to_have_text('Cliente não encontrado')
    await page.get_by_role('link',name='Voltar para clientes',exact=True).click();await expect(page.get_by_role('heading',name='Clientes',exact=True)).to_be_visible()
   evidence.append({'scenario':'retry e voltar em detalhe/edição inexistentes','source':'404 API real'})
   h=await inject('/auth/me',500);await page.goto('http://localhost:5173/painel');await expect(page.get_by_role('alert')).to_contain_text('O servidor apresentou um erro')
   await clear('/auth/me',h);await page.get_by_role('button',name='Sair',exact=True).click();await expect(page.get_by_role('heading',name='Entrar',exact=True)).to_be_visible();await checkpoint('17-login','Sair após 500 simulado na restauração da sessão')
   assert not errors,errors;assert not unexpected,unexpected
   (E/'supplement.json').write_text(json.dumps({'checks':evidence,'consoleExpectedResourceFailures':console,'unexpectedConsole':unexpected,'pageErrors':errors},indent=2,ensure_ascii=False))
   print(f'PASS: {len(evidence)} checkpoints; forms/dialogs 375px; all supplementary controls; simulated errors identified; no unexpected console/page errors.')
  finally:
   if cid:await api('DELETE',f'/clientes/{cid}')
   await browser.close();await req.dispose()
asyncio.run(main())

"""Stage 6: isolated copy of provided API on 3334 and Vite on 5174.
No changes to original server/data or front .env. No mocked API responses.
"""
import asyncio,json,os,signal,subprocess,tempfile,hashlib
from pathlib import Path
from playwright.async_api import async_playwright,expect
ROOT=Path(__file__).resolve().parents[1]; SERVER=ROOT.parent/'servidor-crm'; E=ROOT/'evidence'
async def main():
 checks=[]; calls=[]; processes=[]
 originals={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (SERVER/'data').glob('*.json')}
 envfile=(ROOT/'.env').read_bytes()
 isolated=Path(tempfile.mkdtemp(prefix='stage6-',dir=ROOT.parent/'work'))
 (isolated/'server.js').write_bytes((SERVER/'server.js').read_bytes()); (isolated/'data').mkdir()
 (isolated/'node_modules').symlink_to(SERVER/'node_modules',target_is_directory=True)
 (isolated/'data/usuarios.json').write_bytes((SERVER/'data/usuarios.json').read_bytes())
 for kind in ['clientes','pedidos','atendimentos']:(isolated/'data'/f'{kind}.json').write_text('[]')
 logfile=(E/'metrics-isolated-server.log').open('w')
 processes.append(subprocess.Popen(['node','server.js'],cwd=isolated,env={**os.environ,'PORT':'3334'},stdout=logfile,stderr=logfile,start_new_session=True))
 processes.append(subprocess.Popen(['npm','run','dev','--','--host','0.0.0.0','--port','5174','--strictPort'],cwd=ROOT,env={**os.environ,'VITE_API_URL':'http://localhost:3334'},stdout=logfile,stderr=logfile,start_new_session=True))
 async with async_playwright() as p:
  request=await p.request.new_context()
  browser=None
  try:
   for port,path in [(3334,'/http/200/ready'),(5174,'/')]:
    for _ in range(150):
     try:
      r=await request.get(f'http://localhost:{port}'+path,timeout=500)
      if r.ok:break
     except Exception:pass
     await asyncio.sleep(.1)
    else:raise AssertionError('Servidor isolado indisponível')
   r=await request.post('http://localhost:3334/auth/login',data={'username':'emilys','password':'emilyspass'});token=(await r.json())['accessToken']
   async def api(method,path,body=None):
    r=await request.fetch('http://localhost:3334'+path,method=method,headers={'Authorization':'Bearer '+token},data=body)
    assert r.ok,(r.status,await r.text());return await r.json()
   async def client(name):return await api('POST','/clientes',{'nome':name,'email':name.lower().replace(' ','-')+'@example.test','telefone':'123','empresa':'Teste','cidade':'Niterói'})
   async def order(cid,status,value,date):return await api('POST',f'/clientes/{cid}/pedidos',{'status':status,'data':date,'itens':[{'titulo':'Item teste','preco':value,'quantidade':1}]})
   browser=await p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
   page=await browser.new_page(viewport={'width':375,'height':850});errors=[]
   page.on('pageerror',lambda e:errors.append(str(e)))
   page.on('request',lambda r:calls.append(r.url) if ':3334/clientes?' in r.url else None)
   await page.goto('http://localhost:5174/login');await page.evaluate('(t)=>sessionStorage.setItem("crm.accessToken",t)',token)
   async def visit(path):await page.goto('http://localhost:5174'+path)
   async def metric(name,text):await expect(page.get_by_role('region',name=name,exact=True)).to_contain_text(text)
   async def dash():await visit('/painel');await expect(page.get_by_role('region',name='Ticket médio',exact=True)).to_be_visible()
   async def badge(cid,text):
    await visit(f'/clientes/{cid}');await expect(page.get_by_label('Selo do cliente',exact=True)).to_have_text(text)
   await dash();await metric('Total de clientes','0');await metric('Ticket médio','0,00')
   a=await client('Cliente Alfa');cid=a['id']
   canceled=await order(cid,'cancelado',9000,'2026-01-03')
   await dash();await metric('Total vendido','0,00');await metric('Ticket médio','0,00')
   await badge(cid,'Sem compras')
   opened=await order(cid,'aberto',1500,'2026-01-01');paid=await order(cid,'pago',500,'2026-01-02')
   await dash();await metric('Total vendido','2.000,00');await metric('Ticket médio','1.000,00')
   for status,value in [('aberto','1.500,00'),('pago','500,00'),('cancelado','9.000,00')]:
    group=page.get_by_role('article',name='Status '+status,exact=True);await expect(group).to_contain_text('1 pedidos');await expect(group).to_contain_text(value)
   await page.screenshot(path=str(E/'metrics-initial.png'),full_page=True)
   await page.get_by_role('main').get_by_role('link',name='Novo cliente',exact=True).click();await expect(page.get_by_role('heading',name='Novo cliente',exact=True)).to_be_visible()
   await badge(cid,'VIP')
   await visit('/clientes');row=page.get_by_role('listitem').filter(has=page.get_by_role('link',name='Cliente Alfa',exact=True));await expect(row.get_by_label('Selo do cliente')).to_have_text('VIP')
   checks.append('Base isolada vazia e só cancelado: ticket zero/Sem compras. Cenário 1500 aberto +500 pago +9000 cancelado: vendido 2000, ticket 1000, grupos 1/1500,1/500,1/9000; VIP lista/detalhe; atalho Novo cliente.')
   await badge(cid,'VIP');article=page.get_by_role('article',name=f'Pedido {opened["id"]}',exact=True)
   await article.get_by_role('button',name='Cancelar pedido',exact=True).click();await expect(page.get_by_label('Selo do cliente')).to_have_text('Regular')
   await page.get_by_role('link',name='Painel',exact=True).click();await metric('Total vendido','500,00');await metric('Ticket médio','500,00')
   await page.get_by_role('link',name='Clientes',exact=True).click();await expect(page.get_by_label('Selo do cliente')).to_have_text('Regular')
   await page.get_by_role('link',name='Cliente Alfa',exact=True).click();await expect(page.get_by_label('Selo do cliente')).to_have_text('Regular')
   checks.append('Cancelamento pelo front atualiza selo imediatamente e, ao revisitar, Painel=500, ticket=500 e selo Regular na lista/detalhe.')
   # Create/edit/delete order through existing UI and check snapshot freshness on revisit.
   orders=page.get_by_role('region',name='Pedidos',exact=True)
   await orders.get_by_role('button',name='Novo pedido',exact=True).click();form=orders.get_by_role('form',name='Novo pedido',exact=True)
   await form.get_by_label('Título',exact=True).fill('Novo');await form.get_by_label('Preço',exact=True).fill('2000');await form.get_by_role('button',name='Salvar pedido',exact=True).click()
   await expect(page.get_by_label('Selo do cliente')).to_have_text('VIP')
   entries=(await api('GET',f'/clientes/{cid}/pedidos'))['pedidos'];newid=entries[-1]['id']
   await page.get_by_role('link',name='Painel',exact=True).click();await metric('Total vendido','2.500,00')
   await badge(cid,'VIP');article=page.get_by_role('article',name=f'Pedido {newid}',exact=True)
   await article.get_by_role('button',name='Editar itens',exact=True).click();form=orders.get_by_role('form',name='Editar itens',exact=True)
   await form.get_by_label('Preço',exact=True).fill('100');await form.get_by_role('button',name='Salvar pedido',exact=True).click();await expect(page.get_by_label('Selo do cliente')).to_have_text('Regular')
   await page.get_by_role('link',name='Painel',exact=True).click();await metric('Total vendido','600,00')
   await badge(cid,'Regular');await article.get_by_role('button',name='Excluir pedido',exact=True).click();await page.get_by_role('dialog').get_by_role('button',name='Confirmar exclusão',exact=True).click()
   await expect(article).to_have_count(0);await page.get_by_role('link',name='Painel',exact=True).click();await metric('Total vendido','500,00')
   checks.append('Criação, edição e exclusão de pedido pelo front atualizam selo e totais ao revisitar: 2500→600→500.')
   zero=await client('Cliente Zero');await order(zero['id'],'aberto',0,'2026-02-01')
   only=await client('Cliente Cancelado');await order(only['id'],'cancelado',9999,'2026-02-02')
   high=await client('Cliente Maior');await order(high['id'],'pago',3000,'2026-02-03')
   mid=await client('Cliente Medio');await order(mid['id'],'aberto',1000,'2026-02-04')
   await badge(zero['id'],'Regular');await badge(only['id'],'Sem compras')
   await visit('/clientes')
   for name,label in [('Cliente Zero','Regular'),('Cliente Cancelado','Sem compras')]:await expect(page.get_by_role('listitem').filter(has=page.get_by_role('link',name=name,exact=True)).get_by_label('Selo do cliente')).to_have_text(label)
   await dash();top=page.get_by_role('region',name='Top 3 clientes',exact=True);names=await top.get_by_role('link').all_text_contents();assert names==['Cliente Maior','Cliente Medio','Cliente Alfa'],names
   for value in ['3.000,00','1.000,00','500,00']:await expect(top).to_contain_text(value)
   checks.append('Pedido válido zero=Regular; só cancelados=Sem compras em lista/detalhe; Top3 decrescente Maior3000, Medio1000, Alfa500, cancelados excluídos.')
   for i in range(100):tail=await client(f'Extra {i:03}')
   last=await order(tail['id'],'pago',100,'2026-12-31')
   await visit('/pedidos');await expect(page.get_by_role('heading',name='Todos os pedidos',exact=True)).to_be_visible()
   await expect(page.get_by_role('link',name=tail['nome'],exact=True)).to_be_visible()
   assert any('limit=100&skip=0' in url for url in calls) and any('limit=100&skip=100' in url for url in calls)
   await dash();await metric('Total de clientes','105')
   await visit('/pedidos');await expect(page.get_by_role('article')).to_have_count(8)
   await page.get_by_label('Status',exact=True).select_option('cancelado');await page.get_by_label('Valor mínimo').fill('9000');await page.get_by_label('Valor máximo').fill('9500')
   await expect(page.get_by_role('article')).to_have_count(1);await expect(page.get_by_role('article')).to_contain_text('9.000,00')
   await page.get_by_label('Status',exact=True).select_option('pago');await page.get_by_label('Valor mínimo').fill('100');await page.get_by_label('Valor máximo').fill('500')
   await expect(page.get_by_role('article')).to_have_count(2)
   await page.get_by_label('Ordenar por').select_option('total-desc');texts=await page.get_by_role('article').all_text_contents();assert '500,00' in texts[0] and '100,00' in texts[1]
   await page.get_by_label('Ordenar por').select_option('total-asc');texts=await page.get_by_role('article').all_text_contents();assert '100,00' in texts[0] and '500,00' in texts[1]
   await page.get_by_label('Ordenar por').select_option('date-desc');texts=await page.get_by_role('article').all_text_contents();assert '31/12/2026' in texts[0]
   await page.get_by_label('Ordenar por').select_option('date-asc');texts=await page.get_by_role('article').all_text_contents();assert '02/01/2026' in texts[0]
   await page.get_by_label('Valor mínimo').fill('501');await expect(page.get_by_role('alert')).to_contain_text('faixa válida')
   await page.get_by_label('Valor mínimo').fill('100');await page.get_by_role('link',name=tail['nome'],exact=True).click();await expect(page).to_have_url(f'http://localhost:5174/clientes/{tail["id"]}')
   checks.append('105 clientes: GET limit=100 skip=0/100; nomes da última página corretos. Cancelados aparecem; filtros de status/faixa inclusivos combinados; quatro ordenações; faixa inválida; link abre cliente.')
   await page.get_by_role('link',name='Editar',exact=True).click();await page.get_by_label('Nome (obrigatório)',exact=True).fill('Nome atualizado')
   await page.get_by_role('button',name='Salvar',exact=True).click();await expect(page.get_by_role('heading',name='Nome atualizado',exact=True)).to_be_visible()
   await page.get_by_role('link',name='Pedidos',exact=True).click();await expect(page.get_by_role('link',name='Nome atualizado',exact=True)).to_be_visible()
   await page.get_by_role('link',name='Nome atualizado',exact=True).click();await page.get_by_role('button',name='Excluir cliente',exact=True).click()
   await expect(page.get_by_role('dialog')).to_contain_text('1 pedidos e 0 atendimentos');await page.get_by_role('dialog').get_by_role('button',name='Confirmar exclusão',exact=True).click()
   await expect(page.get_by_role('heading',name='Clientes',exact=True)).to_be_visible();await page.get_by_role('link',name='Painel',exact=True).click();await metric('Total de clientes','104');await metric('Total vendido','4.500,00')
   await page.get_by_role('link',name='Pedidos',exact=True).click();await expect(page.get_by_role('article')).to_have_count(7);await expect(page.get_by_role('link',name='Nome atualizado',exact=True)).to_have_count(0)
   checks.append('Edição de cliente atualiza nome em Todos os pedidos; exclusão com cascata atualiza número de clientes, total e lista ao revisitar.')
   await page.screenshot(path=str(E/'metrics-orders-mobile.png'),full_page=True)
   for path in ['/painel','/pedidos','/clientes',f'/clientes/{cid}']:
    await visit(path)
    for width in [375,1280]:
     await page.set_viewport_size({'width':width,'height':850});assert not await page.evaluate('document.documentElement.scrollWidth > innerWidth')
   assert not errors,errors
   checks.append('Sem erros JS não tratados; quatro telas sem overflow a 375/1280px; API fornecida real sem mocks em base isolada.')
   (E/'metrics-real.json').write_text(json.dumps({'source':'REAL_PROVIDED_SERVER_ISOLATED_DATA','checks':checks,'clientPageRequests':calls,'pageErrors':errors},indent=2,ensure_ascii=False))
   print('\n'.join(checks))
  finally:
   if browser:await browser.close()
   await request.dispose()
   for process in processes:
    try:os.killpg(process.pid,signal.SIGTERM);process.wait(timeout=10)
    except ProcessLookupError:pass
   assert (ROOT/'.env').read_bytes()==envfile
   assert {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (SERVER/'data').glob('*.json')}==originals
asyncio.run(main())

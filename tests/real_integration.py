"""Real servidor-crm integration. Starts/restarts supplied server; leaves it running.
Uses a dedicated test client; deletes only that client and its test children.
Run: python tests/real_integration.py (Vite must already run on 5173).
"""
import asyncio, json, os, signal, subprocess, time
from pathlib import Path
from playwright.async_api import async_playwright, expect
ROOT=Path(__file__).resolve().parents[1]; SERVER=ROOT.parent/'servidor-crm'; E=ROOT/'evidence'
async def main():
 checks=[]; observed={}; process=None; test_id=None; token=None
 original={name:json.loads((SERVER/'data'/f'{name}.json').read_text()) for name in ['clientes','pedidos','atendimentos','usuarios']}
 log=(E/'real-server.log').open('a')
 async with async_playwright() as p:
  request=await p.request.new_context()
  async def start():
   nonlocal process
   process=subprocess.Popen(['npm','start'],cwd=SERVER,stdout=log,stderr=log,start_new_session=True)
   (E/'real-server.pid').write_text(str(process.pid))
   for _ in range(100):
    try:
     r=await request.get('http://localhost:3333/http/200/ready',timeout=500)
     if r.status==200:return
    except Exception: pass
    await asyncio.sleep(.1)
   raise AssertionError('Server did not start')
  async def stop():
   os.killpg(process.pid,signal.SIGTERM); process.wait(timeout=10)
  async def call(method,path,body=None,auth=True):
   r=await request.fetch('http://localhost:3333'+path,method=method,data=body,headers={'Authorization':'Bearer '+token} if auth and token else {})
   data=await r.json(); return r.status,data
  async def login_api():
   nonlocal token
   status,data=await call('POST','/auth/login',{'username':'emilys','password':'emilyspass'},False)
   assert status==200 and isinstance(data['accessToken'],str); token=data['accessToken']
   observed['login']={'status':status,'body':{**data,'accessToken':'[REDACTED UUID]'}}
  await start()
  browser=await p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
  page=await browser.new_page(viewport={'width':375,'height':850})
  errors=[]; page.on('pageerror',lambda e:errors.append(str(e)))
  async def heading(text): await expect(page.get_by_role('heading',name=text,exact=True)).to_be_visible()
  async def alert(text): await expect(page.get_by_role('alert')).to_contain_text(text)
  async def login_ui(password='emilyspass'):
   await page.get_by_label('Usuário',exact=True).fill('emilys'); await page.get_by_label('Senha',exact=True).fill(password)
   await page.get_by_role('button',name='Entrar',exact=True).click()
  async def search(q): await page.get_by_label('Buscar por nome ou e-mail').fill(q)
  try:
   await login_api()
   for path in ['/auth/me','/clientes?limit=5&skip=0','/pedidos','/clientes/1/pedidos','/clientes/1/atendimentos']:
    status,data=await call('GET',path); assert status==200
    observed[path]={'status':status,'body':data}
   for query in ['limit=0&skip=-1','limit=-5&skip=0','limit=1000&skip=0','limit=2.5&skip=1.5','limit=abc&skip=abc']:
    status,data=await call('GET','/clientes?'+query); observed[query]={'status':status,'limit':data['limit'],'skip':data['skip'],'length':len(data['clientes']),'total':data['total']}
   checks.append('Login real retorna accessToken; Bearer funciona em /auth/me; clientes/pedidos/atendimentos e limites de paginação observados.')
   target='http://localhost:5173/clientes/12?origem=pedidos#historico'
   await page.goto(target); await expect(page).to_have_url('http://localhost:5173/login')
   await login_ui('senha-incorreta'); await alert('Usuário ou senha incorretos.')
   await expect(page.get_by_role('button',name='Entrar',exact=True)).to_be_enabled()
   await login_ui(); await expect(page).to_have_url(target); await heading('Gustavo Rangel')
   await expect(page.get_by_text(observed['/auth/me']['body']['nome'],exact=True)).to_be_visible()
   checks.append('Senha incorreta real (400) no formulário; login restaura pathname/query/hash e nome vem de /auth/me.')
   await page.goto('http://localhost:5173/clientes'); await heading('Clientes')
   await expect(page.get_by_role('link',name='Marina Albuquerque',exact=True)).to_be_visible()
   await page.get_by_role('button',name='Próxima',exact=True).click(); await expect(page.get_by_role('link',name='Lucas Pimentel',exact=True)).to_be_visible()
   await page.get_by_role('button',name='Próxima',exact=True).click(); await expect(page.get_by_role('link',name='Gustavo Rangel',exact=True)).to_be_visible()
   await expect(page.get_by_role('button',name='Próxima',exact=True)).to_be_disabled()
   for q in ['Gustavo Rangel','gustavo.rangel@exemplo.com']:
    await search(q); await expect(page.get_by_role('link',name='Gustavo Rangel',exact=True)).to_be_visible()
    await expect(page.get_by_text('Página 1 de 1',exact=True)).to_be_visible()
   checks.append('Paginação real 5/5/2 e busca por nome/e-mail do cliente 12, fora da primeira página; skip reiniciado.')
   await page.goto('http://localhost:5173/clientes/novo'); await heading('Novo cliente')
   await page.get_by_role('button',name='Salvar',exact=True).click(); await alert('Informe o nome')
   await page.get_by_label('Nome (obrigatório)',exact=True).fill('Teste integração Codex')
   await page.get_by_label('E-mail (obrigatório)',exact=True).fill('invalido')
   await page.get_by_role('button',name='Salvar',exact=True).click(); await alert('Informe um e-mail válido')
   await page.get_by_label('E-mail (obrigatório)',exact=True).fill('marina.albuquerque@exemplo.com')
   await page.get_by_role('button',name='Salvar',exact=True).click(); await alert('Já existe um cliente')
   email=f'codex-teste-{int(time.time())}@example.test'
   await page.get_by_label('E-mail (obrigatório)',exact=True).fill(email)
   for name,value in [('Telefone','21900000000'),('Empresa','Teste integração'),('Cidade','Niterói')]:await page.get_by_label(name,exact=True).fill(value)
   await page.get_by_role('button',name='Salvar',exact=True).click(); await heading('Clientes')
   _,data=await call('GET','/clientes?q='+email); assert data['total']==1; test_id=data['clientes'][0]['id']
   await search(email); await page.get_by_role('link',name='Teste integração Codex',exact=True).click(); await heading('Teste integração Codex')
   await page.get_by_role('link',name='Editar',exact=True).click(); await heading('Editar cliente')
   await page.get_by_label('E-mail (obrigatório)',exact=True).fill('marina.albuquerque@exemplo.com')
   await page.get_by_role('button',name='Salvar',exact=True).click(); await alert('Já existe um cliente')
   await page.get_by_label('E-mail (obrigatório)',exact=True).fill(email)
   await page.get_by_label('Nome (obrigatório)',exact=True).fill('Teste integração editado')
   await page.get_by_role('button',name='Salvar',exact=True).click(); await heading('Teste integração editado')
   await page.reload(); await heading('Teste integração editado')
   assert any(c['id']==test_id and c['nome']=='Teste integração editado' for c in json.loads((SERVER/'data/clientes.json').read_text()))
   checks.append('Validação local; criação e edição reais; 409 em ambos; volta à lista/detalhe atualizados e persistência JSON após reload.')
   for _ in range(2):
    status,_=await call('POST',f'/clientes/{test_id}/pedidos',{'itens':[{'titulo':'Item de teste','preco':12.5,'quantidade':2}]}); assert status==201
   for channel in ['telefone','email','whatsapp']:
    status,_=await call('POST',f'/clientes/{test_id}/atendimentos',{'titulo':'Teste','texto':'Atendimento de teste','canal':channel}); assert status==201
   observed['test_counts']={}
   for kind in ['pedidos','atendimentos']:
    _,data=await call('GET',f'/clientes/{test_id}/{kind}'); observed['test_counts'][kind]=data
   await page.get_by_role('button',name='Excluir cliente',exact=True).click(); await expect(page.get_by_role('dialog')).to_contain_text('2 pedidos e 3 atendimentos')
   await page.screenshot(path=str(E/'real-delete-counts.png'),full_page=True)
   await page.get_by_role('button',name='Cancelar',exact=True).click(); assert (await call('GET',f'/clientes/{test_id}'))[0]==200
   await page.get_by_role('button',name='Excluir cliente',exact=True).click(); await expect(page.get_by_role('dialog')).to_contain_text('2 pedidos e 3 atendimentos')
   await page.get_by_role('button',name='Confirmar exclusão').click(); await heading('Clientes')
   await search(email); await expect(page.get_by_text('Nenhum cliente encontrado.',exact=True)).to_be_visible()
   assert (await call('GET',f'/clientes/{test_id}'))[0]==404
   for kind in ['pedidos','atendimentos']:assert all(x['clienteId']!=test_id for x in json.loads((SERVER/'data'/f'{kind}.json').read_text()))
   test_id=None
   checks.append('Cliente real com 2 pedidos e 3 atendimentos; contagens visíveis; cancelar preserva; confirmar apaga em cascata e atualiza lista.')
   await page.goto('http://localhost:5173/clientes/999'); await alert('Cliente não encontrado')
   await page.goto('http://localhost:5173/xyz'); await heading('Página não encontrada')
   await page.get_by_role('link',name='Voltar para o Painel').click(); await heading('Painel')
   await page.get_by_role('button',name='Sair',exact=True).click(); await heading('Entrar')
   assert await page.evaluate("sessionStorage.getItem('crm.accessToken')") is None
   await login_ui(); await heading('Painel')
   checks.append('Cliente inexistente, /xyz/link para Painel e logout real verificados.')
   # Route forwards to actual supplied /http endpoint; status/body come from real server.
   async def actual_500(route):
    response=await route.fetch(url='http://localhost:3333/http/500/Teste-integracao')
    await route.fulfill(response=response)
   await page.route('http://localhost:3333/auth/me',actual_500)
   await page.reload(); await alert('O servidor apresentou um erro.')
   await page.screenshot(path=str(E/'real-500.png'),full_page=True)
   await page.unroute('http://localhost:3333/auth/me',actual_500)
   await page.get_by_role('button',name='Tentar novamente').click(); await heading('Painel')
   checks.append('500 real de /http/500 encaminhado para a leitura de sessão por Playwright: erro na tela e retry funcional; sem modificar servidor.')
   await stop()
   await page.reload(); await alert('Não foi possível conectar ao servidor.')
   await page.screenshot(path=str(E/'real-offline.png'),full_page=True)
   await start()
   await page.get_by_role('button',name='Tentar novamente').click(); await heading('Entrar'); await alert('Sua sessão expirou. Entre novamente.')
   assert await page.evaluate("sessionStorage.getItem('crm.accessToken')") is None
   await page.screenshot(path=str(E/'real-expired.png'),full_page=True)
   await login_ui(); await heading('Painel')
   checks.append('API realmente parada: rede falha na tela; API reiniciada: token antigo retorna 401, sessão limpa, mensagem e novo login funcionam.')
   assert not await page.evaluate('document.documentElement.scrollWidth > innerWidth')
   assert not errors,errors
   for name, before in original.items():assert json.loads((SERVER/'data'/f'{name}.json').read_text())==before, name
   checks.append('Dados originais preservados; nenhum erro JS não tratado; viewport 375px sem overflow.')
   (E/'real-integration.json').write_text(json.dumps({'source':'REAL_PROVIDED_SERVER','checks':checks,'observed':observed,'pageErrors':errors},indent=2,ensure_ascii=False))
   print('\n'.join(checks))
  finally:
   if test_id:
    await login_api(); await call('DELETE',f'/clientes/{test_id}')
   await browser.close(); await request.dispose()
asyncio.run(main())

"""Simulated responses only. Run with Vite active: python tests/session_browser.py"""
import asyncio, json
from pathlib import Path
from playwright.async_api import async_playwright, expect
async def main():
 results=[]
 async with async_playwright() as p:
  browser=await p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
  page=await browser.new_page(viewport={'width':375,'height':850})
  errors=[]
  page.on('pageerror',lambda e:errors.append(str(e)))
  state={'login':200,'me':200,'network':False}
  calls=[]
  async def handle(route):
   req=route.request
   login=req.url.endswith('/auth/login')
   calls.append({'path':req.url.split(':3333')[-1],'method':req.method,'protected':not login})
   if req.url.endswith('/pedidos') and '/clientes/' not in req.url:
    await route.fulfill(status=200,json={'pedidos':[], 'total':0})
    return
   if '/clientes?' in req.url:
    await route.fulfill(status=200,json={'clientes':[], 'total':0, 'skip':0, 'limit':100})
    return
   if req.url.endswith('/clientes/42/pedidos') or req.url.endswith('/clientes/42/atendimentos'):
    kind=req.url.rsplit('/',1)[-1]
    await route.fulfill(status=200,json={kind:[], 'total':0})
    return
   if req.url.endswith('/clientes/42'):
    assert req.headers.get('authorization')=='Bearer test-token'
    await route.fulfill(status=200,json={'id':42,'nome':'Cliente 42','email':'cliente42@teste.com'})
    return
   if state['network']: await route.abort('failed'); return
   if login:
    assert 'authorization' not in req.headers
    assert req.post_data_json=={'username':'emilys','password':'emilyspass'}
   else:
    assert req.url.endswith('/auth/me')
    assert req.headers.get('authorization')=='Bearer test-token'
   status=state['login' if login else 'me']
   body=({'accessToken':'test-token'} if login else {'nome':'Emily Johnson'}) if status==200 else {}
   await route.fulfill(status=status,json=body)
  await page.route('http://localhost:3333/**',handle)
  async def submit():
   await page.get_by_label('Usuário',exact=True).fill('emilys')
   await page.get_by_label('Senha',exact=True).fill('emilyspass')
   await page.get_by_role('button',name='Entrar',exact=True).click()
  async def heading(name): await expect(page.get_by_role('heading',name=name,exact=True)).to_be_visible()
  async def alert(text): await expect(page.get_by_role('alert')).to_contain_text(text)
  async def logged_out(): assert await page.evaluate("sessionStorage.getItem('crm.accessToken')") is None
  target='http://localhost:5173/clientes/42?origem=pedidos&filtro=a%20b#historico'
  await page.goto(target)
  await expect(page).to_have_url('http://localhost:5173/login')
  await page.reload()
  state['login']=401
  await submit(); await alert('Usuário ou senha incorretos.')
  await expect(page.get_by_role('button',name='Entrar',exact=True)).to_be_enabled()
  await logged_out()
  results.append('Rota protegida exige login; senha incorreta aparece no formulário; loading finalizado.')
  state['login']=200
  await submit(); await expect(page).to_have_url(target)
  await expect(page.get_by_text('Emily Johnson',exact=True)).to_be_visible()
  results.append('Retorno completo preservado inclusive reload do Login; nome de /auth/me; header Bearer validado.')
  await page.goto('http://localhost:5173/xyz'); await heading('Página não encontrada')
  await page.get_by_role('link',name='Voltar para o Painel').click(); await heading('Painel')
  await page.get_by_role('button',name='Sair',exact=True).click()
  await expect(page).to_have_url('http://localhost:5173/login'); await logged_out()
  await page.goto('http://localhost:5173/xyz'); await expect(page).to_have_url('http://localhost:5173/login')
  results.append('/xyz autenticado mostra aviso/link; logout limpa sessão; /xyz sem login é protegido.')
  await page.goto('http://localhost:5173/login')
  await page.evaluate("history.replaceState(null, '', '/login')")
  await page.reload() # fresh direct visit, without the previous /xyz return state
  cases=[(400,'Usuário ou senha incorretos.'),(404,'Recurso não encontrado.'),(409,'Já existe um cliente'),(500,'O servidor apresentou um erro.')]
  for status,text in cases:
   state['login']=status
   await submit(); await alert(text)
   await expect(page.get_by_role('button',name='Entrar',exact=True)).to_be_enabled()
   results.append(f'Login: {status} visível e loading finalizado.')
  state['network']=True
  await submit(); await alert('Não foi possível conectar ao servidor.')
  await expect(page.get_by_role('button',name='Entrar',exact=True)).to_be_enabled()
  results.append('Login: falha de rede visível e loading finalizado.')
  state.update(network=False,login=200)
  await submit(); await heading('Painel')
  results.append('Login direto usa Painel como padrão.')
  for status,text in cases:
   state['me']=status
   await page.reload(); await alert('Dados inválidos.' if status == 400 else text)
   state['me']=200
   await page.get_by_role('button',name='Tentar novamente').click(); await heading('Painel')
   results.append(f'Protegida: {status} visível, loading finalizado e retry recupera sessão.')
  state['network']=True
  await page.reload(); await alert('Não foi possível conectar ao servidor.')
  state['network']=False
  await page.get_by_role('button',name='Tentar novamente').click(); await heading('Painel')
  results.append('Protegida: rede falha com mensagem e retry funciona.')
  state['me']=401
  await page.goto('http://localhost:5173/pedidos?status=pago#lista')
  await expect(page).to_have_url('http://localhost:5173/login')
  await alert('Sua sessão expirou. Entre novamente.'); await logged_out()
  await page.screenshot(path='evidence/session-expired-mobile.png',full_page=True)
  state['me']=200
  await submit(); await expect(page).to_have_url('http://localhost:5173/pedidos?status=pago#lista'); await heading('Todos os pedidos')
  results.append('401 SIMULADO limpa sessão, mostra mensagem e restaura destino após novo login.')
  assert not await page.evaluate('document.documentElement.scrollWidth > innerWidth')
  await page.screenshot(path='evidence/session-menu-mobile.png',full_page=True)
  state['me']=401
  await page.evaluate("async () => { const {api} = await import('/src/services/api.ts'); try { await api.protected('/auth/me', sessionStorage.getItem('crm.accessToken')); } catch {} }")
  await expect(page).to_have_url('http://localhost:5173/login')
  await alert('Sua sessão expirou. Entre novamente.'); await logged_out()
  results.append('401 em chamada protegida durante sessão ativa também limpa sessão e redireciona, sem reload.')
  assert not errors,errors
  results.append('375px sem overflow e sem erros JS não tratados.')
  Path('evidence/session-browser.json').write_text(json.dumps({'source':'SIMULATED_API_NOT_REAL_INTEGRATION','checks':results,'requests':calls,'pageErrors':errors},indent=2,ensure_ascii=False))
  print('\n'.join(results))
  await browser.close()
asyncio.run(main())

"""Optional visual QA; requires playwright and its Chromium install."""
import os,subprocess,time,json
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/demo_frames';OUT.mkdir(exist_ok=True)
server=subprocess.Popen(['python','-m','streamlit','run','app.py','--server.port','8507','--server.address','127.0.0.1'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,env={**os.environ,'OMP_NUM_THREADS':'2','OPENBLAS_NUM_THREADS':'2'})
try:
 with sync_playwright() as p:
  b=p.chromium.launch(headless=True,args=['--no-sandbox']);page=b.new_page(viewport={'width':1440,'height':1000},device_scale_factor=1)
  for attempt in range(30):
   try:page.goto('http://127.0.0.1:8507');break
   except Exception:time.sleep(.5)
  page.get_by_text('A patient-specific view',exact=True).wait_for(timeout=60000)
  def snap(name):
   page.wait_for_timeout(500);page.screenshot(path=str(OUT/f'{name}.png'),full_page=False)
  def nav(name):
   page.get_by_text(name,exact=True).first.click();page.wait_for_timeout(600)
  snap('overview');nav('Patient Profile');snap('profile');nav('Live Digital Twin');snap('live_initial')
  page.get_by_role('button',name='Start / Resume',exact=True).click();page.wait_for_timeout(4500);page.get_by_role('button',name='Pause',exact=True).click();snap('live_running')
  page.get_by_role('button',name='Step +5 min',exact=True).click();snap('live_step')
  for i in range(7):page.get_by_role('button',name='Advance +1 hour',exact=True).click();page.wait_for_timeout(100)
  snap('live_meal');page.get_by_text('Inspect evolving twin state',exact=True).click();page.mouse.wheel(0,650);snap('state');page.mouse.wheel(0,-1500)
  nav('Risk and Explainability');snap('explain');page.mouse.wheel(0,650);snap('features');page.mouse.wheel(0,-1600)
  nav('Scenario Simulator');snap('scenario_glucose')
  for name,file in [('Meal annotation now','scenario_meal'),('Recent activity','scenario_activity'),('Missing sensor interval','scenario_missing'),('Alternate historical profile','scenario_profile')]:
   page.get_by_role('combobox').last.click();page.get_by_role('option',name=name,exact=True).click();snap(file)
  nav('Model Performance');snap('performance');page.mouse.wheel(0,650);snap('calibration');page.mouse.wheel(0,550);snap('importance');page.mouse.wheel(0,-2500)
  nav('Prediction Log');snap('log');page.get_by_text('Retrospective evaluation: reveal complete recorded timeline',exact=True).click();page.mouse.wheel(0,600);snap('retrospective')
  assert not page.locator('[data-testid="stException"]').count()
  (OUT/'qa.json').write_text(json.dumps({'visual_pages':7,'frames':len(list(OUT.glob('*.png'))),'browser_errors':0},indent=2));b.close()
finally:server.terminate();server.wait()

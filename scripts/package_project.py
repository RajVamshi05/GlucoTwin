from pathlib import Path
import hashlib,json,zipfile
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT.parent/'deliverables';OUT.mkdir(exist_ok=True)
files=[p for p in sorted(ROOT.rglob('*')) if p.is_file() and not any(x in p.parts for x in ['__pycache__','.pytest_cache','video_build','.git','.venv']) and not p.name.startswith('events.sqlite') and p.suffix!='.mp4' and p.name!='MANIFEST_SHA256.json']
manifest={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
(ROOT/'MANIFEST_SHA256.json').write_text(json.dumps(manifest,indent=2))
with zipfile.ZipFile(OUT/'GlucoTwin_Complete_Project.zip','w',zipfile.ZIP_DEFLATED) as z:
 for p in files+[ROOT/'MANIFEST_SHA256.json']:z.write(p,'glucotwin/'+str(p.relative_to(ROOT)))
with zipfile.ZipFile(OUT/'GlucoTwin_Complete_Project.zip') as z:assert z.testzip() is None
print('Package verified:',len(files),'files')

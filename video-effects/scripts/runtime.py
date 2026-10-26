"""Explicit, persistent runtime settings. No installer or network actions."""
from pathlib import Path
import json,os,shutil,subprocess,sys,platform
ROOT=Path(__file__).resolve().parents[1]
KEYS={'gsap':'VIDEO_EFFECTS_GSAP','hyperframes':'VIDEO_EFFECTS_HYPERFRAMES','browser':'HYPERFRAMES_BROWSER_PATH'}
def settings():
 p=ROOT/'runtime.local.json'
 saved=json.loads(p.read_text()) if p.exists() else {}
 return {k:os.environ.get(env) or saved.get(k) for k,env in KEYS.items()}
def activate():
 for k,value in settings().items():
  if value:os.environ[KEYS[k]]=str(value)
def configure(gsap,hyperframes,browser):
 values={'gsap':gsap,'hyperframes':hyperframes,'browser':browser}
 for k,value in values.items():
  p=Path(value).expanduser().resolve()
  if not p.is_file():raise ValueError('Runtime file missing: '+k)
  values[k]=str(p)
 target=ROOT/'runtime.local.json'
 if target.exists():raise ValueError('Runtime configuration already exists; keep a backup before changing it')
 target.write_text(json.dumps(values,indent=2)+'\n');target.chmod(0o600)
 return target

def doctor():
 values=settings();checks=[]
 checks.append({'name':'python','ok':sys.version_info>=(3,10),'version':platform.python_version()})
 for exe in ('node','ffmpeg','ffprobe'):
  path=shutil.which(exe);version=None
  if path:
   try:version=subprocess.check_output([path,'--version' if exe=='node' else '-version'],stderr=subprocess.STDOUT,timeout=10).decode().splitlines()[0]
   except (OSError,subprocess.SubprocessError):path=None
  ok=bool(path)
  if exe=='node' and version:ok=ok and int(version.lstrip('v').split('.')[0])>=20
  checks.append({'name':exe,'ok':ok,'path':path,'version':version})
 for k,path in values.items():checks.append({'name':k,'ok':bool(path and Path(path).is_file()),'path':path})
 return {'ready':all(x['ok'] for x in checks),'checks':checks,'supported_release_target':'macOS; other operating systems not qualified','installs_performed':False}

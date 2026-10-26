#!/usr/bin/env python3
"""Install only verified package files; explicit upgrades preserve the complete old skill."""
from pathlib import Path
import argparse,hashlib,json,shutil,tempfile,uuid,datetime
root=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--agent',choices=['codex','claude'],required=True);p.add_argument('--root',type=Path);p.add_argument('--upgrade',action='store_true');a=p.parse_args()
base=(a.root or Path.home()/('.codex' if a.agent=='codex' else '.claude')/'skills').expanduser().resolve();dest=base/'video-effects'
if dest.is_symlink():raise SystemExit('Refusing a symlink destination')
if dest.exists() and not a.upgrade:raise SystemExit('Destination exists. Use --upgrade to preserve it in a backup and install the new version.')
manifest=json.loads((root/'MANIFEST.json').read_text());verified=[]
for name,expected in manifest['files'].items():
 relative=Path(name)
 if relative.is_absolute() or '..' in relative.parts:raise SystemExit('Unsafe package path: '+name)
 src=root/relative
 if not src.is_file() or src.is_symlink() or not src.resolve().is_relative_to(root.resolve()) or hashlib.sha256(src.read_bytes()).hexdigest()!=expected:raise SystemExit('Package integrity check failed: '+name)
 if relative.parts[0]=='video-effects':verified.append((src,Path(*relative.parts[1:])))
if not any(str(rel)=='SKILL.md' for _,rel in verified):raise SystemExit('Missing skill entrypoint')
base.mkdir(parents=True,exist_ok=True);stage=Path(tempfile.mkdtemp(prefix='.video-effects-staging-',dir=base));backup=None
try:
 for src,relative in verified:
  target=stage/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,target)
 if dest.exists():
  config=dest/'runtime.local.json'
  if config.exists():
   if config.is_symlink():raise ValueError('Refusing a symlink runtime configuration')
   json.loads(config.read_text());shutil.copy2(config,stage/config.name)
  backup=base/('video-effects-backup-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S')+'-'+uuid.uuid4().hex[:6]);dest.rename(backup)
 try:stage.rename(dest)
 except OSError:
  if backup and not dest.exists():backup.rename(dest)
  raise
except Exception:
 if stage.exists():shutil.rmtree(stage)
 raise
print(json.dumps({'installed':str(dest),'version':manifest.get('version'),'backup':str(backup) if backup else None,'dependencies_installed':False},indent=2))

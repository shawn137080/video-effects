#!/usr/bin/env python3
"""Allowlisted standalone skill release. Never packages generated output or runtime config."""
from pathlib import Path
import argparse,hashlib,json,zipfile,re
ROOT=Path(__file__).resolve().parents[1]
TOP={'README.md','README.zh-CN.md','LICENSE','THIRD-PARTY.md','CONTRIBUTING.md','VALIDATION.md','install.py','.gitignore'}
TREES={'video-effects','tests','tools','examples','.github'}
EXT={'.md','.py','.json','.js','.ttf','.txt','.yaml','.yml','.swift'}
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def files(root=ROOT):
 result=[]
 for f in sorted(root.rglob('*')):
  if not f.is_file():continue
  rel=f.relative_to(root)
  if '__pycache__' in rel.parts or f.suffix=='.pyc' or '.git' in rel.parts:continue
  if len(rel.parts)==1 and f.name in TOP:pass
  elif rel.parts[0] in TREES and (f.suffix in EXT or f.name=='LICENSE'):pass
  elif f.name=='MANIFEST.json' and len(rel.parts)==1:continue
  elif rel.parts[0] in ('dist','outputs'):continue
  else:raise ValueError('Unallowlisted release file: '+str(rel))
  if f.is_symlink() or f.name=='runtime.local.json' or f.name.startswith('.env'):raise ValueError('Private runtime or symlink: '+str(rel))
  if f.suffix!='.ttf':
   s=f.read_text()
   if re.search(r'/(?:Users|home)/[a-zA-Z0-9_.-]+/',s):raise ValueError('Personal path: '+str(rel))
   if re.search(r'(?:gh[pousr]_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9]{24,})',s):raise ValueError('Potential credential: '+str(rel))
  result.append(f)
 return result

def manifest(root=ROOT):return {'name':'video-effects','version':'1.0.0','license':'MIT','effect_families':25,'files':{str(f.relative_to(root)):digest(f) for f in files(root)}}
def main():
 p=argparse.ArgumentParser();p.add_argument('--manifest',action='store_true');p.add_argument('--check',action='store_true');p.add_argument('--output',type=Path);a=p.parse_args();m=manifest()
 if a.manifest:(ROOT/'MANIFEST.json').write_text(json.dumps(m,indent=2)+'\n')
 if a.check or a.output:
  if json.loads((ROOT/'MANIFEST.json').read_text())!=m:raise ValueError('Manifest stale; review changes, then run --manifest')
 if a.output:
  a.output.parent.mkdir(parents=True,exist_ok=True)
  with zipfile.ZipFile(a.output,'x',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
   for f in files()+[ROOT/'MANIFEST.json']:
    info=zipfile.ZipInfo('video-effects/'+str(f.relative_to(ROOT)),date_time=(2026,10,25,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,f.read_bytes())
  a.output.with_suffix('.sha256').write_text(digest(a.output)+'  '+a.output.name+'\n')
 print(json.dumps({'files':len(m['files']),'license':m['license'],'check':'passed' if a.check else 'manifest prepared','archive':str(a.output) if a.output else None}))
if __name__=='__main__':
 try:main()
 except (ValueError,OSError) as e:raise SystemExit(str(e))

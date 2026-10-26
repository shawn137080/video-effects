#!/usr/bin/env python3
"""Compile and render one source-bound effect, never a whole editorial pipeline."""
from pathlib import Path
import argparse, array, hashlib, json, math, os, re, shutil, subprocess, sys, uuid, wave
import runtime
import scene_craft
ROOT=Path(__file__).resolve().parents[1]
FPS=30

def digest(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x): Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def run(args,log=None):
 r=subprocess.run([str(x) for x in args],stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
 if log: Path(log).write_bytes(r.stdout)
 if r.returncode: raise ValueError('Command failed: '+(str(log) if log else r.stdout.decode(errors='replace')[-2000:]))
 return r.stdout

def probe(p): return json.loads(run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',p]))
def local(value,base):
 p=Path(value).expanduser();p=(base/p).resolve() if not p.is_absolute() else p.resolve()
 if not p.is_file(): raise ValueError('Missing local asset: '+str(p))
 return p

def seconds(v,name,lo=0,hi=60):
 if type(v) not in (int,float) or not math.isfinite(v) or not lo<=v<=hi: raise ValueError('Invalid '+name)
 return v

def frame_time(v,name):
 v=seconds(v,name);f=round(v*FPS)
 if abs(v*FPS-f)>.02: raise ValueError(name+' must land on a 30fps frame (e.g. 0.5, 1, 1.2)')
 return f

def preflight(config,base):
 n=config.get('effect')
 if type(n) is not int or n not in scene_craft.FAMILIES: raise ValueError('Unknown effect; run catalog')
 count=frame_time(config.get('duration',3.6),'duration');start=frame_time(config.get('startTime',0),'startTime')
 if count<18 or count>900: raise ValueError('Use 0.6–30 seconds per effect')
 color=config.get('accentColor','#efe282')
 if not re.fullmatch(r'#[0-9a-fA-F]{6}',color): raise ValueError('accentColor must be #RRGGBB')
 for key in ('demo','showHeader','showTitles','sourceAudio'):
  if key in config and type(config[key]) is not bool: raise ValueError(key+' must be boolean')
 source=local(config['inputFile'],base);sources={'raw':(source,start,count)};probes={}
 def video_check(p,f,frames):
  info=probe(p)
  if not any(s['codec_type']=='video' for s in info['streams']): raise ValueError('Expected video: '+str(p))
  if (f+frames)/FPS>float(info['format']['duration'])+.001: raise ValueError('Source too short: '+str(p))
  return info
 probes['raw']=video_check(source,start,count)
 d=dict(config.get('design',{}));d.update(mainText=config.get('mainText',scene_craft.FAMILIES[n]),subText=config.get('subText',''))
 assets={'raw':{'file':str(source),'compiled_file':'assets/raw.mp4'}}
 images={'.png','.jpg','.jpeg','.webp'}
 for field,key in [('cutoutFile','matte'),('mediaFile','secondary'),('freezeFile','freeze'),('breakStill','breakStill'),('destinationMatte','destinationMatte')]:
  if config.get(field):
   p=local(config[field],base);offset=frame_time(config.get('cutoutStartTime',config.get('startTime',0)) if key=='matte' else config.get('mediaStartTime',0) if key=='secondary' else 0,field+' offset')
   assets[key]={'file':str(p),'compiled_file':'assets/'+key+p.suffix.lower()};d[key]=key
   if p.suffix.lower() in images:sources[key]=(p,None,None)
   else:probes[key]=video_check(p,offset,count);sources[key]=(p,offset,count)
 for i,path in enumerate(config.get('cardFiles',[])):
  p=local(path,base)
  if p.suffix.lower() not in images: raise ValueError('cardFiles must be images')
  key='card'+str(i);assets[key]={'file':str(p),'compiled_file':'assets/'+key+p.suffix.lower()};sources[key]=(p,None,None)
 if 'cardFiles' in config:d['cards']=['card'+str(i) for i in range(len(config['cardFiles']))]
 for key in ('items','payoff','dataPoints','dataSource','timerSeconds','freezeFrame','cueFrames','motionFrames','zoomKeys','timerTrack','refinement'):
  if key in config:d[key]=config[key]
 # A freeze is always extracted from this normalized raw clip unless explicitly supplied.
 if n in (13,24) and 'freeze' not in d:
  f=d.get('freezeFrame',d.get('cueFrames',{}).get('cover',min(count-1,round(count*.28))))
  if type(f) is not int or not 0<=f<count: raise ValueError('freezeFrame out of range')
  d['freezeFrame']=f;d['freeze']='freeze';assets['freeze']={'file':'generated.png','compiled_file':'assets/freeze.png'}
 if n==13 and 'freezeFrame' in d:d.setdefault('cueFrames',{}).setdefault('cover',d['freezeFrame'])
 beats=[{'id':'effect','effect':n,'frames':count,'start_frame':0,'end_frame':count,'picture':{'asset':'raw'},'design':d}]
 if n==15:
  p=local(config['nextFile'],base);nf=frame_time(config.get('nextStartTime',0),'nextStartTime');nc=frame_time(config.get('nextDuration',.8),'nextDuration')
  if nc<18: raise ValueError('Next scene needs at least18frames')
  probes['next']=video_check(p,nf,nc);sources['next']=(p,nf,nc);assets['next']={'file':str(p),'compiled_file':'assets/next.mp4'}
  if 'secondary' not in d:d['secondary']='next'
  beats[0]['transition']='through';beats.append({'id':'next','effect':0,'frames':nc,'start_frame':count,'end_frame':count+nc,'picture':{'asset':'next'},'design':{},'captions':[]})
 p={'treatment':'scene-craft','fps':FPS,'frames':sum(b['frames'] for b in beats),'assets':assets,'beats':beats,'locale':config.get('locale','en'),'typography':'editorial-condensed','header':config.get('header','Video Effects'),'headerSub':config.get('headerSub','Reusable motion'),'accentColor':color,'demo':config.get('demo',False),'showHeader':config.get('showHeader',False),'showTitles':config.get('showTitles',True)}
 scene_craft.validate(p)
 return p,sources,probes

def normalize(source,offset,count,dest,alpha=False):
 args=['ffmpeg','-v','error','-n']
 if alpha:args+=['-c:v','libvpx-vp9'] if source.suffix.lower()=='.webm' else []
 args+=['-ss',offset/FPS,'-i',source,'-vf','fps=30,scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1','-frames:v',count,'-an']
 args+=['-c:v','libvpx-vp9','-pix_fmt','yuva420p','-auto-alt-ref','0','-deadline','realtime','-cpu-used','6','-crf','22','-b:v','0'] if alpha else ['-c:v','libx264','-pix_fmt','yuv420p','-crf','18','-preset','fast']
 run(args+[dest])

def build(config,target):
 config=Path(config).resolve();c=json.loads(config.read_text());p,sources,probes=preflight(c,config.parent)
 gsap=local(runtime.settings().get('gsap') or 'missing-gsap',Path.cwd());out=Path(target).resolve()
 out.mkdir(parents=True,exist_ok=False);a=out/'assets';a.mkdir();receipt_sources={}
 for key,(f,start,count) in sources.items():
  original=digest(f);suffix=f.suffix.lower() if start is None else '.webm' if key in ('matte','destinationMatte') else '.mp4';dest=a/(key+suffix)
  if start is None:shutil.copy2(f,dest)
  else:normalize(f,start,count,dest,key in ('matte','destinationMatte'))
  if digest(f)!=original:raise ValueError('Source changed during compile')
  p['assets'][key].update(file=str(dest),compiled_file='assets/'+dest.name)
  receipt_sources[key]={'sha256':original,'source_in_frame':start,'frames':count,'file':str(f)}
 d=p['beats'][0]['design']
 if d.get('freeze')=='freeze' and 'freeze' not in sources:
  run(['ffmpeg','-v','error','-n','-i',a/'raw.mp4','-vf',f"select=eq(n\\,{d['freezeFrame']})",'-frames:v','1',a/'freeze.png'])
  p['assets']['freeze']['file']=str(a/'freeze.png')
 # Original voice only; no music library, transcription or editorial assembly.
 parts=[]
 for key in ['raw']+(['next'] if 'next' in sources else []):
  f,start,count=sources[key];samples=count*1600*2
  if c.get('sourceAudio',True) and any(s['codec_type']=='audio' for s in probes[key]['streams']):
   raw=run(['ffmpeg','-v','error','-ss',start/FPS,'-i',f,'-t',count/FPS,'-vn','-ar','48000','-ac','2','-f','s16le','-'])
   raw=raw[:samples*2].ljust(samples*2,b'\0')
  else:raw=b'\0'*(samples*2)
  parts.append(raw)
 with wave.open(str(a/'voice-mix.wav'),'wb') as w:w.setparams((2,2,48000,0,'NONE','not compressed'));w.writeframes(b''.join(parts))
 shutil.copy2(gsap,a/'gsap.min.js')
 for name in ['Manrope.ttf','Manrope-OFL.txt']:shutil.copy2(ROOT/'effects/_assets/studio3d'/name,a/name)
 doc,_=scene_craft.document(p,out);(out/'index.html').write_text(doc);save(out/'hyperframes.json',{'paths':{'assets':'assets'}});save(out/'effect-plan.json',p)
 save(out/'receipt.json',{'schema':'video-effects/1','frames':p['frames'],'fps':FPS,'sources':receipt_sources,'files':{str(f.relative_to(out)):digest(f) for f in sorted(out.rglob('*')) if f.is_file()},'compiler':{n:digest(Path(__file__).with_name(n)) for n in ['effects.py','scene_craft.py','scene_phone.js']},'scope':'standalone effect preview; no publication or human approval'})
 return out

def verify(project):
 p=Path(project).resolve();r=json.loads((p/'receipt.json').read_text())
 if r.get('schema')!='video-effects/1':raise ValueError('Unsupported receipt')
 for name,sha in r['files'].items():
  rel=Path(name)
  if rel.is_absolute() or '..' in rel.parts:raise ValueError('Unsafe receipt path')
  f=p/rel
  if not f.is_file() or not f.resolve().is_relative_to(p) or digest(f)!=sha:raise ValueError('Stale compiled file: '+name)
 for name,sha in r['compiler'].items():
  if name not in ('effects.py','scene_craft.py','scene_phone.js') or digest(Path(__file__).with_name(name))!=sha:raise ValueError('Compiler changed; recompile into new folder')
 return r

def render(project,target):
 project=Path(project).resolve();r=verify(project);cli=local(runtime.settings().get('hyperframes') or 'missing-hyperframes',Path.cwd());out=Path(target).resolve();out.mkdir(parents=True,exist_ok=False)
 def native(args,log):run(['node',cli,*args],out/log)
 video=out/('effect-'+out.name+'-'+uuid.uuid4().hex[:8]+'.mp4')
 native(['check',project,'--json','--snapshots'],'check.log')
 native(['render',project,'--output',video,'--fps','30','--workers','1','--strict','--no-browser-gpu','--experimental-fast-capture=false','--low-memory-mode'],'render.log')
 info=probe(video);v=next(s for s in info['streams'] if s['codec_type']=='video')
 if (v['width'],v['height'],v['r_frame_rate'],int(v['nb_frames']))!=(1080,1920,'30/1',r['frames']):raise ValueError('Encoded frame count/geometry mismatch')
 run(['ffmpeg','-v','error','-xerror','-i',video,'-f','null','-'])
 for name,frame in [('start',0),('mid',r['frames']//2),('end',r['frames']-1)]:run(['ffmpeg','-v','error','-n','-i',video,'-vf',f'select=eq(n\\,{frame})','-frames:v','1',out/(name+'.jpg')])
 from render_audit import white_band
 white_band(video,out/'white-band-audit.json')
 save(out/'qa.json',{'video':video.name,'sha256':digest(video),'frames':r['frames'],'full_decode':'passed','visual_review':'pending','audio_review':'pending','scope':'unexpected white-band screening is not a source-preservation audit or human acceptance'})
 return video

def main():
 runtime.activate();p=argparse.ArgumentParser(description=__doc__);sp=p.add_subparsers(dest='command',required=True)
 sp.add_parser('catalog');sp.add_parser('doctor')
 a=sp.add_parser('configure');a.add_argument('--gsap',required=True);a.add_argument('--hyperframes',required=True);a.add_argument('--browser',required=True)
 a=sp.add_parser('build');a.add_argument('--params',required=True);a.add_argument('--output',required=True)
 a=sp.add_parser('render');a.add_argument('--project',required=True);a.add_argument('--output',required=True)
 a=sp.add_parser('verify');a.add_argument('--project',required=True)
 args=p.parse_args()
 if args.command=='catalog':print((ROOT/'catalog.json').read_text())
 elif args.command=='doctor':
  result=runtime.doctor();print(json.dumps(result,indent=2));return 0 if result['ready'] else 2
 elif args.command=='configure':print(runtime.configure(args.gsap,args.hyperframes,args.browser))
 elif args.command=='build':print(build(args.params,args.output))
 elif args.command=='render':print(render(args.project,args.output))
 else:print(json.dumps(verify(args.project),indent=2))
 return 0
if __name__=='__main__':
 try:sys.exit(main())
 except (ValueError,OSError,KeyError,TypeError) as e:raise SystemExit(str(e))

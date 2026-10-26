"""Optional local processing with explicitly provided runtimes; no downloads or uploads."""
from pathlib import Path
import argparse,json,hashlib,os,shutil,subprocess,sys,math,uuid
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def run(args,log=None):
 p=subprocess.run(list(map(str,args)),stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
 if log:Path(log).write_bytes(p.stdout)
 if p.returncode:raise ValueError('Processing failed: '+(str(log) if log else p.stdout.decode(errors='replace')[-1000:]))
 return p.stdout

def file(path):
 p=Path(path).expanduser().resolve()
 if not p.is_file():raise ValueError('Required local file missing: '+str(p))
 return p

def probe(p):return json.loads(run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',p]))
def fresh(path):p=Path(path).resolve();p.mkdir(parents=True,exist_ok=False);return p

def vision(source,target,mode,fps=30):
 source=file(source)
 if sys.platform!='darwin':raise ValueError('This native Vision backend requires macOS')
 if not 1<=fps<=30:raise ValueError('FPS must be 1..30')
 compiler=shutil.which('swiftc')
 if not compiler:raise ValueError('Existing Apple Swift compiler required; no automatic install')
 code=ROOT/'scripts/native/vision.swift';out=Path(target).resolve();metadata=probe(source);v=next(x for x in metadata['streams'] if x['codec_type']=='video')
 fingerprint=hashlib.sha256((sha(source)+sha(code)+sha(__file__)+mode+str(fps)+os.uname().release).encode()).hexdigest()
 if (out/'receipt.json').exists():
  receipt=json.loads((out/'receipt.json').read_text());artifact=out/receipt['file']
  if receipt.get('cache_key')==fingerprint and artifact.is_file() and sha(artifact)==receipt['sha256']:return out
  raise ValueError('Cache differs; choose a new output directory')
 out=fresh(out);frames=out/'frames';frames.mkdir();result=out/'processed';result.mkdir()
 run([compiler,'-O',code,'-o',out/'vision'],out/'compile.log')
 run(['ffmpeg','-v','error','-n','-i',source,'-vf',f'fps={fps}','-start_number','0',frames/'%06d.png'])
 run([out/'vision',mode,frames,result],out/'vision.log')
 if mode=='segment':
  output=out/'cutout.webm';run(['ffmpeg','-v','error','-n','-framerate',str(fps),'-i',result/'%06d.png','-c:v','libvpx-vp9','-pix_fmt','yuva420p','-auto-alt-ref','0','-crf','22','-b:v','0',output])
 else:
  raw=json.loads((result/'landmarks.json').read_text());track=[];previous=None
  for row in raw:
   candidates=[]
   for hand in row['hands']:
    points=hand['points'];wrist=next((p for k,p in points.items() if 'wrist' in k.lower()),None)
    if wrist and wrist['confidence']>=.35 and 0<=wrist['x']<=1 and 0<=wrist['y']<=1:candidates.append((wrist,points))
   chosen=min(candidates,key=lambda x:(x[0]['x']-(previous or {'x':.5})['x'])**2+(x[0]['y']-(previous or {'y':.5})['y'])**2) if candidates else None
   valid=chosen is not None and (previous is None or math.hypot(chosen[0]['x']-previous['x'],chosen[0]['y']-previous['y'])<.3)
   point=chosen[0] if valid else None;track.append({'time':row['frame']/fps,'visible':valid,'anchor':point,'landmarks':chosen[1] if valid else {}});previous=point
  output=out/'tracking.json';save(output,{'fps':fps,'width':v['width'],'height':v['height'],'source_sha256':sha(source),'track':track,'semantics':'hand wrist position; no intent inference','lost_policy':'hide, no gap interpolation'})
 save(out/'receipt.json',{'file':output.name,'sha256':sha(output),'source_sha256':sha(source),'cache_key':fingerprint,'frames':len(list(frames.glob('*.png'))),'mode':mode,'fps':fps,'network':False,'human_visual_acceptance':'pending'})
 return out

def main():
 p=argparse.ArgumentParser(description='Optional source-bound mattes and hand landmarks; macOS only')
 p.add_argument('command',choices=['segment','track']);p.add_argument('--input',required=True);p.add_argument('--output',required=True);p.add_argument('--fps',type=int,default=30)
 a=p.parse_args();print(vision(a.input,a.output,a.command,a.fps))
if __name__=='__main__':
 try:main()
 except (ValueError,OSError,KeyError) as e:raise SystemExit(str(e))

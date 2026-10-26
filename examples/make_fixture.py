#!/usr/bin/env python3
"""Generate clearly synthetic geometry and 25 effect configs; no real person/media."""
from pathlib import Path
import argparse,json,struct,zlib,subprocess,hashlib
ROOT=Path(__file__).resolve().parents[1]
def png(path,background,foreground=False,card=False):
 w,h=540,960;rows=[]
 for y in range(h):
  row=bytearray()
  for x in range(w):
   c=background
   if card:c=(60+int(x/w*90),100+int(y/h*70),200,255)
   elif (x-270)**2+(y-470)**2<70**2 or (180<x<360 and 550<y<800):c=(73,128,217,255)
   elif not foreground and (x%90<2 or y%90<2):c=(51,62,73,255)
   row.extend(c)
  rows.append(b'\0'+bytes(row))
 def chunk(t,b):return struct.pack('>I',len(b))+t+b+struct.pack('>I',zlib.crc32(t+b)&0xffffffff)
 path.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',w,h,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(b''.join(rows)))+chunk(b'IEND',b''))
def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();o=a.output.resolve();o.mkdir(parents=True,exist_ok=False)
 png(o/'source.png',(19,28,39,255));png(o/'matte.png',(0,0,0,0),foreground=True);png(o/'other.png',(40,78,70,255));png(o/'card.png',(0,0,0,255),card=True)
 for n in ['source','other']:
  subprocess.run(['ffmpeg','-v','error','-n','-loop','1','-i',str(o/(n+'.png')),'-f','lavfi','-i','anullsrc=r=48000:cl=stereo','-t','4','-vf','scale=1080:1920,fps=30','-c:v','libx264','-pix_fmt','yuv420p','-preset','fast','-c:a','aac',str(o/(n+'.mp4'))],check=True)
 catalog=json.loads((ROOT/'video-effects/catalog.json').read_text())
 for r in catalog:
  n=r['id'];c={'effect':n,'inputFile':'source.mp4','startTime':0,'duration':3.6,'mainText':r['name'],'subText':'Synthetic fixture','showHeader':True,'header':'SYNTHETIC TEST','headerSub':'Geometry, not a person','sourceAudio':False}
  if n in (1,3,9,11,12,16,17,22,26):c['cutoutFile']='matte.png'
  if n in (7,10,12,16,25):c['mediaFile']='other.png' if n!=10 else 'other.mp4'
  if n in (1,22):c['cardFiles']=['card.png','other.png','source.png']
  if n in (2,5,6):c['items']=['Inspect','Align','Preview']
  if n==8:c.update(dataPoints=[1,2,3,5],dataSource='Synthetic fixture values, not measured business results')
  if n in (13,24):c['freezeFrame']=27
  if n==15:c.update(nextFile='other.mp4',nextDuration=.8)
  if n==4:c.update(refinement='gesture-v3',zoomKeys=[{'frame':f,'scale':s} for f,s in [(0,1),(18,1.72),(32,.94),(45,1)]],motionFrames=[18,32])
  if n in (9,10,17):
   c['refinement']='gesture-v3'
   c['cueFrames']={9:{'reveal':30},10:{'insert':12,'exit':96},17:{'break':36}}[n]
   if n==17:c['breakStill']='source.png'
  if n==21:c.update(refinement='gesture-v3',timerTrack=[{'x':780,'y':1120}]*108,cueFrames={'timer':18})
  (o/f'{n:02d}-{r["slug"]}.json').write_text(json.dumps(c,indent=2)+'\n')
 (o/'SOURCE-NOTICE.txt').write_text('Original procedural geometry fixture. No real presenter, gesture or production-quality matte. Timer coordinates are synthetic test values.\n')
 print(o)
if __name__=='__main__':main()

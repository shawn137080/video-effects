"""Portable encoded white-band screening. Not the host's source-bound core audit."""
import subprocess,json
from pathlib import Path
from prepare_media import sha,save

def white_band(video,receipt):
 # Preserve every frame, reduce only the bottom 10% spatially. Unexpected near-white
 # bottom row against a darker row above reveals the observed viewport-loss failure.
 cmd=['ffmpeg','-v','error','-i',str(video),'-an','-vf','crop=iw:ih/10:0:ih-ih/10,scale=64:16:flags=area','-pix_fmt','rgb24','-f','rawvideo','-']
 p=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE);size=64*16*3;count=0;bad=[]
 while True:
  chunk=bytearray()
  while len(chunk)<size:
   b=p.stdout.read(size-len(chunk))
   if not b:break
   chunk.extend(b)
  if not chunk:break
  if len(chunk)!=size:p.kill();raise ValueError('Truncated audit frame')
  upper=chunk[:64*3];bottom=chunk[-64*3:]
  uniform=sum(min(bottom[i:i+3])>=249 for i in range(0,len(bottom),3))>=62
  delta=sum(abs(a-b) for a,b in zip(upper,bottom))/len(upper)
  if uniform and delta>18:bad.append(count)
  count+=1
 err=p.stderr.read();code=p.wait();p.stdout.close();p.stderr.close()
 if code:raise ValueError('Audit decode failed: '+err.decode(errors='replace')[-500:])
 report={'scope':'unexpected white lower-band screen; not source-preservation or semantic QA','video_sha256':sha(video),'auditor_sha256':sha(__file__),'frames':count,'bad_frames':bad,'passed':count>0 and not bad}
 save(receipt,report)
 if not report['passed']:raise ValueError('Encoded white-band screen failed; inspect '+str(receipt))
 return report

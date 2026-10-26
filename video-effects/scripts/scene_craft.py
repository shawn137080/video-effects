"""Original 25-family live compositions with shared scene motion and type hierarchy.

No prior effect renders are consumed. Source video, matched mattes and explicit
media are composited anew. Camera values are authored, not extracted from a third-party project.
"""
from pathlib import Path
import html,json,math,shutil,subprocess

FAMILIES={1:'Orbit',2:'Chat Takeover',3:'Frame Escape',4:'Snap Zoom',5:'Checklist',6:'Headline Storm',7:'Zoom Portal',8:'Growth Metric',9:'Studio Reveal',10:'B-roll Overlay',11:'Paper Cutout',12:'Dolly Zoom',13:'Magazine Cover',14:'Liquid Glass',15:'Zoom Through Cut',16:'Green Screen',17:'Frame Break',19:'3D Phone Mockup',21:'Timer',22:'Media Wall',23:'Spotlight',24:'Freeze Callout',25:'Before / After',26:'Text Behind',28:'Doodle'}
MATTE={1,3,9,11,12,16,17,22,26}
SECONDARY={7,10,12,15,16,25}
CUE_KEYS={1:{'orbit'},2:{'takeover'},3:{'escape'},4:{'snap1','snap2'},9:{'reveal'},10:{'insert','exit'},15:{'approach','pass'},6:{'head0','head1','head2','head3','resolve'},7:{'open','expand'},13:{'cover'},17:{'break'},21:{'timer'},22:{'wall'},25:{'compare'},28:{'draw'}}
SUBS={1:'Depth, in motion.',2:'Let the conversation take over.',3:'Step beyond the frame.',4:'One frame. Instant impact.',5:'One clear step at a time.',6:'Make the headline land.',7:'Open another perspective.',8:'Make the numbers visible.',9:'Shape the light.',10:'Show what you mean.',11:'Cut it. Layer it. Stick it.',12:'Keep the subject. Move the world.',13:'Make the cover.',14:'Light. Refraction. Depth.',15:'Push through to the next scene.',16:'Put the story behind you.',17:'Break the boundary.',19:'Give your screen dimension.',21:'Make time visible.',22:'Build a world of ideas.',23:'Guide the eye.',24:'Hold the moment.',25:'Show the difference.',26:'Type with real depth.',28:'Draw attention.'}

def validate(p):
    if p.get('treatment') not in (None,'scene-craft'):raise ValueError('Unknown edit treatment')
    if p.get('treatment')!='scene-craft':return
    if p.get('locale','en') not in ('en','zh-Hans'):raise ValueError('Unsupported scene locale')
    if p.get('typography','classic') not in ('classic','editorial-condensed'):raise ValueError('Unknown scene typography preset')
    for key in ('header','headerSub'):
        if not isinstance(p.get(key),str) or not 1<=len(p[key])<=32:raise ValueError('Scene hierarchy needs short '+key)
    for b in p['beats']:
        n=b.get('effect',0);d=b.get('design',{})
        if 'refinement' in d:
            if d['refinement']!='gesture-v3' or n not in (4,9,10,15,17,21):raise ValueError('Unsupported gesture refinement')
            if n==4:
                zoom=d.get('zoomKeys',[])
                if not 2<=len(zoom)<=12 or any(type(k.get('frame')) is not int or not 0<=k['frame']<b['frames'] or type(k.get('scale')) not in (int,float) or not math.isfinite(k['scale']) or not .8<=k['scale']<=2 for k in zoom):raise ValueError('Invalid source zoomKeys')
                if [k['frame'] for k in zoom]!=sorted(set(k['frame'] for k in zoom)):raise ValueError('Ordered zoomKeys required')
            if n==21:
                track=d.get('timerTrack',[])
                if len(track)!=b['frames'] or any(type(k.get(axis)) not in (int,float) or not math.isfinite(k[axis]) or not bounds[0]<=k[axis]<=bounds[1] for k in track for axis,bounds in [('x',(200,880)),('y',(500,1260))]):raise ValueError('Measured timerTrack required')
        cues=d.get('cueFrames',{})
        if not isinstance(cues,dict) or any(k not in CUE_KEYS.get(n,set()) or type(v) is not int or not 0<=v<b['frames'] for k,v in cues.items()):raise ValueError('Invalid gesture cueFrames: '+b['id'])
        motion=d.get('motionFrames',[])
        if not isinstance(motion,list) or any(type(v) is not int or not 0<=v<b['frames'] for v in motion) or motion!=sorted(set(motion)):raise ValueError('Invalid motionFrames: '+b['id'])
        if n and n not in FAMILIES:raise ValueError('Unsupported live effect')
        if n==15 and (b is p['beats'][-1] or b.get('transition')!='through'):raise ValueError('Through needs an authored next-scene handoff')
        for key in ('mainText','subText'):
            if key in d and (not isinstance(d[key],str) or len(d[key])>(28 if key=='mainText' else 52)):raise ValueError('Short readable '+key+' required')
        keys=[]
        if n in MATTE:keys.append('matte')
        if n in SECONDARY:keys.append('secondary')
        if n in (13,24):keys.append('freeze')
        if d.get('refinement')=='gesture-v3' and n==17:keys.append('breakStill')
        if d.get('refinement')=='gesture-v3' and n==15:keys.append('destinationMatte')
        for key in keys:
            if d.get(key) not in p['assets']:raise ValueError('Live effect needs explicit '+key+': '+b['id'])
        if n in (1,22):
            if not 3<=len(d.get('cards',[]))<=6 or any(k not in p['assets'] for k in d['cards']):raise ValueError('Orbit/wall needs 3..6 source-bound cards')
        if n==8:
            values=d.get('dataPoints',[])
            if not 2<=len(values)<=8 or any(type(x) not in (int,float) or not math.isfinite(x) for x in values) or not d.get('dataSource'):raise ValueError('Chart requires finite data and source')
        if n==24 and not 0<=d.get('freezeFrame',-1)<b['frames']:raise ValueError('Freeze anchor required')
        if n in (2,5,6) and (not 1<=len(d.get('items',[]))<=(3 if n==6 else 4) or any(not isinstance(x,str) or len(x)>26 for x in d['items'])):raise ValueError('Use short authored items')
        for key in keys:
            info=p['assets'][d[key]].get('probe')
            if info and key=='matte' and float(info['format']['duration'])+.001 < b['frames']/p['fps']:raise ValueError('Matte too short')

CSS="""
@font-face{font-family:Kit;src:url(assets/Manrope.ttf)}
@font-face{font-family:Display;src:url(assets/Anton.ttf)}
@font-face{font-family:Editorial;src:url(assets/InstrumentSerif.ttf)}
*{box-sizing:border-box}html,body{margin:0;width:1080px;height:1920px;overflow:hidden;background:#101416}
#edit{width:100%;height:100%;position:relative;overflow:hidden;color:#fff;font-family:Kit,sans-serif}
.sc-world,.sc-scene,.sc-impulse,.sc-content,.sc-full{position:absolute;inset:0;transform-origin:50% 48%}
.sc-scene{visibility:hidden;overflow:hidden;background:#101416}.sc-content{overflow:hidden}.sc-full>video,.sc-full>img{position:absolute;width:100%;height:100%;object-fit:cover}
.sc-footage{position:absolute;inset:0;transform:translateY(60px) scale(.75);transform-origin:50% 50%}
.sc-footage{mask-image:linear-gradient(90deg,transparent,#000 5%,#000 95%,transparent),linear-gradient(0deg,transparent,#000 6%,#000 94%,transparent);mask-composite:intersect}.sc-footage video,.sc-footage img{width:100%;height:100%;object-fit:cover}
.sc-vignette{position:absolute;inset:0;pointer-events:none;background:linear-gradient(#0b1014 0%,#0b1014ed 9%,#0b101400 35%,#0b101400 58%,#0b101477 75%,#0b1014a0 100%)}
.sc-header{position:absolute;left:90px;top:260px;width:900px;text-align:center;z-index:70;text-shadow:0 3px 3px #0008,0 8px 25px #0008}
.sc-header strong{display:block;font-size:90px;font-weight:850;text-transform:uppercase;letter-spacing:-3px;line-height:1.05;color:var(--accent)}
.sc-header span{display:block;font-size:33px;font-weight:750;margin-top:9px;letter-spacing:-.5px}
.sc-lower{position:absolute;left:85px;top:1320px;width:910px;text-align:center;z-index:75;text-shadow:0 3px 2px #0009,0 8px 25px #0009}
.sc-count{position:absolute;left:0;top:-32px;font-size:24px;font-weight:800;letter-spacing:2px;line-height:1.4}
.sc-name{font-size:87px;font-weight:850;letter-spacing:-4px;line-height:1.05;color:var(--accent)}
.sc-explain{font-size:31px;font-weight:650;line-height:1.2;margin-top:13px}
.sc-card{position:absolute;border:1px solid #ffffff56;border-radius:24px;box-shadow:0 18px 40px #0007,0 3px 1px #ffffff1a;background:linear-gradient(130deg,#293338f5,#101719f5);color:#f5f4ee;overflow:hidden}
.sc-small{font-size:25px;letter-spacing:2px;font-weight:750;color:#cbd0c6}
.sc-big{font-size:55px;font-weight:850;letter-spacing:-2px;line-height:1.05}
.sc-paper{background:#f0eddf;color:#20252a;border:1px solid #fff;box-shadow:0 13px 23px #0006}
.sc-frost{background:linear-gradient(115deg,#ffffff50,#d9f5ff18 45%,#8aa9bc45);backdrop-filter:blur(26px) saturate(1.35);border:2px solid #ffffffb0;box-shadow:inset 0 3px 2px #fff8,inset 0 -3px 4px #5a738e77,0 30px 65px #0006;overflow:hidden}
.sc-frost:after{content:'';position:absolute;inset:7px;border-radius:inherit;border:1px solid #fff4;pointer-events:none}
.sc-caption{position:absolute;top:1390px;left:100px;width:880px;text-align:center;font-size:48px;line-height:1.16;font-weight:800;z-index:80;text-shadow:0 3px 6px #000,0 10px 25px #000}
.sc-chip{display:inline-block;padding:9px 18px;border-radius:100px;background:var(--accent);color:#121719;font-size:24px;font-weight:850;letter-spacing:1px;text-shadow:none}
"""

EDITORIAL_TYPE="""
@font-face{font-family:SceneHeadline;src:url(assets/BarlowCondensed-ExtraBold.ttf);font-weight:800;font-style:normal}
@font-face{font-family:SceneSupport;src:url(assets/Inter.ttf);font-weight:100 900;font-style:normal}
.sc-header,.sc-lower{text-shadow:0 3px 12px #0008}
.sc-header strong{font-family:SceneHeadline,sans-serif;font-size:112px;font-weight:800;letter-spacing:.3px;line-height:.96}
.sc-header span{font-family:SceneSupport,sans-serif;font-weight:550;letter-spacing:.3px;font-size:34px;margin-top:14px}
.sc-name{font-family:SceneHeadline,sans-serif;font-weight:800;text-transform:uppercase;letter-spacing:.5px;font-size:110px!important;line-height:.98}
.sc-count{font-family:SceneSupport,sans-serif;font-weight:650;font-size:23px;letter-spacing:1.4px}
.sc-caption{font-family:SceneSupport,sans-serif;font-weight:650;letter-spacing:-.8px}
"""

# CJK glyphs are embedded rather than relying on the render host's system fonts.
# Keep the Latin faces used by the accepted editorial preset.
CHINESE_TYPE='\n'.join('@font-face{font-family:'+family+';src:url(assets/NotoSansSC.ttf);font-weight:100 900;unicode-range:U+2E80-9FFF,U+F900-FAFF,U+FF00-FFEF;}' for family in ('Kit','Display','Editorial','SceneHeadline','SceneSupport'))+"""
.sc-header strong{font-size:88px;line-height:1.22;letter-spacing:1px;font-weight:900}
.sc-header span{font-size:32px;line-height:1.35;font-weight:600;letter-spacing:1px;margin-top:8px}
.sc-name{font-size:96px!important;line-height:1.2;letter-spacing:2px;font-weight:900}
.sc-caption{font-size:49px;line-height:1.35;font-weight:750;letter-spacing:0}
[id$="-behind"],[id$="-break-label"],[id$="-paper-word"]{font-weight:900!important}
.sc-frost,.sc-frost .sc-small,.sc-frost>div{color:#132a34!important;text-shadow:0 1px 0 #ffffff60}
[id$="-cover"]>div:nth-child(2){background:#14262bef;color:#f6f0db;padding:14px 18px;font-weight:750}
[id$="-coverlines"]{font-family:Kit,sans-serif!important;font-weight:850!important;font-size:52px!important;line-height:1.2!important;letter-spacing:1px;background:#11292be8!important;padding:14px 20px;border-left:4px solid var(--accent)!important}
"""

ZH_COPY={
    'TIMER':'计时',
    'CREATOR KIT / MESSAGES':'CREATOR KIT / 对话',
    'BEYOND<br>THE FRAME':'跳出<br>画框',
    'CUT / PASTE':'剪下 / 贴上',
    'PERSPECTIVE SHIFT':'透视拉伸',
    'THE MOTION ISSUE / 025':'创意影像 / 第 025 期',
    'MAKE<br>YOUR<br>MOVE.':'让<br>创意<br>动起来',
    'OPTICAL MATERIAL / 01':'光学材质 / 01',
    'Liquid clarity.':'流动的光。',
    'A softer surface. Real depth.':'柔和表面，立体层次。',
    'BACKGROUND / YOUR STORY':'换个背景，讲个故事',
    'YOUR SCREEN.<br>IN DIMENSION.':'你的画面<br>有了立体感',
    'FOCUS / COUNTDOWN':'专注 / 倒计时',
    'FREEZE':'定格', 'Right here.':'就是这一刻。',
    'ORIGINAL':'原片', 'GRADED':'调色后',
    'COMMENT “EFFECT”':'留言 “EFFECT”',
}

def scene(p,b,index):
    """Independent live DOM and deterministic local choreography, global time passed in."""
    e=html.escape;fps=p['fps'];start=b['start_frame']/fps;dur=b['frames']/fps
    n=b.get('effect',0);d=b.get('design',{});prefix='fx-'+b['id'];j=[];vcount=0;initialized=set()
    def cue(name,default):return d.get('cueFrames',{}).get(name,default*fps)/fps
    def id(k):return prefix+'-'+k
    def asset(k):return e(p['assets'][k]['compiled_file'],quote=True)
    def vid(k,aid=None,cls='sc-full',in_frame=0):
        nonlocal vcount
        vcount+=1
        selected=aid or b["picture"]["asset"]
        if Path(p['assets'][selected]['file']).suffix.lower() in ('.png','.jpg','.jpeg','.webp'):
            return f'<div id="{id(k)}" class="{cls}"><img src="{asset(selected)}"></div>'
        return f'<div id="{id(k)}" class="{cls}"><video id="{id(k)}-video" src="{asset(aid or b["picture"]["asset"])}" muted playsinline data-start="{start}" data-duration="{dur}" data-media-start="{in_frame/fps}" data-track-index="{index*12+vcount}"></video></div>'
    def box(k,inner,style='',cls='sc-card'):return f'<div id="{id(k)}" class="{cls}" style="{style}">{inner}</div>'
    def tween(k,a,z,t=0,length=.24,ease='power3.out'):
        # A late gesture must settle inside its shot, never animate across a cut.
        length=min(length,max(1/fps,dur-t))
        if k not in initialized:
            j.append(f"gsap.set('#{id(k)}',{json.dumps(a)});")
            initialized.add(k)
        z=dict(z,duration=length,ease=ease,immediateRender=False)
        j.append(f"tl.fromTo('#{id(k)}',{json.dumps(a)},{json.dumps(z)},{start+t});")
    def setat(k,props,t=0):j.append(f"tl.set('#{id(k)}',{json.dumps(props)},{start+t});")
    def im(k,aid,style='',cls='sc-full'):return box(k,f'<img src="{asset(aid)}">',style,cls)
    def entrance(k,t=0,side=1):tween(k,dict(opacity=0,x=side*180,y=28,rotation=side*7,scale=.82),dict(opacity=1,x=0,y=0,rotation=side*1.5,scale=1),t,.28,'back.out(1.25)')
    def source(k='source'):return vid(k,cls='sc-footage',in_frame=b['picture'].get('in_frame',0))
    def matte(k='person'):return vid(k,d['matte'],'sc-footage')
    body=box('room',vid('room-source',in_frame=b['picture'].get('in_frame',0)),cls='sc-full',style='filter:blur(24px) brightness(.42);transform:scale(1.08)')+box('base',source(),cls='sc-full')
    # This opt-in treatment follows measured source gestures without changing older plans.
    if d.get('refinement')=='gesture-v3' and n==4:
        # Reaching/opening the hand pushes in; withdrawing/pinching pulls back.
        setat('base',{'transformOrigin':'54% 57%'})
        keys=d['zoomKeys']
        for left,right in zip(keys,keys[1:]):
            tween('base',{'scale':left['scale']},{'scale':right['scale']},left['frame']/fps,(right['frame']-left['frame'])/fps,'power2.inOut')
        body+=box('zoom-mark','', 'left:770px;top:590px;width:70px;height:70px;border-top:3px solid #fff9;border-right:3px solid #fff9;background:none;box-shadow:none;border-radius:0')
        tween('zoom-mark',{'opacity':0},{'opacity':.8},keys[1]['frame']/fps,.07)
        tween('zoom-mark',{'opacity':.8},{'opacity':0},keys[-2]['frame']/fps,.13)
    elif d.get('refinement')=='gesture-v3' and n==9:
        at=cue('reveal',.8)
        stage='<svg viewBox="0 0 1080 1920" width="1080" height="1920"><defs><radialGradient id="stage'+str(index)+'"><stop stop-color="#b4c5c6"/><stop offset=".55" stop-color="#556975"/><stop offset="1" stop-color="#121e2b"/></radialGradient><linearGradient id="floor'+str(index)+'" x2="0" y2="1"><stop stop-color="#586c77"/><stop offset="1" stop-color="#12202a"/></linearGradient></defs><rect width="1080" height="1920" fill="url(#stage'+str(index)+')"/><path d="M0 1300Q540 1170 1080 1300V1920H0Z" fill="url(#floor'+str(index)+')"/><ellipse cx="540" cy="1610" rx="380" ry="85" fill="#050e17" opacity=".45"/><path d="M0 1300Q540 1170 1080 1300" stroke="#bccbd6" stroke-opacity=".2" fill="none"/></svg>'
        lamps=''
        for side,x in [('left',105),('right',810)]:
            lamps+=box('lamp-'+side,'<div style="position:absolute;left:69px;top:180px;width:8px;height:850px;background:linear-gradient(90deg,#101821,#aebcca,#111823)"></div><div style="position:absolute;top:0;left:0;width:160px;height:230px;background:radial-gradient(ellipse,#fff,#e3edf4 65%,#4c6374);border:14px solid #18242d;box-shadow:0 0 65px #beddfc55,inset 0 0 22px #fff;clip-path:polygon(18% 0,82% 0,100% 20%,100% 80%,82% 100%,18% 100%,0 80%,0 20%)"></div>',f'left:{x}px;top:510px;width:160px;height:1050px;transform:rotate({-12 if side=="left" else 12}deg);background:none;border:0;box-shadow:none;overflow:visible','sc-full')
        body+=box('studio-rig',stage+lamps,cls='sc-full')
        body+=box('studio-person',matte(),cls='sc-full',style='filter:drop-shadow(-5px 0 4px #c5e9ff77) drop-shadow(7px 0 6px #e9dbbe66)')
        for k in ('studio-rig','studio-person'):tween(k,{'opacity':0},{'opacity':1},at,.17)
        body+=box('sweep','',cls='sc-full',style='background:linear-gradient(115deg,transparent 20%,#def4ff88 45%,#ffffffcc 50%,transparent 65%);mix-blend-mode:screen')
        tween('sweep',{'x':-1400,'opacity':0},{'x':0,'opacity':.6},at-.07,.1)
        tween('sweep',{'x':0,'opacity':.6},{'x':1400,'opacity':0},at+.03,.2)
    elif d.get('refinement')=='gesture-v3' and n==10:
        setat('base',{'x':155,'scale':.88})
        inner='<div style="height:48px;background:linear-gradient(#34444c,#15242e);padding:17px 19px;display:flex;gap:8px"><i style="width:10px;height:10px;border-radius:100%;background:#f1776f"></i><i style="width:10px;height:10px;border-radius:100%;background:#edd385"></i><i style="width:10px;height:10px;border-radius:100%;background:#87c9a7"></i></div><div style="position:relative;height:532px">'+vid('broll',d['secondary'])+'</div>'
        body+=box('insert',inner,'left:72px;top:510px;width:470px;height:580px;border:2px solid #d9e6ecb0;border-radius:22px;box-shadow:12px 30px 55px #0009,inset 0 2px 0 #fff8;background:#101e29;transform-origin:50% 80%')
        tween('insert',{'opacity':0,'x':-170,'y':110,'rotationY':-22,'rotationZ':-7,'scale':.68,'transformPerspective':1200},{'opacity':1,'x':0,'y':0,'rotationY':8,'rotationZ':-3,'scale':1},cue('insert',.2),.25,'back.out(1.4)')
        tween('insert',{'opacity':1,'scale':1},{'opacity':0,'scale':.85,'x':-80,'y':60},cue('exit',dur-.17),.17,'power2.in')
    elif d.get('refinement')=='gesture-v3' and n==15:
        inside=vid('gate-bg',d['secondary'])+vid('gate-person',d['destinationMatte'],'sc-footage')
        # The next shot is visible inside the depth frame before it fills the screen.
        body+=f'<style>#{id("gate-person")}{{transform:translateY(15px) scale(.75)}}#{id("gate-person")} video{{object-fit:contain}}</style>'
        body+=box('gate',inside,'left:405px;top:470px;width:270px;height:480px;border:7px solid #eff4f7;border-radius:14px;box-shadow:0 0 0 14px #6d859b55,0 0 0 31px #6d859b22,0 22px 70px #0008;transform-origin:50% 50%;background:#11202d','sc-card')
        tween('gate',{'opacity':0,'scale':.05,'rotationY':-35,'transformPerspective':1000},{'opacity':1,'scale':1,'rotationY':0},cue('approach',.7),.2,'power3.out')
        tween('gate',{'scale':1,'y':0,'borderRadius':14},{'scale':4.1,'y':250,'borderRadius':0},cue('pass',1.03),(b['frames']-1)/fps-cue('pass',1.03),'power3.in')
    elif d.get('refinement')=='gesture-v3' and n==17:
        at=cue('break',.9)
        frame_style='left:110px;top:430px;width:860px;height:1130px;border:24px solid #e4ebef;border-radius:30px;box-shadow:inset 0 0 0 3px #738895,0 0 0 3px #8ba0ae,0 20px 70px #0009;background:none'
        body=box('backdrop','',cls='sc-full',style='background:radial-gradient(ellipse,#344958,#0e1922 75%)')+box('framed',source(),cls='sc-full',style='clip-path:inset(430px 110px 360px round 30px)')
        body+=box('solid-frame','',frame_style,'sc-full')
        cracks='<svg width="1080" height="1920"><path d="M660 1030L540 840L590 705L410 440M660 1030L760 830L940 650M660 1030L820 1100L970 1390M660 1030L470 1100L350 1380L140 1540M660 1030L400 980L270 710L120 600M660 1030L690 1280L600 1540" stroke="#e4f2ff" stroke-width="4" fill="none"/><path d="M660 1030L540 840L590 705L410 440M660 1030L820 1100L970 1390" stroke="#294558" stroke-width="2" fill="none"/></svg>'
        body+=box('cracks',cracks,cls='sc-full')
        tween('cracks',{'opacity':0},{'opacity':1},max(0,at-2/fps),1/fps)
        tween('cracks',{'opacity':1},{'opacity':0},at+.12,.12)
        polys=['0% 0%,50% 0%,61% 54%,0% 30%','50% 0%,100% 0%,100% 35%,61% 54%','0% 30%,61% 54%,0% 62%','61% 54%,100% 35%,100% 66%','0% 62%,61% 54%,32% 100%,0% 100%','61% 54%,100% 66%,100% 100%,32% 100%']
        for i,poly in enumerate(polys):
            content=box('texture'+str(i),im('freeze-shard'+str(i),d['breakStill'],cls='sc-footage'),cls='sc-full',style='clip-path:inset(430px 110px 360px round 30px)')+box('rim'+str(i),'',frame_style,'sc-full')
            body+=box('shard'+str(i),content,cls='sc-full',style=f'clip-path:polygon({poly});filter:drop-shadow(9px 12px 5px #0007);transform-origin:61% 54%')
            setat('shard'+str(i),{'opacity':0});setat('shard'+str(i),{'opacity':1},at)
            sign=-1 if i%2==0 else 1
            tween('shard'+str(i),{'x':0,'y':0,'rotation':0,'scale':1},{'x':sign*(430+i*70),'y':(i//2-1)*600,'rotation':sign*(22+i*9),'scale':.7},at,.48,'power2.out')
            tween('shard'+str(i),{'opacity':1},{'opacity':0},at+.18,.3)
        setat('solid-frame',{'opacity':0},at)
        tween('framed',{'clipPath':'inset(430px 110px 360px round 30px)'},{'clipPath':'inset(0px 0px 0px round 0px)'},at,.22,'power3.out')
    elif d.get('refinement')=='gesture-v3' and n==21:
        # The footprint is below the measured index tip, in the same camera space.
        body+=f'<style>#{id("source")}{{transform:translateY(-80px) scale(.75)}}</style>'
        inner='<div style="font:650 20px Kit;letter-spacing:3px;color:#b7cdd7">TIMER</div><div id="'+id('time')+'" style="font-size:56px;line-height:1.1;font-weight:850;font-variant-numeric:tabular-nums;letter-spacing:-2px;margin-top:5px">00.00</div><div style="position:absolute;right:17px;top:15px;width:8px;height:8px;border-radius:50%;background:#dff5a7;box-shadow:0 0 14px #dff5a799"></div>'
        panel=box('timer',inner,'left:-125px;top:0;width:250px;height:130px;padding:15px 22px;border-radius:23px;background:linear-gradient(130deg,#314d60ee,#0e202ceb);backdrop-filter:blur(18px);border:2px solid #c9e3ee99;box-shadow:0 15px 30px #0008,inset 0 2px 0 #fff5;transform-origin:50% 0%')
        body+=box('timer-anchor',panel,'left:0;top:0;width:1px;height:1px;overflow:visible;background:none;border:0;box-shadow:none','sc-full')
        at=cue('timer',.6)
        tween('timer',{'opacity':0,'scale':.65,'y':-15},{'opacity':1,'scale':1,'y':0},at,.17,'back.out(1.6)')
        tracks=d['timerTrack'];j.append(f"const hand{index}={json.dumps(tracks)};const timerClock{index}={{f:0}};function handTimer{index}(){{const f=timerClock{index}.f,i=Math.min(hand{index}.length-1,Math.floor(f)),q=hand{index}[i],r=hand{index}[Math.min(i+1,hand{index}.length-1)],u=f-i;gsap.set('#{id('timer-anchor')}',{{x:q.x+(r.x-q.x)*u,y:q.y+(r.y-q.y)*u}});document.getElementById('{id('time')}').textContent=Math.max(0,f/{fps}-{at}).toFixed(2).padStart(5,'0');}}tl.to(timerClock{index},{{f:{b['frames']-1},duration:{(b['frames']-1)/fps},ease:'none',onUpdate:handTimer{index}}},{start});handTimer{index}();")
    elif n==1:
        body+=matte()
        for i,c in enumerate(d['cards']):body+=box('orbit'+str(i),f'<img src="{asset(c)}" style="width:100%;height:100%;object-fit:cover"><div style="position:absolute;inset:0;border:4px solid #fff9;border-radius:20px"></div>',f'left:0;top:0;width:155px;height:195px;border-radius:20px', 'sc-card')
        orbit_at=cue('orbit',0)
        for i in range(len(d['cards'])):j.append(f"gsap.set('#{id('orbit'+str(i))}',{{scale:0,opacity:0}});")
        j.append(f"const orbit{index}={{t:0}};tl.to(orbit{index},{{t:1,duration:{dur-orbit_at},ease:'none',onUpdate:()=>{{for(let i=0;i<{len(d['cards'])};i++){{const a=orbit{index}.t*Math.PI*1.55+i*Math.PI*2/{len(d['cards'])},z=Math.sin(a),x=440*Math.cos(a),y=140*z;gsap.set('#{id('orbit')}'+i,{{x:445+x*.97+y*.22,y:985+y*.97-x*.22,scale:(.68+(z+1)*.2)*Math.min(1,orbit{index}.t*12),rotationY:-Math.cos(a)*42,rotationZ:-Math.cos(a)*8,zIndex:z>0?20:0,opacity:.85+.15*(z+1)/2}});}}}}}},{start+orbit_at});")
        setat('person',{'zIndex':10})
        body+=f'<style>#{id("source")},#{id("person")}{{transform:translateY(-80px) scale(.68)}}</style>'
    elif n==2:
        body+=box('chat-world','',cls='sc-full',style='background:radial-gradient(ellipse at 20% 30%,#344547,#10181b 80%)')
        takeover=cue('takeover',.02)
        tween('chat-world',{'opacity':0,'scale':.8,'y':550},{'opacity':.98,'scale':1,'y':0},takeover,.3)
        body+=box('chat-label','<span class="sc-small">CREATOR KIT / MESSAGES</span>', 'left:100px;top:460px;border:0;box-shadow:none;background:none')
        for i,t in enumerate(d['items']):
            body+=box('bubble'+str(i),e(t),f'left:{115+i%2*160}px;top:{550+i*175}px;width:690px;padding:35px;font-size:44px;font-weight:750;background:{"var(--accent)" if i==len(d["items"])-1 else "#e5e9e3"};color:#182125;border-radius:28px 28px 6px 28px')
            entrance('bubble'+str(i),takeover+.05+i*.18,1 if i%2 else -1)
        body+=box('pip',vid('pip-source'),'left:785px;top:1080px;width:180px;height:180px;border-radius:100%;border:4px solid #fff;overflow:hidden','sc-card')
    elif n==3:
        body=box('back','',cls='sc-full',style='background:radial-gradient(ellipse at 50% 40%,#314043,#101617 80%)')
        body+=box('window',source(),cls='sc-full',style='clip-path:inset(860px 120px 370px round 36px)')
        body+=box('border','', 'left:120px;top:860px;width:840px;height:690px;border:7px solid #eee9cf;border-radius:36px;background:transparent','sc-full')
        body+=matte()
        tween('person',{'clipPath':'inset(860px 120px 370px round 36px)'},{'clipPath':'inset(0px 0px 0px round 0px)'},cue('escape',.12),.3,'back.out(1.1)')
        body+=box('break-label','BEYOND<br>THE FRAME','left:135px;top:420px;width:810px;padding:24px 0;font:95px/.95 Display;color:var(--accent);background:none;border:0;box-shadow:none')
    elif n==4:
        # Actual one-frame snap, followed by a readable hold.
        setat('base',{'scale':1.19,'transformOrigin':'53% 70%'},cue('snap1',.19))
        setat('base',{'scale':1.34},cue('snap2',.49))
        body+=box('focus','<span style="border:2px solid #fff8;padding:8px 20px">× 1.34</span>','left:790px;top:540px;font-size:28px;background:none;border:0;box-shadow:none')
        tween('focus',{'opacity':0},{'opacity':1},cue('snap2',.49),.08)
    elif n==5:
        content='<div class="sc-small" style="margin-bottom:16px">THE PROCESS</div>'
        for i,t in enumerate(d['items']):content+=f'<div id="{id("row"+str(i))}" style="font-size:35px;font-weight:800;display:flex;gap:20px;padding:8px 0;border-top:1px solid #fff2"><span style="width:36px;height:36px;border:2px solid #e9df7c;border-radius:9px"><span id="{id("tick"+str(i))}" style="color:var(--accent)">✓</span></span>{e(t)}</div>'
        body+=box('check',content,'left:110px;top:425px;width:860px;padding:24px 35px')
        entrance('check',0,-1)
        for i in range(len(d['items'])):
            tween('row'+str(i),{'opacity':0,'x':45},{'opacity':1,'x':0},i*.16,.2)
            tween('tick'+str(i),{'opacity':0,'scale':.2},{'opacity':1,'scale':1},.22+i*.22,.15,'back.out(2)')
    elif n==6:
        positions=[(90,430,400,-7),(570,438,410,7),(115,570,360,-4),(490,585,490,3)]
        words=d['items']+[d.get('payoff','MAKE IT MOVE')]
        for i,t in enumerate(words):
            x,y,w,rot=positions[i];body+=box('head'+str(i),f'<div style="height:18px;background:#202b2d"></div><div style="padding:16px;background:#f0eddf;color:#101010;font-family:{"Display" if i%2 else "Editorial"};font-size:{49 if i<3 else 58}px;line-height:1.02">{e(t)}</div>',f'left:{x}px;top:{y}px;width:{w}px;border-radius:4px','sc-card sc-paper')
            tween('head'+str(i),{'opacity':0,'x':(-1 if i%2==0 else 1)*600,'rotation':rot*2,'scale':.8},{'opacity':1,'x':0,'rotation':rot,'scale':1},cue('head'+str(i),i*.09),.15,'back.out(1.1)')
            if i<3:tween('head'+str(i),{'opacity':1},{'opacity':0},cue('resolve',dur*.77),.13)
    elif n==7:
        body+=box('portal',vid('portal-video',d['secondary']),cls='sc-full',style='clip-path:circle(0px at 540px 980px)')
        body+=box('ring','', 'left:300px;top:740px;width:480px;height:480px;border:9px solid #fff4;border-top-color:var(--accent);border-radius:50%;background:none;box-shadow:0 0 45px #fff4','sc-full')
        tween('ring',{'scale':.1,'opacity':0,'rotation':-90},{'scale':1,'opacity':1,'rotation':0},cue('open',0),.22)
        tween('portal',{'clipPath':'circle(0px at 540px 980px)'},{'clipPath':'circle(235px at 540px 980px)'},cue('open',0),.22)
        tween('portal',{'clipPath':'circle(235px at 540px 980px)'},{'clipPath':'circle(1800px at 540px 980px)'},cue('expand',dur*.45),.3,'power3.in')
        tween('ring',{'scale':1,'opacity':1},{'scale':5,'opacity':0},cue('expand',dur*.45),.3,'power3.in')
    elif n==8:
        vals=d['dataPoints'];lo=min(vals);hi=max(vals);pts=[(30+i*700/(len(vals)-1),170-(v-lo)/max(hi-lo,1)*110) for i,v in enumerate(vals)]
        path='M '+' L '.join(f'{x},{y}' for x,y in pts)
        content=f'<div class="sc-small">{e(d["dataSource"])}</div><svg width="780" height="190" viewBox="0 0 780 190"><path d="M30 175H750" stroke="#fff3" fill="none"/><path id="{id("curve")}" d="{path}" stroke="var(--accent)" stroke-width="8" fill="none" stroke-linecap="round" pathLength="1"/></svg><div id="{id("number")}" style="position:absolute;right:35px;top:57px;font-size:66px;font-weight:850">0</div>'
        body+=box('metric',content,'left:110px;top:425px;width:860px;height:260px;padding:24px 35px')
        entrance('metric',0,1);tween('curve',{'strokeDasharray':1,'strokeDashoffset':1},{'strokeDashoffset':0},.15,dur*.7,'none')
        j.append(f"const count{index}={{v:0}};tl.to(count{index},{{v:{vals[-1]},duration:{dur*.7},ease:'power2.out',onUpdate:()=>document.getElementById('{id('number')}').textContent=Math.round(count{index}.v)}},{start+.15});")
    elif n==9:
        body+=box('studio','',cls='sc-full',style='background:radial-gradient(ellipse at 70% 38%,#c3cbac,#495a50 40%,#111b1b 75%)')+box('rim',matte(),cls='sc-full',style='filter:drop-shadow(8px 0 5px #e9e7a588)')
        tween('studio',{'clipPath':'inset(0 100% 0 0)'},{'clipPath':'inset(0 0% 0 0)'},.07,.48)
        tween('rim',{'clipPath':'inset(0 100% 0 0)'},{'clipPath':'inset(0 0% 0 0)'},.07,.48)
        body+=box('light','', 'left:-400px;top:0;width:240px;height:1920px;background:linear-gradient(90deg,transparent,#fff9,transparent);filter:blur(35px)','sc-full')
        tween('light',{'x':0,'rotation':-12},{'x':1800,'rotation':-12},.06,.5,'power2.inOut')
    elif n==10:
        body+=box('insert',vid('broll',d['secondary']), 'left:145px;top:427px;width:790px;height:260px;border:5px solid #eee9d8;border-radius:24px')
        entrance('insert',.03,1)
        tween('insert',{'opacity':1,'scale':1},{'opacity':0,'scale':.85,'y':-55},dur-.22,.2,'power2.in')
    elif n==11:
        body=box('paper','<svg width="1080" height="1920"><defs><pattern id="grid'+str(index)+'" width="55" height="55" patternUnits="userSpaceOnUse"><path d="M55 0H0V55" stroke="#9baba633" fill="none"/></pattern></defs><rect width="1080" height="1920" fill="url(#grid'+str(index)+')"/><path d="M0 800L190 740L360 830L550 760L770 820L1080 730V1540H0Z" fill="#d3c664"/><path d="M90 450L300 570L110 600L370 470M800 600L970 470L820 500L970 620" stroke="#aebcca" stroke-width="20" fill="none"/></svg>',cls='sc-full',style='background:#e9e5d8')
        body+=box('sticker',matte(),cls='sc-full',style='filter:drop-shadow(10px 0 #fff) drop-shadow(-10px 0 #fff) drop-shadow(0 10px #fff) drop-shadow(0 -10px #fff) drop-shadow(14px 19px 0 #1e292c55)')
        tween('sticker',{'x':900,'y':-80,'rotation':14,'scale':.7},{'x':0,'y':0,'rotation':-2,'scale':.88},.04,.38,'back.out(1.4)')
        body+=box('paper-word','CUT / PASTE','left:100px;top:455px;font:100px Display;color:#192324;background:#f7f5e9;border-radius:0;padding:26px 24px')
        entrance('paper-word',.14,-1)
    elif n==12:
        body=box('dolly-bg',vid('perspective',d['secondary']),cls='sc-full')+matte()
        tween('dolly-bg',{'scaleX':1,'scaleY':1},{'scaleX':1.9,'scaleY':1.3},0,dur*.9,'sine.inOut')
        body+=box('lens','↔  PERSPECTIVE SHIFT','left:180px;top:500px;width:720px;text-align:center;font-size:31px;font-weight:800;padding:20px;background:#102020bb')
    elif n==13:
        body+=box('cover-freeze',im('cover-still',d['freeze'],cls='sc-footage'),cls='sc-full')
        cover_at=cue('cover',.12)
        setat('cover-freeze',{'opacity':0});setat('cover-freeze',{'opacity':1},cover_at)
        body+=box('cover','<div style="font:130px/1.25 Display;margin-bottom:38px;color:#f2eccf">CREATOR</div><div style="border-top:2px solid #f2eccf;padding-top:14px;letter-spacing:4px;font-size:25px">THE MOTION ISSUE / 025</div>', 'left:110px;top:425px;width:860px;background:none;border:0;box-shadow:none')
        body+=box('coverlines','<span style="color:var(--accent)">MAKE<br>YOUR<br>MOVE.</span>','left:120px;top:1100px;width:300px;font:65px/.9 Display;background:none;border:0;box-shadow:none')
        body+=box('barcode','', 'left:820px;top:1130px;width:140px;height:85px;background:repeating-linear-gradient(90deg,#fff 0 3px,#18252a 3px 5px,#fff 5px 9px);border-radius:0')
        entrance('cover',max(0,cover_at-.08),-1);entrance('coverlines',cover_at+.06,0);entrance('barcode',cover_at+.16,1)
    elif n==14:
        body+=box('glass','<div class="sc-small">OPTICAL MATERIAL / 01</div><div style="font-size:58px;font-weight:800;margin-top:18px">Liquid clarity.</div><div style="font-size:27px;margin-top:10px;color:#edf6f6">A softer surface. Real depth.</div><div id="'+id('shine')+'" style="position:absolute;left:-220px;top:-50px;width:110px;height:450px;background:linear-gradient(90deg,transparent,#fff8,transparent);filter:blur(15px)"></div>', 'left:110px;top:425px;width:860px;height:265px;padding:28px 40px;border-radius:40px 68px 36px 60px','sc-card sc-frost')
        entrance('glass',0,1);tween('glass',{'borderRadius':'40px 68px 36px 60px'},{'borderRadius':'65px 35px 60px 38px'},.3,max(.3,dur-.3),'sine.inOut');tween('shine',{'x':0},{'x':1250},.18,dur*.7,'sine.inOut')
    elif n==15:
        # The scene-level Through handoff is authored by the shared director.
        body+=box('target','<svg width="190" height="190"><path d="M0 55V0H55M135 0H190V55M190 135V190H135M55 190H0V135" stroke="#e9e285" stroke-width="5" fill="none"/></svg>','left:500px;top:850px;width:190px;height:190px;border:0;box-shadow:none;background:none')
        tween('target',{'opacity':0,'scale':1.4},{'opacity':1,'scale':1},.05,.18)
        tween('target',{'opacity':1},{'opacity':0},dur-.22,.1)
    elif n==16:
        body=box('replacement',vid('evidence',d['secondary']),cls='sc-full')+box('subject',matte(),cls='sc-full',style='filter:drop-shadow(5px 0 4px #f3e99488) drop-shadow(15px 14px 18px #0008)')
        tween('replacement',{'scale':1.06},{'scale':1.14},0,dur,'none')
        body+=box('evidence-label','BACKGROUND / YOUR STORY','left:160px;top:490px;width:760px;font-size:27px;letter-spacing:3px;text-align:center;background:none;border:0;box-shadow:none')
    elif n==17:
        # Shards belong to the border; live source and matte stay synchronized.
        body=box('backdrop','',cls='sc-full',style='background:#111c1e')+box('framed',source(),cls='sc-full',style='clip-path:inset(450px 120px 350px round 28px)')
        for i,poly in enumerate(['0 0,50% 0,42% 35%,0 38%','50% 0,100% 0,100% 38%,42% 35%','0 38%,42% 35%,56% 68%,0 66%','42% 35%,100% 38%,100% 66%,56% 68%','0 66%,56% 68%,50% 100%,0 100%','56% 68%,100% 66%,100% 100%,50% 100%']):
            body+=box('shard'+str(i),'',f'left:120px;top:450px;width:840px;height:1120px;border:14px solid #ece8d0;border-radius:28px;clip-path:polygon({poly});background:none','sc-full')
            tween('shard'+str(i),{'x':0,'y':0,'rotation':0,'opacity':1},{'x':(-1 if i%2==0 else 1)*800,'y':(i//2-1)*450,'rotation':(-1 if i%2==0 else 1)*45,'opacity':0},cue('break',.28),.35,'power3.out')
        tween('framed',{'clipPath':'inset(450px 120px 350px round 28px)'},{'clipPath':'inset(0px 0px 0px round 0px)'},cue('break',.28),.3,'power3.out')
        body+=matte();tween('person',{'opacity':0},{'opacity':1},cue('break',.28),.1)
    elif n==19:
        body+=box('phone-shade','',cls='sc-full',style='background:#071215c7')
        body+=f'<canvas id="{id("phone-canvas")}" width="1080" height="1920" class="sc-full"></canvas>'
        body+=box('speaker',vid('speaker-source'),'left:100px;top:835px;width:230px;height:300px;border-radius:110px;border:3px solid #ffffff75')
        body+=box('phone-caption','YOUR SCREEN.<br>IN DIMENSION.','left:130px;top:455px;padding:12px 0;font:42px/1.05 Display;letter-spacing:1px;border:0;box-shadow:none;background:none')
    elif n==21:
        content=f'<div class="sc-small">FOCUS / COUNTDOWN</div><div id="{id("time")}" style="font-size:90px;font-weight:850;line-height:1.4;letter-spacing:-6px">00:03</div><svg width="160" height="160" viewBox="0 0 160 160" style="position:absolute;right:40px;top:43px"><circle cx="80" cy="80" r="65" stroke="#ffffff25" stroke-width="9" fill="none"/><circle id="{id("timer-ring")}" cx="80" cy="80" r="65" stroke="var(--accent)" stroke-width="9" fill="none" pathLength="1" stroke-linecap="round" transform="rotate(-90 80 80)"/></svg>'
        timer_at=cue('timer',0)
        body+=box('timer',content,'left:110px;top:430px;width:860px;height:240px;padding:28px 40px');entrance('timer',timer_at,-1)
        tween('timer-ring',{'strokeDasharray':1,'strokeDashoffset':0},{'strokeDashoffset':1},timer_at+.15,max(1/fps,dur-timer_at-.15),'none')
        j.append(f"const tm{index}={{v:{d.get('timerSeconds',3)}}};tl.to(tm{index},{{v:0,duration:{max(1/fps,dur-timer_at-.15)},ease:'none',onUpdate:()=>document.getElementById('{id('time')}').textContent='00:'+tm{index}.v.toFixed(1).padStart(4,'0')}},{start+timer_at+.15});")
    elif n==22:
        for i,c in enumerate(d['cards']):
            body+=im('wall'+str(i),c,f'left:{35+i%3*350}px;top:{440+i//3*350}px;width:310px;height:330px;border:5px solid #eae9db;border-radius:16px','sc-card')
            entrance('wall'+str(i),cue('wall',0)+i*.045,-1 if i%2 else 1)
        body+=matte()
    elif n==23:
        body+=box('spot','',cls='sc-full',style='background:radial-gradient(ellipse 230px 290px at 58% 51%,transparent 0%,transparent 76%,#031014dc 100%)')
        tween('spot',{'opacity':0},{'opacity':1},.06,.2)
        body+=box('focus-line','<svg width="900" height="260"><path d="M140 60Q620 -60 740 230" stroke="#ece685" stroke-width="6" fill="none"/><path d="M710 208L740 230L750 196" stroke="#ece685" stroke-width="6" fill="none"/></svg>','left:85px;top:455px;background:none;border:0;box-shadow:none')
        tween('focus-line',{'opacity':0},{'opacity':1},.19,.2)
    elif n==24:
        at=d['freezeFrame']/fps
        body+=box('hold',im('freeze-image',d['freeze'],cls='sc-footage'),cls='sc-full')
        setat('hold',{'opacity':0});setat('hold',{'opacity':1},at)
        body+=box('freeze-note','<span class="sc-chip">FREEZE</span><div style="font-size:51px;font-weight:850;margin-top:12px">Right here.</div>','left:120px;top:450px;width:400px;padding:24px 30px')
        tween('freeze-note',{'opacity':0,'y':-60,'rotation':-8},{'opacity':1,'y':0,'rotation':-2},at,.2,'back.out(1.5)')
        body+=box('arrow','<svg width="550" height="420"><path id="'+id('arrowpath')+'" d="M30 20Q460 0 440 315L400 270M440 315L480 275" stroke="#f0e37e" stroke-width="8" fill="none" pathLength="1" stroke-linecap="round"/></svg>','left:450px;top:700px;width:550px;height:420px;background:none;border:0;box-shadow:none')
        tween('arrowpath',{'strokeDasharray':1,'strokeDashoffset':1},{'strokeDashoffset':0},at,.28,'none')
    elif n==25:
        body+=box('after',vid('grade',d['secondary'],'sc-footage'),cls='sc-full')
        tween('after',{'clipPath':'inset(0 0 0 100%)'},{'clipPath':'inset(0 0 0 42%)'},cue('compare',.1),min(dur*.62,.36),'power2.inOut')
        body+=box('divider','', 'left:0;top:390px;width:3px;height:920px;background:#f2e67e','sc-full')
        tween('divider',{'x':1080},{'x':454},cue('compare',.1),min(dur*.62,.36),'power2.inOut')
        body+=box('comparelabels','<span>ORIGINAL</span><span style="float:right;color:var(--accent)">GRADED</span>','left:120px;top:465px;width:840px;font-size:28px;font-weight:850;background:none;border:0;box-shadow:none')
    elif n==26:
        body+=box('behind','CREATE','left:60px;top:620px;width:960px;padding:45px 0;font:230px/1 Display;text-align:center;color:var(--accent);background:none;border:0;box-shadow:none')+matte()
        tween('behind',{'y':230,'scale':.75,'opacity':0,'rotationX':50},{'y':0,'scale':1,'opacity':1,'rotationX':0},.03,.4,'back.out(1.2)')
    elif n==28:
        paths=['M120 970Q30 640 230 650Q350 670 300 580','M800 600L827 532L853 600L920 622L854 648L830 718L802 650L735 625Z','M170 1180Q470 1330 780 1160','M920 1100Q990 950 930 850L894 890M930 850L969 877']
        for i,path in enumerate(paths):
            body+=f'<svg id="{id("doodle"+str(i))}" class="sc-full" viewBox="0 0 1080 1920"><path id="{id("path"+str(i))}" d="{path}" stroke="{["#eee9cc","#eee47b","#eee9cc","#eee47b"][i]}" stroke-width="8" fill="none" stroke-linecap="round" stroke-linejoin="round" pathLength="1"/></svg>'
            tween('path'+str(i),{'strokeDasharray':1,'strokeDashoffset':1},{'strokeDashoffset':0},cue('draw',0)+i*.06,.23,'none')
            j.append(f"tl.to('#{id('doodle'+str(i))}',{{x:3,y:-3,rotation:.25,duration:.09,repeat:{max(1,int(dur/.09)-2)},yoyo:true,ease:'steps(1)'}},{start+i*.12});")
    if n==11:body+=f'<style>#{id("header")} strong,#{id("header")} span,#{id("lower")} .sc-name{{color:#14202a;text-shadow:none}}</style>'
    # Hierarchy belongs to the same complete scene as the live effects.
    # Keep decorative shading below legible effect text; source layers supply depth.
    body+=f'<div id="{id("header")}" class="sc-header"><strong>{e(p["header"])}</strong><span>{e(d.get("subText",p["headerSub"]))}</span></div>'
    if n:
        main=d.get('mainText',FAMILIES[n]);sub=d.get('subText',SUBS[n]);size=min(93,round(900/max(len(main),1)*1.65))
        body+=f'<div id="{id("lower")}" class="sc-lower"><div class="sc-count">{list(FAMILIES).index(n)+1:02d} / 25</div><div class="sc-name" style="font-size:{size}px">{e(main)}</div></div>'
        tween('lower',{'opacity':0,'y':28,'scale':.92},{'opacity':1,'y':0,'scale':1},0,.22,'back.out(1.15)')
    else:
        if b['id']=='cta':
            body+=box('hero','COMMENT “EFFECT”','left:110px;top:465px;width:860px;padding:24px;text-align:center;font:80px/1.2 Display;color:var(--accent);background:#101a1de0;border:1px solid #ffffff40;box-shadow:0 20px 30px #0004')
            entrance('hero',.1,-1)
        for c,k in zip(b.get('captions',[]),range(20)):
            name='caption'+str(k);body+=box(name,e(c['text']),'opacity:'+str(1 if c['local_frame']==0 else 0),'sc-caption')
            setat(name,{'opacity':0});setat(name,{'opacity':1},c['local_frame']/fps);setat(name,{'opacity':0},(c['local_frame']+c['frames'])/fps-.000001)
    if p.get('locale')=='zh-Hans':
        for original,translated in ZH_COPY.items():body=body.replace(original,translated)
        # The large word must stay behind the presenter, with enough side clearance.
        body=body.replace('>CREATE</div>','>创作</div>')
    return body,j


def motion_samples(p):
    """Absolute-time smooth drift plus authored decaying impact, applied to every pixel."""
    impulses=[]
    for i,b in enumerate(p['beats']):
        n=b.get('effect',0);at=b['start_frame']/p['fps']
        offsets={4:[.19,.49],5:[.22,.44,.66],6:[.09,.27],9:[.28],17:[.28],24:[b.get('design',{}).get('freezeFrame',0)/p['fps']]}.get(n,[.12] if n else [.2])
        if 'motionFrames' in b.get('design',{}):offsets=[f/p['fps'] for f in b['design']['motionFrames']]
        for k,off in enumerate(offsets):impulses.append((at+off,(-1 if i%2 else 1),.65 if len(offsets)>1 else 1))
    result=[]
    for frame in range(p['frames']):
        t=frame/p['fps'];x=8*math.sin(t*4.1)+3*math.sin(t*9.3);y=6*math.sin(t*3.3+.4);r=.17*math.sin(t*4.7);scale=1.075
        for at,sign,gain in impulses:
            u=t-at
            if 0<=u<.6:
                envelope=math.exp(-u*9)
                v=math.cos(u*25)*envelope*gain
                x+=24*sign*v;y-=14*v;r+=.55*sign*v;scale+=.035*v
        result.append({'frame':frame,'x':round(x,4),'y':round(y,4),'rotation':round(r,5),'scale':round(scale,6)})
    return result


def document(p,out):
    root=Path(__file__).resolve().parents[1];fonts=root/'effects/_assets/studio3d';a=out/'assets'
    for f in ('Anton.ttf','Anton-OFL.txt','InstrumentSerif.ttf','InstrumentSerif-OFL.txt'):shutil.copyfile(fonts/f,a/f)
    type_css='[style*="Display"]{line-height:1.2!important}[id*="-tick"]{display:block;font-size:26px;line-height:30px;text-align:center}'
    if p.get('typography')=='editorial-condensed':
        type_fonts=root/'effects/_assets/typography'
        for f in ('BarlowCondensed-ExtraBold.ttf','BarlowCondensed-ExtraBold-OFL.txt','Inter.ttf','Inter-OFL.txt'):shutil.copyfile(type_fonts/f,a/f)
        type_css+=EDITORIAL_TYPE
    if p.get('locale')=='zh-Hans':
        type_fonts=root/'effects/_assets/typography'
        for f in ('NotoSansSC.ttf','NotoSansSC-OFL.txt','NotoSansSC-SOURCE.json'):shutil.copyfile(type_fonts/f,a/f)
        type_css+=CHINESE_TYPE
    bodies=[];js=[];cues=[]
    for i,b in enumerate(p['beats']):
        body,steps=scene(p,b,i);wrap='scene-'+b['id'];tran='transition-'+b['id']
        bodies.append(f'<div id="{wrap}" class="sc-scene"><div id="{tran}" class="sc-content">{body}</div></div>')
        s,e=b['start_frame']/p['fps'],b['end_frame']/p['fps']
        # Scenes cut; their contents animate. Explicit visibility also handles exact t=0.
        initial='visible' if s==0 else 'hidden'
        js.extend([f"gsap.set('#{wrap}',{{visibility:'{initial}'}});",f"tl.set('#{wrap}',{{visibility:'visible'}},{max(0,s-.000001)});",f"tl.set('#{wrap}',{{visibility:'hidden'}},{e-.000001});"]+steps)
        if b.get('effect')==15 and b.get('design',{}).get('refinement')!='gesture-v3':
            dest='transition-'+p['beats'][i+1]['id']
            js.extend([f"tl.to('#{tran}',{{scale:5.5,filter:'blur(10px)',transformOrigin:'55% 52%',duration:.2,ease:'power4.in'}},{e-.2});",f"tl.fromTo('#{dest}',{{scale:5.5,filter:'blur(10px)',transformOrigin:'55% 52%'}},{{scale:1,filter:'blur(0px)',duration:.27,ease:'power4.out',immediateRender:false}},{e});"])
        cues.extend({'start':c['start_frame']/p['fps'],'end':c['end_frame']/p['fps'],'text':c['text'],'beat':b['id']} for c in b.get('captions',[]))
    samples=motion_samples(p);(out/'scene-motion.json').write_text(json.dumps(samples))
    js.append('const motion='+json.dumps(samples)+';const clock={t:0};function moveScene(){const a=Math.min(motion.length-1,clock.t*'+str(p['fps'])+'),i=Math.floor(a),f=a-i,u=motion[i],v=motion[Math.min(i+1,motion.length-1)];gsap.set("#scene-world",{x:u.x+(v.x-u.x)*f,y:u.y+(v.y-u.y)*f,rotation:u.rotation+(v.rotation-u.rotation)*f,scale:u.scale+(v.scale-u.scale)*f});}tl.to(clock,{t:'+str(p['frames']/p['fps'])+',duration:'+str(p['frames']/p['fps'])+',ease:"none",onUpdate:moveScene},0);moveScene();')
    duration=p['frames']/p['fps'];phone=next((b for b in p['beats'] if b.get('effect')==19),None);extras=''
    if phone:
        for f in ('three.module.js','RoomEnvironment.js','THREE-LICENSE.txt'):shutil.copyfile(fonts/f,a/f)
        source=out/p['assets'][phone['picture']['asset']]['compiled_file']
        subprocess.run(['ffmpeg','-v','error','-n','-i',str(source),'-vf','scale=360:640','-frames:v',str(phone['frames']),str(a/'phone-%03d.jpg')],check=True)
        rig=Path(__file__).with_name('scene_phone.js').read_text().replace('__CONFIG__',json.dumps({'canvas':'fx-'+phone['id']+'-phone-canvas','start':phone['start_frame']/p['fps'],'duration':phone['frames']/p['fps'],'frames':phone['frames'],'fps':p['fps']}))
        extras='<script type="importmap">{"imports":{"three":"./assets/three.module.js"}}</script><script type="module">'+rig+'</script>'
    type_css += ('' if p.get('demo',False) else '.sc-count{display:none}')
    type_css += ('' if p.get('showHeader',False) else '.sc-header{display:none}')
    type_css += ('' if p.get('showTitles',True) else '.sc-lower{display:none}')
    doc=f'''<!doctype html><html><head><meta charset="utf-8"><script src="assets/gsap.min.js"></script><style>{CSS}{type_css}</style></head><body><div id="edit" data-composition-id="edit" data-start="0" data-width="1080" data-height="1920" data-duration="{duration}" data-fps="{p['fps']}" style="--accent:{p.get('accentColor','#efe282')}"><div id="scene-world" class="sc-world">{''.join(bodies)}</div><audio id="master-audio" src="assets/voice-mix.wav" data-start="0" data-duration="{duration}" data-track-index="999" data-volume="1"></audio></div><script>document.fonts.ready.then(()=>{{const tl=gsap.timeline({{paused:true}});{''.join(js)}tl.to({{}},{{duration:{duration}}},0);window.__timelines=window.__timelines||{{}};window.__timelines.edit=tl;window.dispatchEvent(new Event('scene-timeline-ready'));}});</script>{extras}</body></html>'''
    return doc,cues

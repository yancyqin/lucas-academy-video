"""Build a continuous, final-time camera curve. No encoded footage is retimed."""
import json, math, hashlib, subprocess
from pathlib import Path
P=Path(__file__).resolve().parent
UI=P.parents[3]/'inception-space-ui'
old=json.loads((P.parent/'v5/edit-plan.json').read_text())['scenes']
final=json.loads((P.parent/'v11/full-plan.json').read_text())
tour=json.loads((P.parent/'v5/tour-plan.json').read_text())
scenes=final['scenes']; by={s['id']:s for s in scenes}

def raw_to_clean(t):
    for s in old:
        a=s['old_first']/24; b=a+s['old_count']/24
        if a-1e-7<=t<=b+1e-7:
            return s['start']+(t-a)*s['count']/s['old_count']
    raise ValueError(t)

def to_final(t):
    c=raw_to_clean(t)
    for s in scenes:
        source=s.get('source')
        if source and source[0]-1e-6<=c<=source[1]+1e-6:
            return s['start']+(c-source[0])/(source[1]-source[0])*(s['end']-s['start'])
    if t<122.21:
        return 29.2916667+(t-43)/(122.21-43)*(86.9166667-29.2916667)
    raise ValueError((t,c))

anchors=[]
for a in tour['anchors']:
    raw=a['at']/24
    if raw<43: continue
    if raw>tour['close']+1e-6: continue
    a=dict(a);a['time']=to_final(raw);a['source_time']=raw
    anchors.append(a)
opening=[
 (0,[0,4.45,39],[0,38,-2],51),
 (6.4,[0,4.45,39],[0,38,-2],51),
 (8.3,[0,4.45,38.6],[0,39,-2],52),
 (13,[0,4.45,36],[-15,8.7,-22],58),
 (16.5,[0,4.45,32],[14,8.4,-22],56),
 (20,[9.8,4.45,31],[25,6.8,21],58),
 (24,[20.2,4.45,28],[27.6,7.9,15.4],56),
]
anchors=[dict(time=t,eye=e,target=a,fov=f) for t,e,a,f in opening]+anchors
# The silence and musical listening section is a deliberate stationary camera.
hold=156.9583333333
def raw_pose(t):
    a,b=next((a,b) for a,b in zip(tour['anchors'],tour['anchors'][1:]) if a['at']/24<=t<=b['at']/24)
    u=(t*24-a['at'])/(b['at']-a['at']);u=u*u*(3-2*u)
    eye=[x+(y-x)*u for x,y in zip(a['eye'],b['eye'])]
    def lens(a):
        x,y,z=[v-w for v,w in zip(a['target'],a['eye'])]
        return math.atan2(x,-z),math.atan2(y,math.hypot(x,z))
    ya,pa=lens(a);yb,pb=lens(b);yaw=ya+math.atan2(math.sin(yb-ya),math.cos(yb-ya))*u;pitch=pa+(pb-pa)*u
    target=[eye[0]+10*math.sin(yaw)*math.cos(pitch),eye[1]+10*math.sin(pitch),eye[2]-10*math.cos(yaw)*math.cos(pitch)]
    return dict(eye=eye,target=target,fov=a['fov']+(b['fov']-a['fov'])*u)
for t in [by['n009']['start'],by['n014']['start']]:
    anchors.append(dict(time=t,**raw_pose(hold)))
anchors.sort(key=lambda a:a['time'])
# Reach the named painting near its introduction, while retaining continuous travel.
# Older editions arrived at the Raft, Wanderer and Temeraire after their labels.
arrival_times={302:411,315:418,424:545.5,499:630,505:635,514:641,522:654,549:674,554.5:690,565:700}
anchors=[a for a in anchors if abs(a.get('source_time',-1)-533)>1e-5]
for a in anchors:
    for raw,t in arrival_times.items():
        if abs(a.get('source_time',-1)-raw)<1e-5:a['time']=t
anchors.sort(key=lambda a:a['time'])
# Convert to unwrapped yaw/pitch, then use component-wise monotone Hermite curves.
last=None
for a in anchors:
    x,y,z=[v-w for v,w in zip(a['target'],a['eye'])]
    yaw=math.atan2(x,-z); pitch=math.atan2(y,math.hypot(x,z))
    if last is not None:yaw=last+math.atan2(math.sin(yaw-last),math.cos(yaw-last))
    a['values']=[*a['eye'],yaw,pitch,a['fov']];last=yaw

inserts=[
 dict(id='real-gallery',kind='video',file='v5/footage/muse-gallery-entry.mp4',start=0,end=7.1,trim=.5,speed=1,fadeIn=0,fadeOut=1.2),
 dict(id='monastery',kind='video',file='v2/footage/O02-monastery.mp4',start=by['n004']['start'],end=by['n004']['end'],trim=.35,speed=9.3/(by['n004']['end']-by['n004']['start']),fadeIn=.6,fadeOut=.8),
 dict(id='cold-water',kind='video',file='v5/footage/cold-water-loop.mp4',start=by['n005']['start'],end=by['n005']['end'],trim=0,speed=18.7083333333/(by['n005']['end']-by['n005']['start']),fadeIn=.8,fadeOut=.8),
]
for id,file,a,b,trim,speed,kind in [
 ('paris','v2/footage/O03-paris.mp4',157.4,166.5,.25,.94,'video'),
 ('engawa','footage/muse/M01-engawa-pond.mp4',691.65,701.9,.15,.9,'video'),
 ('seirai-in','../mono-no-aware-photos/01-green-courtyard.jpg',711,718.55,0,1,'photo'),
 ('real-petals','footage/free/sakura-water-5471897.mp4',724.1,730.45,.25,1,'video'),
 ('persimmons','footage/muse/M02-autumn-persimmons.mp4',744.25,750.4,.15,.78,'video'),
 ('round-window','footage/muse/M03-round-window.mp4',tour['oldCredits']-40,tour['oldCredits'],0,.25,'video')]:
    path=P.parent/file if file.startswith('v') else P.parent/file
    # The production footage folder is the parent of versioned work folders.
    if file.startswith('footage/'):path=P.parent/file
    if file.startswith('../mono-'):path=P.parents[1]/'mono-no-aware-photos/01-green-courtyard.jpg'
    aa=to_final(a);bb=to_final(b)
    inserts.append(dict(id=id,kind=kind,file=str(path),start=aa,end=bb,trim=trim,speed=speed*(b-a)/(bb-aa),fadeIn=1.3,fadeOut=1.3))
for i in inserts:
    if not Path(i['file']).is_absolute():i['file']=str(P.parent/i['file'])
    assert Path(i['file']).is_file(),i
flat=[dict(id=f['name'],start=to_final(f['start']),end=to_final(f['end'])) for f in tour['flat'] if f['name']!='chopin-portrait']
flat.append(dict(id='monk-sea',start=by['listen-clearing']['start'],end=by['listen-clearing']['end']))
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=UI,text=True).strip()
hashes={}
for name in ['src/inception/world/rooms/romanticismLayout.js','src/inception/world/render/threeRomanticismSalon.ts','src/inception/world/render/threeMuseum.ts','content/inception/artworks/romanticism-salon-v1.json','content/inception/artworks/romanticism-sculptures-v1.json']:
    hashes[name]=hashlib.sha256((UI/name).read_bytes()).hexdigest()
plan=dict(fps=60,width=1920,height=1080,frames=math.ceil(final['duration']*60),duration=math.ceil(final['duration']*60)/60,
          audio_source=str(P.parent/'v11/delivery'),source_timeline=str(P.parent/'v11/full-plan.json'),anchors=anchors,
          scenes=scenes,inserts=inserts,flat=flat,ui_head=head,ui_file_sha256=hashes,
          interpolation='PCHIP camera position, unwrapped yaw, pitch and FOV sampled directly at final frame times',speech_speed_changed=False)
(P/'capture-plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2))
print('Prepared',plan['frames'],'frames;',len(anchors),'camera waypoints;',len(inserts),'external inserts')

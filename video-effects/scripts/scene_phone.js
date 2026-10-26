// Original procedural Three.js handset. Same scene parent as the live composition.
import * as THREE from 'three';
import { RoomEnvironment } from './assets/RoomEnvironment.js';
const C=__CONFIG__, canvas=document.getElementById(C.canvas);
const renderer=new THREE.WebGLRenderer({canvas,alpha:true,antialias:true,preserveDrawingBuffer:true});
renderer.setSize(1080,1920,false);renderer.setPixelRatio(1);renderer.outputColorSpace=THREE.SRGBColorSpace;
renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.25;
const scene=new THREE.Scene(),camera=new THREE.OrthographicCamera(-540,540,960,-960,1,3000);
camera.position.set(0,0,1400);camera.lookAt(0,0,0);
const env=new THREE.PMREMGenerator(renderer);scene.environment=env.fromScene(new RoomEnvironment(),.03).texture;
scene.add(new THREE.HemisphereLight(0xfffaf0,0x324c53,2.5));
const key=new THREE.DirectionalLight(0xfff8e9,4);key.position.set(-300,600,800);scene.add(key);
const rim=new THREE.DirectionalLight(0xa7d4ff,3);rim.position.set(600,-100,400);scene.add(rim);
function roundRect(w,h,r){const s=new THREE.Shape(),x=-w/2,y=-h/2;s.moveTo(x+r,y);s.lineTo(x+w-r,y);s.quadraticCurveTo(x+w,y,x+w,y+r);s.lineTo(x+w,y+h-r);s.quadraticCurveTo(x+w,y+h,x+w-r,y+h);s.lineTo(x+r,y+h);s.quadraticCurveTo(x,y+h,x,y+h-r);s.lineTo(x,y+r);s.quadraticCurveTo(x,y,x+r,y);return s;}
const group=new THREE.Group();scene.add(group);
const geometry=new THREE.ExtrudeGeometry(roundRect(386,760,49),{depth:24,bevelEnabled:true,bevelSize:7,bevelThickness:6,bevelSegments:5,curveSegments:32});geometry.translate(0,0,-12);
const body=new THREE.Mesh(geometry,new THREE.MeshPhysicalMaterial({color:0x768d8c,metalness:.9,roughness:.23,clearcoat:.65}));group.add(body);
const black=new THREE.Mesh(new THREE.ShapeGeometry(roundRect(370,744,43),32),new THREE.MeshStandardMaterial({color:0x060a0b,roughness:.25}));black.position.z=19;group.add(black);
const texCanvas=document.createElement('canvas');texCanvas.width=360;texCanvas.height=640;const ctx=texCanvas.getContext('2d');
const tex=new THREE.CanvasTexture(texCanvas);tex.colorSpace=THREE.SRGBColorSpace;
const screenGeo=new THREE.ShapeGeometry(roundRect(348,710,33),32);const pos=screenGeo.attributes.position,uv=screenGeo.attributes.uv;for(let i=0;i<uv.count;i++)uv.setXY(i,(pos.getX(i)+174)/348,(pos.getY(i)+355)/710);
const screen=new THREE.Mesh(screenGeo,new THREE.MeshBasicMaterial({map:tex}));screen.position.z=20;group.add(screen);
const island=new THREE.Mesh(new THREE.ShapeGeometry(roundRect(112,29,14),24),new THREE.MeshBasicMaterial({color:0x070a0c}));island.position.set(0,329,22);group.add(island);
const button=new THREE.Mesh(new THREE.BoxGeometry(8,85,12),new THREE.MeshStandardMaterial({color:0x9aa7a0,metalness:.8,roughness:.2}));button.position.set(198,110,0);group.add(button);
const images=Array.from({length:C.frames},(_,i)=>{const im=new Image();im.src='assets/phone-'+String(i+1).padStart(3,'0')+'.jpg';return im;});
const ready=Promise.all(images.map(im=>im.decode()));
function draw(time){const t=Math.max(0,Math.min(C.duration,time-C.start)),u=Math.min(1,t/.36),settle=1-Math.pow(1-u,3);const f=Math.min(C.frames-1,Math.floor(t*C.fps));if(images[f].complete){ctx.drawImage(images[f],0,0,360,640);tex.needsUpdate=true;}group.position.set(135+(1-settle)*360,60-(1-settle)*180,0);group.rotation.set(.05*Math.cos(t*2),-.42+(settle*.26)+.1*Math.sin(t*2),-.1+(1-settle)*.4);group.scale.setScalar(.75+.25*settle);renderer.render(scene,camera);}
function bind(){const tl=window.__timelines?.edit;if(!tl)return;const prior=tl.eventCallback('onUpdate');tl.eventCallback('onUpdate',()=>{if(prior)prior();draw(tl.time());});ready.then(()=>{draw(tl.time());window.__scenePhoneReady=true;});}
if(window.__timelines?.edit)bind();else window.addEventListener('scene-timeline-ready',bind,{once:true});
window.addEventListener('hf-seek',e=>{const work=ready.then(()=>draw(e.detail.time));if(e.detail.waitUntil)e.detail.waitUntil(work);});

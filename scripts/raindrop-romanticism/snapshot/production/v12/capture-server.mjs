import http from 'node:http';
import {readFile,writeFile,mkdir,stat,rename} from 'node:fs/promises';
import {spawn} from 'node:child_process';
import path from 'node:path';
const root=import.meta.dirname;
await mkdir(path.join(root,'raw'),{recursive:true});
const server=http.createServer(async(req,res)=>{
 try{
  const u=new URL(req.url,'http://127.0.0.1');
  if(u.pathname==='/film-capture/' || u.pathname==='/film-capture/index.html'){
   res.setHeader('Content-Type','text/html');res.end(await readFile(path.join(root,'capture.html')));return;
  }
  if(u.pathname==='/film-capture/plan.json'){
   res.setHeader('Content-Type','application/json');res.end(await readFile(path.join(root,'capture-plan.json')));return;
  }
  if(u.pathname==='/film-capture/status'){
   res.setHeader('Content-Type','application/json');
   try{res.end(await readFile(path.join(root,'capture-status.json')));}catch{res.end('{}');}return;
  }
  if(u.pathname==='/film-capture/progress'&&req.method==='POST'){
   let parts=[];for await(const c of req)parts.push(c);
   const value=JSON.parse(Buffer.concat(parts));value.updated_at=new Date().toISOString();
   await writeFile(path.join(root,'capture-status.json'),JSON.stringify(value,null,2));res.end('ok');return;
  }
  if(u.pathname==='/film-capture/complete'){
   const name=u.searchParams.get('name');if(!/^(walk-\d{3}|smoke-\d{3})$/.test(name))throw Error('Invalid chunk');
   const target=path.join(root,'raw',name+'.mp4');
   try{const s=await stat(target);res.end(JSON.stringify({exists:s.size>1000}));}catch{res.end('{"exists":false}');}return;
  }
  if(u.pathname==='/film-capture/save'&&req.method==='POST'){
   const name=u.searchParams.get('name'),count=Number(u.searchParams.get('count'));
   if(!/^(walk-\d{3}|smoke-\d{3})$/.test(name)||!(count>0&&count<=1200))throw Error('Invalid chunk');
   const dst=path.join(root,'raw',name),parts=[];for await(const c of req)parts.push(c);
   await writeFile(dst+'.h264',Buffer.concat(parts));
   await new Promise((ok,fail)=>{
    const p=spawn('/opt/homebrew/bin/ffmpeg',['-v','error','-y','-r','60','-i',dst+'.h264','-c','copy','-frames:v',String(count),'-video_track_timescale','15360',dst+'.tmp.mp4']);
    p.stderr.on('data',d=>process.stderr.write(d));p.on('exit',code=>code?fail(Error('ffmpeg '+code)):ok());
   });
   await rename(dst+'.tmp.mp4',dst+'.mp4');
   console.log('Saved',name,count,'frames',new Date().toISOString());res.end('ok');return;
  }
  const upstream=http.request({hostname:'127.0.0.1',port:8095,path:req.url,method:req.method,headers:{...req.headers,host:'127.0.0.1:8095'}},r=>{
   res.writeHead(r.statusCode,r.headers);r.pipe(res);
  });upstream.on('error',e=>{res.writeHead(502);res.end(String(e));});req.pipe(upstream);
 }catch(e){console.error(e);res.writeHead(500);res.end(String(e));}
});
server.listen(8078,'127.0.0.1',()=>console.log('Offline film renderer: http://127.0.0.1:8078/film-capture/'));

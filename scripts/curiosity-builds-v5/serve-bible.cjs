(async()=>{
 const {createServer}=await import('/Users/yqin/repo/playground/lucas-academy-bible/node_modules/vite/dist/node/index.js');
 const server=await createServer({root:'/Users/yqin/repo/playground/lucas-academy-bible',server:{host:'127.0.0.1',port:5193,strictPort:true,hmr:false,watch:{ignored:['**/*']}}});
 await server.listen();console.log('Bible capture preview: http://127.0.0.1:5193');
})().catch(e=>{console.error(e);process.exit(1)});

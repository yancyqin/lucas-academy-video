(async()=>{
 const {createServer}=await import('/Users/yqin/repo/playground/inception-space-ui/node_modules/vite/dist/node/index.js');
 const server=await createServer({root:'/Users/yqin/repo/playground/inception-space-ui',server:{host:'127.0.0.1',port:5192,strictPort:true,hmr:false,watch:{ignored:['**/*']}}});
 await server.listen();console.log('Capture-only preview ready at http://127.0.0.1:5192 (automatic reload disabled).');
})().catch(e=>{console.error(e);process.exit(1)});

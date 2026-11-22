const common={viewport:{width:1280,height:720},scale:1.5,locale:'en-US',css:'.la-chrome,.weekly-toolbar,.brainstorm-weekly-toolbar{display:none!important}'};
const center=async(p,sel)=>{await p.locator(sel).waitFor({state:'visible',timeout:60000});await p.locator(sel).evaluate(e=>e.scrollIntoView({block:'center'}));await p.waitForTimeout(700)};
const focus=async(p,sel)=>{await p.locator(sel).evaluate(e=>{e.style.minHeight='660px';e.scrollIntoView({block:'center'});});await p.addStyleTag({content:'body::before{content:"";position:fixed;inset:0;background:#080e19;z-index:999}.cd{position:fixed!important;inset:24px!important;z-index:1000!important;width:calc(100% - 48px)!important;height:calc(100% - 48px)!important;box-sizing:border-box;overflow:hidden}'});await p.waitForTimeout(300);};
module.exports=[
 {name:'chess-comeback-play',url:'http://127.0.0.1:5191/weekly/?edition=002&lang=en',...common,
  async prepare(p){await center(p,'[data-chess-demo]');await focus(p,'[data-chess-demo]');await p.locator('[data-chess-demo] .cd-play').click();await p.locator('[data-chess-demo] .cd-option').first().waitFor({state:'visible',timeout:120000});},
  async run(r){await r.hold(.7);await r.click('[data-chess-demo] .cd-option');await r.hold(.5);await r.click('[data-chess-demo] .comeback-target');r.mark('revived');await r.hold(8);}},
 {name:'chess-rockfall-play',url:'http://127.0.0.1:5191/weekly/?edition=003&lang=en',...common,
  async prepare(p){await center(p,'[data-underground-demo]');await focus(p,'[data-underground-demo]');await p.locator('[data-underground-demo] .cd-play').click();await p.locator('[data-underground-demo] .rock-impact').first().waitFor({state:'visible',timeout:120000});},
  async run(r){r.mark('rockfall');await r.hold(10);}}
];

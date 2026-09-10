/* Optional operator-run browser QA. Only pass a SYNTHETIC local export, never product data.
   PLAYWRIGHT_MODULE selects an already installed Playwright package; nothing is downloaded.
   Usage: node tests/viewer/browser.cjs http://127.0.0.1:PORT/<id>/index.html output-directory
*/
const assert=require("node:assert/strict"),fs=require("node:fs"),path=require("node:path");
const {chromium}=require(process.env.PLAYWRIGHT_MODULE || "playwright");
(async()=>{
  const url=new URL(process.argv[2]),out=path.resolve(process.argv[3]);
  assert.equal(url.protocol,"http:");assert.equal(url.hostname,"127.0.0.1");
  fs.mkdirSync(out,{recursive:true});
  const browser=await chromium.launch({channel:process.env.VIEWER_BROWSER || "msedge",headless:true});
  try {
    const context=await browser.newContext({viewport:{width:1440,height:1000}});
    const page=await context.newPage(),errors=[],external=[];
    page.on("pageerror",e=>errors.push(e.message));
    page.on("request",r=>{if(new URL(r.url()).origin!==url.origin) external.push(r.url());});
    await page.goto(url.href);
    await page.locator("canvas").first().waitFor();
    assert.equal(await page.locator("canvas").count(),3);
    const count=await page.locator("#nodes button").count();assert.ok(count>0);
    const captured=await page.locator("#memory-data").textContent();
    const data=JSON.parse(captured);
    await context.setOffline(true);
    await page.locator("#method").selectOption("declared");
    assert.ok(await page.locator("#edges button").count()>0);
    await page.locator("#reset").click();
    await page.locator("#search").fill("NO_MATCH_SYNTHETIC_SENTINEL");
    assert.equal(await page.locator("#nodes button").count(),0);
    assert.match(await page.locator("#status").innerText(),/not proof of absence/);
    await page.locator("#reset").click();
    await page.locator("#nodes button").first().focus();await page.keyboard.press("Enter");
    assert.notEqual(await page.locator("#selection-title").innerText(),"Select a node or relation.");
    await page.locator("#path-start").click();
    await page.locator("#nodes button").nth(1).click();
    await page.locator("#path-find").click();
    assert.match(await page.locator("#path-result").innerText(),/Navigation only/);
    // Choose a real source-bearing node through the accessible list.
    for(let i=0;i<count;i++) {
      await page.locator("#nodes button").nth(i).click();
      if(await page.locator("#sources button").count()) {
        await page.locator("#sources button").first().click();
        assert.ok((await page.locator(".source-copy").innerText()).length>60);break;
      }
    }
    assert.equal(await page.locator(".source-copy").count(),1);
    await page.screenshot({path:path.join(out,"desktop.png"),fullPage:true});
    if(data.code) {
      await page.locator("#layer").selectOption("code");
      assert.match(await page.locator("#status").innerText(),/freshness unknown/);
      if(data.mapping_compatible) {
        await page.locator("#layer").selectOption("mapping");
        assert.ok(await page.locator("#nodes button").count()>0);
        await page.locator("#view").selectOption("current");
        await page.screenshot({path:path.join(out,"mapping.png"),fullPage:true});
      } else {
        assert.ok(await page.locator('#layer option[value="mapping"]').evaluate(option=>option.disabled));
        assert.match(await page.locator("#status").innerText(),/REVISION MISMATCH/);
      }
    } else {
      assert.ok(await page.locator('#layer option[value="code"]').evaluate(option=>option.disabled));
      await page.locator("#layer").focus();await page.keyboard.press("ArrowDown");
      assert.equal(await page.locator("#layer").inputValue(),"document");
    }
    await page.locator("#reset").click();
    await page.setViewportSize({width:320,height:900});
    await page.waitForFunction(()=>{
      const graph=document.getElementById("graph").getBoundingClientRect();
      return [...document.querySelectorAll("#graph canvas")].every(c=>Math.abs(c.getBoundingClientRect().width-graph.width)<2);
    });
    await page.locator("#nodes button").first().click();
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
    await page.screenshot({path:path.join(out,"mobile.png"),fullPage:true});
    await page.setViewportSize({width:1280,height:900});
    await page.evaluate(()=>document.documentElement.style.fontSize="200%");
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
    assert.equal(await page.evaluate(()=>globalThis.pwned),undefined);
    assert.deepEqual(errors,[]);assert.deepEqual(external,[]);
    console.log(JSON.stringify({status:"passed",browser:await browser.version(),nodes:count,
      code:data.code?.coverage || "not_requested",mapping:data.mapping_compatible,offlineInteractions:true,
      keyboard:true,mobileWidth:320,textZoom:"200%",pageErrors:errors,externalRequests:external,screenshots:out}));
  } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1});

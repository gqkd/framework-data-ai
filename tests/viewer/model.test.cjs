const test=require("node:test");
const assert=require("node:assert/strict");
const {prepare,select,path}=require("../../assets/memory-viewer/model.js");
const cytoscape=require("../../third_party/cytoscape/dist/cytoscape.min.js");
const node=(id,method="derived")=>({id,kind:"component",label:id,identity:{scope:"product:demo"},data:{views:[{view:"current"}]},provenance:{assertion_method:method}});
const edge=(id,source,target,method="declared")=>({id,source,target,relation:"applies_to",provenance:{assertion_method:method}});
function fixture() {
  return {document:{nodes:[node("a"),node("b"),node("c")],edges:[edge("ab","a","b"),edge("bc","b","c")]},
    code:{nodes:[{id:"a",kind:"file",name:"module.py",repository:"repo",provenance:{assertion_method:"derived"}}],
      edges:[{...edge("unresolved","a",null,"derived"),resolution:"unresolved"}]},
    bridges:[{component:"a",files:["a"],view:"current"}],hypotheses:[{claim:"Maybe",provenance:{assertion_method:"inferred"}}]};
}
test("graph namespaces stay separate and input is immutable",()=>{
  const input=fixture(), before=JSON.stringify(input), all=prepare(input);
  assert.equal(JSON.stringify(input),before);
  assert.notEqual(all.nodes.find(n=>n.layer==="document").id,all.nodes.find(n=>n.layer==="code").id);
  assert.equal(select(all,{layer:"document"}).nodes.length,3);
  assert.equal(select(all,{layer:"code"}).nodes.length,1);
});
test("declared relation filter keeps derived endpoint nodes",()=>{
  const result=select(prepare(fixture()),{layer:"document",method:"declared"});
  assert.equal(result.nodes.length,3); assert.equal(result.edges.length,2);
});
test("bounded filtering never dangles resolved edges and reports truncation",()=>{
  const result=select(prepare(fixture()),{layer:"document"},{nodes:2,edges:1});
  assert.equal(result.nodes.length,2);assert.equal(result.totalNodes,3);assert.ok(result.truncated);
  assert.ok(result.edges.every(e=>result.nodes.some(n=>n.id===e.source)&&result.nodes.some(n=>n.id===e.target)));
});
test("unresolved targets remain explicit but never become guessed nodes",()=>{
  const result=select(prepare(fixture()),{layer:"code"});
  assert.equal(result.edges[0].target,null); assert.equal(result.nodes.length,1);
  assert.equal(path(result,"code:a","code:unknown"),null);
});
test("paths retain direction and are bounded by displayed nodes and edges",()=>{
  const result=select(prepare(fixture()),{layer:"document"});
  assert.deepEqual(path(result,"document:a","document:c").map(s=>s.direction),["forward","forward"]);
  assert.deepEqual(path(result,"document:c","document:a").map(s=>s.direction),["reverse","reverse"]);
  assert.deepEqual(path(result,"document:a","document:a"),[]);
  assert.equal(path({...result,edges:[]},"document:a","document:c"),null);
});
test("current mapping can include captured files but is not implementation proof",()=>{
  const all=prepare(fixture());
  assert.equal(select(all,{layer:"mapping",view:"current"}).edges.filter(e=>e.layer==="mapping").length,1);
  assert.equal(select(all,{layer:"hypothesis"}).nodes[0].method,"inferred");
  const separate=fixture();separate.bridges=[];
  assert.equal(prepare(separate).edges.filter(e=>e.layer==="mapping").length,0);
});
test("real pinned renderer accepts opaque IDs and headless navigation",()=>{
  const visible=select(prepare(fixture()),{layer:"document"});
  const cy=cytoscape({headless:true,elements:visible.nodes.map(n=>({data:{id:n.id}})).concat(
    visible.edges.map(e=>({data:{id:e.id,source:e.source,target:e.target}})))});
  assert.equal(cy.nodes().length,3); assert.equal(cy.edges().length,2);
  cy.getElementById("document:a").select(); assert.equal(cy.$(":selected").length,1);cy.destroy();
});
test("search, scope, kind and view filters compose without implicit neighbours",()=>{
  const all=prepare(fixture());
  assert.equal(select(all,{layer:"document",search:"a",kind:"component",scope:"product:demo",view:"current"}).nodes.length,1);
  assert.equal(select(all,{layer:"document",scope:"absent"}).nodes.length,0);
  assert.equal(select(all,{layer:"code",view:"target"}).nodes.length,0);
});

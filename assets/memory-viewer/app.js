/* Untrusted labels, paths and source text are always inserted as text, never HTML. */
(() => {
  "use strict";
  const data = JSON.parse(document.getElementById("memory-data").textContent);
  const model = MemoryViewer.prepare(data), byId = new Map([...model.nodes,...model.edges].map(n=>[n.id,n]));
  const el = id => document.getElementById(id);
  const controls = ["layer","search","scope","kind","method","view","relation"];
  const sourceIndex = new Map([...data.document.sources,...(data.code?.sources || [])].map(s=>[s.id,s]));
  const append = (parent,tag,text) => {const node=document.createElement(tag); node.textContent=text; parent.append(node); return node;};
  const codeOption = el("layer").querySelector('option[value="code"]');
  codeOption.disabled = !data.code;
  el("layer").querySelector('option[value="mapping"]').disabled = !data.mapping_compatible;
  el("layer").querySelector('option[value="hypothesis"]').disabled = !data.hypotheses.length;
  function options(id, values) {
    [...new Set(values)].filter(Boolean).sort().forEach(value=>{
      const option=append(el(id),"option",value); option.value=value;
    });
  }
  options("scope",model.nodes.map(n=>n.scope)); options("kind",model.nodes.map(n=>n.kind));
  options("relation",model.edges.map(e=>e.label));
  data.warnings.forEach(w=>append(el("warnings"),"li",w));
  el("diagnostics").textContent=JSON.stringify({document_snapshot:data.document.snapshot,
    code_snapshot:data.code?.snapshot || null, mapping_compatible:data.mapping_compatible,
    code_observation:data.observation.code, issues:data.document.issues,gaps:data.document.gaps,
    code_repositories:data.code?.repositories || [], code_limitations:data.code?.limitations || []},null,2);
  let cy=null, visible=null, selected=null, origin=null;
  function source(location) {
    const record=sourceIndex.get(location.source);
    if(!record) return;
    const button=append(el("sources"),"button",record.path + " · lines " + location.start_line + "–" + location.end_line);
    button.type="button";
    button.addEventListener("click",()=>{
      const old=el("sources").querySelector(".source-copy"); if(old) old.remove();
      const box=append(el("sources"),"div",""); box.className="source-copy";
      append(box,"p",record.revision);
      const text=data.source_text[record.id];
      append(box,"pre",text === undefined ?
        "Code source body is not included. Use the captured repository, path, revision and line range; no live file has been opened." :
        text.split("\n").map((line,i)=>(i+1)+ "  " + line).join("\n"));
    });
  }
  function inspect(id) {
    const item=byId.get(id); if(!item) return;
    selected=item.kind ? id : null;
    el("path-start").disabled=!selected; el("path-find").disabled=!selected || !origin;
    el("selection-title").textContent=item.label;
    const records=new Set(item.raw.provenance?.records || []);
    el("record").textContent=JSON.stringify(records.size ? {record:item.raw,
      provider_evidence:data.code.records.filter(r=>records.has(r.id))} : item.raw,null,2);
    el("selection").replaceChildren(); el("sources").replaceChildren();
    append(el("selection"),"p","Layer: " + item.layer);
    const provenance=item.raw.provenance || item.raw.declaration;
    if(provenance) {
      append(el("selection"),"p","Source kind: " + provenance.source_kind);
      append(el("selection"),"p","Assertion method: " + provenance.assertion_method);
      if(provenance.confidence !== undefined) append(el("selection"),"p","Confidence: " + provenance.confidence + " (inferred, not a constraint)");
      (provenance.sources || provenance.locations || []).forEach(source);
    }
    if(item.raw.observation) append(el("selection"),"p",JSON.stringify(item.raw.observation));
    if(item.raw.target === null) append(el("selection"),"p","Unresolved target — no edge is drawn and no target is guessed.");
    if(cy) {cy.elements().unselect(); const selected=cy.getElementById(id); if(selected.length) selected.select();}
    document.querySelectorAll("[data-item]").forEach(b=>b.setAttribute("aria-pressed",String(b.dataset.item===id)));
  }
  function itemButton(parent,item) {
    const b=append(parent,"button",item.label + " · " + (item.kind || item.method) +
      (item.raw.target === null ? " · unresolved" : ""));
    b.type="button"; b.dataset.item=item.id; b.setAttribute("aria-pressed","false"); b.addEventListener("click",()=>inspect(item.id));
  }
  function draw() {
    const filter=Object.fromEntries(controls.map(id=>[id,el(id).value]));
    visible=MemoryViewer.select(model,filter,data.limits);
    selected=null; origin=null;
    el("path-start").disabled=true; el("path-find").disabled=true;
    el("path-origin").textContent="Select two displayed nodes to trace their connection.";
    el("path-result").replaceChildren();
    el("selection-title").textContent="Select a node or relation.";
    el("selection").replaceChildren(); el("sources").replaceChildren(); el("record").textContent="No selection";
    el("graph-title").textContent=el("layer").selectedOptions[0].textContent;
    el("status").textContent=visible.nodes.length + " / " + visible.totalNodes + " matching nodes · " +
      visible.edges.length + " relations among displayed nodes" + (visible.truncated ? " · DISPLAY LIMITED — narrow filters." : "") +
      (visible.nodes.length ? "" : " · No nodes match these filters; this is not proof of absence.") +
      " · Documents: " + data.document.coverage + " · Code: " + (data.code ? data.code.coverage + " (captured; freshness unknown)" : "not requested") +
      (data.code && !data.mapping_compatible ? " · REVISION MISMATCH: mapping disabled." : "");
    el("nodes").replaceChildren(); el("edges").replaceChildren();
    visible.nodes.forEach(n=>itemButton(el("nodes"),n)); visible.edges.forEach(e=>itemButton(el("edges"),e));
    const elements=visible.nodes.map((n,i)=>({data:{id:n.id,label:n.label.length>40 ? n.label.slice(0,37)+"…" : n.label,layer:n.layer},
      position:{x:(i%8)*160,y:Math.floor(i/8)*120}}))
      .concat(visible.edges.filter(e=>e.target).map(e=>({data:{id:e.id,source:e.source,target:e.target,label:e.label,layer:e.layer}})));
    if(cy) cy.destroy();
    cy=cytoscape({container:el("graph"),elements,style:[
      {selector:"node",style:{"background-color":"#174ec2","label":"data(label)","color":"#152a41","font-size":14,"text-valign":"bottom","text-margin-y":7,"text-wrap":"wrap","text-max-width":130,"width":24,"height":24}},
      {selector:'node[layer = "code"]',style:{"background-color":"#087e80","shape":"round-rectangle"}},
      {selector:'node[layer = "hypothesis"]',style:{"background-color":"#8f3974","shape":"diamond"}},
      {selector:"edge",style:{"width":1.3,"line-color":"#9aaabe","target-arrow-color":"#9aaabe","target-arrow-shape":"triangle","curve-style":"bezier"}},
      {selector:'edge[layer = "mapping"]',style:{"line-style":"dashed","line-color":"#8f3974","target-arrow-color":"#8f3974"}},
      {selector:":selected",style:{"background-color":"#d76b00","line-color":"#d76b00","target-arrow-color":"#d76b00","border-width":3,"border-color":"#152a41"}}
    ],layout:{name:"cose",randomize:false,animate:false,padding:35,nodeDimensionsIncludeLabels:true,
      nodeRepulsion:12000,idealEdgeLength:120,componentSpacing:100,numIter:400},
      minZoom:0.1,maxZoom:3});
    cy.on("tap","node, edge",event=>inspect(event.target.id()));
  }
  controls.forEach(id=>el(id).addEventListener(id==="search"?"input":"change",draw));
  el("fit").addEventListener("click",()=>cy?.fit(undefined,35));
  el("path-start").addEventListener("click",()=>{origin=selected;el("path-origin").textContent="From: " + byId.get(origin).label;el("path-find").disabled=!selected;el("path-result").replaceChildren();});
  el("path-find").addEventListener("click",()=>{
    el("path-result").replaceChildren();
    const steps=MemoryViewer.path(visible,origin,selected);
    if(steps===null) append(el("path-result"),"li","No path in the displayed subgraph. Filtered, truncated or unobserved relations are not covered.");
    else if(!steps.length) append(el("path-result"),"li","Same node; zero steps.");
    else for(const step of steps) {
      const li=append(el("path-result"),"li",step.direction + " · ");
      const b=append(li,"button",byId.get(step.edge).label); b.type="button";b.addEventListener("click",()=>inspect(step.edge));
    }
    append(el("path-result"),"li","Navigation only — not causality, implementation proof or impact analysis.");
  });
  el("reset").addEventListener("click",()=>{controls.forEach(id=>el(id).value=id==="layer"?"document":"");draw();});
  // Refit only when the canvas size changes, not when an inspector record is selected.
  new ResizeObserver(()=>requestAnimationFrame(()=>{if(cy){cy.resize();cy.fit(undefined,35);}})).observe(el("graph"));
  draw();
})();

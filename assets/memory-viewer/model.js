/* Presentation-only IDs are prefixed; no canonical graph is modified. */
(function (root) {
  "use strict";
  function prepare(data) {
    const nodes = [], edges = [];
    const doc = data.document;
    const scope = n => n.identity ? n.identity.scope : n.repository || "";
    function addNode(n, layer) {
      nodes.push({id:layer + ":" + n.id, original:n.id, layer, label:n.label || n.name || n.claim || n.id,
        kind:n.kind, scope:scope(n), views:(n.data?.views || []).map(v=>v.view).concat(n.data?.view || []),
        method:n.provenance?.assertion_method || "", raw:n});
    }
    function addEdge(e, layer) {
      edges.push({id:layer + ":" + e.id, original:e.id, layer, label:e.relation,
        source:layer + ":" + e.source, target:e.target ? layer + ":" + e.target : null,
        method:e.provenance?.assertion_method || "", raw:e});
    }
    doc.nodes.forEach(n=>addNode(n,"document"));
    doc.edges.forEach(e=>addEdge(e,"document"));
    if(data.code) {
      data.code.nodes.forEach(n=>addNode(n,"code"));
      data.code.edges.forEach(e=>addEdge(e,"code"));
    }
    const fileViews = new Map();
    data.bridges.forEach(b=>b.files.forEach(file=>fileViews.set(file,[...(fileViews.get(file) || []),b.view])));
    for(const n of nodes) if(n.layer === "code") n.views = fileViews.get(n.original) || [];
    data.bridges.forEach((b,i)=>b.files.forEach((file,j)=>edges.push({
      id:"mapping:" + i + ":" + j, layer:"mapping", label:"declared location · not implementation proof",
      source:"document:" + b.component, target:"code:" + file, method:"derived", raw:b
    })));
    data.hypotheses.forEach((h,i)=>addNode({...h,id:String(i),kind:"hypothesis"},"hypothesis"));
    return {nodes,edges};
  }
  function select(all, filter={}, limits={nodes:250,edges:1500}) {
    const inLayer = n => filter.layer === "mapping" ? ["document","code"].includes(n.layer) : n.layer === (filter.layer || "document");
    const matchingEdges = all.edges.filter(e=>(filter.layer === "mapping" || e.layer === (filter.layer || "document")) &&
      (!filter.method || e.method === filter.method) && (!filter.relation || e.label === filter.relation));
    const incident = new Set(matchingEdges.flatMap(e=>[e.source,e.target]));
    let candidates = all.nodes.filter(n=>inLayer(n) && (!filter.scope || n.scope === filter.scope) &&
      (!filter.kind || n.kind === filter.kind) &&
      (!filter.method || n.method === filter.method || incident.has(n.id)) &&
      (!filter.relation || incident.has(n.id)) &&
      (!filter.view || n.views.includes(filter.view)) &&
      (!filter.search || (n.label + " " + n.original + " " + JSON.stringify(n.raw.data || n.raw.file || "")).toLowerCase().includes(filter.search.toLowerCase())));
    candidates = candidates.slice().sort((a,b)=>a.id < b.id ? -1 : a.id > b.id ? 1 : 0);
    const nodes = candidates.slice(0,Math.min(250,Math.max(1,limits.nodes)));
    const ids = new Set(nodes.map(n=>n.id));
    const eligibleEdges = matchingEdges.filter(e=>ids.has(e.source) && (!e.target || ids.has(e.target)));
    const edges = eligibleEdges.slice(0,Math.min(1500,Math.max(1,limits.edges)));
    return {nodes,edges,totalNodes:candidates.length,totalEdges:eligibleEdges.length,
      truncated:nodes.length < candidates.length || edges.length < eligibleEdges.length};
  }
  function path(visible, from, to) {
    const ids = new Set(visible.nodes.map(n=>n.id));
    if(!ids.has(from) || !ids.has(to)) return null;
    const queue=[from], seen=new Map([[from,null]]), adjacency=new Map();
    for(const e of visible.edges.slice().sort((a,b)=>a.id < b.id ? -1 : a.id > b.id ? 1 : 0)) {
      if(!e.target || !ids.has(e.source) || !ids.has(e.target)) continue;
      for(const [a,b,direction] of [[e.source,e.target,"forward"],[e.target,e.source,"reverse"]]) {
        if(!adjacency.has(a)) adjacency.set(a,[]);
        adjacency.get(a).push({node:b,edge:e.id,direction});
      }
    }
    for(let i=0;i<queue.length;i++) {
      const current=queue[i]; if(current===to) break;
      for(const step of adjacency.get(current) || []) if(!seen.has(step.node)) {
        seen.set(step.node,{previous:current,...step}); queue.push(step.node);
      }
    }
    if(!seen.has(to)) return null;
    const steps=[]; for(let at=to;at!==from;) {const step=seen.get(at);steps.unshift(step);at=step.previous;}
    return steps;
  }
  const api = {prepare,select,path};
  if(typeof module !== "undefined" && module.exports) module.exports = api;
  else root.MemoryViewer = api;
})(globalThis);

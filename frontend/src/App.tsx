import { useMemo, useState } from "react";

type Test = { id:string; name:string; source_path:string; framework:string; runner:string|null; suite:string|null; tags:string[]; metadata:Record<string,unknown> };
type Capability = { id:string; name:string; supported:boolean; description:string };
type ExecutionResult = { request_id:string; status:string; results:{test_id:string;outcome:string;duration_seconds:number|null;message:string|null}[]; error:string|null };

const API = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

function App(){
  const [projectPath,setProjectPath]=useState("");
  const [tests,setTests]=useState<Test[]>([]);
  const [capabilities,setCapabilities]=useState<Capability[]>([]);
  const [query,setQuery]=useState("");
  const [selected,setSelected]=useState<Test|null>(null);
  const [loading,setLoading]=useState(false);
  const [error,setError]=useState("");
  const [authorizeExecution,setAuthorizeExecution]=useState(false);
  const [executionLoading,setExecutionLoading]=useState(false);
  const [executionResult,setExecutionResult]=useState<ExecutionResult|null>(null);

  async function discover(){
    setLoading(true); setError(""); setSelected(null); setAuthorizeExecution(false); setExecutionResult(null);
    try{
      const body=JSON.stringify({project_path:projectPath});
      const [testResponse,capResponse]=await Promise.all([
        fetch(API+"/api/v1/tests/discovery",{method:"POST",headers:{"Content-Type":"application/json"},body}),
        fetch(API+"/api/v1/adapters/capabilities",{method:"POST",headers:{"Content-Type":"application/json"},body})
      ]);
      if(!testResponse.ok) throw new Error(await testResponse.text());
      if(!capResponse.ok) throw new Error(await capResponse.text());
      const testData=await testResponse.json(); const capData=await capResponse.json();
      setTests(testData.tests); setCapabilities(capData.capabilities);
    }catch(e){setError(e instanceof Error?e.message:"Discovery failed");}
    finally{setLoading(false);}
  }

  async function executeSelected(){
    if(!selected||!projectPath||!authorizeExecution||!selected.runner) return;
    setExecutionLoading(true); setError(""); setExecutionResult(null);
    try{
      const response=await fetch(API+"/api/v1/executions",{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({
          project_path:projectPath,
          runner:selected.runner,
          test_ids:[selected.id],
          authorize_execution:true,
          timeout_seconds:300
        })
      });
      const result=await response.json();
      if(!response.ok) throw new Error(result.detail??"Execution request failed");
      setExecutionResult(result as ExecutionResult);
    }catch(e){setError(e instanceof Error?e.message:"Execution failed");}
    finally{setExecutionLoading(false);}
  }

  const filtered=useMemo(()=>tests.filter(t=>[t.name,t.source_path,t.suite??"",...t.tags].join(" ").toLowerCase().includes(query.toLowerCase())),[tests,query]);
  const groups=useMemo(()=>filtered.reduce<Record<string,Test[]>>((acc,t)=>{const key=t.source_path; (acc[key]??=[]).push(t); return acc;},{}),[filtered]);

  return <div className="shell">
    <aside className="sidebar"><div className="brand"><span className="mark">AI</span><div><strong>Automation</strong><small>Command Center</small></div></div><nav>{["Overview","Test Explorer","Test Execution","Automation","Failures & Debugging","Reports & Analytics","Framework","AI Assistant"].map((x,i)=><button className={i===1?"nav active":"nav"} key={x}>{x}</button>)}</nav></aside>
    <main className="main">
      <header><div><p className="eyebrow">CONTROL PLANE / TEST EXPLORER</p><h1>Test Explorer</h1><p className="muted">Discover normalized tests from the connected project. Framework-specific parsing stays in adapters.</p></div><div className="status"><span className="dot"/>Discovery only</div></header>
      <section className="connect card"><div><label>Project path</label><input value={projectPath} onChange={e=>setProjectPath(e.target.value)} placeholder="/workspace/project" /></div><button onClick={discover} disabled={!projectPath||loading}>{loading?"Discovering…":"Discover tests"}</button></section>
      {error&&<div className="error">{error}</div>}
      <section className="metrics"><div className="metric"><span>Tests</span><strong>{tests.length}</strong></div><div className="metric"><span>Visible</span><strong>{filtered.length}</strong></div><div className="metric"><span>Runner</span><strong>{tests[0]?.runner??"—"}</strong></div><div className="metric"><span>Capabilities</span><strong>{capabilities.filter(c=>c.supported).length}/{capabilities.length}</strong></div></section>
      <section className="workspace card">
        <div className="explorer"><div className="toolbar"><input value={query} onChange={e=>setQuery(e.target.value)} placeholder="Search tests, files, tags…" /><span>{filtered.length} results</span></div><div className="tree">{Object.keys(groups).length===0?<div className="empty">No discovered tests. Connect a project and run discovery.</div>:Object.entries(groups).map(([file,items])=><div className="group" key={file}><div className="file">▾ <span>{file}</span><b>{items.length}</b></div>{items.map(t=><button className={selected?.id===t.id?"test selected":"test"} onClick={()=>{setSelected(t);setAuthorizeExecution(false);setExecutionResult(null);}} key={t.id}><span>✓</span><span>{t.name}</span>{t.tags.length>0&&<em>{t.tags.join(", ")}</em>}</button>)}</div>)}</div></div>
        <div className="detail">{selected?<><p className="eyebrow">TEST DETAIL</p><h2>{selected.name}</h2><div className="chips"><span>{selected.runner}</span><span>{selected.framework}</span><span>{selected.metadata.kind as string}</span></div><dl><dt>Source</dt><dd>{selected.source_path}:{String(selected.metadata.line??"")}</dd><dt>Suite</dt><dd>{selected.suite??"—"}</dd><dt>Tags</dt><dd>{selected.tags.length?selected.tags.join(", "):"—"}</dd><dt>Test ID</dt><dd>{selected.id}</dd></dl><div className="execution-controls"><label className="authorization"><input type="checkbox" checked={authorizeExecution} onChange={e=>setAuthorizeExecution(e.target.checked)} /> I authorize running this test; it may cause side effects in the selected project.</label><button onClick={executeSelected} disabled={!authorizeExecution||executionLoading||!selected.runner}>{executionLoading?"Running…":"Run selected test"}</button><small>Local pytest only · 300-second timeout · review the project before authorizing execution.</small>{executionResult&&<div className="execution-result"><strong>Run status: {executionResult.status}</strong>{executionResult.error&&<p>{executionResult.error}</p>}{executionResult.results.map(result=><div className="result-row" key={result.test_id}><span>{result.outcome}</span>{result.duration_seconds!==null&&<small>{result.duration_seconds.toFixed(2)}s</small>}{result.message&&<p>{result.message}</p>}</div>)}</div>}</div></>:<div className="empty detail-empty">Select a test to inspect its normalized metadata.</div>}</div>
      </section>
      <section className="card capabilities"><div><p className="eyebrow">ADAPTER CAPABILITIES</p><h2>What this project supports</h2></div><div className="cap-grid">{capabilities.map(c=><div className="cap" key={c.id}><span className={c.supported?"supported":"unsupported"}>{c.supported?"Supported":"Unsupported"}</span><strong>{c.name}</strong><small>{c.description}</small></div>)}</div></section>
    </main>
  </div>
}
export default App;

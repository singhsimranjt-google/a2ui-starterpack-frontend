import React from 'react';

// Props Interface for strict typing
interface A2UIRendererProps {
  payload: any[];
  onAction: (action: any) => void;
  appState: Record<string, any>;
  setAppState: React.Dispatch<React.SetStateAction<Record<string, any>>>;
  listData?: any[];
}

export function A2UIRenderer({ payload, onAction, appState, setAppState, listData = [] }: A2UIRendererProps) {
  if (!payload || !Array.isArray(payload)) return null;
  
  // 1. Locate the rendering events in the payload array
  const updateEvent = payload.find(p => p.surfaceUpdate);
  const renderEvent = payload.find(p => p.beginRendering);
  
  if (!updateEvent) return null;
  
  // 2. Build a quick-lookup map of all components by ID
  const comps = updateEvent.surfaceUpdate.components;
  const compMap: Record<string, any> = {};
  comps.forEach((c: any) => compMap[c.id] = c.component);
  
  // 3. Determine the root element to start rendering from
  const rootId = renderEvent ? renderEvent.beginRendering.root : (comps[0]?.id || "root");

  /**
   * The recursive rendering function.
   * @param id - The ID of the component to render.
   * @param dataContext - Local data context (used inside loops/lists).
   */
  const renderComp = (id: string, dataContext: any = null): React.ReactNode => {
    const c = compMap[id];
    if(!c) return null;
    
    // --- Data Binding Resolver ---
    // Resolves variables based on literal strings, local context, or global appState
    const resolveData = (pathObj: any) => {
      if (!pathObj) return "";
      if (pathObj.literalString) return pathObj.literalString;
      if (pathObj.path && dataContext && dataContext[pathObj.path]) return dataContext[pathObj.path];
      if (pathObj.path && appState && appState[pathObj.path]) return appState[pathObj.path];
      return pathObj.path || "Text";
    };

    // --- Layout Components ---
    if(c.Column) {
      return (
        <div key={id} style={{ display:'flex', flexDirection:'column', gap:'12px' }}>
          {c.Column.children.explicitList.map((childId: string) => renderComp(childId, dataContext))}
        </div>
      );
    }
    if(c.Row) {
      return (
        <div key={id} style={{ display:'flex', flexDirection:'row', gap:'15px', alignItems:'center', flexWrap:'wrap' }}>
          {c.Row.children.explicitList.map((childId: string) => renderComp(childId, dataContext))}
        </div>
      );
    }
    if(c.Card) {
      return (
        <div key={id} className="a2ui-card" style={{ marginTop: '12px', border: '1px solid #e0e0e0', padding: '20px', borderRadius: '12px', background: 'white', boxShadow: '0 2px 8px rgba(0,0,0,0.04)', width: '100%', boxSizing: 'border-box' }}>
          {renderComp(c.Card.child, dataContext)}
        </div>
      );
    }

    // --- Iteration Components ---
    if(c.List) {
      return (
        <div key={id} style={{ display:'flex', flexDirection:'column', gap:'15px' }}>
          {listData.map((item, idx) => (
            <div key={`${id}-${idx}`}>
              {renderComp(c.List.template, item)}
            </div>
          ))}
          {listData.length === 0 && <div style={{color: '#888'}}>No list data provided.</div>}
        </div>
      );
    }

    // --- UI Elements ---
    if(c.Text && c.Text.text) {
      const text = resolveData(c.Text.text);
      if(c.Text.usageHint === 'h1') return <h1 key={id} style={{margin: '0 0 10px 0'}}>{text}</h1>;
      if(c.Text.usageHint === 'h2') return <h2 key={id} style={{margin: '0 0 10px 0'}}>{text}</h2>;
      return <div key={id}><strong>{text}</strong></div>;
    }
    
    if(c.Image) {
      const url = resolveData(c.Image.url) || "";
      return (
        <div key={id} style={{ width:'80px', height:'80px', background:'#eee', display:'flex', alignItems:'center', justifyContent:'center', borderRadius:'8px', overflow:'hidden', flexShrink: 0 }}>
          <img src={url} alt="img" style={{ width:'100%', height:'100%', objectFit:'cover', display: url ? 'block' : 'none' }}/>
        </div>
      );
    }
    
    // --- Interactive Inputs ---
    if(c.Button) {
      const resolvedContext: Record<string, any> = {};
      if (c.Button.action.context) {
        Object.keys(c.Button.action.context).forEach(k => {
          resolvedContext[k] = resolveData(c.Button.action.context[k]);
        });
      }
      const resolvedAction = { ...c.Button.action, context: resolvedContext };
      return (
        <button 
          key={id} 
          style={{ background: 'var(--primary-color)', color: 'white', padding: '10px 24px', border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '15px', fontWeight: 500 }}
          onClick={() => onAction(resolvedAction)}
        >
          {c.Button.label.literalString}
        </button>
      );
    }
    
    if(c.TextField) {
       const path = c.TextField.text?.path;
       return (
         <div key={id}>
           <label style={{ fontWeight: 500, fontSize: '14px', color: '#555' }}>{c.TextField.label.literalString}</label><br/>
           <input 
             style={{ width: '100%', padding: '10px 12px', margin: '8px 0 16px 0', border: '1px solid #ccc', borderRadius: '6px', boxSizing: 'border-box', fontSize: '14px' }}
             type="text" 
             value={appState[path] || ""}
             onChange={e => {
               if(path && setAppState) setAppState(prev => ({...prev, [path]: e.target.value}));
             }} 
           />
         </div>
       );
    }
    
    if(c.DateTimeInput) {
       const path = c.DateTimeInput.value?.path;
       return (
         <div key={id}>
           <label style={{ fontWeight: 500, fontSize: '14px', color: '#555' }}>{c.DateTimeInput.label.literalString}</label><br/>
           <input 
             style={{ width: '100%', padding: '10px 12px', margin: '8px 0 16px 0', border: '1px solid #ccc', borderRadius: '6px', boxSizing: 'border-box', fontSize: '14px' }}
             type="datetime-local" 
             value={appState[path] || ""}
             onChange={e => {
               if(path && setAppState) setAppState(prev => ({...prev, [path]: e.target.value}));
             }} 
           />
         </div>
       );
    }
    
    if(c.RadioButtonGroup) {
      const path = c.RadioButtonGroup.selectedValue?.path;
      return (
        <div key={id} style={{marginBottom: '15px'}}>
          <label style={{ fontWeight: 500, fontSize: '14px', color: '#555' }}>{c.RadioButtonGroup.label?.literalString || "Select Option"}</label><br/>
          <div style={{ marginTop: '8px' }}>
            {c.RadioButtonGroup.options?.map((opt: any, i: number) => (
              <label key={i} style={{marginRight: '20px', fontWeight: 'normal', cursor: 'pointer', fontSize: '14px', color: '#555'}}>
                <input 
                  type="radio" 
                  name={id} 
                  value={opt.value}
                  checked={appState[path] === opt.value}
                  onChange={e => {
                     if(path && setAppState) setAppState(prev => ({...prev, [path]: e.target.value}));
                  }} 
                /> 
                <span style={{marginLeft: '4px'}}>{opt.label.literalString}</span>
              </label>
            ))}
          </div>
        </div>
      );
    }
    
    // Fallback for unimplemented tags
    return <div key={id} style={{color:'red', border: '1px dashed red', padding: '5px'}}>Unknown Component: {Object.keys(c)[0]}</div>;
  }
  
  // Render the root element
  return <div className="a2ui-framework-container">{renderComp(rootId)}</div>;
}

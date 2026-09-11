import { useState, useEffect, useRef } from 'react';
import { A2UIRenderer } from './components/A2UIRenderer';
import './index.css';

// Styling for the App container
const styles = {
  chatContainer: {
    maxWidth: '700px',
    margin: '0 auto',
    background: 'var(--card-bg)',
    borderRadius: '12px',
    boxShadow: '0 4px 20px rgba(0,0,0,0.08)',
    padding: '25px',
    minHeight: '600px',
    display: 'flex',
    flexDirection: 'column' as const,
  },
  chatHistory: {
    flexGrow: 1,
    overflowY: 'auto' as const,
    paddingBottom: '20px',
  },
  msgUser: {
    margin: '15px 0',
    display: 'flex',
    flexDirection: 'column' as const,
    alignItems: 'flex-end' as const,
  },
  msgAgent: {
    margin: '15px 0',
    display: 'flex',
    flexDirection: 'column' as const,
    alignItems: 'flex-start' as const,
  },
  bubbleUser: {
    display: 'inline-block',
    padding: '12px 18px',
    borderRadius: '18px',
    maxWidth: '85%',
    lineHeight: 1.5,
    background: 'var(--bubble-user)',
    color: 'white',
    borderBottomRightRadius: '4px',
  },
  bubbleAgent: {
    display: 'inline-block',
    padding: '12px 18px',
    borderRadius: '18px',
    maxWidth: '85%',
    lineHeight: 1.5,
    background: 'var(--bubble-agent)',
    color: 'black',
    borderBottomLeftRadius: '4px',
  },
  chatInputArea: {
    display: 'flex',
    gap: '10px',
    marginTop: '20px',
    borderTop: '1px solid #eee',
    paddingTop: '20px',
  },
  input: {
    flexGrow: 1,
    padding: '12px',
    border: '1px solid #ddd',
    borderRadius: '24px',
    outline: 'none',
    paddingLeft: '20px',
  },
  btn: {
    background: 'var(--primary-color)',
    color: 'white',
    padding: '10px 24px',
    border: 'none',
    borderRadius: '24px',
    cursor: 'pointer',
    fontSize: '15px',
    fontWeight: 500,
  }
};

// Types for the Chat History
type ChatMessage = {
  role: 'user' | 'agent';
  text?: string;
  payload?: any; // The A2UI JSON payload
};

export default function App() {
  const [history, setHistory] = useState<ChatMessage[]>([]);
  const [appState, setAppState] = useState<Record<string, any>>({});
  const [inputText, setInputText] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom of chat
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [history]);

  // Generic Network Request Handler (SSE)
  const sendRequest = async (payload: any) => {
    setIsLoading(true);
    try {
      // Point this to your actual Google ADK Python backend URL
      const response = await fetch('http://localhost:8080/v1/agent/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let done = false;
      
      while (!done && reader) {
        const { value, done: doneReading } = await reader.read();
        done = doneReading;
        if (value) {
          const chunk = decoder.decode(value, { stream: true });
          
          // Basic Server-Sent Events (SSE) string parsing
          const lines = chunk.split('\n');
          for (const line of lines) {
            if (line.trim().startsWith('data: ')) {
              try {
                const data = JSON.parse(line.replace('data: ', '').trim());
                if (data.part) {
                   setHistory(h => [...h, { role: 'agent', payload: data.part.data }]);
                }
              } catch(e) {
                // Ignore incomplete JSON chunks in this simple parser
              }
            }
          }
        }
      }
    } catch (e) {
      console.error("Backend error:", e);
      setHistory(h => [...h, { role: 'agent', text: "Error connecting to backend! Ensure your server is running." }]);
    } finally {
      setIsLoading(false);
    }
  };

  // Handler for sending text chat messages
  const handleSendMessage = () => {
    if (!inputText.trim()) return;
    setHistory(h => [...h, { role: 'user', text: inputText }]);
    sendRequest({ text: inputText });
    setInputText("");
  };

  // Handler for A2UI Action Events (Button Clicks)
  const handleAction = (action: any) => {
    console.log("A2UI Action Triggered:", action);
    
    // Log the action to the chat history for visual feedback
    setHistory(h => [...h, { role: 'user', text: `Action Triggered: ${action.name}` }]);
    
    // Send the structured action back to the LLM agent
    sendRequest({ action: action });
  };
  
  // Generic mock data for demonstration purposes
  const mockListData = [
    { id: "item1", name: "Apple MacBook Air M3", price: "$1,099", imageUrl: "https://store.storeimages.cdn-apple.com/4982/as-images.apple.com/is/mba13-midnight-select-202402" },
    { id: "item2", name: "Dell XPS 13", price: "$1,299", imageUrl: "https://i.dell.com/is/image/DellContent/content/dam/ss2/product-images/dell-client-products/notebooks/xps-notebooks/13-9340/media-gallery/silver/touch/notebook-xps-13-9340-t-sl-gallery-1.png" }
  ];

  return (
    <div style={styles.chatContainer}>
      <h2 style={{ color: 'var(--primary-color)', textAlign: 'center', margin: '0 0 20px 0' }}>
        A2UI React Starter Framework
      </h2>
      
      <div style={styles.chatHistory}>
        {history.length === 0 ? (
          <div style={{ textAlign:'center', marginTop:'150px', color: '#666' }}>
            <p>Welcome to the A2UI Starter Kit!</p>
            <p>Type a message below to start talking to your Agent.</p>
            <button style={{...styles.btn, marginTop: '20px'}} onClick={() => {
              setHistory([{ role: 'user', text: "Show me top rated laptops" }]);
              sendRequest({ text: "Show me top rated laptops" });
            }}>
              Or Run Example Demo
            </button>
          </div>
        ) : (
          history.map((msg, i) => (
            <div key={i} style={msg.role === 'user' ? styles.msgUser : styles.msgAgent}>
              {msg.text && <div style={msg.role === 'user' ? styles.bubbleUser : styles.bubbleAgent}>{msg.text}</div>}
              {msg.payload && (
                <A2UIRenderer 
                  payload={msg.payload} 
                  onAction={handleAction} 
                  appState={appState} 
                  setAppState={setAppState} 
                  listData={mockListData}
                />
              )}
            </div>
          ))
        )}
        {isLoading && (
          <div style={styles.msgAgent}>
            <div style={{...styles.bubbleAgent, fontStyle: 'italic', color: '#666', background: 'transparent'}}>Agent is typing...</div>
          </div>
        )}
        <div ref={chatEndRef} />
      </div>

      <div style={styles.chatInputArea}>
        <input 
          style={styles.input}
          type="text" 
          placeholder="Ask the agent to do something..." 
          value={inputText}
          onChange={e => setInputText(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleSendMessage()}
          disabled={isLoading}
        />
        <button 
          style={{...styles.btn, opacity: (isLoading || !inputText.trim()) ? 0.5 : 1}} 
          onClick={handleSendMessage} 
          disabled={isLoading || !inputText.trim()}
        >
          Send
        </button>
      </div>
    </div>
  );
}

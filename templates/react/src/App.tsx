import React, { useState } from 'react';
import { Bot, Send, Sparkles } from 'lucide-react';
import { A2UIRenderer, A2UIComponentPayload } from './components/A2UIRenderer';
import './App.css';

export function App() {
  const [prompt, setPrompt] = useState('');
  const [loading, setLoading] = useState(false);
  const [components, setComponents] = useState<A2UIComponentPayload[]>([
    {
      id: 'init-1',
      kind: 'metric_card',
      title: 'Google ADK Agent Ready',
      summary: 'Connected to Gemini reasoning pipeline. Streaming A2UI action components.',
      timestamp: new Date().toLocaleTimeString(),
      data: {
        engine: 'Google ADK 1.0',
        model: 'gemini-2.5-flash',
        mode: 'reactive-stream'
      }
    },
    {
      id: 'init-2',
      kind: 'action_panel',
      title: 'Available Agent Capabilities',
      summary: 'Dynamic Form Generation, Statistical Cards, Interactive Decision Trees.',
      timestamp: new Date().toLocaleTimeString(),
      data: {
        actions: ['generate_report', 'analyze_dataset', 'render_ui_form']
      }
    }
  ]);

  const handleSend = () => {
    if (!prompt.trim() || loading) return;

    setLoading(true);
    const newComponent: A2UIComponentPayload = {
      id: `comp-${Date.now()}`,
      kind: 'action_panel',
      title: `Agent Reaction: ${prompt}`,
      summary: `Synthesized A2UI JSON response for your query.`,
      timestamp: new Date().toLocaleTimeString(),
      data: {
        userPrompt: prompt,
        executionStatus: 'COMPLETED',
        suggestedActions: ['Approve', 'Modify Parameters', 'Export']
      }
    };

    setTimeout(() => {
      setComponents((prev) => [newComponent, ...prev]);
      setPrompt('');
      setLoading(false);
    }, 450);
  };

  return (
    <div className="app-layout">
      {/* Header */}
      <header className="top-bar">
        <div className="brand-section">
          <div className="brand-icon">
            <Bot size={26} />
          </div>
          <div>
            <h1>{{PROJECT_TITLE}}</h1>
            <span className="brand-badge">A2UI React + Vite Engine</span>
          </div>
        </div>

        <div className="status-badge">
          <span className="dot"></span>
          <span>ADK Streaming Online</span>
        </div>
      </header>

      {/* Main Container */}
      <main style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
        {/* Interaction Panel */}
        <section className="prompt-card">
          <h2>Send Intent to Google ADK Agent</h2>
          <p className="prompt-desc">
            Type any command or query. The agent will process it and emit rich A2UI schema components.
          </p>

          <div className="search-box">
            <input
              type="text"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSend()}
              placeholder="e.g. Synthesize a live performance dashboard or user feedback form..."
              disabled={loading}
            />
            <button onClick={handleSend} disabled={loading || !prompt.trim()}>
              {loading ? <Sparkles className="animate-spin" size={18} /> : <Send size={18} />}
              <span>{loading ? 'Thinking...' : 'Dispatch'}</span>
            </button>
          </div>
        </section>

        {/* Dynamic UI Stream */}
        <section className="a2ui-stream-section">
          <h2>Emitted Agent A2UI Stream</h2>
          <div className="component-grid">
            {components.map((comp) => (
              <A2UIRenderer key={comp.id} component={comp} />
            ))}
          </div>
        </section>
      </main>
    </div>
  );
}

export default App;

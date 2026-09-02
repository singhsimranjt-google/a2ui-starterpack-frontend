import React, { useState, useEffect, useRef } from 'react';
import { A2uiSurface } from '@a2ui/react/v0_9';
import { materialCatalog } from './catalogs/MaterialBasicCatalog';
import { MessageProcessor } from '@a2ui/web_core/v0_9';
import { marked } from 'marked';
import DOMPurify from 'dompurify';

import { ChatHeader } from './components/chat-header/ChatHeader';
import { ChatInput } from './components/chat-input/ChatInput';
import { AgentLoader } from './components/agent-loader/AgentLoader';
import { ChatMessage, AgentStatus } from './models/chat.types';

import './App.css';

// 1. Create a global MessageProcessor configured with our custom materialCatalog
const processor = new MessageProcessor([materialCatalog], (action) => {
  console.log("Action dispatched from surface:", action);
});

export function App() {
  const [agentStatus, setAgentStatus] = useState<AgentStatus>('connected');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // We need a dummy piece of state just to force a re-render when a surface is created/updated
  const [, setForceRender] = useState(0);

  useEffect(() => {
    // Listen for new surfaces being created by the Python agent
    const sub = processor.onSurfaceCreated((surface) => {
      setForceRender(prev => prev + 1); // Force react to re-render
    });

    // Auto scroll
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });

    return () => sub.unsubscribe();
  }, [messages, agentStatus]);

  useEffect(() => {
    // Initial greeting
    sendInitialGreeting();
  }, []);

  const sendInitialGreeting = async () => {
    setAgentStatus('executing');
    try {
      const data = await postChat('Hello');
      const surfaceId = processA2uiPayload(data.a2ui);
      setMessages([{
        sender: 'agent',
        text: data.text || 'Hello! 👋 I am your Weather Agent.',
        timestamp: new Date().toLocaleTimeString(),
        surfaceId,
      }]);
      setAgentStatus('connected');
    } catch (err) {
      console.error('Failed to fetch initial greeting:', err);
      setMessages([{
        sender: 'agent',
        text: '⚠️ Could not connect to Weather Agent at `http://127.0.0.1:8080/api/agent/chat`. Please start the backend service.',
        timestamp: new Date().toLocaleTimeString(),
      }]);
      setAgentStatus('idle');
    }
  };

  const handleSend = async (prompt: string) => {
    const text = prompt.trim();
    if (!text) return;

    setMessages(prev => [...prev, {
      sender: 'user',
      text,
      timestamp: new Date().toLocaleTimeString(),
    }]);

    setAgentStatus('executing');

    try {
      const data = await postChat(text);
      const surfaceId = processA2uiPayload(data.a2ui);

      setMessages(prev => [...prev, {
        sender: 'agent',
        text: data.text || 'Response received from weather agent.',
        timestamp: new Date().toLocaleTimeString(),
        surfaceId,
      }]);
      setAgentStatus('connected');
    } catch (err) {
      console.error('Failed to communicate with agent backend:', err);
      setMessages(prev => [...prev, {
        sender: 'agent',
        text: `⚠️ Could not reach Weather Agent at \`http://127.0.0.1:8080\`. Please ensure the backend is running.`,
        timestamp: new Date().toLocaleTimeString(),
      }]);
      setAgentStatus('idle');
    }
  };

  const postChat = async (prompt: string): Promise<any> => {
    const response = await fetch("http://127.0.0.1:8080/api/agent/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt })
    });
    if (!response.ok) {
      throw new Error(`Agent backend responded with status: ${response.status}`);
    }
    return response.json();
  };

  const processA2uiPayload = (a2ui?: any[]): string | undefined => {
    if (!a2ui || !Array.isArray(a2ui) || a2ui.length === 0) {
      return undefined;
    }
    try {
      let surfaceId: string | undefined;
      for (const msg of a2ui) {
        if (msg.createSurface?.surfaceId) {
          surfaceId = msg.createSurface.surfaceId;
          break;
        }
        if (msg.updateComponents?.surfaceId) {
          surfaceId = msg.updateComponents.surfaceId;
          break;
        }
      }
      processor.processMessages(a2ui);
      return surfaceId;
    } catch (error) {
      console.error('A2UI message processing failed:', error);
      return undefined;
    }
  };

  const createMarkup = (text: string) => {
    return { __html: DOMPurify.sanitize(marked.parse(text, { async: false }) as string) };
  };

  return (
    <div className="app-layout">
      {/* Top Navigation Bar */}
      <ChatHeader title="Weather Agent UI" status={agentStatus} />

      {/* Chat Workspace */}
      <main className="chat-container">
        <div className="messages-stream">
          {messages.map((msg, idx) => (
            <div key={idx} className={`message-row ${msg.sender}`}>
              {/* Metadata: Sender and Timestamp */}
              <div className="sender-info">
                <span className="sender-name">{msg.sender === 'user' ? 'You' : 'Weather Agent'}</span>
                <span className="time-stamp">{msg.timestamp}</span>
              </div>

              {/* Horizontal Bubble Row: Avatar + Message Body on same level */}
              <div className={`message-bubble-wrapper ${msg.sender}`}>
                <div className={`avatar ${msg.sender}`}>
                  {msg.sender === 'user' && (
                    <svg className="google-user-avatar" viewBox="0 0 24 24" width="22" height="22">
                      <path fill="#1a73e8" d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z" />
                    </svg>
                  )}
                  {msg.sender === 'agent' && (
                    <svg className="adk-agent-avatar" viewBox="0 0 24 24" width="22" height="22">
                      <defs>
                        <linearGradient id="adkAvatarGradReact" x1="0%" y1="0%" x2="100%" y2="100%">
                          <stop offset="0%" stopColor="#1a73e8" />
                          <stop offset="60%" stopColor="#4285f4" />
                          <stop offset="100%" stopColor="#34a853" />
                        </linearGradient>
                      </defs>
                      <path fill="url(#adkAvatarGradReact)" d="M19 9l1.25-2.75L23 5l-2.75-1.25L19 1l-1.25 2.75L15 5l2.75 1.25L19 9zm-7.5.5L9 4 6.5 9.5 1 12l5.5 2.5L9 20l2.5-5.5L17 12l-5.5-2.5zM19 15l-1.25 2.75L15 19l2.75 1.25L19 23l1.25-2.75L23 19l-2.75-1.25L19 15z" />
                    </svg>
                  )}
                </div>

                <div className="message-content">
                  {/* Render A2UI Component Surface if present and successfully processed */}
                  {msg.surfaceId && (
                    <div className="a2ui-surface-wrapper">
                      <A2uiSurface surface={processor.model.getSurface(msg.surfaceId)!} />
                    </div>
                  )}

                  {/* Fallback: Display markdown-rendered text only when A2UI surface is not present */}
                  {!msg.surfaceId && msg.text && (
                    <div
                      className="text-body markdown-content"
                      dangerouslySetInnerHTML={createMarkup(msg.text)}
                    />
                  )}
                </div>
              </div>
            </div>
          ))}

          {/* Agent Thinking / Loading Component */}
          {agentStatus === 'executing' && <AgentLoader />}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <ChatInput onSend={handleSend} disabled={agentStatus === 'executing'} />
      </main>
    </div>
  );
}

export default App;

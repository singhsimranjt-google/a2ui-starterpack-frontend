import os
import re
import json

def extract_css(angular_file):
    with open(angular_file, 'r') as f:
        content = f.read()
    match = re.search(r'styles: \[`(.*?)`\]', content, re.DOTALL)
    if match:
        css = match.group(1).strip()
        css = css.replace(':host', '.component-host')
        return css
    return ""

def write_react_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        f.write(content)

# 1. Models
write_react_file('../react/src/models/chat.types.ts', """
export type AgentStatus = 'idle' | 'executing' | 'connected' | 'error';

export interface ChatMessage {
  sender: 'user' | 'agent';
  text?: string;
  timestamp: string;
  surfaceId?: string;
}
""")

# 2. ChatHeader
css = extract_css('src/app/components/chat-header/chat-header.component.ts')
write_react_file('../react/src/components/chat-header/ChatHeader.css', css)
write_react_file('../react/src/components/chat-header/ChatHeader.tsx', """
import React from 'react';
import './ChatHeader.css';

interface Props {
  title: string;
  status: 'idle' | 'executing' | 'connected' | 'error';
}

export function ChatHeader({ title, status }: Props) {
  return (
    <header className="app-header component-host">
      <div className="brand-group">
        <div className="logo-icon">
          <svg className="adk-logo" viewBox="0 0 24 24" width="28" height="28">
            <path
              fill="#1a73e8"
              d="M19 9l1.25-2.75L23 5l-2.75-1.25L19 1l-1.25 2.75L15 5l2.75 1.25L19 9zm-7.5.5L9 4 6.5 9.5 1 12l5.5 2.5L9 20l2.5-5.5L17 12l-5.5-2.5zM19 15l-1.25 2.75L15 19l2.75 1.25L19 23l1.25-2.75L23 19l-2.75-1.25L19 15z"
            />
          </svg>
        </div>
        <div className="title-details">
          <h1>{title}</h1>
        </div>
      </div>
      <div className="status-indicator">
        <span className={`status-dot ${status}`}></span>
        <span className="status-label">Agent: {status.toUpperCase()}</span>
      </div>
    </header>
  );
}
""")

# 3. ChatInput
css = extract_css('src/app/components/chat-input/chat-input.component.ts')
write_react_file('../react/src/components/chat-input/ChatInput.css', css)
write_react_file('../react/src/components/chat-input/ChatInput.tsx', """
import React, { useState } from 'react';
import './ChatInput.css';

interface Props {
  onSend: (text: string) => void;
  disabled: boolean;
}

export function ChatInput({ onSend, disabled }: Props) {
  const [text, setText] = useState('');

  const handleSend = () => {
    if (disabled || !text.trim()) return;
    onSend(text);
    setText('');
  };

  return (
    <div className="input-container component-host">
      <div className="input-bar">
        <input
          type="text"
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Ask 'What is the weather in Delhi?' to see the A2UI weather card..."
          disabled={disabled}
        />
        <button
          onClick={handleSend}
          disabled={disabled || !text.trim()}
          className="send-btn"
        >
          {disabled ? 'Checking...' : 'Send'}
        </button>
      </div>
    </div>
  );
}
""")

# 4. AgentLoader
css = extract_css('src/app/components/agent-loader/agent-loader.component.ts')
write_react_file('../react/src/components/agent-loader/AgentLoader.css', css)
write_react_file('../react/src/components/agent-loader/AgentLoader.tsx', """
import React from 'react';
import './AgentLoader.css';

export function AgentLoader() {
  return (
    <div className="message-row agent component-host">
      <div className="sender-info">
        <span className="sender-name">Weather Agent</span>
        <span className="thinking-label">Thinking...</span>
      </div>

      <div className="message-bubble-wrapper agent loader-bubble">
        <div className="avatar agent">
          <svg className="adk-agent-avatar rotating" viewBox="0 0 24 24" width="22" height="22">
            <defs>
              <linearGradient id="adkLoaderGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stop-color="#1a73e8" />
                <stop offset="60%" stop-color="#4285f4" />
                <stop offset="100%" stop-color="#34a853" />
              </linearGradient>
            </defs>
            <path fill="url(#adkLoaderGrad)" d="M19 9l1.25-2.75L23 5l-2.75-1.25L19 1l-1.25 2.75L15 5l2.75 1.25L19 9zm-7.5.5L9 4 6.5 9.5 1 12l5.5 2.5L9 20l2.5-5.5L17 12l-5.5-2.5zM19 15l-1.25 2.75L15 19l2.75 1.25L19 23l1.25-2.75L23 19l-2.75-1.25L19 15z"/>
          </svg>
        </div>

        <div className="loader-container">
          <div className="dot dot-blue"></div>
          <div className="dot dot-red"></div>
          <div className="dot dot-yellow"></div>
          <div className="dot dot-green"></div>
        </div>
      </div>
    </div>
  );
}
""")

print("Successfully wrote components.")

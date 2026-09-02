
import React from 'react';
import './AgentLoader.css';

export function AgentLoader() {
  return (
    <div className="message-row agent">
      <div className="sender-info">
        <span className="sender-name">Weather Agent</span>
        <span className="thinking-label">Thinking...</span>
      </div>

      <div className="message-bubble-wrapper agent loader-bubble">
        <div className="avatar agent">
          <svg className="adk-agent-avatar rotating" viewBox="0 0 24 24" width="22" height="22">
            <defs>
              <linearGradient id="adkLoaderGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#1a73e8" />
                <stop offset="60%" stopColor="#4285f4" />
                <stop offset="100%" stopColor="#34a853" />
              </linearGradient>
            </defs>
            <path fill="url(#adkLoaderGrad)" d="M19 9l1.25-2.75L23 5l-2.75-1.25L19 1l-1.25 2.75L15 5l2.75 1.25L19 9zm-7.5.5L9 4 6.5 9.5 1 12l5.5 2.5L9 20l2.5-5.5L17 12l-5.5-2.5zM19 15l-1.25 2.75L15 19l2.75 1.25L19 23l1.25-2.75L23 19l-2.75-1.25L19 15z" />
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

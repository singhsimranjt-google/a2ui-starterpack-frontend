
import { useState } from 'react';
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
    <div className="input-container">
      <div className="input-bar">
        <input
          type="text"
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Say 'Hi' to see the A2UI Agent response..."
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

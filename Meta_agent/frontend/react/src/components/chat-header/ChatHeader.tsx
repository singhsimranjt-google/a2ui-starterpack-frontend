
import './ChatHeader.css';

interface Props {
  title: string;
  status: 'idle' | 'executing' | 'connected' | 'error';
}

export function ChatHeader({ title, status }: Props) {
  return (
    <header className="app-header">
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

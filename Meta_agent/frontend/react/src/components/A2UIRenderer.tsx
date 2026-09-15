import React from 'react';
import { Sparkles, Terminal, Activity, CheckCircle2 } from 'lucide-react';

export interface A2UIComponentPayload {
  id: string;
  kind: 'metric_card' | 'action_panel' | 'code_snippet' | 'log_stream';
  title: string;
  summary: string;
  data?: Record<string, any>;
  timestamp: string;
}

interface A2UIRendererProps {
  component: A2UIComponentPayload;
}

export const A2UIRenderer: React.FC<A2UIRendererProps> = ({ component }) => {
  const getIcon = () => {
    switch (component.kind) {
      case 'metric_card':
        return <Activity className="w-5 h-5 text-blue-400" />;
      case 'action_panel':
        return <Sparkles className="w-5 h-5 text-purple-400" />;
      case 'code_snippet':
        return <Terminal className="w-5 h-5 text-emerald-400" />;
      default:
        return <CheckCircle2 className="w-5 h-5 text-cyan-400" />;
    }
  };

  return (
    <div style={{
      background: '#111827',
      border: '1px solid #1f2937',
      borderRadius: '14px',
      padding: '1.5rem',
      display: 'flex',
      flexDirection: 'column',
      gap: '0.85rem'
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          {getIcon()}
          <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#60a5fa', textTransform: 'uppercase' }}>
            {component.kind.replace('_', ' ')}
          </span>
        </div>
        <span style={{ fontSize: '0.75rem', color: '#6b7280', fontFamily: 'monospace' }}>
          {component.timestamp}
        </span>
      </div>

      <h3 style={{ fontSize: '1.1rem', fontWeight: 600, color: '#f3f4f6' }}>
        {component.title}
      </h3>

      <p style={{ fontSize: '0.925rem', color: '#9ca3af', lineHeight: 1.5 }}>
        {component.summary}
      </p>

      {component.data && (
        <div style={{
          background: '#030712',
          border: '1px solid #1f2937',
          borderRadius: '8px',
          padding: '0.75rem',
          marginTop: '0.25rem',
          overflowX: 'auto'
        }}>
          <pre style={{ margin: 0, fontFamily: 'monospace', fontSize: '0.8rem', color: '#a5b4fc' }}>
            {JSON.stringify(component.data, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
};

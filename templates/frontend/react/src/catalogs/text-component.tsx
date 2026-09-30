/**
 * Text for the A2UI catalog (React), rendered with the same DOM + class names
 * as the Angular renderer (<div class="a2ui-text h2"><h2>..</h2></div>,
 * <span class="a2ui-text caption">..</span>) so ONE stylesheet (index.css)
 * styles both apps.
 *
 * Why: the stock React Text uses CSS-module classes that are empty in this
 * build (class="undefined ..."), so index.css never matched, and captions were
 * wrapped in <em>, which the browser shows in italics.
 */
import React from 'react';
import { createComponentImplementation, useMarkdownRenderer } from '@a2ui/react/v0_9';
import { TextApi } from '@a2ui/web_core/v0_9';

const HEADINGS = new Set(['h1', 'h2', 'h3', 'h4', 'h5']);

/** Body text may contain markdown (**bold**, lists); headings and captions never do. */
function useMarkdownHtml(text: string, enabled: boolean): string | null {
  const render = useMarkdownRenderer();
  const [html, setHtml] = React.useState<string | null>(null);
  React.useEffect(() => {
    if (!enabled || !render) {
      setHtml(null);
      return;
    }
    let active = true;
    render(text)
      .then((h) => active && setHtml(h))
      .catch(() => active && setHtml(null));
    return () => {
      active = false;
    };
  }, [text, render, enabled]);
  return html;
}

export const MaterialText = createComponentImplementation(TextApi, ({ props }) => {
  const p = props as any;
  const text = typeof p.text === 'string' ? p.text : String(p.text ?? '');
  const variant: string = p.variant || 'body';
  const isHeading = HEADINGS.has(variant);
  const isCaption = variant === 'caption';
  const html = useMarkdownHtml(text, !isHeading && !isCaption);
  const style: React.CSSProperties | undefined =
    typeof p.weight === 'number' ? { flex: p.weight, minWidth: 0 } : undefined;
  const className = `a2ui-text ${variant}`;

  if (isHeading) {
    const Tag = variant as 'h1';
    return (
      <div className={className} style={style}>
        <Tag>{text}</Tag>
      </div>
    );
  }
  if (isCaption) {
    return <span className={className} style={style}>{text}</span>;
  }
  return html !== null ? (
    <div className={`${className} markdown-content`} style={style} dangerouslySetInnerHTML={{ __html: html }} />
  ) : (
    <div className={className} style={style}>{text}</div>
  );
});


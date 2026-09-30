/**
 * Grid for the A2UI catalog (React port of the Angular MaterialGridComponent).
 *
 * The agent only says "these are items" (plus an optional column count the user
 * asked for). Every pixel decision - gap, minimum card width, collapsing on
 * narrow screens - lives here in the renderer, never in the agent's JSON.
 */
import React from 'react';
import { z } from 'zod';
import { createComponentImplementation } from '@a2ui/react/v0_9';
import { childList } from '@a2ui/web_core/v0_9';
import { Common } from './vega-components';

export const GridApi = {
  name: 'Grid',
  schema: z.object({
    ...Common,
    children: childList(),
    columns: z.number().int().min(1).max(4).optional(),
  }),
};

const GRID_CSS = `
.a2ui-grid-host { display: block; width: 100%; margin-bottom: 12px; }
.a2ui-grid {
  --gap: var(--a2ui-grid-gap, 12px);
  --min: var(--a2ui-grid-min, 180px);
  display: grid;
  gap: var(--gap);
  grid-template-columns: repeat(auto-fill, minmax(var(--min), 1fr));
}
/* At most --cols columns; drops to fewer on its own when a column would be narrower than --min. */
.a2ui-grid.fixed {
  grid-template-columns: repeat(auto-fill,
    minmax(max(var(--min), calc((100% - (var(--cols) - 1) * var(--gap)) / var(--cols))), 1fr));
}
.a2ui-grid > .cell { min-width: 0; display: flex; }
.a2ui-grid > .cell > * { flex: 1; min-width: 0; }
`;


/** Injects the grid CSS once per page. */
function useGridCss() {
  React.useEffect(() => {
    if (document.getElementById('a2ui-grid-css')) return;
    const style = document.createElement('style');
    style.id = 'a2ui-grid-css';
    style.textContent = GRID_CSS;
    document.head.appendChild(style);
  }, []);
}

export const MaterialGrid = createComponentImplementation(GridApi, ({ props, buildChild }) => {
  useGridCss();
  const p = props as any;
  const n = Number(p.columns);
  const columns = n >= 1 && n <= 4 ? Math.floor(n) : null;
  // A template child list resolves to [{id, basePath}, ...] - one entry per data row.
  const children: any[] = Array.isArray(p.children) ? p.children : [];

  return (
    <div className="a2ui-grid-host">
      <div
        className={columns ? 'a2ui-grid fixed' : 'a2ui-grid'}
        style={columns ? ({ '--cols': columns } as React.CSSProperties) : undefined}
      >
        {children.map((child, i) => (
          <div className="cell" key={typeof child === 'string' ? child : `${child.id}-${child.basePath ?? i}`}>
            {typeof child === 'string' ? buildChild(child) : buildChild(child.id, child.basePath)}
          </div>
        ))}
      </div>
    </div>
  );
});

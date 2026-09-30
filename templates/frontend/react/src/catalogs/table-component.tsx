/**
 * Table for the A2UI catalog (React port of the Angular MaterialTableComponent).
 *
 * Columns marked `"editable": true` render inputs. Each committed edit is written
 * back to the data model at the bound `rows` path (via the binder's `setRows`),
 * so a Button whose action context references the same path sends the edited rows.
 */
import React from 'react';
import { z } from 'zod';
import { createComponentImplementation } from '@a2ui/react/v0_9';
import { Common, DynamicStr, DynamicValue, rowsOf } from './vega-components';

type Row = Record<string, any>;
type TableColumn = { key: string; label: string; type?: 'text' | 'number'; editable?: boolean };

export const TableApi = {
  name: 'Table',
  schema: z.object({
    ...Common,
    title: DynamicStr.optional(),
    columns: z.array(z.object({
      key: z.string(),
      label: z.string(),
      type: z.enum(['text', 'number']).optional(),
      editable: z.boolean().optional(),
    })),
    rows: DynamicValue,
    pageSize: z.number().optional(),
  }),
};

const TABLE_CSS = `
.a2ui-table { display: block; width: 100%; margin-bottom: 16px; }
.a2ui-table .t-title { font-weight: 500; margin-bottom: 8px; }
.a2ui-table .t-wrap { overflow-x: auto; border: 1px solid #e0e3e7; border-radius: 8px; }
.a2ui-table table { width: 100%; border-collapse: collapse; font-size: 13px; }
.a2ui-table th, .a2ui-table td { padding: 8px 12px; text-align: left; border-bottom: 1px solid #eef0f2; color: #202124; }
.a2ui-table th { background: #f8f9fa; font-weight: 500; }
.a2ui-table .num { text-align: right; }
.a2ui-table .empty { text-align: center; color: #80868b; }
.a2ui-table .edit-mark { color: #1a73e8; font-size: 11px; margin-left: 4px; }
.a2ui-table td.editable { padding: 4px 8px; background: #f8fbff; }
.a2ui-table .cell-input {
  display: block; width: 100%; min-width: 64px; box-sizing: border-box;
  font: inherit; font-size: 13px; line-height: 20px; padding: 4px 8px;
  color: #202124; -webkit-text-fill-color: #202124; caret-color: #1a73e8;
  color-scheme: light; /* stop the OS dark theme from making the text white */
  background: #ffffff; border: 1px solid #dadce0; border-radius: 4px;
}
.a2ui-table .cell-input.num { text-align: right; }
.a2ui-table .cell-input:hover { border-color: #9aa0a6; }
.a2ui-table .cell-input:focus { outline: none; border-color: #1a73e8; box-shadow: 0 0 0 1px #1a73e8; }
.a2ui-table .t-pager { display: flex; gap: 8px; align-items: center; justify-content: flex-end; margin-top: 6px; font-size: 12px; }
.a2ui-table .t-pager button { border: 1px solid #dadce0; background: #fff; border-radius: 4px; cursor: pointer; padding: 2px 8px; }
`;

/** Injects the table CSS once per page. */
function useTableCss() {
  React.useEffect(() => {
    if (document.getElementById('a2ui-table-css')) return;
    const style = document.createElement('style');
    style.id = 'a2ui-table-css';
    style.textContent = TABLE_CSS;
    document.head.appendChild(style);
  }, []);
}

/**
 * Uncontrolled input: the user types freely and the value is committed on
 * blur / Enter (like Angular's (change)), so the data model is not rewritten
 * on every keystroke. `key` on the parent resets it when the model changes.
 */
function EditableCell({ value, column, onCommit }: {
  value: unknown;
  column: TableColumn;
  onCommit: (text: string) => void;
}) {
  const initial = value === null || value === undefined ? '' : String(value);
  return (
    <input
      key={initial}
      className={`cell-input${column.type === 'number' ? ' num' : ''}`}
      type={column.type === 'number' ? 'number' : 'text'}
      defaultValue={initial}
      aria-label={column.label}
      onBlur={(e) => { if (e.currentTarget.value !== initial) onCommit(e.currentTarget.value); }}
      onKeyDown={(e) => { if (e.key === 'Enter') e.currentTarget.blur(); }}
    />
  );
}

export const MaterialTable = createComponentImplementation(TableApi, ({ props }) => {
  useTableCss();
  const p = props as any;
  const title = String(p.title || '');
  const columns: TableColumn[] = Array.isArray(p.columns) ? p.columns : [];
  const rows: Row[] = rowsOf(p.rows);
  const pageSize = Number(p.pageSize) || 5;
  const [page, setPage] = React.useState(0);
  const pageCount = Math.max(1, Math.ceil(rows.length / pageSize));
  const pageStart = Math.min(page, pageCount - 1) * pageSize;
  const pageRows = rows.slice(pageStart, pageStart + pageSize);

  const editCell = (rowIndex: number, column: TableColumn, text: string) => {
    const next = rows.map((row) => ({ ...row }));
    if (!next[rowIndex]) return;
    if (column.type === 'number') {
      const num = Number(text);
      next[rowIndex][column.key] = text.trim() === '' || Number.isNaN(num) ? null : num;
    } else {
      next[rowIndex][column.key] = text;
    }
    // Keep the shape the agent bound: either the array itself or {rows: [...]}.
    const current = p.rows;
    const isWrapped = current && !Array.isArray(current) && Array.isArray(current.rows);
    p.setRows?.(isWrapped ? { ...current, rows: next } : next);
  };

  return (
    <div className="a2ui-table">
      {title && <div className="t-title">{title}</div>}
      <div className="t-wrap">
        <table>
          <thead>
            <tr>
              {columns.map((c) => (
                <th key={c.key} className={c.type === 'number' ? 'num' : undefined}>
                  {c.label}
                  {c.editable && <span className="edit-mark" title="Editable">&#9998;</span>}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {pageRows.length === 0 ? (
              <tr><td colSpan={columns.length || 1} className="empty">No data</td></tr>
            ) : (
              pageRows.map((r, ri) => (
                <tr key={pageStart + ri}>
                  {columns.map((c) => (
                    <td
                      key={c.key}
                      className={[c.type === 'number' ? 'num' : '', c.editable ? 'editable' : ''].join(' ').trim() || undefined}
                    >
                      {c.editable ? (
                        <EditableCell
                          value={r[c.key]}
                          column={c}
                          onCommit={(text) => editCell(pageStart + ri, c, text)}
                        />
                      ) : (
                        String(r[c.key] ?? '')
                      )}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
      {pageCount > 1 && (
        <div className="t-pager">
          <button onClick={() => setPage(page - 1)} disabled={page === 0}>&lsaquo;</button>
          <span>{page + 1} / {pageCount}</span>
          <button onClick={() => setPage(page + 1)} disabled={page >= pageCount - 1}>&rsaquo;</button>
        </div>
      )}
    </div>
  );
});

/**
 * Interactive Vega-Lite charts for the A2UI catalog (React port of the Angular
 * vega-components.ts).
 *
 *  - `Chart`     : bar | line | area | point | pie built from rows in the data model.
 *  - `VegaChart` : renders a complete Vega-Lite spec produced by a backend tool
 *                  (KPI trend, office map, well logs). The backend binds `spec` to
 *                  "/plots/<id>" and attaches the spec to the data model.
 *
 * vega + vega-lite + vega-embed (~1 MB) are loaded lazily on the first chart,
 * so they are not part of the initial bundle.
 */
import React from 'react';
import { z } from 'zod';
import { createComponentImplementation } from '@a2ui/react/v0_9';
import type { EmbedOptions, Result as EmbedResult, VisualizationSpec } from 'vega-embed';

type Spec = Record<string, any>;
type Row = Record<string, any>;

// ---------------------------------------------------------------------------
// Schemas (mirror backend/manager_dashboard/catalogs/extended_catalog.json)
// The `{path}` object in each union is what tells the A2UI binder to resolve
// the value from the data model (and to generate a setter such as setRows).
// ---------------------------------------------------------------------------

export const DynamicValue = z.union([
  z.string(), z.number(), z.boolean(), z.array(z.any()),
  z.object({ path: z.string() }).passthrough(),
  z.object({ call: z.string() }).passthrough(),
]);
export const DynamicStr = z.union([z.string(), z.object({ path: z.string() }).passthrough()]);
export const Common = {
  accessibility: z.any().optional(),
  weight: z.number().optional(),
};

export const ChartApi = {
  name: 'Chart',
  schema: z.object({
    ...Common,
    title: DynamicStr.optional(),
    chartType: z.enum(['bar', 'line', 'area', 'point', 'pie']),
    data: DynamicValue,
    x: z.string(),
    y: z.string(),
    color: z.string().optional(),
  }),
};

export const VegaChartApi = {
  name: 'VegaChart',
  schema: z.object({
    ...Common,
    title: DynamicStr.optional(),
    // Normally {"path": "/plots/<id>"}; an inline spec object or JSON string also works.
    spec: z.union([z.object({ path: z.string() }).passthrough(), z.record(z.string(), z.any()), z.string()]),
  }),
};

// ---------------------------------------------------------------------------
// <VegaView>: lazy vega-embed wrapper shared by both components
// ---------------------------------------------------------------------------

type EmbedFn = (el: HTMLElement, spec: VisualizationSpec, opts?: EmbedOptions) => Promise<EmbedResult>;
let embedLoader: Promise<EmbedFn> | null = null;

function loadEmbed(): Promise<EmbedFn> {
  embedLoader ??= import('vega-embed').then((m) => m.default as unknown as EmbedFn);
  return embedLoader;
}

const msgStyle: React.CSSProperties = { color: '#80868b', fontSize: 12, padding: '8px 0' };
const titleStyle: React.CSSProperties = { fontWeight: 500, marginBottom: 8 };

function VegaView({ spec, exportable = false, fileName = 'chart' }: {
  spec: Spec | null;
  exportable?: boolean;
  fileName?: string;
}) {
  const host = React.useRef<HTMLDivElement>(null);
  const [error, setError] = React.useState('');
  const [ready, setReady] = React.useState(false);
  // Re-embed only when the spec content changes, not on every parent render.
  const specKey = React.useMemo(() => (spec ? JSON.stringify(spec) : ''), [spec]);

  React.useEffect(() => {
    const el = host.current;
    if (!el || !specKey) return;
    let cancelled = false;
    let result: EmbedResult | undefined;

    // Vega tags data objects in place, so never hand it objects owned by the
    // A2UI data model. A JSON round-trip is a safe deep copy.
    const copy = JSON.parse(specKey) as Spec;
    const options: EmbedOptions = {
      renderer: 'canvas',
      actions: exportable ? { export: true, source: false, compiled: false, editor: false } : false,
      downloadFileName: fileName,
      mode: copy['$schema'] ? undefined : 'vega-lite',
    };

    setReady(false);
    setError('');
    loadEmbed()
      .then((embed) => embed(el, copy as VisualizationSpec, options))
      .then((res) => {
        if (cancelled) {
          res.finalize();
          return;
        }
        result = res;
        setReady(true);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        console.error('[VegaChart] render failed', err);
        setError(err instanceof Error ? err.message : String(err));
      });

    return () => {
      cancelled = true;
      result?.finalize(); // removes Vega listeners, timers and the tooltip handler
    };
  }, [specKey, exportable, fileName]);

  return (
    <div style={{ display: 'block', width: '100%' }}>
      <div ref={host} style={{ display: 'block', width: '100%', maxWidth: '100%', overflowX: 'auto', overflowY: 'hidden' }} />
      {error ? (
        <div style={{ ...msgStyle, color: '#d93025' }}>Could not draw the chart: {error}</div>
      ) : !ready ? (
        <div style={msgStyle}>Loading chart…</div>
      ) : null}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Chart: bar | line | area | point | pie  ->  Vega-Lite spec
// ---------------------------------------------------------------------------

const PALETTE = ['#1a73e8', '#34a853', '#fbbc04', '#ea4335', '#9334e6', '#00acc1', '#ff6d00', '#5f6368'];
const SCHEMA = 'https://vega.github.io/schema/vega-lite/v6.json';
const DATE_LIKE = /^\d{4}-\d{2}(-\d{2})?([T ]\d{2}:\d{2}(:\d{2}(\.\d+)?)?(Z|[+-]\d{2}:?\d{2})?)?$/;

/** Unwraps a bound prop and guarantees an array of row objects. */
export function rowsOf(raw: unknown): Row[] {
  if (Array.isArray(raw)) return raw.filter((r): r is Row => !!r && typeof r === 'object');
  const rows = raw && typeof raw === 'object' ? (raw as Row)['rows'] : undefined;
  return Array.isArray(rows) ? rows.filter((r): r is Row => !!r && typeof r === 'object') : [];
}

/** Vega-Lite treats "." and "[" in field names as nested access; escape them. */
function field(name: string): string {
  return name.replace(/([.[\]\\])/g, '\\$1');
}

function toNumber(value: unknown): number | null {
  if (typeof value === 'number') return Number.isFinite(value) ? value : null;
  if (typeof value === 'string' && value.trim() !== '') {
    const n = Number(value.replace(/,/g, ''));
    return Number.isFinite(n) ? n : null;
  }
  return null;
}

function xTypeOf(values: unknown[]): 'quantitative' | 'temporal' | 'nominal' {
  const present = values.filter((v) => v !== null && v !== undefined && v !== '');
  if (!present.length) return 'nominal';
  if (present.every((v) => typeof v === 'number')) return 'quantitative';
  if (present.every((v) => typeof v === 'string' && DATE_LIKE.test(v) && !Number.isNaN(Date.parse(v)))) {
    return 'temporal';
  }
  return 'nominal';
}

export function buildChartSpec(type: string, rawRows: Row[], x: string, y: string, color: string): Spec {
  const rows = rawRows.map((r) => ({ ...r, [y]: toNumber(r[y]) }));
  const colorField = color && color !== y ? color : '';
  const base: Spec = {
    $schema: SCHEMA,
    data: { values: rows },
    width: 'container',
    height: 240,
    config: {
      font: 'Roboto, Arial, sans-serif',
      view: { stroke: null },
      axis: { labelColor: '#3c4043', titleColor: '#3c4043', gridColor: '#eef0f2', domainColor: '#dadce0', tickColor: '#dadce0' },
      legend: { labelColor: '#3c4043', titleColor: '#3c4043', orient: 'top', labelLimit: 120 },
      range: { category: PALETTE },
    },
  };
  const yTip = { field: field(y), type: 'quantitative', title: y, format: ',' };

  if (type === 'pie') {
    return {
      ...base,
      transform: [
        { filter: `isValid(datum[${JSON.stringify(y)}])` },
        { aggregate: [{ op: 'sum', field: field(y), as: '__value' }], groupby: [field(x)] },
        { joinaggregate: [{ op: 'sum', field: '__value', as: '__total' }] },
        { calculate: 'datum.__total ? datum.__value / datum.__total : 0', as: '__share' },
      ],
      params: [{ name: 'hover', select: { type: 'point', on: 'pointerover', clear: 'pointerout' } }],
      mark: { type: 'arc', stroke: '#ffffff', strokeWidth: 1.5, cursor: 'pointer' },
      encoding: {
        theta: { field: '__value', type: 'quantitative', stack: true },
        color: { field: field(x), type: 'nominal', title: x, sort: null, legend: { orient: 'right' } },
        opacity: { condition: { param: 'hover', value: 1 }, value: 0.55 },
        tooltip: [
          { field: field(x), type: 'nominal', title: x },
          { field: '__value', type: 'quantitative', title: y, format: ',' },
          { field: '__share', type: 'quantitative', title: 'Share', format: '.1%' },
        ],
      },
    };
  }

  const xType = type === 'bar' ? 'nominal' : xTypeOf(rows.map((r) => r[x]));
  const xEnc: Spec = {
    field: field(x),
    type: xType,
    title: x,
    axis: xType === 'nominal' ? { labelAngle: rows.length > 5 ? -35 : 0, labelLimit: 100 } : {},
  };
  if (xType === 'nominal') xEnc['sort'] = null; // keep the data order
  const yEnc: Spec = { field: field(y), type: 'quantitative', title: y, axis: { format: '~s' } };
  const colorEnc: Spec = colorField
    ? { field: field(colorField), type: 'nominal', title: colorField }
    : { value: PALETTE[0] };
  const tooltip = [
    { field: field(x), type: xType === 'temporal' ? 'temporal' : xType, title: x },
    yTip,
    ...(colorField && colorField !== x ? [{ field: field(colorField), type: 'nominal', title: colorField }] : []),
  ];

  if (type === 'bar') {
    return {
      ...base,
      params: [{ name: 'hover', select: { type: 'point', on: 'pointerover', clear: 'pointerout' } }],
      mark: { type: 'bar', cornerRadiusEnd: 3, cursor: 'pointer' },
      encoding: {
        x: xEnc,
        y: yEnc,
        color: colorEnc,
        opacity: { condition: { param: 'hover', value: 1 }, value: 0.55 },
        tooltip,
      },
    };
  }

  // line | area | point: series layer + points that grow on hover (nearest point wins).
  const series = colorField ? { color: colorEnc } : {};
  const layers: Spec[] = [];
  if (type === 'area') {
    layers.push({
      mark: { type: 'area', opacity: 0.25, line: false, color: colorField ? undefined : PALETTE[0] },
      encoding: { x: xEnc, y: { ...yEnc, stack: null }, ...series },
    });
  }
  if (type === 'line' || type === 'area') {
    layers.push({
      mark: { type: 'line', strokeWidth: 2, color: colorField ? undefined : PALETTE[0] },
      encoding: { x: xEnc, y: yEnc, ...series },
    });
  }
  layers.push({
    params: [{ name: 'hover', select: { type: 'point', on: 'pointerover', clear: 'pointerout', nearest: true } }],
    mark: { type: 'point', filled: true, cursor: 'pointer' },
    encoding: {
      x: xEnc,
      y: yEnc,
      color: colorEnc,
      size: { condition: { param: 'hover', empty: false, value: 140 }, value: type === 'point' ? 60 : 30 },
      opacity: { value: 1 },
      tooltip,
    },
  });
  return { ...base, layer: layers };
}

export const MaterialChart = createComponentImplementation(ChartApi, ({ props }) => {
  const p = props as any;
  const title = String(p.title || '');
  const rows = rowsOf(p.data);
  const spec = React.useMemo(
    () => buildChartSpec(String(p.chartType || 'bar'), rows, String(p.x || ''), String(p.y || ''), String(p.color || '')),
    // rows is a fresh array each render; key on its content instead.
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [p.chartType, p.x, p.y, p.color, JSON.stringify(rows)],
  );

  return (
    <div style={{ display: 'block', width: '100%', marginBottom: 16 }}>
      {title && <div style={titleStyle}>{title}</div>}
      {rows.length === 0
        ? <div style={{ color: '#80868b', fontSize: 13 }}>No data</div>
        : <VegaView spec={spec} fileName={title || 'chart'} />}
    </div>
  );
});

// ---------------------------------------------------------------------------
// VegaChart: full spec from a backend tool (KPI trend, maps, well logs)
// ---------------------------------------------------------------------------

function specOf(raw: unknown): Spec | null {
  if (typeof raw === 'string') {
    try {
      const parsed: unknown = JSON.parse(raw);
      return parsed && typeof parsed === 'object' ? (parsed as Spec) : null;
    } catch {
      return null;
    }
  }
  // An unresolved binding ({path}) means the data has not arrived yet.
  if (!raw || typeof raw !== 'object' || Array.isArray(raw) || 'path' in raw) return null;
  return raw as Spec;
}

export const MaterialVegaChart = createComponentImplementation(VegaChartApi, ({ props }) => {
  const p = props as any;
  const title = String(p.title || '');
  const spec = specOf(p.spec);

  return (
    <div style={{ display: 'block', width: '100%', marginBottom: 12 }}>
      {title && <div style={titleStyle}>{title}</div>}
      {spec
        ? <VegaView spec={spec} exportable fileName={title || 'plot'} />
        : <div style={{ color: '#80868b', fontSize: 13 }}>Loading plot data…</div>}
    </div>
  );
});

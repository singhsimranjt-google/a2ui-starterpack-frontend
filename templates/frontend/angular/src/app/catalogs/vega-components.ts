/**
 * Interactive Vega-Lite charts for the A2UI catalog.
 *
 *  - `Chart`     : bar | line | area | point | pie built from rows (same props as before),
 *                  now rendered with Vega-Lite: hover tooltips + highlight.
 *  - `VegaChart` : renders a complete Vega-Lite spec produced by a backend tool
 *                  (e.g. well logs from LAS files). The backend binds `spec` to
 *                  "/plots/<id>" and attaches the spec to the data model.
 *
 * vega + vega-lite + vega-embed (~1 MB) are loaded lazily on the first chart,
 * so they are not part of the initial bundle.
 */
import {
  ChangeDetectionStrategy,
  Component,
  ElementRef,
  NgZone,
  afterRenderEffect,
  computed,
  inject,
  input,
  signal,
  viewChild,
} from '@angular/core';
import { z } from 'zod';
import { CatalogComponent } from '@a2ui/angular/v0_9';
import type { EmbedOptions, Result as EmbedResult, VisualizationSpec } from 'vega-embed';

type Spec = Record<string, any>;
type Row = Record<string, any>;

// ---------------------------------------------------------------------------
// Schemas (mirror backend/manager_dashboard/catalogs/extended_catalog.json)
// ---------------------------------------------------------------------------

const DynamicValue = z.union([
  z.string(), z.number(), z.boolean(), z.array(z.any()),
  z.object({ path: z.string() }).passthrough(),
  z.object({ call: z.string() }).passthrough(),
]);
const DynamicStr = z.union([z.string(), z.object({ path: z.string() }).passthrough()]);
const Common = {
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
// <a2ui-vega-view>: lazy vega-embed wrapper shared by both components
// ---------------------------------------------------------------------------

type EmbedFn = (el: HTMLElement, spec: VisualizationSpec, opts?: EmbedOptions) => Promise<EmbedResult>;
let embedLoader: Promise<EmbedFn> | null = null;

function loadEmbed(): Promise<EmbedFn> {
  embedLoader ??= import('vega-embed').then((m) => m.default as unknown as EmbedFn);
  return embedLoader;
}

@Component({
  selector: 'a2ui-vega-view',
  standalone: true,
  template: `
    <div #host class="vega-host"></div>
    @if (error()) {
      <div class="vega-msg error">Could not draw the chart: {{ error() }}</div>
    } @else if (!ready()) {
      <div class="vega-msg">Loading chart…</div>
    }
  `,
  styles: [`
    :host { display: block; width: 100%; }
    .vega-host { display: block; width: 100%; max-width: 100%; overflow-x: auto; overflow-y: hidden; }
    .vega-msg { color: #80868b; font-size: 12px; padding: 8px 0; }
    .vega-msg.error { color: #d93025; }
  `],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class VegaViewComponent {
  /** Vega-Lite (or Vega, if $schema says so) spec. Null renders nothing. */
  readonly spec = input<Spec | null>(null);
  /** Show the "..." menu with Save as PNG/SVG. */
  readonly exportable = input(false);
  readonly fileName = input('chart');

  readonly error = signal('');
  readonly ready = signal(false);

  private readonly host = viewChild.required<ElementRef<HTMLDivElement>>('host');
  private readonly zone = inject(NgZone);

  constructor() {
    afterRenderEffect((onCleanup) => {
      const spec = this.spec();
      const el = this.host().nativeElement;
      const exportable = this.exportable();
      const fileName = this.fileName();
      let cancelled = false;
      let result: EmbedResult | undefined;
      onCleanup(() => {
        cancelled = true;
        result?.finalize(); // removes Vega listeners, timers and the tooltip handler
      });
      if (!spec) return;

      // Vega tags data objects in place, so never hand it objects owned by the
      // A2UI data model. Specs are plain JSON, so a JSON round-trip is a safe copy.
      const copy = JSON.parse(JSON.stringify(spec)) as Spec;
      const options: EmbedOptions = {
        renderer: 'canvas',
        actions: exportable ? { export: true, source: false, compiled: false, editor: false } : false,
        downloadFileName: fileName,
        mode: copy['$schema'] ? undefined : 'vega-lite',
      };

      // Outside Angular: pointer events on the chart must not trigger app-wide change detection.
      this.zone.runOutsideAngular(() => {
        loadEmbed()
          .then((embed) => embed(el, copy as VisualizationSpec, options))
          .then((res) => {
            if (cancelled) {
              res.finalize();
              return;
            }
            result = res;
            this.zone.run(() => {
              this.error.set('');
              this.ready.set(true);
            });
          })
          .catch((err: unknown) => {
            if (cancelled) return;
            console.error('[VegaChart] render failed', err);
            this.zone.run(() => this.error.set(err instanceof Error ? err.message : String(err)));
          });
      });
    });
  }
}

// ---------------------------------------------------------------------------
// Chart: bar | line | area | point | pie  ->  Vega-Lite spec
// ---------------------------------------------------------------------------

const PALETTE = ['#1a73e8', '#34a853', '#fbbc04', '#ea4335', '#9334e6', '#00acc1', '#ff6d00', '#5f6368'];
const SCHEMA = 'https://vega.github.io/schema/vega-lite/v6.json';
const DATE_LIKE = /^\d{4}-\d{2}(-\d{2})?([T ]\d{2}:\d{2}(:\d{2}(\.\d+)?)?(Z|[+-]\d{2}:?\d{2})?)?$/;

/** Unwraps a bound prop and guarantees an array of row objects. */
function rowsOf(raw: unknown): Row[] {
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
    // Pie = sum of y per x category, with the share in the tooltip.
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

@Component({
  selector: 'a2ui-mat-chart',
  standalone: true,
  imports: [VegaViewComponent],
  template: `
    @if (title()) { <div class="c-title">{{ title() }}</div> }
    @if (rows().length === 0) {
      <div class="empty">No data</div>
    } @else {
      <a2ui-vega-view [spec]="spec()" [fileName]="title() || 'chart'" />
    }
  `,
  styles: [`
    :host { display: block; width: 100%; margin-bottom: 16px; }
    .c-title { font-weight: 500; margin-bottom: 8px; }
    .empty { color: #80868b; font-size: 13px; }
  `],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class MaterialChartComponent extends CatalogComponent<any> {
  title = computed(() => String(this.props()['title']?.value() || ''));
  rows = computed(() => rowsOf(this.props()['data']?.value()));
  spec = computed(() =>
    buildChartSpec(
      String(this.props()['chartType']?.value() || 'bar'),
      this.rows(),
      String(this.props()['x']?.value() || ''),
      String(this.props()['y']?.value() || ''),
      String(this.props()['color']?.value() || ''),
    ),
  );
}

// ---------------------------------------------------------------------------
// VegaChart: full spec from a backend tool (e.g. well logs)
// ---------------------------------------------------------------------------

@Component({
  selector: 'a2ui-vega-chart',
  standalone: true,
  imports: [VegaViewComponent],
  template: `
    @if (title()) { <div class="c-title">{{ title() }}</div> }
    @if (spec()) {
      <a2ui-vega-view [spec]="spec()" [exportable]="true" [fileName]="title() || 'plot'" />
    } @else {
      <div class="empty">Loading plot data…</div>
    }
  `,
  styles: [`
    :host { display: block; width: 100%; margin-bottom: 12px; }
    .c-title { font-weight: 500; margin-bottom: 8px; }
    .empty { color: #80868b; font-size: 13px; }
  `],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class MaterialVegaChartComponent extends CatalogComponent<any> {
  title = computed(() => String(this.props()['title']?.value() || ''));
  spec = computed<Spec | null>(() => {
    const raw: unknown = this.props()['spec']?.value();
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
  });
}

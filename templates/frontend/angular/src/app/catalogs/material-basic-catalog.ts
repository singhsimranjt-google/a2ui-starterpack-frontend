import {
  Component,
  computed,
  effect,
  signal,
  ChangeDetectionStrategy,
  Injectable,
  inject
} from '@angular/core';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatDividerModule } from '@angular/material/divider';
import { MatIconModule } from '@angular/material/icon';
import { MatSelectModule } from '@angular/material/select';
import { MatTimepickerModule } from '@angular/material/timepicker';

import { MatCheckboxModule } from '@angular/material/checkbox';
import { FormsModule } from '@angular/forms';

import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatNativeDateModule } from '@angular/material/core';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';

import { GoogleMapsModule } from '@angular/google-maps';
import { z } from 'zod';

import {
  BasicCatalogBase,
  CatalogComponent,
  ComponentHostComponent,
  A2uiRendererService
} from '@a2ui/angular/v0_9';
import { CardApi, ButtonApi, DividerApi, DataContext, TextFieldApi, CheckBoxApi, RowApi, IconApi, DateTimeInputApi, ImageApi, ChoicePickerApi, childList } from '@a2ui/web_core/v0_9';
import { ChartApi, MaterialChartComponent, VegaChartApi, MaterialVegaChartComponent } from './vega-components';

/**
 * Bespoke Angular Material Card wrapper for A2UI Basic Catalog
 */
@Component({
  selector: 'a2ui-mat-card',
  standalone: true,
  imports: [MatCardModule, ComponentHostComponent],
  template: `
    <mat-card appearance="outlined" class="a2ui-material-card">
      <mat-card-content>
        @if (child()) {
          <a2ui-v09-component-host [componentKey]="child()!" [surfaceId]="surfaceId()">
          </a2ui-v09-component-host>
        }
      </mat-card-content>
    </mat-card>
  `,
  styles: [`
    .a2ui-material-card {
      width: 100% !important;
      border-radius: var(--a2ui-card-border-radius, 24px) !important;
      background: var(--a2ui-card-background, #ffffff) !important;
      box-shadow: var(--a2ui-card-box-shadow) !important;
      border: var(--a2ui-card-border, 1px solid #e0e3e7) !important;
      padding: 6px 10px !important;
      box-sizing: border-box !important;
    }
  `],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class MaterialCardComponent extends CatalogComponent<typeof CardApi> {
  child = computed(() => this.props()['child']?.value());
}

/**
 * Bespoke Angular Material Button wrapper for A2UI Basic Catalog
 */
@Component({
  selector: 'a2ui-mat-button',
  standalone: true,
  imports: [ComponentHostComponent],
  template: `
    <button
      [disabled]="props()['isValid']?.value() === false"
      (click)="handleClick()"
      class="a2ui-material-button"
    >
      @if (child()) {
        <a2ui-v09-component-host [componentKey]="child()!" [surfaceId]="surfaceId()">
        </a2ui-v09-component-host>
      }
    </button>
  `,
  styles: [`
    .a2ui-material-button {
      border-radius: 4px !important;
      font-family: var(--font-family-sans, 'Google Sans', sans-serif);
      font-size: 14px;
      font-weight: 500;
      padding: 10px 20px !important;
      background-color: #1a73e8 !important; /* Official Google Blue */
      border: none !important;
      cursor: pointer;
      box-shadow: 0 1px 2px 0 rgba(60,64,67,0.3), 0 1px 3px 1px rgba(60,64,67,0.15) !important;
      transition: box-shadow 0.2s ease-in-out, background-color 0.2s ease-in-out;
    }
    
    /* VERY IMPORTANT: ::ng-deep pierces Angular's view encapsulation to target the child Text component */
    .a2ui-material-button ::ng-deep * {
      color: #ffffff !important; 
    }

    .a2ui-material-button:hover:not(:disabled) {
      box-shadow: 0 1px 3px 0 rgba(60,64,67,0.3), 0 4px 8px 3px rgba(60,64,67,0.15) !important;
      background-color: #1557b0 !important; /* Darker blue on hover */
    }

    .a2ui-material-button:disabled {
      background-color: #cccccc !important;
      box-shadow: none !important;
      cursor: not-allowed;
    }
  `],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class MaterialButtonComponent extends CatalogComponent<typeof ButtonApi> {
  private rendererService = inject(A2uiRendererService);
  surface = computed(() => this.rendererService.surfaceGroup.getSurface(this.surfaceId()));

  variant = computed(() => this.props()['variant']?.value() || 'primary');
  child = computed(() => this.props()['child']?.value());

  handleClick() {
    const action = this.props()['action']?.value();
    if (action) {
      const surface = this.surface();
      if (surface) {
        const dataContext = new DataContext(surface, this.dataContextPath());
        const resolvedAction = dataContext.resolveAction(action);
        surface.dispatchAction(resolvedAction, this.componentId());
      }
    }
  }
}

/**
 * Bespoke Angular Material Divider wrapper for A2UI Basic Catalog
 */
@Component({
  selector: 'a2ui-mat-divider',
  standalone: true,
  imports: [MatDividerModule],
  template: `<mat-divider class="a2ui-material-divider"></mat-divider>`,
  styles: [`
    .a2ui-material-divider {
      margin: 14px 0 !important;
      border-top-color: var(--google-grey-200, #e8eaed) !important;
    }
  `],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class MaterialDividerComponent extends CatalogComponent<typeof DividerApi> { }

/**
 * textfield a2ui
 */
@Component({
  selector: 'a2ui-mat-textfield',
  standalone: true,
  imports: [FormsModule],
  template: `
    <div class="a2ui-textfield-container">
      <label class="a2ui-textfield-label">{{ label() }}</label>
      <input 
        type="text" 
        [ngModel]="value()" 
        (ngModelChange)="onValueChange($event)"
        class="a2ui-textfield-input"
      >
    </div>
  `,
  styles: [`
    .a2ui-textfield-container {
      width: 100%;
      margin-bottom: 12px;
      display: flex;
      flex-direction: column;
    }
    .a2ui-textfield-label {
      font-size: 12px;
      font-weight: bold;
      margin-bottom: 4px;
      font-family: sans-serif;
      color: #333333 !important;
    }
    .a2ui-textfield-input {
      padding: 12px !important;
      border: 1px solid #000000 !important;
      border-radius: 4px !important;
      
      /* Force browser dark-mode engines to back off */
      color-scheme: light !important;
      background: #ffffff !important;
      color: #000000 !important;
      -webkit-appearance: none !important;
      appearance: none !important;
      
      font-size: 16px !important;
      font-family: sans-serif !important;
      box-sizing: border-box !important;
      outline: none !important;
    }
    .a2ui-textfield-input:focus {
      border: 2px solid #1a73e8 !important;
      padding: 11px !important; /* Adjust padding to prevent jumping when border gets thicker */
    }
  `],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class MaterialTextFieldComponent extends CatalogComponent<typeof TextFieldApi> {
  private rendererService = inject(A2uiRendererService);
  surface = computed(() => this.rendererService.surfaceGroup.getSurface(this.surfaceId()));

  label = computed(() => this.props()['label']?.value() || '');
  value = computed(() => this.props()['value']?.value() || '');

  inputType = computed(() => {
    return this.label().toLowerCase().includes('date') ? 'date' : 'text';
  });

  onValueChange(newValue: string) {
    // const surface = this.surface();
    // if (surface) {
    //   const path = (this.props()['value'] as any).path();
    //   if (path) surface.dataModel.set(path, newValue);
    // }
    this.props()['value']?.onUpdate(newValue);
  }
}

/**
 * checkbox a2ui
 */
@Component({
  selector: 'a2ui-mat-checkbox',
  standalone: true,
  imports: [MatCheckboxModule, FormsModule],
  template: `
    <mat-checkbox [ngModel]="value()" (ngModelChange)="onValueChange($event)" style="margin-bottom: 12px;">
      {{ label() }}
    </mat-checkbox>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class MaterialCheckboxComponent extends CatalogComponent<typeof CheckBoxApi> {
  private rendererService = inject(A2uiRendererService);
  surface = computed(() => this.rendererService.surfaceGroup.getSurface(this.surfaceId()));

  label = computed(() => this.props()['label']?.value() || '');
  value = computed(() => {
    const val = this.props()['value']?.value() as any;
    return val === 'true' || val === true;
  });

  onValueChange(newValue: boolean) {
    const surface = this.surface();
    if (surface) {
      // const path = (this.props()['value'] as any).path();
      // if (path) surface.dataModel.set(path, newValue);
      this.props()['value']?.onUpdate(newValue);
    }
  }
}
/**
 * Bespoke Angular wrapper for A2UI Row Component
 */
@Component({
  selector: 'a2ui-mat-row',
  standalone: true,
  imports: [ComponentHostComponent],
  template: `
    <div class="row" [style.justify-content]="justify()" [style.align-items]="align()">
      @for (child of children(); track $index) {
        <!-- The critical fix: wrapping the host in a native div -->
        <div style="display: block;">
          <a2ui-v09-component-host [componentKey]="child" [surfaceId]="surfaceId()">
          </a2ui-v09-component-host>
        </div>
      }
    </div>
  `,
  styles: [`.row { display: flex; flex-direction: row; flex-wrap: wrap; gap: 12px 24px; }`],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class MaterialRowComponent extends CatalogComponent<typeof RowApi> {
  private static readonly J: Record<string, string> = {
    start: 'flex-start', center: 'center', end: 'flex-end', stretch: 'stretch',
    spaceBetween: 'space-between', spaceAround: 'space-around', spaceEvenly: 'space-evenly',
  };
  private static readonly A: Record<string, string> = { start: 'flex-start', center: 'center', end: 'flex-end', stretch: 'stretch' };
  children = computed(() => this.props()['children']?.value() || []);
  justify = computed(() => MaterialRowComponent.J[String(this.props()['justify']?.value() ?? 'start')] ?? 'flex-start');
  align = computed(() => MaterialRowComponent.A[String(this.props()['align']?.value() ?? 'center')] ?? 'center');
}


/**
 * Official Angular Material Datepicker wrapped for A2UI
 */
@Component({
  selector: 'a2ui-mat-datetime',
  standalone: true,
  imports: [
    MatFormFieldModule,
    MatInputModule,
    MatDatepickerModule,
    MatTimepickerModule,
    MatNativeDateModule,
    FormsModule,
  ],
  template: `
    <div style="display: flex; gap: 12px; width: 100%;">
      @if (showDate()) {
        <mat-form-field appearance="outline" style="flex: 1; margin-bottom: 12px;">
          <mat-label>{{ label() || 'Pick a date' }}</mat-label>
          <input matInput [matDatepicker]="datePicker"
                 [ngModel]="dateValue()" (ngModelChange)="onDateChange($event)">
          <mat-datepicker-toggle matIconSuffix [for]="datePicker"></mat-datepicker-toggle>
          <mat-datepicker #datePicker></mat-datepicker>
        </mat-form-field>
      }
      @if (showTime()) {
        <mat-form-field appearance="outline" style="flex: 1; margin-bottom: 12px;">
          <mat-label>{{ label() || 'Pick a time' }}</mat-label>
          <input matInput [matTimepicker]="timePicker"
                 [ngModel]="timeValue()" (ngModelChange)="onTimeChange($event)">
          <mat-timepicker-toggle matIconSuffix [for]="timePicker"></mat-timepicker-toggle>
          <mat-timepicker #timePicker interval="30min"></mat-timepicker>
        </mat-form-field>
      }
    </div>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class MaterialDateTimeInputComponent extends CatalogComponent<typeof DateTimeInputApi> {
  label = computed(() => this.props()['label']?.value() || '');

  showTime = computed(() => this.props()['enableTime']?.value() === true);
  // Back-compat: if neither flag is set, behave as a plain date picker
  showDate = computed(
    () => this.props()['enableDate']?.value() === true || !this.showTime()
  );

  private raw = computed(() => String(this.props()['value']?.value() ?? ''));

  // Accepts "2026-09-18", "2026-09-18T14:30", "2026-09-18T14:30:00.000Z"
  dateValue = computed<Date | null>(() => {
    const m = this.raw().match(/^(\d{4})-(\d{2})-(\d{2})/);
    if (!m) return null;
    return new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3]));
  });

  // Accepts "14:30" or the time portion of a full ISO string
  timeValue = computed<Date | null>(() => {
    const m = this.raw().match(/(?:^|T)(\d{2}):(\d{2})/);
    if (!m) return null;
    const base = this.dateValue() ?? new Date();
    const out = new Date(base);
    out.setHours(Number(m[1]), Number(m[2]), 0, 0);
    return out;
  });

  onDateChange(newValue: any) {
    const d = this.toDate(newValue);
    if (!d) return;
    this.commit(d, this.showTime() ? this.timeValue() : null);
  }

  onTimeChange(newValue: any) {
    const t = this.toDate(newValue);
    if (!t) return;
    this.commit(this.showDate() ? this.dateValue() : null, t);
  }

  private toDate(v: any): Date | null {
    if (!v) return null;
    const d = v instanceof Date ? v : new Date(v);
    return isNaN(d.getTime()) ? null : d;
  }

  /** Emits YYYY-MM-DD, HH:MM, or YYYY-MM-DDTHH:MM depending on which fields are on. */
  /** Emits YYYY-MM-DD for date-only, or full ISO YYYY-MM-DDTHH:MM:00 whenever a time is set. */
  private commit(date: Date | null, time: Date | null) {
    const pad = (n: number) => String(n).padStart(2, '0');

    // A time-only field still needs a date anchor, or datetime.fromisoformat() rejects it
    const d = date ?? (time ? new Date() : null);
    const datePart = d
      ? `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
      : '';
    const timePart = time
      ? `${pad(time.getHours())}:${pad(time.getMinutes())}:00`
      : '';

    const out = timePart ? `${datePart}T${timePart}` : datePart;
    this.props()['value']?.onUpdate(out);
  }
}

/**
 * A2UI catalog Icon names -> Material Icons ligature names.
 * Kept identical to the React catalog so both frontends render the same glyph.
 */
const ICON_LIGATURE_OVERRIDES: Record<string, string> = {
  play: 'play_arrow',
  rewind: 'fast_rewind',
  favoriteOff: 'favorite_border',
  starOff: 'star_border',
};

/**
 * Bespoke Angular wrapper for A2UI Icon Component
 */
@Component({
  selector: 'a2ui-mat-icon',
  standalone: true,
  imports: [MatIconModule],
  template: `<mat-icon style="display: flex; justify-content: center; align-items: center; width: 24px; height: 24px;">{{ ligature() }}</mat-icon>`,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class MaterialIconComponent extends CatalogComponent<typeof IconApi> {
  name = computed(() => this.props()['name']?.value() || '');

  // The Material Icons ligature font expects snake_case (locationOn -> location_on).
  // Without this, 24 of the 59 catalog icons render as raw text in Angular.
  ligature = computed(() => {
    const raw = String(this.name() ?? '');
    return ICON_LIGATURE_OVERRIDES[raw] ?? raw.replace(/[A-Z]/g, (l) => `_${l.toLowerCase()}`);
  });
}


declare const google: any;

type LatLng = { lat: number; lng: number };

/** Loads the Maps JavaScript API once per page. */
let mapsScriptPromise: Promise<void> | null = null;
function loadGoogleMaps(key: string): Promise<void> {
  if ((window as any).google?.maps?.marker) return Promise.resolve();
  if (!mapsScriptPromise) {
    mapsScriptPromise = new Promise<void>((resolve, reject) => {
      (window as any).__a2uiMapsReady = () => resolve();
      const s = document.createElement('script');
      s.src = `https://maps.googleapis.com/maps/api/js?key=${encodeURIComponent(key)}` +
        '&libraries=marker&loading=async&callback=__a2uiMapsReady';
      s.async = true;
      s.onerror = () => {
        mapsScriptPromise = null;
        reject(new Error('Google Maps JS failed to load'));
      };
      document.head.appendChild(s);
    });
  }
  return mapsScriptPromise;
}


/**
 * If `url` is a Google Static Maps URL, return its key + marker coordinates.
 * "markers=color:red|37.77,-122.41|34.05,-118.24" -> [{lat,lng},{lat,lng}]
 */
function parseStaticMapUrl(url: string): { key: string; markers: LatLng[] } | null {
  try {
    const u = new URL(url);
    if (u.hostname !== 'maps.googleapis.com' || !u.pathname.includes('/maps/api/staticmap')) {
      return null;
    }
    const markers: LatLng[] = [];
    for (const group of u.searchParams.getAll('markers')) {
      for (const part of group.split('|')) {
        const [lat, lng] = part.split(',').map(Number);
        if (part.includes(',') && Number.isFinite(lat) && Number.isFinite(lng)) {
          markers.push({ lat, lng });
        }
      }
    }
    return { key: u.searchParams.get('key') ?? '', markers };
  } catch {
    return null;
  }
}


/**
 * Bespoke Angular wrapper for A2UI Image Component.
 * Progressive enhancement: a Google Static Maps URL is upgraded to a live, interactive map.
 */
@Component({
  selector: 'a2ui-mat-image',
  standalone: true,
  imports: [GoogleMapsModule],
  template: `
    @if (mapInfo(); as info) {
      @if (mapsReady()) {
        <google-map
          height="320px"
          width="100%"
          [options]="mapOptions()"
          (mapInitialized)="fitToMarkers($event)">
          @for (m of info.markers; track $index) {
            <map-advanced-marker [position]="m" (mapClick)="selected.set(m)" />
          }
        </google-map>
        @if (selected(); as s) {
          <div style="font-size: 12px; margin: 6px 0 12px;">📍 {{ s.lat }}, {{ s.lng }}</div>
        }
      } @else if (mapsError()) {
        <img [src]="url()" style="width: 100%; border-radius: 8px; margin-bottom: 12px;" />
      } @else {
        <div style="height: 320px; display: grid; place-items: center;">Loading map…</div>
      }
        } @else {
      <img [src]="url()" [attr.alt]="alt()" [class]="'img ' + variant()" [style.object-fit]="fit()" />
    }
  `,
  styles: [`
    :host { display: block; }
    .img { display: block; width: 100%; max-height: 200px; border-radius: 8px; margin-bottom: 12px; }
    .img.icon { width: 24px; height: 24px; margin: 0; border-radius: 4px; }
    .img.avatar { width: 56px; height: 56px; margin: 0; border-radius: 50%; }
    .img.smallFeature { max-height: 140px; }
    .img.largeFeature { max-height: 360px; }
    .img.header { max-height: 180px; }
  `],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class MaterialImageComponent extends CatalogComponent<any> {
  url = computed(() => this.props()['url']?.value() || '');
  variant = computed(() => String(this.props()['variant']?.value() ?? 'mediumFeature'));
  fit = computed(() => {
    const f = String(this.props()['fit']?.value() ?? 'cover');
    return f === 'scaleDown' ? 'scale-down' : f;
  });
  alt = computed(() => String(this.props()['description']?.value() ?? ''));

  mapInfo = computed(() => parseStaticMapUrl(this.url()));

  mapsReady = signal(false);
  mapsError = signal(false);
  selected = signal<LatLng | null>(null);

  mapOptions = computed(() => ({
    mapId: 'DEMO_MAP_ID',
    center: this.mapInfo()?.markers[0] ?? { lat: 20, lng: 0 },
    zoom: 5,
    mapTypeControl: false,
    streetViewControl: false,
  }));

  // Field-initialised effect: loads the Maps JS API as soon as a map URL arrives.
  private readonly loadMaps = effect(() => {
    const info = this.mapInfo();
    if (!info?.key) return;
    loadGoogleMaps(info.key)
      .then(() => this.mapsReady.set(true))
      .catch(() => this.mapsError.set(true));
  });

  fitToMarkers(map: any) {
    const markers = this.mapInfo()?.markers ?? [];
    if (markers.length < 2) return;
    const bounds = new google.maps.LatLngBounds();
    markers.forEach((m) => bounds.extend(m));
    map.fitBounds(bounds);
  }
}



/**
 * Bespoke Angular Material <mat-select> dropdown for A2UI ChoicePicker.
 * Renders as a real dropdown instead of the default radio/checkbox list.
 */
@Component({
  selector: 'a2ui-mat-choicepicker',
  standalone: true,
  imports: [MatFormFieldModule, MatSelectModule, FormsModule],
  template: `
    <mat-form-field appearance="outline" style="width: 100%; margin-bottom: 12px;">
      <mat-label>{{ label() }}</mat-label>
      <mat-select
        [multiple]="isMultiple()"
        [ngModel]="isMultiple() ? selected() : selected()[0]"
        (ngModelChange)="onValueChange($event)">
        @for (opt of options(); track opt.value) {
          <mat-option [value]="opt.value">{{ opt.label }}</mat-option>
        }
      </mat-select>
    </mat-form-field>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class MaterialChoicePickerComponent extends CatalogComponent<typeof ChoicePickerApi> {
  label = computed(() => this.props()['label']?.value() || '');

  // "multipleSelection" -> multi-select dropdown; default is single-select
  isMultiple = computed(
    () => this.props()['variant']?.value() === 'multipleSelection'
  );

  options = computed(() => {
    const raw = (this.props()['options']?.value() as any) || [];
    if (!Array.isArray(raw)) return [];
    return raw.map((o: any) => ({
      value: String(o?.value ?? ''),
      // label may arrive as a plain string or a resolved DynamicString
      label: String(
        typeof o?.label === 'object' ? (o?.label?.value ?? o?.value) : (o?.label ?? o?.value)
      ),
    }));
  });

  // A2UI binds ChoicePicker.value to a string ARRAY, even when single-select
  selected = computed<string[]>(() => {
    const val = this.props()['value']?.value() as any;
    if (Array.isArray(val)) return val.map(String);
    if (val === undefined || val === null || val === '') return [];
    return [String(val)];
  });

  onValueChange(newValue: string | string[]) {
    const next = Array.isArray(newValue) ? newValue : newValue ? [newValue] : [];
    this.props()['value']?.onUpdate(next);
  }
}


// ---------------------------------------------------------------------------
// Extended components: Table + Chart
// These mirror backend/manager_dashboard/catalogs/extended_catalog.json.
// Without them the renderer silently skips "Table"/"Chart" nodes.
// ---------------------------------------------------------------------------

const DynamicValue = z.union([
  z.string(), z.number(), z.boolean(), z.array(z.any()),
  z.object({ path: z.string() }).passthrough(),
  z.object({ call: z.string() }).passthrough(),
]);
const DynamicStr = z.union([z.string(), z.object({ path: z.string() }).passthrough()]);
const ExtCommon = {
  accessibility: z.any().optional(),
  weight: z.number().optional(),
};

export const TableApi = {
  name: 'Table',
  schema: z.object({
    ...ExtCommon,
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

type TableColumn = { key: string; label: string; type?: 'text' | 'number'; editable?: boolean };

/** Unwraps a bound prop and guarantees an array of row objects. */
function asRows(raw: any): Record<string, any>[] {
  if (Array.isArray(raw)) return raw.filter((r) => r && typeof r === 'object');
  if (raw && typeof raw === 'object' && Array.isArray(raw.rows)) return raw.rows;
  return [];
}

@Component({
  selector: 'a2ui-mat-table',
  standalone: true,
  template: `
    @if (title()) { <div class="t-title">{{ title() }}</div> }
    <div class="t-wrap">
      <table>
        <thead>
          <tr>
            @for (c of columns(); track c.key) {
              <th [class.num]="c.type === 'number'">
                {{ c.label }}
                @if (c.editable) { <span class="edit-mark" title="Editable">&#9998;</span> }
              </th>
            }
          </tr>
        </thead>
        <tbody>
          @for (r of pageRows(); track $index; let ri = $index) {
            <tr>
              @for (c of columns(); track c.key) {
                <td [class.num]="c.type === 'number'" [class.editable]="c.editable">
                  @if (c.editable) {
                    <input
                      class="cell-input"
                      [class.num]="c.type === 'number'"
                      [type]="c.type === 'number' ? 'number' : 'text'"
                      [value]="r[c.key] ?? ''"
                      [attr.aria-label]="c.label"
                      (change)="editCell(pageStart() + ri, c, $any($event.target).value)" />
                  } @else {
                    {{ r[c.key] ?? '' }}
                  }
                </td>
              }
            </tr>
          } @empty {
            <tr><td [attr.colspan]="columns().length || 1" class="empty">No data</td></tr>
          }
        </tbody>
      </table>
    </div>
    @if (pageCount() > 1) {
      <div class="t-pager">
        <button (click)="page.set(page() - 1)" [disabled]="page() === 0">&lsaquo;</button>
        <span>{{ page() + 1 }} / {{ pageCount() }}</span>
        <button (click)="page.set(page() + 1)" [disabled]="page() >= pageCount() - 1">&rsaquo;</button>
      </div>
    }
  `,
  styles: [`
    :host { display: block; width: 100%; margin-bottom: 16px; }
    .t-title { font-weight: 500; margin-bottom: 8px; }
    .t-wrap { overflow-x: auto; border: 1px solid #e0e3e7; border-radius: 8px; }
    table { width: 100%; border-collapse: collapse; font-size: 13px; }
    th, td { padding: 8px 12px; text-align: left; border-bottom: 1px solid #eef0f2; }
    th { background: #f8f9fa; font-weight: 500; }
    .num { text-align: right; }
    .empty { text-align: center; color: #80868b; }
    .edit-mark { color: #1a73e8; font-size: 11px; margin-left: 4px; }
    td.editable { padding: 4px 8px; background: #f8fbff; }
    .cell-input {
      display: block; width: 100%; min-width: 64px; box-sizing: border-box;
      font: inherit; font-size: 13px; line-height: 20px; padding: 4px 8px;
      color: #202124; -webkit-text-fill-color: #202124; caret-color: #1a73e8;
      color-scheme: light;             /* stop the OS dark theme from making the text white */
      background: #ffffff; border: 1px solid #dadce0; border-radius: 4px;
    }
    .cell-input.num { text-align: right; }
    .cell-input::placeholder { color: #9aa0a6; -webkit-text-fill-color: #9aa0a6; }
    .cell-input:hover { border-color: #9aa0a6; }
    .cell-input:focus { outline: none; border-color: #1a73e8; box-shadow: 0 0 0 1px #1a73e8; }

    .t-pager { display: flex; gap: 8px; align-items: center; justify-content: flex-end; margin-top: 6px; font-size: 12px; }
    .t-pager button { border: 1px solid #dadce0; background: #fff; border-radius: 4px; cursor: pointer; padding: 2px 8px; }
  `],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class MaterialTableComponent extends CatalogComponent<any> {
  title = computed(() => this.props()['title']?.value() || '');
  columns = computed<TableColumn[]>(() => {
    const raw = this.props()['columns']?.value();
    return Array.isArray(raw) ? raw : [];
  });
  rows = computed(() => asRows(this.props()['rows']?.value()));
  pageSize = computed(() => Number(this.props()['pageSize']?.value()) || 5);
  page = signal(0);
  pageCount = computed(() => Math.max(1, Math.ceil(this.rows().length / this.pageSize())));
  pageStart = computed(() => Math.min(this.page(), this.pageCount() - 1) * this.pageSize());
  pageRows = computed(() => this.rows().slice(this.pageStart(), this.pageStart() + this.pageSize()));

  /**
   * Writes one edited cell back to the data model at the bound `rows` path, so a
   * Button whose action context references the same path sends the edited rows.
   */
  editCell(rowIndex: number, column: TableColumn, text: string): void {
    const rowsProp = this.props()['rows'];
    const current = rowsProp?.value();
    const next = this.rows().map((row) => ({ ...row }));
    if (!next[rowIndex]) return;

    if (column.type === 'number') {
      const num = Number(text);
      next[rowIndex][column.key] = text.trim() === '' || Number.isNaN(num) ? null : num;
    } else {
      next[rowIndex][column.key] = text;
    }

    // Keep the shape the agent bound: either the array itself or {rows: [...]}.
    const isWrapped = current && !Array.isArray(current) && Array.isArray(current.rows);
    rowsProp?.onUpdate(isWrapped ? { ...current, rows: next } : next);
  }
}


/**
 * Grid: a responsive collection layout. The agent only says "these are items"
 * (plus an optional column count the user asked for); every pixel decision
 * (gap, min card width, collapsing on narrow screens) lives here.
 */
export const GridApi = {
  name: 'Grid',
  schema: z.object({
    ...ExtCommon,
    children: childList(),
    columns: z.number().int().min(1).max(4).optional(),
  }),
};

@Component({
  selector: 'a2ui-mat-grid',
  standalone: true,
  imports: [ComponentHostComponent],
  template: `
    <div class="grid" [class.fixed]="!!columns()" [style.--cols]="columns()">
      @for (child of children(); track $index) {
        <div class="cell">
          <a2ui-v09-component-host [componentKey]="child" [surfaceId]="surfaceId()" />
        </div>
      }
    </div>
  `,
  styles: [`
    :host { display: block; width: 100%; margin-bottom: 12px; }
    .grid {
      --gap: var(--a2ui-grid-gap, 12px);
      --min: var(--a2ui-grid-min, 180px);
      display: grid;
      gap: var(--gap);
      grid-template-columns: repeat(auto-fill, minmax(var(--min), 1fr));
    }
    /* At most --cols columns; drops to fewer on its own when a column would be narrower than --min. */
    .grid.fixed {
      grid-template-columns: repeat(auto-fill,
        minmax(max(var(--min), calc((100% - (var(--cols) - 1) * var(--gap)) / var(--cols))), 1fr));
    }
    .cell { min-width: 0; display: flex; }
    .cell > * { flex: 1; min-width: 0; }
  `],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class MaterialGridComponent extends CatalogComponent<typeof GridApi> {
  children = computed(() => this.props()['children']?.value() || []);
  columns = computed(() => {
    const n = Number(this.props()['columns']?.value());
    return n >= 1 && n <= 4 ? Math.floor(n) : null;
  });
}


/**
 * Bespoke Angular Material Extended Catalog for A2UI v0.9
 */
@Injectable({
  providedIn: 'root',
})
export class MaterialBasicCatalog extends BasicCatalogBase {
  constructor() {
    super({
      components: {
        card: { ...CardApi, component: MaterialCardComponent },
        button: { ...ButtonApi, component: MaterialButtonComponent },
        divider: { ...DividerApi, component: MaterialDividerComponent },
        dateTimeInput: { ...DateTimeInputApi, component: MaterialDateTimeInputComponent },
        textField: { ...TextFieldApi, component: MaterialTextFieldComponent },
        checkBox: { ...CheckBoxApi, component: MaterialCheckboxComponent },
        choicePicker: { ...ChoicePickerApi, component: MaterialChoicePickerComponent },
        row: { ...RowApi, component: MaterialRowComponent },
        icon: { ...IconApi, component: MaterialIconComponent },
        image: { ...ImageApi, component: MaterialImageComponent },
      },
      extraComponents: [
        { ...TableApi, component: MaterialTableComponent },
        { ...ChartApi, component: MaterialChartComponent },
        { ...VegaChartApi, component: MaterialVegaChartComponent },
        { ...GridApi, component: MaterialGridComponent },
      ]
    });
  }
}

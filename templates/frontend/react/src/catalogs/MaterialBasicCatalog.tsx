import React from 'react';
import {
  Card,
  CardContent,
  Button,
  Divider,
  Box,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  OutlinedInput,
  Checkbox,
  FormControlLabel,
} from '@mui/material';
import { basicCatalog, createComponentImplementation, ReactComponentImplementation } from '@a2ui/react/v0_9';
import {
  Catalog,
  CardApi,
  RowApi,
  ButtonApi,
  DividerApi,
  IconApi,
  ImageApi,
  TextFieldApi,
  CheckBoxApi,
  ChoicePickerApi,
  DateTimeInputApi,
} from '@a2ui/web_core/v0_9';

import { LocalizationProvider, DatePicker, TimePicker } from '@mui/x-date-pickers';
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs';
import dayjs from 'dayjs';

import { MaterialChart, MaterialVegaChart } from './vega-components';
import { MaterialTable } from './table-component';
import { GoogleMapView, parseStaticMapUrl } from './google-map';
import { MaterialGrid } from './grid-component';
import { MaterialText } from './text-component';

/**
 * 1. Card  —  mirrors MaterialCardComponent (<mat-card appearance="outlined">)
 */
const MaterialCard = createComponentImplementation(CardApi, ({ props, buildChild }) => (
  <Card
    variant="outlined"
    sx={{
      width: '100%',
      boxSizing: 'border-box',
      borderRadius: 'var(--a2ui-card-border-radius, 24px)',
      background: 'var(--a2ui-card-background, #ffffff)',
      boxShadow: 'var(--a2ui-card-box-shadow)',
      border: 'var(--a2ui-card-border, 1px solid #e0e3e7)',
      padding: '6px 10px',
      mb: 2,
    }}
  >
    <CardContent sx={{ p: 1, '&:last-child': { pb: 1 } }}>
      {props.child ? buildChild(props.child) : null}
    </CardContent>
  </Card>
));

/**
 * 2. Button  —  mirrors MaterialButtonComponent
 * NOTE: A2UI Buttons render a CHILD component (usually a Text), not a `label` string.
 */
const MaterialButton = createComponentImplementation(ButtonApi, ({ props, buildChild }) => (
  <Button
    disableElevation={false}
    disabled={props.isValid === false}
    onClick={props.action}
    sx={{
      borderRadius: '4px',
      fontFamily: "var(--font-family-sans, 'Google Sans', sans-serif)",
      fontSize: 14,
      fontWeight: 500,
      textTransform: 'none',
      padding: '10px 20px',
      backgroundColor: '#1a73e8',
      border: 'none',
      boxShadow: '0 1px 2px 0 rgba(60,64,67,0.3), 0 1px 3px 1px rgba(60,64,67,0.15)',
      transition: 'box-shadow 0.2s ease-in-out, background-color 0.2s ease-in-out',
      // Equivalent of Angular's ::ng-deep — force the child Text to render white
      '& *': { color: '#ffffff !important' },
      '&:hover:not(:disabled)': {
        boxShadow: '0 1px 3px 0 rgba(60,64,67,0.3), 0 4px 8px 3px rgba(60,64,67,0.15)',
        backgroundColor: '#1557b0',
      },
      '&:disabled': {
        backgroundColor: '#cccccc',
        boxShadow: 'none',
        cursor: 'not-allowed',
        '& *': { color: '#ffffff !important' },
      },
    }}
  >
    {props.child ? buildChild(props.child) : null}
  </Button>
));

/**
 * 3. Divider  —  mirrors MaterialDividerComponent
 */
const MaterialDivider = createComponentImplementation(DividerApi, () => (
  <Divider sx={{ my: '14px', borderTopColor: 'var(--google-grey-200, #e8eaed)' }} />
));

/**
 * 4. TextField  —  mirrors MaterialTextFieldComponent (bespoke native input, NOT mat-form-field)
 */
const MaterialTextField = createComponentImplementation(TextFieldApi, ({ props }) => {
  const [focused, setFocused] = React.useState(false);

  return (
    <div
      style={{
        width: '100%',
        marginBottom: 12,
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      <label
        style={{
          fontSize: 12,
          fontWeight: 'bold',
          marginBottom: 4,
          fontFamily: 'sans-serif',
          color: '#333333',
        }}
      >
        {props.label || ''}
      </label>
      <input
        type="text"
        value={props.value ?? ''}
        onChange={(e) => props.setValue(e.target.value)}
        onFocus={() => setFocused(true)}
        onBlur={() => setFocused(false)}
        style={{
          padding: focused ? 11 : 12,
          border: focused ? '2px solid #1a73e8' : '1px solid #000000',
          borderRadius: 4,
          // Force browser dark-mode engines to back off
          colorScheme: 'light',
          background: '#ffffff',
          color: '#000000',
          WebkitAppearance: 'none',
          appearance: 'none',
          fontSize: 16,
          fontFamily: 'sans-serif',
          boxSizing: 'border-box',
          outline: 'none',
        }}
      />
    </div>
  );
});

/**
 * 5. CheckBox  —  mirrors MaterialCheckboxComponent (<mat-checkbox>)
 */
const MaterialCheckbox = createComponentImplementation(CheckBoxApi, ({ props }) => {
  const checked = props.value === true || String(props.value) === 'true';

  return (
    <FormControlLabel
      sx={{ mb: '12px' }}
      control={
        <Checkbox
          checked={checked}
          onChange={(e) => props.setValue(e.target.checked)}
          sx={{ color: '#1a73e8', '&.Mui-checked': { color: '#1a73e8' } }}
        />
      }
      label={props.label || ''}
    />
  );
});

/**
 * 6. Row  —  mirrors MaterialRowComponent (flex row, gap 24px, each child in a block wrapper)
 *
 * A2UI child lists hold EITHER a plain component id, OR a {id, basePath} ref
 * (the latter when the row sits inside a repeated/List data context). Handle both,
 * otherwise nested rows silently render empty.
 */
const JUSTIFY: Record<string, string> = {
  start: 'flex-start', center: 'center', end: 'flex-end', stretch: 'stretch',
  spaceBetween: 'space-between', spaceAround: 'space-around', spaceEvenly: 'space-evenly',
};
const ALIGN: Record<string, string> = { start: 'flex-start', center: 'center', end: 'flex-end', stretch: 'stretch' };

const MaterialRow = createComponentImplementation(RowApi, ({ props, buildChild }) => {
  const p = props as any;
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'row',
        flexWrap: 'wrap', // never overflow the card
        rowGap: 8,
        columnGap: 12,
        justifyContent: JUSTIFY[String(p.justify ?? 'start')] ?? 'flex-start',
        alignItems: ALIGN[String(p.align ?? 'center')] ?? 'center',
      }}
    >
      {(props.children || []).map((child, i) => (
        <div key={i} style={{ display: 'block' }}>
          {typeof child === 'string' ? buildChild(child) : buildChild(child.id, child.basePath)}
        </div>
      ))}
    </div>
  );
});


/**
 * 7. DateTimeInput  —  mirrors MaterialDateTimeInputComponent
 * (mat-datepicker + mat-timepicker → MUI X DatePicker / TimePicker)
 */
const MaterialDateTimeInput = createComponentImplementation(DateTimeInputApi, ({ props }) => {
  const label = props.label || '';
  const showTime = props.enableTime === true;
  // Back-compat: if neither flag is set, behave as a plain date picker
  const showDate = props.enableDate === true || !showTime;

  const raw = String(props.value ?? '');

  // Accepts "2026-09-18", "2026-09-18T14:30", "2026-09-18T14:30:00.000Z"
  const dm = raw.match(/^(\d{4})-(\d{2})-(\d{2})/);
  const dateValue = dm ? new Date(Number(dm[1]), Number(dm[2]) - 1, Number(dm[3])) : null;

  // Accepts "14:30" or the time portion of a full ISO string
  const tm = raw.match(/(?:^|T)(\d{2}):(\d{2})/);
  let timeValue: Date | null = null;
  if (tm) {
    const base = dateValue ?? new Date();
    timeValue = new Date(base);
    timeValue.setHours(Number(tm[1]), Number(tm[2]), 0, 0);
  }

  const pad = (n: number) => String(n).padStart(2, '0');

  /** Emits YYYY-MM-DD for date-only, or full ISO YYYY-MM-DDTHH:MM:00 whenever a time is set. */
  const commit = (date: Date | null, time: Date | null) => {
    // A time-only field still needs a date anchor, or datetime.fromisoformat() rejects it
    const d = date ?? (time ? new Date() : null);
    const datePart = d ? `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}` : '';
    const timePart = time ? `${pad(time.getHours())}:${pad(time.getMinutes())}:00` : '';
    props.setValue(timePart ? `${datePart}T${timePart}` : datePart);
  };

  return (
    <LocalizationProvider dateAdapter={AdapterDayjs}>
      <Box sx={{ display: 'flex', gap: '12px', width: '100%' }}>
        {showDate && (
          <DatePicker
            label={label || 'Pick a date'}
            value={dateValue ? dayjs(dateValue) : null}
            onChange={(v) =>
              commit(v && v.isValid() ? v.toDate() : null, showTime ? timeValue : null)
            }
            slotProps={{ textField: { sx: { flex: 1, mb: '12px' } } }}
          />
        )}
        {showTime && (
          <TimePicker
            label={label || 'Pick a time'}
            value={timeValue ? dayjs(timeValue) : null}
            // minutesStep={5}
            onChange={(v) =>
              commit(showDate ? dateValue : null, v && v.isValid() ? v.toDate() : null)
            }
            slotProps={{ textField: { sx: { flex: 1, mb: '12px' } } }}
          />
        )}
      </Box>
    </LocalizationProvider>
  );
});

/**
 * A2UI catalog Icon names -> Material Icons ligature names.
 *
 * Most catalog names map by simply camelCase -> snake_case (locationOn -> location_on).
 * These four have NO matching ligature in the Material Icons font at all, so the
 * font falls back to rendering the raw text. They must be mapped explicitly.
 */
const ICON_LIGATURE_OVERRIDES: Record<string, string> = {
  play: 'play_arrow',
  rewind: 'fast_rewind',
  favoriteOff: 'favorite_border',
  starOff: 'star_border',
};

const toMaterialLigature = (name: string): string =>
  ICON_LIGATURE_OVERRIDES[name] ??
  name.replace(/[A-Z]/g, (l) => `_${l.toLowerCase()}`);

/**
 * 8. Icon  —  mirrors MaterialIconComponent (<mat-icon>)
 */
const MaterialIcon = createComponentImplementation(IconApi, ({ props }) => {
  const iconName = typeof props.name === 'string' ? props.name : String(props.name ?? '');
  const ligature = toMaterialLigature(iconName);

  return (
    <span
      className="material-icons a2ui-icon"
      style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        width: 24,
        height: 24,
        fontSize: 24,
        color: 'inherit',
      }}
    >
      {ligature}
    </span>
  );
});

/**
 * 9. Image  —  mirrors MaterialImageComponent
 * Size comes ONLY from the semantic `variant`; the agent never sends width/height.
 */
const IMG_BASE: React.CSSProperties = {
  display: 'block', width: '100%', maxHeight: 200, borderRadius: 8, marginBottom: 12,
};
const IMG_VARIANT: Record<string, React.CSSProperties> = {
  icon: { width: 24, height: 24, margin: 0, borderRadius: 4 },
  avatar: { width: 56, height: 56, margin: 0, borderRadius: '50%' },
  smallFeature: { maxHeight: 140 },
  mediumFeature: {},
  largeFeature: { maxHeight: 360 },
  header: { maxHeight: 180 },
};

const MaterialImage = createComponentImplementation(ImageApi, ({ props }) => {
  const p = props as any;
  const url = String(p.url || '');
  // A Google Static Maps URL (from viz.save_google_map) becomes a live Google Map.
  const mapInfo = parseStaticMapUrl(url);
  if (mapInfo?.key) return <GoogleMapView info={mapInfo} fallbackUrl={url} />;

  const variant = String(p.variant ?? 'mediumFeature');
  const fitRaw = String(p.fit ?? 'cover');
  const fit = (fitRaw === 'scaleDown' ? 'scale-down' : fitRaw) as React.CSSProperties['objectFit'];
  return (
    <img
      src={url}
      alt={String(p.description ?? '')}
      style={{ ...IMG_BASE, ...(IMG_VARIANT[variant] ?? {}), objectFit: fit }}
    />
  );
});


/**
 * 10. ChoicePicker  —  mirrors MaterialChoicePickerComponent (<mat-select> real dropdown)
 */
const MaterialChoicePicker = createComponentImplementation(ChoicePickerApi, ({ props }) => {
  const label = props.label || '';

  // "multipleSelection" -> multi-select dropdown; default is single-select
  const isMultiple = props.variant === 'multipleSelection';

  const options = (Array.isArray(props.options) ? props.options : []).map((o: any) => ({
    value: String(o?.value ?? ''),
    // label may arrive as a plain string or a resolved DynamicString
    label: String(
      typeof o?.label === 'object' ? (o?.label?.value ?? o?.value) : (o?.label ?? o?.value)
    ),
  }));

  // A2UI binds ChoicePicker.value to a string ARRAY, even when single-select
  let selected: string[] = [];
  if (Array.isArray(props.value)) selected = props.value.map(String);
  else if (props.value !== undefined && props.value !== null && props.value !== '')
    selected = [String(props.value)];

  const onValueChange = (v: string | string[]) => {
    const next = Array.isArray(v) ? v : v ? [v] : [];
    props.setValue(next);
  };

  return (
    <FormControl fullWidth sx={{ mb: '12px' }}>
      <InputLabel>{label}</InputLabel>
      <Select
        multiple={isMultiple}
        value={isMultiple ? selected : (selected[0] ?? '')}
        onChange={(e) => onValueChange(e.target.value as string | string[])}
        input={<OutlinedInput label={label} />}
      >
        {options.map((opt) => (
          <MenuItem key={opt.value} value={opt.value}>
            {opt.label}
          </MenuItem>
        ))}
      </Select>
    </FormControl>
  );
});

/**
 * Bespoke React Material Extended Catalog for A2UI v0.9
 * (1:1 with Angular's MaterialBasicCatalog)
 *
 * Built as a real Catalog (not an object spread) so the id, the basic functions
 * (formatString, formatCurrency, length, ...) and the function invoker all stay
 * wired up. Table / Chart / VegaChart mirror backend extended_catalog.json;
 * without them the renderer silently skips those nodes.
 */
const overrides: ReactComponentImplementation[] = [
  MaterialCard,
  MaterialButton,
  MaterialDivider,
  MaterialDateTimeInput,
  MaterialTextField,
  MaterialCheckbox,
  MaterialChoicePicker,
  MaterialRow,
  MaterialIcon,
  MaterialImage,
  MaterialTable,
  MaterialChart,
  MaterialVegaChart,
  MaterialGrid,
  MaterialText,
];
const components = new Map<string, ReactComponentImplementation>(basicCatalog.components);
for (const impl of overrides) components.set(impl.name, impl);
export const materialCatalog = new Catalog<ReactComponentImplementation>(
  basicCatalog.id,
  [...components.values()],
  [...basicCatalog.functions.values()],
  basicCatalog.themeSchema,
);
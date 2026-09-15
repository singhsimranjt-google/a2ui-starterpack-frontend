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
import { basicCatalog, createComponentImplementation } from '@a2ui/react/v0_9';
import {
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
const MaterialRow = createComponentImplementation(RowApi, ({ props, buildChild }) => (
  <div style={{ display: 'flex', flexDirection: 'row', alignItems: 'center', gap: 24 }}>
    {(props.children || []).map((child, i) => (
      <div key={i} style={{ display: 'block' }}>
        {typeof child === 'string'
          ? buildChild(child)
          : buildChild(child.id, child.basePath)}
      </div>
    ))}
  </div>
));

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
            minutesStep={30}              /* Angular's interval="30min" */
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
 * 8. Icon  —  mirrors MaterialIconComponent (<mat-icon>)
 */
const MaterialIcon = createComponentImplementation(IconApi, ({ props }) => {
  const iconName = typeof props.name === 'string' ? props.name : String(props.name ?? '');
  // The Material Icons ligature font expects snake_case (locationOn -> location_on)
  const ligature = iconName.replace(/[A-Z]/g, (l) => `_${l.toLowerCase()}`);

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
 */
const MaterialImage = createComponentImplementation(ImageApi, ({ props }) => (
  <img
    src={props.url || ''}
    style={{
      width: '100%',
      maxHeight: 200,
      objectFit: 'cover',
      borderRadius: 8,
      marginBottom: 12,
    }}
  />
));

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
 */
export const materialCatalog = {
  ...basicCatalog,
  components: new Map([
    ...basicCatalog.components,
    [CardApi.name, MaterialCard],
    [ButtonApi.name, MaterialButton],
    [DividerApi.name, MaterialDivider],
    [DateTimeInputApi.name, MaterialDateTimeInput],
    [TextFieldApi.name, MaterialTextField],
    [CheckBoxApi.name, MaterialCheckbox],
    [ChoicePickerApi.name, MaterialChoicePicker],
    [RowApi.name, MaterialRow],
    [IconApi.name, MaterialIcon],
    [ImageApi.name, MaterialImage],
  ]),
};

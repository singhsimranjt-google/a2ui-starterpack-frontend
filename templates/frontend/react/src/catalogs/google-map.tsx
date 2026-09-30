/**
 * Google Maps for the A2UI Image component (React port of the Angular
 * MaterialImageComponent upgrade).
 *
 * Progressive enhancement: when an Image `url` is a Google Static Maps URL
 * (built server-side by viz.save_google_map), it is upgraded to a live,
 * interactive Google Map using the same key and markers. If the Maps JS API
 * fails to load, the static image is shown instead. No extra npm packages.
 */
import React from 'react';

declare const google: any;

export type LatLng = { lat: number; lng: number };

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
export function parseStaticMapUrl(url: string): { key: string; markers: LatLng[] } | null {
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

export function GoogleMapView({ info, fallbackUrl }: {
  info: { key: string; markers: LatLng[] };
  fallbackUrl: string;
}) {
  const host = React.useRef<HTMLDivElement>(null);
  const [status, setStatus] = React.useState<'loading' | 'ready' | 'error'>('loading');
  const [selected, setSelected] = React.useState<LatLng | null>(null);
  // Rebuild the map only when the key or markers actually change.
  const infoKey = JSON.stringify(info);

  React.useEffect(() => {
    let cancelled = false;
    const markers: any[] = [];
    setStatus('loading');
    loadGoogleMaps(info.key)
      .then(() => {
        if (cancelled || !host.current) return;
        const map = new google.maps.Map(host.current, {
          center: info.markers[0] ?? { lat: 20, lng: 0 },
          zoom: 5,
          mapId: 'DEMO_MAP_ID',
          mapTypeControl: false,
          streetViewControl: false,
        });
        for (const m of info.markers) {
          const marker = new google.maps.marker.AdvancedMarkerElement({ position: m, map });
          marker.addListener('click', () => setSelected(m));
          markers.push(marker);
        }
        if (info.markers.length > 1) {
          const bounds = new google.maps.LatLngBounds();
          info.markers.forEach((m) => bounds.extend(m));
          map.fitBounds(bounds);
        }
        setStatus('ready');
      })
      .catch(() => {
        if (!cancelled) setStatus('error');
      });
    return () => {
      cancelled = true;
      // markers.forEach((marker) => marker.setMap(null));
      markers.forEach((marker) => (marker.map = null));
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [infoKey]);

  if (status === 'error') {
    return <img src={fallbackUrl} style={{ width: '100%', borderRadius: 8, marginBottom: 12 }} />;
  }
  return (
    <div style={{ width: '100%', marginBottom: 12 }}>
      <div style={{ position: 'relative', width: '100%', height: 320, borderRadius: 8, overflow: 'hidden' }}>
        <div ref={host} style={{ width: '100%', height: '100%' }} />
        {status === 'loading' && (
          <div style={{ position: 'absolute', inset: 0, display: 'grid', placeItems: 'center', color: '#80868b', fontSize: 13 }}>
            Loading map…
          </div>
        )}
      </div>
      {selected && (
        <div style={{ fontSize: 12, margin: '6px 0 0' }}>📍 {selected.lat}, {selected.lng}</div>
      )}
    </div>
  );
}

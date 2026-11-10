import { useEffect, useMemo } from 'react';
import { MapContainer, Marker, Popup, TileLayer, useMap } from 'react-leaflet';
import L from 'leaflet';

import 'leaflet/dist/leaflet.css';

import EmptyState from './EmptyState';

/**
 * Icono de marcador generado con `divIcon` (evita problemas con las rutas de
 * los assets de Leaflet al empaquetar con Vite).
 */
const pinIcon = (color) =>
  L.divIcon({
    className: 'map-pin',
    html: `<span class="map-pin__dot" style="background-color:${color}"></span>`,
    iconSize: [20, 20],
    iconAnchor: [10, 20],
    popupAnchor: [0, -18],
  });

/** Ajusta el mapa para que todos los marcadores sean visibles. */
function FitBounds({ signature, points }) {
  const map = useMap();

  useEffect(() => {
    if (!points.length) return;
    const bounds = L.latLngBounds(points.map((point) => [point.lat, point.lon]));
    map.fitBounds(bounds.pad(0.25), { maxZoom: 16 });
    // `signature` representa las coordenadas: evita re-centrar en cada render
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [signature]);

  return null;
}

/**
 * Mapa interactivo con OpenStreetMap.
 *
 * Uso de teselas: se solicitan únicamente las visibles en pantalla desde el
 * servidor oficial de OpenStreetMap (`tile.openstreetmap.org`) con su
 * atribución. No se cachean ni se reutilizan teselas fuera de este panel.
 */
export default function MapView({ points = [], emptyTitle, emptyDescription, legend }) {
  const signature = useMemo(
    () => points.map((point) => `${point.lat}:${point.lon}`).join('|'),
    [points],
  );

  if (!points.length) {
    return (
      <EmptyState icon="🗺️" title={emptyTitle} description={emptyDescription} />
    );
  }

  const center = [points[0].lat, points[0].lon];

  return (
    <div className="map-frame">
      <MapContainer center={center} zoom={13} className="map-frame__canvas" scrollWheelZoom>
        <TileLayer
          url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contribuidores'
          maxZoom={19}
        />
        <FitBounds signature={signature} points={points} />
        {points.map((point) => (
          <Marker key={point.id} position={[point.lat, point.lon]} icon={pinIcon(point.color)}>
            <Popup>
              <strong>{point.title}</strong>
              <br />
              <span className="mono">
                {point.lat.toFixed(5)}, {point.lon.toFixed(5)}
              </span>
              <br />
              <span>{point.fecha}</span>
              {point.extra && (
                <>
                  <br />
                  <span>{point.extra}</span>
                </>
              )}
            </Popup>
          </Marker>
        ))}
      </MapContainer>
      {legend && <div className="map-legend">{legend}</div>}
    </div>
  );
}

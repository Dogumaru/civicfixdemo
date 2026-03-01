import { useState, useEffect, useRef } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import { fetchReports, fetchHeatmapData } from '../api';
import { Layers, Filter, RefreshCw } from 'lucide-react';

// Fix default marker icons
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
});

const SEVERITY_MARKER_COLORS = {
  LOW: '#22c55e',
  MEDIUM: '#f59e0b',
  HIGH: '#f97316',
  CRITICAL: '#ef4444',
};

const CATEGORY_ICONS = {
  pothole: '🕳️',
  streetlight: '💡',
  trash: '🗑️',
  graffiti: '🎨',
  other: '❓',
};

function createCustomIcon(severity) {
  const color = SEVERITY_MARKER_COLORS[severity] || '#3b82f6';
  return L.divIcon({
    className: 'custom-marker',
    html: `<div style="
      width: 24px; height: 24px; border-radius: 50%;
      background: ${color}; border: 3px solid white;
      box-shadow: 0 2px 8px rgba(0,0,0,0.3);
    "></div>`,
    iconSize: [24, 24],
    iconAnchor: [12, 12],
  });
}

// Heatmap layer component
function HeatmapLayer({ points }) {
  const map = useMap();

  useEffect(() => {
    if (!points.length) return;

    // Simple circle-based heatmap (no extra library needed)
    const circles = points.map(p =>
      L.circle([p.latitude, p.longitude], {
        radius: 200 + p.intensity * 300,
        color: 'transparent',
        fillColor: p.intensity > 0.7 ? '#ef4444' : p.intensity > 0.4 ? '#f97316' : '#f59e0b',
        fillOpacity: 0.25,
      })
    );

    const group = L.layerGroup(circles);
    group.addTo(map);

    return () => {
      map.removeLayer(group);
    };
  }, [points, map]);

  return null;
}

export default function MapPage() {
  const [reports, setReports] = useState([]);
  const [heatmap, setHeatmap] = useState([]);
  const [showHeatmap, setShowHeatmap] = useState(true);
  const [filter, setFilter] = useState('all');
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    setLoading(true);
    try {
      const params = filter !== 'all' ? { category: filter } : {};
      const [reps, heat] = await Promise.all([
        fetchReports(params),
        fetchHeatmapData(),
      ]);
      setReports(reps);
      setHeatmap(heat);
    } catch (err) {
      console.error('Failed to load map data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [filter]);

  return (
    <div className="space-y-4">
      {/* Header & Controls */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">City Issue Map</h2>
          <p className="text-sm text-gray-500">{reports.length} reports plotted</p>
        </div>
        <div className="flex items-center gap-3">
          {/* Category Filter */}
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="border rounded-lg px-3 py-2 text-sm bg-white"
          >
            <option value="all">All Categories</option>
            <option value="pothole">🕳️ Potholes</option>
            <option value="streetlight">💡 Streetlights</option>
            <option value="trash">🗑️ Trash</option>
            <option value="graffiti">🎨 Graffiti</option>
          </select>

          {/* Heat map toggle */}
          <button
            onClick={() => setShowHeatmap(!showHeatmap)}
            className={`btn-secondary flex items-center gap-2 text-sm ${showHeatmap ? 'bg-orange-50 text-orange-700 border-orange-200' : ''}`}
          >
            <Layers size={16} />
            Heat Zones {showHeatmap ? 'ON' : 'OFF'}
          </button>

          <button onClick={loadData} className="btn-secondary flex items-center gap-2 text-sm">
            <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
            Refresh
          </button>
        </div>
      </div>

      {/* Legend */}
      <div className="flex items-center gap-4 text-xs">
        <span className="text-gray-500">Severity:</span>
        {Object.entries(SEVERITY_MARKER_COLORS).map(([label, color]) => (
          <span key={label} className="flex items-center gap-1">
            <span className="w-3 h-3 rounded-full inline-block" style={{ background: color }} />
            {label}
          </span>
        ))}
      </div>

      {/* Map */}
      <div className="card p-0 overflow-hidden" style={{ height: '600px' }}>
        <MapContainer
          center={[39.9526, -75.1652]}
          zoom={13}
          style={{ height: '100%', width: '100%' }}
          scrollWheelZoom={true}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          {showHeatmap && <HeatmapLayer points={heatmap} />}

          {reports.map((report) => (
            <Marker
              key={report.id}
              position={[report.latitude, report.longitude]}
              icon={createCustomIcon(report.severity)}
            >
              <Popup>
                <div className="text-sm min-w-[200px]">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-xl">{CATEGORY_ICONS[report.category]}</span>
                    <div>
                      <p className="font-bold capitalize">{report.category}</p>
                      <p className="text-xs text-gray-500">{report.address || 'No address'}</p>
                    </div>
                  </div>
                  <div className="space-y-1">
                    <p><strong>Severity:</strong> <span className={`badge ${
                      report.severity === 'CRITICAL' ? 'badge-critical' :
                      report.severity === 'HIGH' ? 'badge-high' :
                      report.severity === 'MEDIUM' ? 'badge-medium' : 'badge-low'
                    }`}>{report.severity}</span></p>
                    <p><strong>Confidence:</strong> {Math.round(report.confidence * 100)}%</p>
                    <p><strong>Status:</strong> {report.status}</p>
                    <p><strong>Est. Cost:</strong> ${report.estimated_cost?.toLocaleString()}</p>
                    <p className="text-xs text-gray-400 mt-1">
                      {new Date(report.created_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>
              </Popup>
            </Marker>
          ))}
        </MapContainer>
      </div>
    </div>
  );
}

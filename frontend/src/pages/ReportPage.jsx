import { useState, useRef, useCallback } from 'react';
import {
  Upload, Camera, MapPin, AlertTriangle, Clock, DollarSign,
  CheckCircle2, Loader2, Sparkles, ChevronRight
} from 'lucide-react';
import { uploadReport } from '../api';

const SEVERITY_COLORS = {
  LOW: 'badge-low',
  MEDIUM: 'badge-medium',
  HIGH: 'badge-high',
  CRITICAL: 'badge-critical',
};

const CATEGORY_ICONS = {
  pothole: '🕳️',
  streetlight: '💡',
  trash: '🗑️',
  graffiti: '🎨',
  other: '❓',
};

export default function ReportPage() {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const [location, setLocation] = useState({ lat: 39.9526, lng: -75.1652 });
  const [address, setAddress] = useState('');
  const [neighborhood, setNeighborhood] = useState('');
  const [reporterName, setReporterName] = useState('');
  const fileInputRef = useRef(null);

  const handleFile = useCallback((f) => {
    if (!f) return;
    setFile(f);
    setResult(null);
    const reader = new FileReader();
    reader.onload = (e) => setPreview(e.target.result);
    reader.readAsDataURL(f);
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setDragActive(false);
    if (e.dataTransfer.files?.[0]) handleFile(e.dataTransfer.files[0]);
  }, [handleFile]);

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    try {
      const report = await uploadReport(
        file, location.lat, location.lng, address, neighborhood, reporterName
      );
      setResult(report);
    } catch (err) {
      console.error(err);
      alert('Upload failed. Make sure the backend is running.');
    } finally {
      setUploading(false);
    }
  };

  const reset = () => {
    setFile(null);
    setPreview(null);
    setResult(null);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Header */}
      <div className="text-center">
        <h2 className="text-3xl font-bold text-gray-900">Report a City Issue</h2>
        <p className="mt-2 text-gray-500">Upload a photo and our AI will instantly classify the problem</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* ── Upload Section ── */}
        <div className="space-y-6">
          {/* Dropzone */}
          <div
            className={`dropzone ${dragActive ? 'active' : ''} ${preview ? 'border-civic-400 bg-civic-50' : ''}`}
            onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
            onDragLeave={() => setDragActive(false)}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              className="hidden"
              onChange={(e) => handleFile(e.target.files?.[0])}
            />

            {preview ? (
              <div className="space-y-3">
                <img src={preview} alt="Preview" className="max-h-64 mx-auto rounded-lg shadow-sm" />
                <p className="text-sm text-gray-500">{file?.name}</p>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="mx-auto w-16 h-16 bg-civic-100 rounded-full flex items-center justify-center">
                  <Camera className="h-8 w-8 text-civic-600" />
                </div>
                <div>
                  <p className="text-lg font-medium text-gray-700">Drop your photo here</p>
                  <p className="text-sm text-gray-400">or click to browse • JPG, PNG up to 10MB</p>
                </div>
              </div>
            )}
          </div>

          {/* Location & Details */}
          <div className="card space-y-4">
            <h3 className="font-semibold text-gray-800 flex items-center gap-2">
              <MapPin size={18} className="text-civic-600" /> Location Details
            </h3>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs text-gray-500">Latitude</label>
                <input
                  type="number"
                  step="0.0001"
                  value={location.lat}
                  onChange={(e) => setLocation(l => ({ ...l, lat: parseFloat(e.target.value) || 0 }))}
                  className="w-full border rounded-lg px-3 py-2 text-sm"
                />
              </div>
              <div>
                <label className="text-xs text-gray-500">Longitude</label>
                <input
                  type="number"
                  step="0.0001"
                  value={location.lng}
                  onChange={(e) => setLocation(l => ({ ...l, lng: parseFloat(e.target.value) || 0 }))}
                  className="w-full border rounded-lg px-3 py-2 text-sm"
                />
              </div>
            </div>
            <input
              placeholder="Street Address (optional)"
              value={address}
              onChange={(e) => setAddress(e.target.value)}
              className="w-full border rounded-lg px-3 py-2 text-sm"
            />
            <input
              placeholder="Neighborhood (optional)"
              value={neighborhood}
              onChange={(e) => setNeighborhood(e.target.value)}
              className="w-full border rounded-lg px-3 py-2 text-sm"
            />
            <input
              placeholder="Your Name (optional)"
              value={reporterName}
              onChange={(e) => setReporterName(e.target.value)}
              className="w-full border rounded-lg px-3 py-2 text-sm"
            />
          </div>

          {/* Submit */}
          <div className="flex gap-3">
            <button
              onClick={handleUpload}
              disabled={!file || uploading}
              className="btn-primary flex-1 flex items-center justify-center gap-2"
            >
              {uploading ? (
                <>
                  <Loader2 className="animate-spin" size={18} />
                  Analyzing...
                </>
              ) : (
                <>
                  <Sparkles size={18} />
                  Upload & Classify with AI
                </>
              )}
            </button>
            {(file || result) && (
              <button onClick={reset} className="btn-secondary">Reset</button>
            )}
          </div>
        </div>

        {/* ── Result Section ── */}
        <div>
          {result ? (
            <ClassificationResult report={result} />
          ) : (
            <div className="card h-full flex flex-col items-center justify-center text-gray-400 space-y-4">
              <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center">
                <Sparkles size={32} />
              </div>
              <div className="text-center">
                <p className="font-medium text-gray-500">AI Classification Results</p>
                <p className="text-sm">Upload a photo to see instant analysis</p>
              </div>
              <div className="text-left text-sm space-y-2 mt-4">
                <p className="flex items-center gap-2"><ChevronRight size={14} /> Issue category detection</p>
                <p className="flex items-center gap-2"><ChevronRight size={14} /> Confidence scoring</p>
                <p className="flex items-center gap-2"><ChevronRight size={14} /> Severity assessment</p>
                <p className="flex items-center gap-2"><ChevronRight size={14} /> Repair cost estimate</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}


function ClassificationResult({ report }) {
  return (
    <div className="classification-result space-y-5">
      {/* Category Header */}
      <div className="flex items-center gap-3">
        <span className="text-4xl">{CATEGORY_ICONS[report.category] || '❓'}</span>
        <div>
          <h3 className="text-xl font-bold text-gray-900 capitalize">{report.category} Detected</h3>
          <p className="text-sm text-gray-600">{report.description}</p>
        </div>
      </div>

      {/* Confidence Bar */}
      <div>
        <div className="flex justify-between text-sm mb-1">
          <span className="font-medium text-gray-700">AI Confidence</span>
          <span className="font-bold text-civic-700">{Math.round(report.confidence * 100)}%</span>
        </div>
        <div className="h-3 bg-gray-200 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-civic-400 to-civic-600 rounded-full transition-all duration-1000"
            style={{ width: `${report.confidence * 100}%` }}
          />
        </div>
      </div>

      {/* Severity */}
      <div className="flex items-center justify-between p-4 bg-white rounded-lg">
        <div className="flex items-center gap-2">
          <AlertTriangle size={20} className={
            report.severity === 'CRITICAL' ? 'text-red-500' :
            report.severity === 'HIGH' ? 'text-orange-500' :
            report.severity === 'MEDIUM' ? 'text-yellow-500' : 'text-green-500'
          } />
          <span className="font-medium">Severity</span>
        </div>
        <span className={`badge ${SEVERITY_COLORS[report.severity]}`}>
          {report.severity}
        </span>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 gap-3">
        <div className="bg-white rounded-lg p-4 text-center">
          <Clock size={20} className="mx-auto text-civic-600 mb-1" />
          <p className="text-2xl font-bold text-gray-900">{report.estimated_repair_days}d</p>
          <p className="text-xs text-gray-500">Est. Repair Time</p>
        </div>
        <div className="bg-white rounded-lg p-4 text-center">
          <DollarSign size={20} className="mx-auto text-civic-600 mb-1" />
          <p className="text-2xl font-bold text-gray-900">
            ${report.estimated_cost?.toLocaleString(undefined, { maximumFractionDigits: 0 })}
          </p>
          <p className="text-xs text-gray-500">Est. Cost</p>
        </div>
      </div>

      {/* Status */}
      <div className="flex items-center gap-2 text-green-600 bg-green-50 rounded-lg p-3">
        <CheckCircle2 size={20} />
        <span className="text-sm font-medium">Report submitted successfully — ID: {report.id?.slice(0, 8)}</span>
      </div>
    </div>
  );
}

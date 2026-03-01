import { useState, useEffect } from 'react';
import {
  Building2, Users, AlertTriangle, CheckCircle2, Clock, DollarSign,
  TrendingDown, MapPin, Filter, RefreshCw, ChevronDown, Loader2,
  UserCheck, XCircle, PlayCircle
} from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell
} from 'recharts';
import { fetchDashboardStats, fetchReports, updateReport, fetchNeighborhoods } from '../api';

const STATUS_CONFIG = {
  open: { color: 'text-red-600 bg-red-50', label: 'Open', icon: AlertTriangle },
  in_progress: { color: 'text-blue-600 bg-blue-50', label: 'In Progress', icon: PlayCircle },
  resolved: { color: 'text-green-600 bg-green-50', label: 'Resolved', icon: CheckCircle2 },
  closed: { color: 'text-gray-600 bg-gray-100', label: 'Closed', icon: XCircle },
};

const SEVERITY_COLORS = { LOW: '#22c55e', MEDIUM: '#f59e0b', HIGH: '#f97316', CRITICAL: '#ef4444' };

export default function AdminPage() {
  const [stats, setStats] = useState(null);
  const [reports, setReports] = useState([]);
  const [neighborhoods, setNeighborhoods] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState({ status: '', category: '', severity: '' });
  const [updatingId, setUpdatingId] = useState(null);

  const loadData = async () => {
    setLoading(true);
    try {
      const params = {};
      if (filter.status) params.status = filter.status;
      if (filter.category) params.category = filter.category;
      if (filter.severity) params.severity = filter.severity;

      const [s, r, n] = await Promise.all([
        fetchDashboardStats(),
        fetchReports({ ...params, limit: 200 }),
        fetchNeighborhoods(),
      ]);
      setStats(s);
      setReports(r);
      setNeighborhoods(n);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadData(); }, [filter]);

  const handleStatusChange = async (id, newStatus) => {
    setUpdatingId(id);
    try {
      await updateReport(id, { status: newStatus });
      await loadData();
    } catch (err) {
      console.error(err);
    } finally {
      setUpdatingId(null);
    }
  };

  const handleAssign = async (id, assignee) => {
    try {
      await updateReport(id, { assigned_to: assignee });
      await loadData();
    } catch (err) {
      console.error(err);
    }
  };

  if (loading && !stats) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="animate-spin text-civic-600" size={40} />
      </div>
    );
  }

  // Neighborhood chart data
  const neighborhoodData = neighborhoods.slice(0, 8).map(n => ({
    name: n.name?.length > 12 ? n.name.slice(0, 12) + '…' : n.name,
    count: n.count,
  }));

  // Budget by severity
  const budgetBySeverity = reports.reduce((acc, r) => {
    acc[r.severity] = (acc[r.severity] || 0) + (r.estimated_cost || 0);
    return acc;
  }, {});
  const budgetData = Object.entries(budgetBySeverity).map(([severity, total]) => ({
    name: severity,
    value: Math.round(total),
    fill: SEVERITY_COLORS[severity] || '#8b5cf6',
  }));

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="bg-amber-100 p-2 rounded-lg">
            <Building2 className="text-amber-700" size={24} />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Township Admin Mode</h2>
            <p className="text-sm text-gray-500">Government operations dashboard</p>
          </div>
        </div>
        <button onClick={loadData} className="btn-secondary flex items-center gap-2">
          <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
          Refresh
        </button>
      </div>

      {/* ── Admin KPIs ── */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <AdminKPI icon={<AlertTriangle className="text-red-500" size={20} />} label="Open Cases" value={stats.open_cases} />
          <AdminKPI icon={<PlayCircle className="text-blue-500" size={20} />} label="In Progress" value={stats.in_progress} />
          <AdminKPI icon={<Clock className="text-amber-500" size={20} />} label="Avg Response" value={`${stats.avg_response_time_hours}h`} />
          <AdminKPI icon={<MapPin className="text-purple-500" size={20} />} label="Hotspot" value={stats.most_affected_neighborhood?.slice(0, 15) || '—'} small />
          <AdminKPI icon={<DollarSign className="text-green-500" size={20} />} label="Budget Impact" value={`$${(stats.total_budget_impact / 1000).toFixed(0)}k`} />
        </div>
      )}

      {/* ── Charts ── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Most Affected Neighborhoods */}
        <div className="card">
          <h3 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
            <MapPin size={18} className="text-civic-600" /> Most Affected Neighborhoods
          </h3>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={neighborhoodData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis type="number" tick={{ fontSize: 12 }} />
              <YAxis type="category" dataKey="name" tick={{ fontSize: 11 }} width={100} />
              <Tooltip />
              <Bar dataKey="count" fill="#6366f1" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Budget by Severity */}
        <div className="card">
          <h3 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
            <DollarSign size={18} className="text-civic-600" /> Budget Impact by Severity
          </h3>
          <ResponsiveContainer width="100%" height={280}>
            <PieChart>
              <Pie
                data={budgetData}
                cx="50%"
                cy="50%"
                innerRadius={50}
                outerRadius={100}
                paddingAngle={4}
                dataKey="value"
                label={({ name, value }) => `${name}: $${(value / 1000).toFixed(0)}k`}
              >
                {budgetData.map((entry, i) => (
                  <Cell key={i} fill={entry.fill} />
                ))}
              </Pie>
              <Tooltip formatter={(val) => `$${val.toLocaleString()}`} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* ── Filters ── */}
      <div className="card">
        <div className="flex flex-wrap items-center gap-3 mb-4">
          <Filter size={18} className="text-gray-400" />
          <select
            value={filter.status}
            onChange={(e) => setFilter(f => ({ ...f, status: e.target.value }))}
            className="border rounded-lg px-3 py-1.5 text-sm"
          >
            <option value="">All Statuses</option>
            <option value="open">Open</option>
            <option value="in_progress">In Progress</option>
            <option value="resolved">Resolved</option>
            <option value="closed">Closed</option>
          </select>
          <select
            value={filter.category}
            onChange={(e) => setFilter(f => ({ ...f, category: e.target.value }))}
            className="border rounded-lg px-3 py-1.5 text-sm"
          >
            <option value="">All Categories</option>
            <option value="pothole">Pothole</option>
            <option value="streetlight">Streetlight</option>
            <option value="trash">Trash</option>
            <option value="graffiti">Graffiti</option>
          </select>
          <select
            value={filter.severity}
            onChange={(e) => setFilter(f => ({ ...f, severity: e.target.value }))}
            className="border rounded-lg px-3 py-1.5 text-sm"
          >
            <option value="">All Severities</option>
            <option value="LOW">Low</option>
            <option value="MEDIUM">Medium</option>
            <option value="HIGH">High</option>
            <option value="CRITICAL">Critical</option>
          </select>
          <span className="text-sm text-gray-400">{reports.length} reports</span>
        </div>

        {/* ── Case Table ── */}
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-left text-gray-500">
                <th className="pb-2 pr-4">ID</th>
                <th className="pb-2 pr-4">Category</th>
                <th className="pb-2 pr-4">Severity</th>
                <th className="pb-2 pr-4">Neighborhood</th>
                <th className="pb-2 pr-4">Status</th>
                <th className="pb-2 pr-4">Assigned</th>
                <th className="pb-2 pr-4">Est. Cost</th>
                <th className="pb-2 pr-4">Response</th>
                <th className="pb-2">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {reports.slice(0, 25).map((r) => {
                const statusConf = STATUS_CONFIG[r.status] || STATUS_CONFIG.open;
                const StatusIcon = statusConf.icon;
                return (
                  <tr key={r.id} className="hover:bg-gray-50">
                    <td className="py-2.5 pr-4 font-mono text-xs text-gray-400">
                      {r.id?.slice(0, 8)}
                    </td>
                    <td className="py-2.5 pr-4 capitalize font-medium">{r.category}</td>
                    <td className="py-2.5 pr-4">
                      <span className={`badge ${
                        r.severity === 'CRITICAL' ? 'badge-critical' :
                        r.severity === 'HIGH' ? 'badge-high' :
                        r.severity === 'MEDIUM' ? 'badge-medium' : 'badge-low'
                      }`}>{r.severity}</span>
                    </td>
                    <td className="py-2.5 pr-4 text-gray-600">{r.neighborhood || '—'}</td>
                    <td className="py-2.5 pr-4">
                      <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium ${statusConf.color}`}>
                        <StatusIcon size={12} />
                        {statusConf.label}
                      </span>
                    </td>
                    <td className="py-2.5 pr-4">
                      <select
                        value={r.assigned_to || ''}
                        onChange={(e) => handleAssign(r.id, e.target.value)}
                        className="border rounded px-2 py-1 text-xs w-28"
                      >
                        <option value="">Unassigned</option>
                        <option value="John Martinez">John Martinez</option>
                        <option value="Sarah Chen">Sarah Chen</option>
                        <option value="Mike O'Brien">Mike O'Brien</option>
                        <option value="Lisa Washington">Lisa Washington</option>
                      </select>
                    </td>
                    <td className="py-2.5 pr-4 text-gray-600">
                      ${r.estimated_cost?.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                    </td>
                    <td className="py-2.5 pr-4 text-gray-500 text-xs">
                      {r.response_time_hours ? `${r.response_time_hours}h` : '—'}
                    </td>
                    <td className="py-2.5">
                      {updatingId === r.id ? (
                        <Loader2 className="animate-spin text-gray-400" size={16} />
                      ) : (
                        <select
                          value={r.status}
                          onChange={(e) => handleStatusChange(r.id, e.target.value)}
                          className="border rounded px-2 py-1 text-xs"
                        >
                          <option value="open">Open</option>
                          <option value="in_progress">In Progress</option>
                          <option value="resolved">Resolved</option>
                          <option value="closed">Closed</option>
                        </select>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}


function AdminKPI({ icon, label, value, small = false }) {
  return (
    <div className="card-hover flex items-center gap-3">
      <div className="p-2 bg-gray-50 rounded-lg">{icon}</div>
      <div>
        <p className={`font-bold text-gray-900 ${small ? 'text-sm' : 'text-xl'}`}>{value}</p>
        <p className="text-xs text-gray-500">{label}</p>
      </div>
    </div>
  );
}

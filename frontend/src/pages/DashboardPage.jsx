import { useState, useEffect } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, LineChart, Line, Legend, Area, AreaChart
} from 'recharts';
import {
  AlertCircle, Clock, CheckCircle2, TrendingUp, DollarSign,
  MapPin, BarChart3, Activity, Loader2
} from 'lucide-react';
import { fetchDashboardStats, fetchReports } from '../api';

const PIE_COLORS = ['#3b82f6', '#f59e0b', '#22c55e', '#ef4444', '#8b5cf6'];
const SEVERITY_COLORS = { LOW: '#22c55e', MEDIUM: '#f59e0b', HIGH: '#f97316', CRITICAL: '#ef4444' };

export default function DashboardPage() {
  const [stats, setStats] = useState(null);
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [s, r] = await Promise.all([
          fetchDashboardStats(),
          fetchReports({ limit: 200 }),
        ]);
        setStats(s);
        setReports(r);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="animate-spin text-civic-600" size={40} />
      </div>
    );
  }
  if (!stats) return <p className="text-center text-gray-500">Failed to load dashboard</p>;

  // Prepare chart data
  const categoryData = Object.entries(stats.category_breakdown).map(([name, value]) => ({
    name: name.charAt(0).toUpperCase() + name.slice(1),
    value,
  }));

  const severityData = Object.entries(stats.severity_breakdown).map(([name, value]) => ({
    name,
    value,
    fill: SEVERITY_COLORS[name] || '#8b5cf6',
  }));

  // Time series (group by day)
  const timeData = getTimeSeriesData(reports);

  return (
    <div className="space-y-8">
      {/* Title */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Public Dashboard</h2>
        <p className="text-sm text-gray-500">Real-time city issue tracking and analytics</p>
      </div>

      {/* ── KPI Cards ── */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <KPICard
          icon={<AlertCircle className="text-red-500" />}
          label="Open Cases"
          value={stats.open_cases}
          sub={`${stats.in_progress} in progress`}
          color="red"
        />
        <KPICard
          icon={<CheckCircle2 className="text-green-500" />}
          label="Resolved"
          value={stats.resolved}
          sub={`of ${stats.total_reports} total`}
          color="green"
        />
        <KPICard
          icon={<Clock className="text-blue-500" />}
          label="Avg Response"
          value={`${stats.avg_response_time_hours}h`}
          sub="resolution time"
          color="blue"
        />
        <KPICard
          icon={<DollarSign className="text-amber-500" />}
          label="Budget Impact"
          value={`$${(stats.total_budget_impact / 1000).toFixed(0)}k`}
          sub="estimated total"
          color="amber"
        />
      </div>

      {/* ── Quick Stats ── */}
      <div className="grid grid-cols-3 gap-4">
        <div className="stat-card">
          <p className="text-3xl font-bold text-civic-700 animate-count">{stats.reports_today}</p>
          <p className="text-sm text-gray-500">Reports Today</p>
        </div>
        <div className="stat-card">
          <p className="text-3xl font-bold text-civic-700 animate-count">{stats.reports_this_week}</p>
          <p className="text-sm text-gray-500">This Week</p>
        </div>
        <div className="stat-card">
          <p className="text-3xl font-bold text-civic-700 animate-count">{stats.reports_this_month}</p>
          <p className="text-sm text-gray-500">This Month</p>
        </div>
      </div>

      {/* ── Charts Row ── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Category Breakdown */}
        <div className="card">
          <h3 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
            <BarChart3 size={18} className="text-civic-600" /> Issues by Category
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={categoryData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="name" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Bar dataKey="value" fill="#3b82f6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Severity Distribution */}
        <div className="card">
          <h3 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
            <Activity size={18} className="text-civic-600" /> Severity Distribution
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={severityData}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={110}
                paddingAngle={4}
                dataKey="value"
                label={({ name, value }) => `${name}: ${value}`}
              >
                {severityData.map((entry, i) => (
                  <Cell key={i} fill={entry.fill} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* ── Timeline ── */}
      <div className="card">
        <h3 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
          <TrendingUp size={18} className="text-civic-600" /> Reports Over Time
        </h3>
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={timeData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="date" tick={{ fontSize: 11 }} />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip />
            <Area type="monotone" dataKey="count" stroke="#3b82f6" fill="#dbeafe" strokeWidth={2} />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* ── Hotspot ── */}
      {stats.most_affected_neighborhood && (
        <div className="card bg-gradient-to-r from-red-50 to-orange-50 border-red-100">
          <div className="flex items-center gap-3">
            <MapPin className="text-red-500" size={24} />
            <div>
              <p className="text-sm text-gray-600">Most Affected Neighborhood</p>
              <p className="text-xl font-bold text-gray-900">{stats.most_affected_neighborhood}</p>
            </div>
          </div>
        </div>
      )}

      {/* ── Recent Reports ── */}
      <div className="card">
        <h3 className="font-semibold text-gray-800 mb-4">Recent Reports</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-left text-gray-500">
                <th className="pb-2">Category</th>
                <th className="pb-2">Severity</th>
                <th className="pb-2">Location</th>
                <th className="pb-2">Status</th>
                <th className="pb-2">Confidence</th>
                <th className="pb-2">Date</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {reports.slice(0, 10).map((r) => (
                <tr key={r.id} className="hover:bg-gray-50">
                  <td className="py-2 capitalize">{r.category}</td>
                  <td className="py-2">
                    <span className={`badge ${
                      r.severity === 'CRITICAL' ? 'badge-critical' :
                      r.severity === 'HIGH' ? 'badge-high' :
                      r.severity === 'MEDIUM' ? 'badge-medium' : 'badge-low'
                    }`}>{r.severity}</span>
                  </td>
                  <td className="py-2 text-gray-600">{r.neighborhood || r.address || '—'}</td>
                  <td className="py-2 capitalize">{r.status.replace('_', ' ')}</td>
                  <td className="py-2">{Math.round(r.confidence * 100)}%</td>
                  <td className="py-2 text-gray-400">{new Date(r.created_at).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}


function KPICard({ icon, label, value, sub, color }) {
  return (
    <div className="card-hover">
      <div className="flex items-center gap-3">
        <div className={`p-2 rounded-lg bg-${color}-50`}>{icon}</div>
        <div>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
          <p className="text-sm font-medium text-gray-700">{label}</p>
          <p className="text-xs text-gray-400">{sub}</p>
        </div>
      </div>
    </div>
  );
}


function getTimeSeriesData(reports) {
  const counts = {};
  reports.forEach((r) => {
    const d = new Date(r.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    counts[d] = (counts[d] || 0) + 1;
  });
  return Object.entries(counts)
    .map(([date, count]) => ({ date, count }))
    .slice(-30);
}

import { BrowserRouter as Router, Routes, Route, NavLink } from 'react-router-dom';
import { Shield, Upload, Map, BarChart3, Building2 } from 'lucide-react';
import ReportPage from './pages/ReportPage';
import MapPage from './pages/MapPage';
import DashboardPage from './pages/DashboardPage';
import AdminPage from './pages/AdminPage';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        {/* ── Navigation ── */}
        <nav className="bg-white border-b border-gray-200 sticky top-0 z-50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16">
              <div className="flex items-center space-x-3">
                <div className="bg-civic-600 p-2 rounded-lg">
                  <Shield className="h-6 w-6 text-white" />
                </div>
                <div>
                  <h1 className="text-xl font-bold text-gray-900">CivicFix</h1>
                  <p className="text-xs text-gray-500 -mt-0.5">AI-Powered City Issue Reporter</p>
                </div>
              </div>
              <div className="flex items-center space-x-1">
                <NavItem to="/" icon={<Upload size={18} />} label="Report" />
                <NavItem to="/map" icon={<Map size={18} />} label="Map" />
                <NavItem to="/dashboard" icon={<BarChart3 size={18} />} label="Dashboard" />
                <NavItem to="/admin" icon={<Building2 size={18} />} label="Admin" />
              </div>
            </div>
          </div>
        </nav>

        {/* ── Content ── */}
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Routes>
            <Route path="/" element={<ReportPage />} />
            <Route path="/map" element={<MapPage />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/admin" element={<AdminPage />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

function NavItem({ to, icon, label }) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        `flex items-center space-x-1.5 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
          isActive
            ? 'bg-civic-50 text-civic-700'
            : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
        }`
      }
    >
      {icon}
      <span>{label}</span>
    </NavLink>
  );
}

export default App;

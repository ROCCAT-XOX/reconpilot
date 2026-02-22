import { Routes, Route, Navigate } from 'react-router-dom'
import MainLayout from './components/layout/MainLayout'
import ProtectedRoute from './components/common/ProtectedRoute'
import ErrorBoundary from './components/common/ErrorBoundary'
import { ToastContainer } from './components/common/Toast'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Projects from './pages/Projects'
import ProjectDetail from './pages/ProjectDetail'
import ScanView from './pages/ScanView'
import Findings from './pages/Findings'
import FindingDetail from './pages/FindingDetail'
import Reports from './pages/Reports'
import Team from './pages/Team'
import Settings from './pages/Settings'

function App() {
  return (
    <ErrorBoundary>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route element={<ProtectedRoute />}>
          <Route path="/" element={<MainLayout />}>
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="dashboard" element={<Dashboard />} />
            <Route path="projects" element={<Projects />} />
            <Route path="projects/:id" element={<ProjectDetail />} />
            <Route path="projects/:projectId/findings" element={<Findings />} />
            <Route path="scans/:id" element={<ScanView />} />
            <Route path="findings" element={<Findings />} />
            <Route path="findings/:id" element={<FindingDetail />} />
            <Route path="reports" element={<Reports />} />
            <Route path="team" element={<Team />} />
            <Route path="settings" element={<Settings />} />
          </Route>
        </Route>
      </Routes>
      <ToastContainer />
    </ErrorBoundary>
  )
}

export default App

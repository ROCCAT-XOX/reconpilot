import { Routes, Route, Navigate } from 'react-router-dom'
import MainLayout from './components/layout/MainLayout'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Projects from './pages/Projects'
import ProjectDetail from './pages/ProjectDetail'
import ScanView from './pages/ScanView'
import FindingExplorer from './pages/FindingExplorer'
import FindingDetail from './pages/FindingDetail'
import Team from './pages/Team'
import Settings from './pages/Settings'

function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/" element={<MainLayout />}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="projects" element={<Projects />} />
        <Route path="projects/:id" element={<ProjectDetail />} />
        <Route path="projects/:projectId/findings" element={<FindingExplorer />} />
        <Route path="scans/:id" element={<ScanView />} />
        <Route path="findings" element={<FindingExplorer />} />
        <Route path="findings/:id" element={<FindingDetail />} />
        <Route path="team" element={<Team />} />
        <Route path="settings" element={<Settings />} />
      </Route>
    </Routes>
  )
}

export default App

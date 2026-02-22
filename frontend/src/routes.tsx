import { Navigate } from 'react-router-dom'
import MainLayout from './components/layout/MainLayout'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Projects from './pages/Projects'
import ProjectDetail from './pages/ProjectDetail'
import ScanView from './pages/ScanView'
import Findings from './pages/Findings'
import Reports from './pages/Reports'
import TeamManagement from './pages/TeamManagement'
import Settings from './pages/Settings'
import { useAuthStore } from './store/authStore'
import { ReactNode } from 'react'

function ProtectedRoute({ children }: { children: ReactNode }) {
  const token = useAuthStore((s) => s.token)
  if (!token) return <Navigate to="/login" replace />
  return <>{children}</>
}

export const routes = [
  { path: '/login', element: <Login /> },
  {
    path: '/',
    element: (
      <ProtectedRoute>
        <MainLayout />
      </ProtectedRoute>
    ),
    children: [
      { index: true, element: <Navigate to="/dashboard" replace /> },
      { path: 'dashboard', element: <Dashboard /> },
      { path: 'projects', element: <Projects /> },
      { path: 'projects/:projectId', element: <ProjectDetail /> },
      { path: 'scans/:scanId', element: <ScanView /> },
      { path: 'findings', element: <Findings /> },
      { path: 'reports', element: <Reports /> },
      { path: 'team', element: <TeamManagement /> },
      { path: 'settings', element: <Settings /> },
    ],
  },
]

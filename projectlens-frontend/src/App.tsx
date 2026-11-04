import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/layout/Layout';
import ErrorBoundary from './components/ui/ErrorBoundary';
import DashboardPage from './pages/DashboardPage';
import NewEvaluationPage from './pages/NewEvaluationPage';
import ProjectWorkspacePage from './pages/ProjectWorkspacePage';
import HistoryReportsPage from './pages/HistoryReportsPage';

export default function App() {
  return (
    <BrowserRouter>
      <Layout>
        <ErrorBoundary sectionName="Application View">
          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/projects/new" element={<NewEvaluationPage />} />
            <Route path="/projects/:projectId" element={<ProjectWorkspacePage />} />
            <Route path="/history" element={<HistoryReportsPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </ErrorBoundary>
      </Layout>
    </BrowserRouter>
  );
}

import { createBrowserRouter } from 'react-router-dom';
import ProtectedRoute from './ProtectedRoute';
import DashboardLayout from '../components/layout/DashboardLayout';

// Pages
import LandingPage from '../pages/LandingPage';
import LoginPage from '../pages/LoginPage';
import RegisterPage from '../pages/RegisterPage';
import Dashboard from '../pages/Dashboard';
import UploadPage from '../pages/UploadPage';
import ContractAnalysisPage from '../pages/ContractAnalysisPage';
import GeneratePage from '../pages/GeneratePage';
import ComparePage from '../pages/ComparePage';
import SignaturePage from '../pages/SignaturePage';
import ProfilePage from '../pages/ProfilePage';
import AdminPage from '../pages/AdminPage';
import SettingsPage from '../pages/SettingsPage';

const router = createBrowserRouter([
  {
    path: '/',
    element: <LandingPage />,
  },
  {
    path: '/login',
    element: <LoginPage />,
  },
  {
    path: '/register',
    element: <RegisterPage />,
  },
  {
    element: <ProtectedRoute />,
    children: [
      {
        element: <DashboardLayout />,
        children: [
          {
            path: '/dashboard',
            element: <Dashboard />,
          },
          {
            path: '/upload',
            element: <UploadPage />,
          },
          {
            path: '/contract/:id',
            element: <ContractAnalysisPage />,
          },
          {
            path: '/generate',
            element: <GeneratePage />,
          },
          {
            path: '/compare',
            element: <ComparePage />,
          },
          {
            path: '/signature/:id?',
            element: <SignaturePage />,
          },
          {
            path: '/profile',
            element: <ProfilePage />,
          },
          {
            path: '/admin',
            element: <AdminPage />,
          },
          {
            path: '/settings',
            element: <SettingsPage />,
          },
        ],
      },
    ],
  },
]);

export default router;
import React from 'react';
import Login from './pages/auth/Login';
import Register from './pages/auth/Register';
import PatientDashboard from './pages/patient/Dashboard';
import DoctorDashboard from './pages/doctor/Dashboard';
import LabDashboard from './pages/lab/LabDashboard';
import AIAssistant from './pages/AIAssistant';

const routes = [
  { path: '/login', element: <Login /> },
  { path: '/register', element: <Register /> },

  
  { path: '/patient', element: <PatientDashboard /> },
  { path: '/patient/ai-assistant', element: <AIAssistant /> },

  
  { path: '/doctor', element: <DoctorDashboard /> },

  
  { path: '/lab', element: <LabDashboard /> },
];

export default routes;

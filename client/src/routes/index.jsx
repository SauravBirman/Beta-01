import React from 'react';
import Login from '../pages/auth/Login';
import Register from '../pages/auth/Register';
import PatientDashboard from '../pages/patient/Dashboard';
import DoctorDashboard from '../pages/doctor/Dashboard';
import LabDashboard from '../pages/lab/LabDashboard';
import AIAssistant from '../pages/AIAssistant';
import PatientLayout from '../layouts/PatientLayout';
import DoctorLayout from '../layouts/DoctorLayout';
import LabLayout from '../layouts/LabLayout';

const routes = [
  { path: '/login', element: <Login /> },
  { path: '/register', element: <Register /> },

  {
    path: '/patient',
    element: <PatientLayout />,
    children: [
      { path: '', element: <PatientDashboard /> },
      { path: 'ai-assistant', element: <AIAssistant /> },
    ],
  },

  {
    path: '/doctor',
    element: <DoctorLayout />,
    children: [
      { path: '', element: <DoctorDashboard /> },
    ],
  },

  {
    path: '/lab',
    element: <LabLayout />,
    children: [
      { path: '', element: <LabDashboard /> },
    ],
  },
];

export default routes;

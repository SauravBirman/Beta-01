import React from 'react';
import { Outlet, Link } from 'react-router-dom';

const PatientLayout = () => {
  return (
    <div>
      <header style={{ padding: '10px', background: '#4CAF50', color: 'white' }}>
        <h1>Patient Portal</h1>
        <nav>
          <Link to="/patient" style={{ marginRight: '10px', color: 'white' }}>Dashboard</Link>
          <Link to="/patient/ai-assistant" style={{ color: 'white' }}>AI Assistant</Link>
        </nav>
      </header>
      <main style={{ padding: '20px' }}>
        <Outlet />
      </main>
    </div>
  );
};

export default PatientLayout;

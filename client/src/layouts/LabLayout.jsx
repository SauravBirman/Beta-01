import React from 'react';
import { Outlet, Link } from 'react-router-dom';

const LabLayout = () => {
  return (
    <div>
      <header style={{ padding: '10px', background: '#FF9800', color: 'white' }}>
        <h1>Lab Portal</h1>
        <nav>
          <Link to="/lab" style={{ color: 'white' }}>Dashboard</Link>
        </nav>
      </header>
      <main style={{ padding: '20px' }}>
        <Outlet />
      </main>
    </div>
  );
};

export default LabLayout;

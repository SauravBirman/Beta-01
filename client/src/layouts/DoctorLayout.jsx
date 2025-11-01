import React from 'react';
import { Outlet, Link } from 'react-router-dom';

const DoctorLayout = () => {
  return (
    <div>
      <header style={{ padding: '10px', background: '#2196F3', color: 'white' }}>
        <h1>Doctor Portal</h1>
        <nav>
          <Link to="/doctor" style={{ color: 'white' }}>Dashboard</Link>
        </nav>
      </header>
      <main style={{ padding: '20px' }}>
        <Outlet />
      </main>
    </div>
  );
};

export default DoctorLayout;

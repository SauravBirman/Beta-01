import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import routes from './routes';

function App() {
  return (
    <Routes>
      {/* Ensure the root path opens the login page first */}
      <Route path="/" element={<Navigate to="/login" replace />} />
      {routes.map((route, index) => (
        <Route
          key={index}
          path={route.path}
          element={route.element}
        >
          {route.children &&
            route.children.map((child, idx) => (
              <Route key={idx} path={child.path} element={child.element} />
            ))}
        </Route>
      ))}
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  );
}

export default App;

import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';

const Sidebar = ({ role = 'patient' }) => {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const location = useLocation();

  const menuItems = {
    patient: [
      { name: 'Dashboard', icon: 'dashboard', path: '/patient/dashboard' },
      { name: 'Health Records', icon: 'folder_open', path: '/patient/health-records' },
      { name: 'AI Assistant', icon: 'smart_toy', path: '/patient/ai-assistant' },
      { name: 'Share Records', icon: 'share', path: '/patient/share-records' },
    ],
    doctor: [
      { name: 'Dashboard', icon: 'dashboard', path: '/doctor/dashboard' },
      { name: 'Patient Summaries', icon: 'people', path: '/doctor/patient-summaries' },
      { name: 'Alerts', icon: 'warning', path: '/doctor/alerts' },
      { name: 'Schedule', icon: 'calendar_month', path: '/doctor/schedule' },
    ],
    lab: [
      { name: 'Dashboard', icon: 'dashboard', path: '/lab/dashboard' },
      { name: 'Upload Reports', icon: 'upload_file', path: '/lab/upload-reports' },
      { name: 'Test Results', icon: 'science', path: '/lab/test-results' },
      { name: 'Quality Control', icon: 'check_circle', path: '/lab/quality-control' },
    ]
  };

  const currentItems = menuItems[role] || menuItems.patient;

  const isActiveLink = (path) => {
    return location.pathname === path || location.pathname.startsWith(path + '/');
  };

  return (
    <div className={`bg-white border-r border-gray-200 min-h-screen transition-all duration-300 ${
      isCollapsed ? 'w-16' : 'w-64'
    } sticky top-0`}>
      
      {/* Sidebar Header */}
      <div className="flex items-center justify-between p-6 border-b border-gray-200">
        {!isCollapsed && (
          <div>
            <h1 className="text-2xl font-bold text-gray-900">MedChain</h1>
            <p className="text-gray-500 text-sm mt-1 capitalize">{role} Portal</p>
          </div>
        )}
        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
          title={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          <svg 
            className={`w-5 h-5 text-gray-600 transition-transform ${isCollapsed ? 'rotate-180' : ''}`}
            fill="none" 
            stroke="currentColor" 
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
          </svg>
        </button>
      </div>

      {/* Navigation Menu with Numbered Boxes */}
      <nav className="p-6 space-y-3">
        {currentItems.map((item, index) => {
          const isActive = isActiveLink(item.path);
          
          return (
            <Link
              key={index}
              to={item.path}
              className={`flex items-center rounded-xl p-4 transition-all duration-200 group border-2 ${
                isActive
                  ? 'bg-blue-50 border-blue-200 shadow-sm'
                  : 'bg-gray-50 border-gray-200 hover:bg-gray-100 hover:border-gray-300'
              } ${isCollapsed ? 'justify-center' : ''}`}
              title={isCollapsed ? item.name : ''}
            >
              {/* Icon */}
              <div className={`flex-shrink-0 flex items-center justify-center text-lg ${isCollapsed ? '' : 'w-10 h-10'} `}>
                <span className={`material-icons ${isActive ? 'text-blue-600' : 'text-gray-600'}`} style={{fontSize: isCollapsed ? 20 : 22}}>{item.icon}</span>
              </div>
              
              {/* Menu Item Text */}
              {!isCollapsed && (
                <div className="ml-4">
                  <span className={`font-semibold block ${
                    isActive ? 'text-blue-700' : 'text-gray-700 group-hover:text-gray-900'
                  }`}>
                    {item.name}
                  </span>
                </div>
              )}
            </Link>
          );
        })}
      </nav>

      {/* Quick Stats Section */}
      {!isCollapsed && (
        <div className="mt-8 px-6">
          <div className="bg-gray-50 rounded-xl p-4 border border-gray-200">
            <h3 className="font-semibold text-gray-900 mb-3">Quick Stats</h3>
            <div className="space-y-2">
              {role === 'patient' && (
                <>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Appointments</span>
                    <span className="text-gray-900 font-semibold">2</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Pending Results</span>
                    <span className="text-gray-900 font-semibold">1</span>
                  </div>
                </>
              )}
              {role === 'doctor' && (
                <>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Patients Today</span>
                    <span className="text-gray-900 font-semibold">8</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Urgent Cases</span>
                    <span className="text-red-600 font-semibold">2</span>
                  </div>
                </>
              )}
              {role === 'lab' && (
                <>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Tests Today</span>
                    <span className="text-gray-900 font-semibold">24</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Pending</span>
                    <span className="text-yellow-600 font-semibold">5</span>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      )}

      {/* User Profile */}
      <div className={`absolute bottom-6 left-6 right-6 ${
        isCollapsed ? 'flex justify-center' : ''
      }`}>
        <div className={`flex items-center ${isCollapsed ? 'justify-center' : 'justify-between'} w-full`}>
          {!isCollapsed && (
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-blue-600 rounded-full flex items-center justify-center">
                <span className="text-white font-semibold text-sm">JD</span>
              </div>
              <div>
                <p className="text-gray-900 font-medium text-sm">John Doe</p>
                <p className="text-gray-500 text-xs capitalize">{role}</p>
              </div>
            </div>
          )}
          {isCollapsed && (
            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-blue-600 rounded-full flex items-center justify-center">
              <span className="text-white font-semibold text-sm">JD</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Sidebar;
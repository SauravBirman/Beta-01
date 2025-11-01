import React, { useState, useEffect } from 'react';
import Navbar from '../../components/Navbar';
import Slidebar from '../../components/Slidebar';

const patients = [
  { id: 1, name: 'Alice Smith', age: 34, note: 'Follow-up in 2 weeks', lastVisit: '2025-01-15', status: 'Stable', priority: 'low' },
  { id: 2, name: 'Bob Johnson', age: 48, note: 'Prescribed medication', lastVisit: '2025-01-14', status: 'Improving', priority: 'medium' },
  { id: 3, name: 'Carlos Diaz', age: 29, note: 'Review lab results', lastVisit: '2025-01-13', status: 'Critical', priority: 'high' },
  { id: 4, name: 'Diana Chen', age: 52, note: 'Surgery scheduled', lastVisit: '2025-01-12', status: 'Stable', priority: 'medium' },
  { id: 5, name: 'Ethan Wilson', age: 41, note: 'Physical therapy', lastVisit: '2025-01-11', status: 'Improving', priority: 'low' },
];

const appointments = [
  { id: 1, patient: 'Alice Smith', time: '09:00 AM', type: 'Follow-up', status: 'Confirmed' },
  { id: 2, patient: 'Bob Johnson', time: '10:30 AM', type: 'Consultation', status: 'Confirmed' },
  { id: 3, patient: 'New Patient', time: '11:45 AM', type: 'First Visit', status: 'Pending' },
  { id: 4, patient: 'Carlos Diaz', time: '02:15 PM', type: 'Emergency', status: 'Confirmed' },
];

const Dashboard = () => {
  const [currentTime, setCurrentTime] = useState(new Date());
  const [activeTab, setActiveTab] = useState('patients');

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 60000);
    return () => clearInterval(timer);
  }, []);

  const getTimeBasedGradient = () => {
    const hours = currentTime.getHours();
    if (hours >= 6 && hours < 12) {
      return 'from-blue-50 via-cyan-50 to-emerald-50';
    } else if (hours >= 12 && hours < 18) {
      return 'from-amber-50 via-orange-50 to-rose-50';
    } else if (hours >= 18 && hours < 21) {
      return 'from-purple-50 via-pink-50 to-indigo-50';
    } else {
      return 'from-indigo-50 via-blue-50 to-cyan-50';
    }
  };

  const getGreeting = () => {
    const hours = currentTime.getHours();
    if (hours >= 5 && hours < 12) return 'Good morning';
    if (hours >= 12 && hours < 17) return 'Good afternoon';
    if (hours >= 17 && hours < 21) return 'Good evening';
    return 'Good night';
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'high': return 'bg-red-100 text-red-800 border-red-200';
      case 'medium': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'low': return 'bg-green-100 text-green-800 border-green-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'Critical': return 'text-red-600';
      case 'Stable': return 'text-green-600';
      case 'Improving': return 'text-blue-600';
      default: return 'text-gray-600';
    }
  };

  return (
    <div>
      <Navbar companyName="MedChain - Doctor" />

      <div className="flex">
        <Slidebar role="doctor" />

        <main className="flex-1 relative overflow-hidden">
          {/* Animated Background */}
          <div className={`absolute top-0 left-0 right-0 h-80 bg-gradient-to-br ${getTimeBasedGradient()} transition-all duration-1000 ease-in-out -z-10`}>
            {/* Floating medical icons */}
            <div className="absolute top-8 left-1/4 text-3xl opacity-20 animate-bounce">🩺</div>
            <div className="absolute top-16 right-1/3 text-2xl opacity-30 animate-pulse delay-300">💊</div>
            <div className="absolute top-24 left-2/3 text-3xl opacity-25 animate-bounce delay-700">📋</div>
            <div className="absolute top-12 right-1/4 text-2xl opacity-20 animate-pulse delay-500">❤️</div>
            <div className="absolute top-32 left-1/3 text-3xl opacity-30 animate-bounce delay-1000">🏥</div>
            
            {/* Animated pulse circles */}
            <div className="absolute top-20 left-10 w-4 h-4 bg-blue-300 rounded-full animate-ping opacity-20"></div>
            <div className="absolute top-8 right-20 w-3 h-3 bg-green-300 rounded-full animate-ping opacity-30 delay-300"></div>
            <div className="absolute top-40 left-20 w-2 h-2 bg-purple-300 rounded-full animate-ping opacity-25 delay-700"></div>
          </div>

          <div className="p-6 relative z-10">
            {/* Header Section */}
            <div className="flex items-center justify-between mb-8">
              <div>
                <h1 className="text-3xl font-bold text-gray-900">{getGreeting()}, Dr. Smith!</h1>
                <p className="text-lg text-gray-600 mt-2">Welcome to your medical dashboard</p>
              </div>
              <div className="text-right">
                <p className="text-sm text-gray-500">Current Time</p>
                <p className="text-xl font-semibold text-gray-900">
                  {currentTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </p>
              </div>
            </div>

            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              <div className="bg-white/90 backdrop-blur-sm rounded-2xl p-6 border border-white/20 shadow-sm hover:shadow-xl transition-all duration-300 hover:-translate-y-1">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-500 font-medium">Today's Appointments</p>
                    <p className="text-3xl font-bold text-gray-900 mt-2">8</p>
                    <p className="text-xs text-green-600 mt-1">✓ 72% completed</p>
                  </div>
                  <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center">
                    <span className="text-2xl">📅</span>
                  </div>
                </div>
              </div>

              <div className="bg-white/90 backdrop-blur-sm rounded-2xl p-6 border border-white/20 shadow-sm hover:shadow-xl transition-all duration-300 hover:-translate-y-1">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-500 font-medium">Pending Results</p>
                    <p className="text-3xl font-bold text-yellow-600 mt-2">4</p>
                    <p className="text-xs text-red-600 mt-1">⚠️ 2 urgent</p>
                  </div>
                  <div className="w-12 h-12 bg-yellow-100 rounded-xl flex items-center justify-center">
                    <span className="text-2xl">🔬</span>
                  </div>
                </div>
              </div>

              <div className="bg-white/90 backdrop-blur-sm rounded-2xl p-6 border border-white/20 shadow-sm hover:shadow-xl transition-all duration-300 hover:-translate-y-1">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-500 font-medium">New Messages</p>
                    <p className="text-3xl font-bold text-blue-600 mt-2">12</p>
                    <p className="text-xs text-gray-500 mt-1">3 from care team</p>
                  </div>
                  <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center">
                    <span className="text-2xl">💬</span>
                  </div>
                </div>
              </div>

              <div className="bg-white/90 backdrop-blur-sm rounded-2xl p-6 border border-white/20 shadow-sm hover:shadow-xl transition-all duration-300 hover:-translate-y-1">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-500 font-medium">Active Patients</p>
                    <p className="text-3xl font-bold text-purple-600 mt-2">24</p>
                    <p className="text-xs text-gray-500 mt-1">+3 this week</p>
                  </div>
                  <div className="w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center">
                    <span className="text-2xl">👥</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Main Content Tabs */}
            <div className="bg-white/90 backdrop-blur-sm rounded-2xl border border-white/20 shadow-sm mb-6">
              <div className="border-b border-gray-200">
                <nav className="flex space-x-8 px-6">
                  <button
                    onClick={() => setActiveTab('patients')}
                    className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                      activeTab === 'patients'
                        ? 'border-blue-500 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700'
                    }`}
                  >
                    Patients Overview
                  </button>
                  <button
                    onClick={() => setActiveTab('appointments')}
                    className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                      activeTab === 'appointments'
                        ? 'border-blue-500 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700'
                    }`}
                  >
                    Today's Schedule
                  </button>
                  <button
                    onClick={() => setActiveTab('alerts')}
                    className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                      activeTab === 'alerts'
                        ? 'border-blue-500 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700'
                    }`}
                  >
                    Critical Alerts
                  </button>
                </nav>
              </div>

              <div className="p-6">
                {activeTab === 'patients' && (
                  <div>
                    <div className="flex items-center justify-between mb-6">
                      <h2 className="text-xl font-semibold text-gray-900">Patient List</h2>
                      <div className="flex space-x-3">
                        <input
                          type="search"
                          placeholder="Search patients..."
                          className="px-4 py-2 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        />
                        <button className="px-4 py-2 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-colors">
                          + New Patient
                        </button>
                      </div>
                    </div>

                    <div className="space-y-4">
                      {patients.map(patient => (
                        <div key={patient.id} className="flex items-center justify-between p-4 bg-gray-50 rounded-xl hover:bg-white hover:shadow-md transition-all duration-200 border border-gray-100">
                          <div className="flex items-center space-x-4">
                            <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl flex items-center justify-center">
                              <span className="text-white font-semibold text-sm">
                                {patient.name.split(' ').map(n => n[0]).join('')}
                              </span>
                            </div>
                            <div>
                              <div className="flex items-center space-x-3">
                                <h3 className="font-semibold text-gray-900">{patient.name}</h3>
                                <span className="text-sm text-gray-500">Age {patient.age}</span>
                                <span className={`px-2 py-1 rounded-full text-xs font-medium border ${getPriorityColor(patient.priority)}`}>
                                  {patient.priority} priority
                                </span>
                              </div>
                              <p className="text-sm text-gray-600 mt-1">{patient.note}</p>
                              <div className="flex items-center space-x-4 mt-2">
                                <span className={`text-sm font-medium ${getStatusColor(patient.status)}`}>
                                  Status: {patient.status}
                                </span>
                                <span className="text-sm text-gray-500">
                                  Last visit: {patient.lastVisit}
                                </span>
                              </div>
                            </div>
                          </div>
                          <div className="flex items-center space-x-3">
                            <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium">
                              View Chart
                            </button>
                            <button className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors text-sm font-medium">
                              Add Note
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {activeTab === 'appointments' && (
                  <div>
                    <h2 className="text-xl font-semibold text-gray-900 mb-6">Today's Schedule</h2>
                    <div className="space-y-4">
                      {appointments.map(appointment => (
                        <div key={appointment.id} className="flex items-center justify-between p-4 bg-gray-50 rounded-xl hover:bg-white hover:shadow-md transition-all duration-200 border border-gray-100">
                          <div className="flex items-center space-x-4">
                            <div className="w-16 h-16 bg-blue-100 rounded-xl flex items-center justify-center">
                              <span className="text-blue-600 font-semibold">{appointment.time}</span>
                            </div>
                            <div>
                              <h3 className="font-semibold text-gray-900">{appointment.patient}</h3>
                              <p className="text-sm text-gray-600">{appointment.type}</p>
                              <span className={`inline-block mt-2 px-3 py-1 rounded-full text-xs font-medium ${
                                appointment.status === 'Confirmed' 
                                  ? 'bg-green-100 text-green-800' 
                                  : 'bg-yellow-100 text-yellow-800'
                              }`}>
                                {appointment.status}
                              </span>
                            </div>
                          </div>
                          <div className="flex items-center space-x-3">
                            <button className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors text-sm font-medium">
                              Start Visit
                            </button>
                            <button className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors text-sm font-medium">
                              Reschedule
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {activeTab === 'alerts' && (
                  <div>
                    <h2 className="text-xl font-semibold text-gray-900 mb-6">Critical Alerts</h2>
                    <div className="text-center py-12">
                      <div className="text-6xl mb-4">🎉</div>
                      <h3 className="text-xl font-semibold text-gray-900 mb-2">No Critical Alerts</h3>
                      <p className="text-gray-600">All patients are currently stable</p>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Quick Actions */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-white/90 backdrop-blur-sm rounded-2xl p-6 border border-white/20 shadow-sm">
                <h3 className="font-semibold text-gray-900 mb-4">Quick Actions</h3>
                <div className="space-y-3">
                  <button className="w-full text-left px-4 py-3 bg-blue-50 text-blue-700 rounded-xl hover:bg-blue-100 transition-colors flex items-center space-x-3">
                    <span>📝</span>
                    <span>Write Prescription</span>
                  </button>
                  <button className="w-full text-left px-4 py-3 bg-green-50 text-green-700 rounded-xl hover:bg-green-100 transition-colors flex items-center space-x-3">
                    <span>🔍</span>
                    <span>Review Lab Results</span>
                  </button>
                  <button className="w-full text-left px-4 py-3 bg-purple-50 text-purple-700 rounded-xl hover:bg-purple-100 transition-colors flex items-center space-x-3">
                    <span>📊</span>
                    <span>View Analytics</span>
                  </button>
                </div>
              </div>

              <div className="bg-white/90 backdrop-blur-sm rounded-2xl p-6 border border-white/20 shadow-sm md:col-span-2">
                <h3 className="font-semibold text-gray-900 mb-4">Recent Activity</h3>
                <div className="space-y-4">
                  <div className="flex items-center space-x-4 p-3 bg-gray-50 rounded-xl">
                    <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                      <span className="text-green-600">✓</span>
                    </div>
                    <div>
                      <p className="font-medium text-gray-900">Completed consultation</p>
                      <p className="text-sm text-gray-500">Alice Smith • 30 mins ago</p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-4 p-3 bg-gray-50 rounded-xl">
                    <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                      <span className="text-blue-600">📋</span>
                    </div>
                    <div>
                      <p className="font-medium text-gray-900">Lab results received</p>
                      <p className="text-sm text-gray-500">Bob Johnson • 2 hours ago</p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-4 p-3 bg-gray-50 rounded-xl">
                    <div className="w-10 h-10 bg-yellow-100 rounded-lg flex items-center justify-center">
                      <span className="text-yellow-600">⏰</span>
                    </div>
                    <div>
                      <p className="font-medium text-gray-900">Appointment reminder</p>
                      <p className="text-sm text-gray-500">Carlos Diaz • 4 hours ago</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
};

export default Dashboard;
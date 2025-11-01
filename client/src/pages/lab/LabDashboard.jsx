import React, { useState, useEffect } from 'react';
import Navbar from '../../components/Navbar';
import Slidebar from '../../components/Slidebar';

const LabDashboard = () => {
  const [reports, setReports] = useState([
    { id: 1, patient: 'John Doe', type: 'Blood Test', date: '2025-10-02', status: 'Pending', size: '120KB' },
    { id: 2, patient: 'Jane Smith', type: 'Urine Test', date: '2025-09-28', status: 'Processed', size: '90KB' },
    { id: 3, patient: 'Alice Brown', type: 'COVID PCR', date: '2025-09-20', status: 'Processed', size: '240KB' },
  ]);

  const [showUploadModal, setShowUploadModal] = useState(false);
  const [newReport, setNewReport] = useState({ patient: '', type: 'Blood Test', date: new Date().toISOString().split('T')[0] });
  const [currentTime, setCurrentTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 60000);
    return () => clearInterval(timer);
  }, []);

  const handleUpload = () => {
    if (!newReport.patient.trim()) return;
    const r = { id: reports.length + 1, ...newReport, status: 'Pending', size: '100KB' };
    setReports([r, ...reports]);
    setNewReport({ patient: '', type: 'Blood Test', date: new Date().toISOString().split('T')[0] });
    setShowUploadModal(false);
  };

  const processReport = (id) => {
    setReports(reports.map(r => r.id === id ? { ...r, status: 'Processed' } : r));
  };

  const pendingCount = reports.filter(r => r.status === 'Pending').length;
  const processedCount = reports.filter(r => r.status === 'Processed').length;

  const getTimeBasedGradient = () => {
    const hours = currentTime.getHours();
    if (hours >= 6 && hours < 12) return 'from-amber-200 via-orange-100 to-blue-100';
    if (hours >= 12 && hours < 18) return 'from-yellow-200 via-amber-100 to-orange-100';
    if (hours >= 18 && hours < 21) return 'from-orange-300 via-pink-200 to-purple-300';
    return 'from-indigo-900 via-purple-900 to-blue-900';
  };

  return (
    <div>
      <Navbar companyName="MedChain - Lab" />

      <div className="flex">
        <Slidebar role="lab" />

        <div className="flex-1 p-6 relative overflow-hidden">
          <div className={`absolute top-0 left-0 right-0 h-64 bg-gradient-to-br ${getTimeBasedGradient()} transition-all duration-1000 ease-in-out -z-10`}>
            <div className="absolute top-8 left-1/4 text-3xl opacity-20 animate-bounce">🧪</div>
            <div className="absolute top-16 right-1/3 text-2xl opacity-30 animate-pulse delay-300">🔬</div>
            <div className="absolute top-24 left-2/3 text-3xl opacity-25 animate-bounce delay-700">🧾</div>
          </div>

          <div className="relative z-10">
            <header className="flex items-center justify-between mb-8">
              <div>
                <h1 className="text-3xl font-bold text-gray-900">Lab Dashboard</h1>
                <p className="text-gray-600 mt-1">Manage incoming lab reports and processing</p>
              </div>

              <div className="flex items-center space-x-3">
                <div className="bg-white/80 backdrop-blur-sm rounded-xl p-3 border border-white/20 shadow-sm">
                  <div className="text-sm text-gray-600">Pending</div>
                  <div className="text-2xl font-bold text-gray-900">{pendingCount}</div>
                </div>
                <div className="bg-white/80 backdrop-blur-sm rounded-xl p-3 border border-white/20 shadow-sm">
                  <div className="text-sm text-gray-600">Processed</div>
                  <div className="text-2xl font-bold text-gray-900">{processedCount}</div>
                </div>
                <button
                  onClick={() => setShowUploadModal(true)}
                  className="bg-blue-600 hover:bg-blue-700 text-white px-5 py-3 rounded-lg font-semibold transition-colors shadow-md"
                >
                  + Upload Report
                </button>
              </div>
            </header>

            <section className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
              <div className="lg:col-span-2 bg-white/90 backdrop-blur-sm rounded-2xl p-6 border border-white/20 shadow-sm">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-xl font-semibold text-gray-900">Recent Reports</h2>
                  <span className="text-sm text-gray-600">{reports.length} total</span>
                </div>

                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Patient</th>
                        <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Type</th>
                        <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Date</th>
                        <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Status</th>
                        <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Size</th>
                        <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {reports.map(r => (
                        <tr key={r.id} className="hover:bg-gray-50">
                          <td className="px-4 py-3 text-sm text-gray-800 font-medium">{r.patient}</td>
                          <td className="px-4 py-3 text-sm text-gray-700">{r.type}</td>
                          <td className="px-4 py-3 text-sm text-gray-600">{r.date}</td>
                          <td className="px-4 py-3 text-sm">
                            <span className={`px-2 py-1 rounded-full text-xs font-medium ${r.status === 'Processed' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'}`}>
                              {r.status}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-sm text-gray-600">{r.size}</td>
                          <td className="px-4 py-3 text-sm">
                            <div className="flex items-center gap-2">
                              <button onClick={() => processReport(r.id)} className="px-3 py-2 bg-green-600 text-white rounded-lg text-sm hover:bg-green-700">Process</button>
                              <button className="px-3 py-2 bg-gray-100 rounded-lg text-sm hover:bg-gray-200">Download</button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              <aside className="bg-white/90 backdrop-blur-sm rounded-2xl p-6 border border-white/20 shadow-sm">
                <h3 className="text-lg font-semibold text-gray-900 mb-3">Quick Actions</h3>
                <div className="flex flex-col gap-3">
                  <button className="w-full text-left bg-blue-600 hover:bg-blue-700 text-white px-4 py-3 rounded-lg">Create Report Batch</button>
                  <button className="w-full text-left bg-orange-500 hover:bg-orange-600 text-white px-4 py-3 rounded-lg">Notify Patients</button>
                  <button className="w-full text-left bg-gray-100 hover:bg-gray-200 px-4 py-3 rounded-lg">Settings</button>
                </div>
              </aside>
            </section>
          </div>

          {showUploadModal && (
            <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
              <div className="bg-white rounded-xl p-6 w-full max-w-md mx-4">
                <h3 className="text-xl font-semibold text-gray-900 mb-4">Upload Lab Report</h3>

                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Patient Name</label>
                    <input type="text" value={newReport.patient} onChange={e => setNewReport({...newReport, patient: e.target.value})} className="w-full px-3 py-2 border border-gray-300 rounded-lg" />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Type</label>
                    <select value={newReport.type} onChange={e => setNewReport({...newReport, type: e.target.value})} className="w-full px-3 py-2 border border-gray-300 rounded-lg">
                      <option>Blood Test</option>
                      <option>Urine Test</option>
                      <option>COVID PCR</option>
                      <option>Other</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Date</label>
                    <input type="date" value={newReport.date} onChange={e => setNewReport({...newReport, date: e.target.value})} className="w-full px-3 py-2 border border-gray-300 rounded-lg" />
                  </div>

                  <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
                    <div className="text-gray-600 mb-2">Drag and drop a file or click to browse</div>
                    <button className="text-blue-600 font-medium">Browse files</button>
                  </div>
                </div>

                <div className="flex gap-3 mt-6">
                  <button onClick={() => setShowUploadModal(false)} className="flex-1 px-4 py-2 border border-gray-300 rounded-lg">Cancel</button>
                  <button onClick={handleUpload} className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg">Upload</button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default LabDashboard;

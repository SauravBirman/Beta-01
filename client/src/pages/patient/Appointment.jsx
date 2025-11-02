import React, { useEffect, useState } from 'react';
import Navbar from '../../components/Navbar';
import Slidebar from '../../components/Slidebar';

// Mock file data - in real app, this would come from your backend
const mockFiles = [
  { id: 1, name: 'Blood Test Results.pdf', type: 'pdf', size: '2.4 MB', date: '2025-01-15', category: 'Lab Reports' },
  { id: 2, name: 'X-Ray Chest.jpg', type: 'image', size: '4.2 MB', date: '2025-01-10', category: 'Imaging' },
  { id: 3, name: 'MRI Scan Results.pdf', type: 'pdf', size: '8.1 MB', date: '2025-01-08', category: 'Imaging' },
  { id: 4, name: 'Prescription.pdf', type: 'pdf', size: '1.2 MB', date: '2025-01-05', category: 'Prescriptions' },
  { id: 5, name: 'ECG Report.pdf', type: 'pdf', size: '3.7 MB', date: '2024-12-20', category: 'Tests' },
  { id: 6, name: 'Doctor Notes.txt', type: 'document', size: '256 KB', date: '2024-12-15', category: 'Notes' },
  { id: 7, name: 'Insurance Card.jpg', type: 'image', size: '1.8 MB', date: '2024-12-10', category: 'Documents' },
  { id: 8, name: 'Lab Report 2.pdf', type: 'pdf', size: '2.1 MB', date: '2024-12-05', category: 'Lab Reports' },
];

export default function Appointment() {
  const [doctor, setDoctor] = useState('');
  const [reason, setReason] = useState('');
  const [mode, setMode] = useState('view');
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [appointments, setAppointments] = useState([]);
  const [errors, setErrors] = useState({});
  const [success, setSuccess] = useState('');
  const [showFilePicker, setShowFilePicker] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [viewMode, setViewMode] = useState('grid'); // 'grid' or 'list'

  const categories = ['All', 'Lab Reports', 'Imaging', 'Prescriptions', 'Tests', 'Notes', 'Documents'];

  useEffect(() => {
    try {
      const stored = localStorage.getItem('appointments');
      if (stored) setAppointments(JSON.parse(stored));
    } catch (e) {}
  }, []);

  const filteredFiles = mockFiles.filter(file => {
    const matchesSearch = file.name.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory = selectedCategory === 'All' || file.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  const handleFileSelect = (file) => {
    setSelectedFiles(prev => {
      const isAlreadySelected = prev.find(f => f.id === file.id);
      if (isAlreadySelected) {
        return prev.filter(f => f.id !== file.id);
      } else {
        return [...prev, file];
      }
    });
  };

  const removeFile = (fileId) => {
    setSelectedFiles(prev => prev.filter(file => file.id !== fileId));
  };

  const getFileIcon = (type) => {
    switch (type) {
      case 'pdf': return '📄';
      case 'image': return '🖼️';
      case 'document': return '📝';
      default: return '📎';
    }
  };

  const submit = () => {
    const errs = {};
    if (!doctor.trim()) errs.doctor = 'Please enter doctor name, ID or hospital.';
    if (selectedFiles.length === 0) errs.files = 'Please select at least one file to share.';
    setErrors(errs);
    if (Object.keys(errs).length) return;

    const appointment = { 
      id: Date.now(), 
      doctor: doctor.trim(), 
      reason: reason.trim(), 
      mode, 
      files: selectedFiles,
      createdAt: new Date().toISOString(),
      status: 'Requested'
    };
    
    const updated = [...appointments, appointment];
    setAppointments(updated);
    try { 
      localStorage.setItem('appointments', JSON.stringify(updated)); 
    } catch (e) {}
    
    setSuccess('Appointment requested successfully! Files will be shared with the doctor.');
    setDoctor(''); 
    setReason(''); 
    setMode('view'); 
    setSelectedFiles([]);
    setTimeout(() => setSuccess(''), 5000);
  };

  return (
    <div>
      <Navbar companyName="MedChain - Patient" />
      <div className="flex">
        <Slidebar role="patient" />

        <main className="flex-1 relative overflow-hidden">
          {/* Animated Background */}
          <div className="absolute top-0 left-0 right-0 h-64 bg-gradient-to-br from-blue-50 via-cyan-50 to-emerald-50 -z-10">
            <div className="absolute top-8 left-1/4 text-3xl opacity-20 animate-bounce">🏥</div>
            <div className="absolute top-16 right-1/3 text-2xl opacity-30 animate-pulse delay-300">📅</div>
            <div className="absolute top-24 left-2/3 text-3xl opacity-25 animate-bounce delay-700">👨‍⚕️</div>
          </div>

          <div className="p-6 relative z-10">
            <div className="max-w-4xl mx-auto">
              {/* Header */}
              <div className="mb-8">
                <h1 className="text-3xl font-bold text-gray-900">Request Appointment</h1>
                <p className="text-lg text-gray-600 mt-2">Schedule an appointment and share your medical records</p>
              </div>

              {/* Success Message */}
              {success && (
                <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-xl flex items-center space-x-3">
                  <span className="text-2xl">✅</span>
                  <p className="text-green-800 font-medium">{success}</p>
                </div>
              )}

              {/* Appointment Form */}
              <div className="bg-white/90 backdrop-blur-sm rounded-2xl p-6 shadow-lg border border-white/20 mb-8">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {/* Left Column */}
                  <div className="space-y-6">
                    <div>
                      <label className="block text-sm font-semibold text-gray-700 mb-3">Doctor / Hospital</label>
                      <input 
                        className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all"
                        value={doctor} 
                        onChange={e => setDoctor(e.target.value)} 
                        placeholder="Dr. Smith or Hospital Name" 
                      />
                      {errors.doctor && <p className="text-sm text-red-600 mt-2 flex items-center space-x-2"><span>⚠️</span> <span>{errors.doctor}</span></p>}
                    </div>

                    <div>
                      <label className="block text-sm font-semibold text-gray-700 mb-3">Reason for Appointment</label>
                      <textarea 
                        className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all"
                        rows={4} 
                        value={reason} 
                        onChange={e => setReason(e.target.value)} 
                        placeholder="Please describe the reason for your appointment..."
                      />
                    </div>
                  </div>

                  {/* Right Column */}
                  <div className="space-y-6">
                    <div>
                      <label className="block text-sm font-semibold text-gray-700 mb-3">Files to Share</label>
                      <div className="border-2 border-dashed border-gray-300 rounded-xl p-4 hover:border-blue-400 transition-colors">
                        <div className="text-center mb-3">
                          <span className="text-4xl">📁</span>
                          <p className="text-gray-600 mt-2">{selectedFiles.length} file(s) selected</p>
                        </div>
                        <button 
                          onClick={() => setShowFilePicker(true)}
                          className="w-full py-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-colors font-medium flex items-center justify-center space-x-2"
                        >
                          <span>➕</span>
                          <span>Choose Files</span>
                        </button>
                        {errors.files && <p className="text-sm text-red-600 mt-2 flex items-center space-x-2"><span>⚠️</span> <span>{errors.files}</span></p>}
                      </div>

                      {/* Selected Files List */}
                      {selectedFiles.length > 0 && (
                        <div className="mt-4 space-y-2">
                          <p className="text-sm font-medium text-gray-700">Selected files:</p>
                          {selectedFiles.map(file => (
                            <div key={file.id} className="flex items-center justify-between bg-gray-50 p-3 rounded-lg">
                              <div className="flex items-center space-x-3">
                                <span className="text-lg">{getFileIcon(file.type)}</span>
                                <div>
                                  <p className="text-sm font-medium text-gray-900">{file.name}</p>
                                  <p className="text-xs text-gray-500">{file.size} • {file.category}</p>
                                </div>
                              </div>
                              <button 
                                onClick={() => removeFile(file.id)}
                                className="text-red-500 hover:text-red-700 transition-colors"
                              >
                                🗑️
                              </button>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>

                    <div>
                      <label className="block text-sm font-semibold text-gray-700 mb-3">Access Level</label>
                      <div className="flex space-x-4">
                        <label className="flex items-center space-x-3 p-3 border-2 border-gray-200 rounded-xl cursor-pointer hover:border-blue-300 transition-colors flex-1">
                          <input 
                            type="radio" 
                            name="mode" 
                            value="view" 
                            checked={mode === 'view'} 
                            onChange={e => setMode(e.target.value)} 
                            className="hidden"
                          />
                          <div className={`w-6 h-6 rounded-full border-2 ${mode === 'view' ? 'border-blue-500 bg-blue-500' : 'border-gray-300'}`}></div>
                          <div>
                            <p className="font-medium">View Only</p>
                            <p className="text-sm text-gray-500">Doctor can view but not edit</p>
                          </div>
                        </label>
                        <label className="flex items-center space-x-3 p-3 border-2 border-gray-200 rounded-xl cursor-pointer hover:border-blue-300 transition-colors flex-1">
                          <input 
                            type="radio" 
                            name="mode" 
                            value="edit" 
                            checked={mode === 'edit'} 
                            onChange={e => setMode(e.target.value)} 
                            className="hidden"
                          />
                          <div className={`w-6 h-6 rounded-full border-2 ${mode === 'edit' ? 'border-blue-500 bg-blue-500' : 'border-gray-300'}`}></div>
                          <div>
                            <p className="font-medium">Allow Editing</p>
                            <p className="text-sm text-gray-500">Doctor can add notes</p>
                          </div>
                        </label>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="flex space-x-4 mt-8 pt-6 border-t border-gray-200">
                  <button 
                    onClick={submit}
                    className="flex-1 py-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-colors font-semibold flex items-center justify-center space-x-2"
                  >
                    <span>📅</span>
                    <span>Request Appointment</span>
                  </button>
                  <button 
                    onClick={() => { setDoctor(''); setReason(''); setSelectedFiles([]); setMode('view'); setErrors({}); }}
                    className="px-6 py-3 border border-gray-300 text-gray-700 rounded-xl hover:bg-gray-50 transition-colors font-medium"
                  >
                    Reset Form
                  </button>
                </div>
              </div>

              {/* Previous Appointments */}
              <div className="bg-white/90 backdrop-blur-sm rounded-2xl p-6 shadow-lg border border-white/20">
                <h2 className="text-xl font-semibold text-gray-900 mb-6">Your Appointments</h2>
                {appointments.length === 0 ? (
                  <div className="text-center py-8">
                    <span className="text-6xl mb-4">📅</span>
                    <p className="text-gray-600">No appointments scheduled yet</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {appointments.map(appointment => (
                      <div key={appointment.id} className="p-4 border border-gray-200 rounded-xl hover:shadow-md transition-all">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center space-x-3 mb-2">
                              <h3 className="font-semibold text-gray-900">{appointment.doctor}</h3>
                              <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                                appointment.status === 'Requested' ? 'bg-yellow-100 text-yellow-800' : 'bg-green-100 text-green-800'
                              }`}>
                                {appointment.status}
                              </span>
                            </div>
                            <p className="text-gray-600 mb-3">{appointment.reason}</p>
                            <div className="flex items-center space-x-4 text-sm text-gray-500">
                              <span>📁 {appointment.files.length} files</span>
                              <span>🔒 {appointment.mode} access</span>
                              <span>🕒 {new Date(appointment.createdAt).toLocaleDateString()}</span>
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Enhanced File Picker Modal */}
          {showFilePicker && (
            <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-4">
              <div className="bg-white rounded-2xl w-full max-w-4xl h-[80vh] flex flex-col shadow-2xl">
                {/* Header */}
                <div className="flex items-center justify-between p-6 border-b border-gray-200">
                  <div>
                    <h3 className="text-xl font-semibold text-gray-900">Select Files to Share</h3>
                    <p className="text-sm text-gray-600 mt-1">Choose files from your medical records</p>
                  </div>
                  <button 
                    onClick={() => setShowFilePicker(false)}
                    className="text-gray-400 hover:text-gray-600 text-2xl transition-colors"
                  >
                    ✕
                  </button>
                </div>

                {/* Toolbar */}
                <div className="p-4 border-b border-gray-200 bg-gray-50">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                      {/* Search */}
                      <div className="relative">
                        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                          <span className="text-gray-400">🔍</span>
                        </div>
                        <input
                          type="text"
                          placeholder="Search files..."
                          value={searchQuery}
                          onChange={(e) => setSearchQuery(e.target.value)}
                          className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        />
                      </div>

                      {/* Category Filter */}
                      <select
                        value={selectedCategory}
                        onChange={(e) => setSelectedCategory(e.target.value)}
                        className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      >
                        {categories.map(category => (
                          <option key={category} value={category}>{category}</option>
                        ))}
                      </select>
                    </div>

                    {/* View Toggle */}
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => setViewMode('grid')}
                        className={`p-2 rounded-lg ${viewMode === 'grid' ? 'bg-blue-100 text-blue-600' : 'text-gray-400'}`}
                      >
                        ⬜
                      </button>
                      <button
                        onClick={() => setViewMode('list')}
                        className={`p-2 rounded-lg ${viewMode === 'list' ? 'bg-blue-100 text-blue-600' : 'text-gray-400'}`}
                      >
                        ☰
                      </button>
                    </div>
                  </div>
                </div>

                {/* Files Grid/List */}
                <div className="flex-1 overflow-auto p-6">
                  {viewMode === 'grid' ? (
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                      {filteredFiles.map(file => (
                        <div
                          key={file.id}
                          onClick={() => handleFileSelect(file)}
                          className={`border-2 rounded-xl p-4 cursor-pointer transition-all ${
                            selectedFiles.find(f => f.id === file.id) 
                              ? 'border-blue-500 bg-blue-50' 
                              : 'border-gray-200 hover:border-blue-300 hover:bg-gray-50'
                          }`}
                        >
                          <div className="flex items-center space-x-3 mb-3">
                            <span className="text-2xl">{getFileIcon(file.type)}</span>
                            <div className="flex-1 min-w-0">
                              <p className="font-medium text-gray-900 truncate">{file.name}</p>
                              <p className="text-sm text-gray-500">{file.category}</p>
                            </div>
                          </div>
                          <div className="flex justify-between text-sm text-gray-500">
                            <span>{file.size}</span>
                            <span>{file.date}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="space-y-2">
                      {filteredFiles.map(file => (
                        <div
                          key={file.id}
                          onClick={() => handleFileSelect(file)}
                          className={`flex items-center space-x-4 p-3 rounded-lg cursor-pointer transition-all ${
                            selectedFiles.find(f => f.id === file.id) 
                              ? 'bg-blue-50 border-2 border-blue-500' 
                              : 'hover:bg-gray-50 border-2 border-transparent'
                          }`}
                        >
                          <span className="text-2xl">{getFileIcon(file.type)}</span>
                          <div className="flex-1 min-w-0">
                            <p className="font-medium text-gray-900">{file.name}</p>
                            <p className="text-sm text-gray-500">{file.category} • {file.size}</p>
                          </div>
                          <div className="text-sm text-gray-500">{file.date}</div>
                        </div>
                      ))}
                    </div>
                  )}

                  {filteredFiles.length === 0 && (
                    <div className="text-center py-12">
                      <span className="text-6xl mb-4">📭</span>
                      <p className="text-gray-600">No files found</p>
                      <p className="text-sm text-gray-500 mt-1">Try adjusting your search or filter</p>
                    </div>
                  )}
                </div>

                {/* Footer */}
                <div className="flex items-center justify-between p-6 border-t border-gray-200 bg-gray-50">
                  <div className="text-sm text-gray-600">
                    {selectedFiles.length} file(s) selected
                  </div>
                  <div className="flex space-x-3">
                    <button
                      onClick={() => {
                        setSelectedFiles([]);
                        setShowFilePicker(false);
                      }}
                      className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={() => setShowFilePicker(false)}
                      className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                    >
                      Add Selected Files
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
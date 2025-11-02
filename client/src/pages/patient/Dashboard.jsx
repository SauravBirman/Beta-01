import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import Navbar from '../../components/Navbar';
import Slidebar from '../../components/Slidebar';

const Dashboard = () => {
  const [records, setRecords] = useState([]);
  const [recordsLoading, setRecordsLoading] = useState(false);
  const [recordsError, setRecordsError] = useState('');

  const [showUploadModal, setShowUploadModal] = useState(false);
  const [showAppointmentModal, setShowAppointmentModal] = useState(false);
  const [appointmentForm, setAppointmentForm] = useState({
    doctor: '',
    hospital: '',
    reason: '',
    fileIds: [],
    mode: 'view'
  });
  const [appointments, setAppointments] = useState([]);
  const [newRecord, setNewRecord] = useState({
    title: '',
    type: 'Lab Report',
    date: new Date().toISOString().split('T')[0],
    file: null,
    symptoms: ''
  });
  const [uploadLoading, setUploadLoading] = useState(false);
  const [uploadError, setUploadError] = useState('');
  const [uploadSuccess, setUploadSuccess] = useState('');

  const [currentTime, setCurrentTime] = useState(new Date());
  const [sunPosition, setSunPosition] = useState(0);
  const [user, setUser] = useState({ firstName: 'John', lastName: '', name: 'John Doe' });

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 60000); // Update every minute

    return () => clearInterval(timer);
  }, []);

  // fetch records from backend
  useEffect(() => {
    let mounted = true;
    const fetchRecords = async () => {
      setRecordsLoading(true);
      setRecordsError('');
      try {
        const token = localStorage.getItem('token');
        const res = await fetch('http://localhost:5000/api/reports/me', {
          headers: token ? { Authorization: `Bearer ${token}` } : {}
        });
        const json = await res.json().catch(() => ({}));
        if (!res.ok) throw new Error(json.message || `Failed to load records (${res.status})`);
        // map server reports to UI records shape
        const items = (json.reports || json.data || json || []).map((r, idx) => ({
          id: r._id || r.id || idx + 1,
          title: r.fileName || r.name || r.summary || 'Report',
          date: (r.createdAt || r.date || '').slice(0,10) || new Date().toISOString().split('T')[0],
          status: r.status || 'Normal',
          type: r.type || 'Lab Report',
          fileUrl: r.ipfsHash || r.fileUrl || '',
          symptoms: r.symptoms || r.notes || ''
        }));
        if (mounted) setRecords(items);
      } catch (err) {
        console.error('Failed to fetch records', err);
        if (mounted) setRecordsError(err.message || 'Failed to load records');
      } finally {
        if (mounted) setRecordsLoading(false);
      }
    };

    fetchRecords();
    return () => { mounted = false; };
  }, []);

  useEffect(() => {
    const hours = currentTime.getHours();
    const minutes = currentTime.getMinutes();
    const totalMinutes = hours * 60 + minutes;
    
    // Calculate sun position (0% at 6 AM, 100% at 6 PM)
    let position = ((totalMinutes - 360) / 720) * 100; // 6 AM to 6 PM = 12 hours = 720 minutes
    position = Math.max(0, Math.min(100, position)); // Clamp between 0 and 100
    setSunPosition(position);
  }, [currentTime]);

  // load user info (first name) from localStorage if available
  useEffect(() => {
    try {
      const raw = localStorage.getItem('userData');
      if (raw) {
        const u = JSON.parse(raw);
        const firstName = u.firstName || (u.name ? u.name.split(' ')[0] : '') || 'John';
        const lastName = u.lastName || (u.name ? (u.name.split(' ')[1] || '') : '');
        setUser({ firstName, lastName, name: u.name || `${firstName} ${lastName}`.trim() });
      }
    } catch (e) {
      // ignore
    }
  }, []);

  const handleUpload = () => {
    // Validate
    setUploadError('');
    if (!newRecord.title.trim()) {
      setUploadError('Please enter a record title');
      return;
    }
    if (!newRecord.file) {
      setUploadError('Please select a file to upload');
      return;
    }

    // Build form data
    const form = new FormData();
    form.append('file', newRecord.file, newRecord.file.name);
  // include metadata fields
  form.append('title', newRecord.title);
  form.append('type', newRecord.type);
  form.append('date', newRecord.date);
  if (newRecord.symptoms) form.append('symptoms', newRecord.symptoms);

    setUploadLoading(true);

    const token = localStorage.getItem('token');
    fetch('http://localhost:5000/api/reports/upload', {
      method: 'POST',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: form
    })
    .then(async res => {
      const json = await res.json().catch(() => ({}));
      // accept any 2xx response as success from the backend
      if (!res.ok) throw new Error(json.message || 'Upload failed');
      const rpt = json.report || json.data || {};
      const record = {
        id: records.length + 1,
        title: newRecord.title,
        date: newRecord.date,
        status: 'Uploaded',
        type: newRecord.type,
        fileUrl: rpt.ipfsHash || rpt.fileUrl || '',
        symptoms: newRecord.symptoms || ''
      };
      setRecords([record, ...records]);
      setUploadSuccess('Record uploaded successfully');
      setTimeout(() => setUploadSuccess(''), 2500);
      // reset
  setNewRecord({ title: '', type: 'Lab Report', date: new Date().toISOString().split('T')[0], file: null, symptoms: '' });
      setShowUploadModal(false);
    })
    .catch(err => {
      console.error('Upload error', err);
      setUploadError(err.message || 'Upload failed');
    })
    .finally(() => setUploadLoading(false));
  };

  const handleFileSelect = (e) => {
    const f = e.target.files && e.target.files[0];
    if (f) setNewRecord(prev => ({ ...prev, file: f }));
  };

  const getTimeBasedGradient = () => {
    const hours = currentTime.getHours();
    
    if (hours >= 6 && hours < 12) {
      return 'from-amber-200 via-orange-100 to-blue-100'; // Morning
    } else if (hours >= 12 && hours < 18) {
      return 'from-yellow-200 via-amber-100 to-orange-100'; // Afternoon
    } else if (hours >= 18 && hours < 21) {
      return 'from-orange-300 via-pink-200 to-purple-300'; // Evening
    } else {
      return 'from-indigo-900 via-purple-900 to-blue-900'; // Night
    }
  };

  const getGreeting = () => {
    const hours = currentTime.getHours();
    
    if (hours >= 5 && hours < 12) return 'Good morning';
    if (hours >= 12 && hours < 17) return 'Good afternoon';
    if (hours >= 17 && hours < 21) return 'Good evening';
    return 'Good night';
  };

  const getSunMoonEmoji = () => {
    const hours = currentTime.getHours();
    
    if (hours >= 6 && hours < 18) {
      return '☀️'; // Sun
    } else {
      return '🌙'; // Moon
    }
  };

  return (
    <div>
      <Navbar companyName="MedChain - Patient" />

      <div className="flex">
        <Slidebar role="patient" />

        <div className="flex-1 p-6 relative overflow-hidden">
          {/* Animated Background */}
          <div className={`absolute top-0 left-0 right-0 h-80 bg-gradient-to-br ${getTimeBasedGradient()} transition-all duration-1000 ease-in-out -z-10`}>
            {/* Sun/Moon Animation */}
            <div 
              className="absolute top-8 text-4xl transition-all duration-1000 ease-in-out"
              style={{
                left: `${sunPosition}%`,
                transform: 'translateX(-50%)'
              }}
            >
              {getSunMoonEmoji()}
            </div>
            
            {/* Cloud Animation */}
            <div className="absolute top-16 left-1/4 text-2xl opacity-70 animate-pulse">☁️</div>
            <div className="absolute top-20 right-1/3 text-2xl opacity-60 animate-pulse delay-300">☁️</div>
            <div className="absolute top-12 left-2/3 text-xl opacity-50 animate-pulse delay-700">☁️</div>
          </div>

          {/* User Welcome Section */}
          <div className="flex items-center space-x-6 mb-8 relative z-10">
            <div className="w-20 h-20 bg-gradient-to-br from-blue-500 to-blue-600 rounded-full flex items-center justify-center shadow-lg border-2 border-white">
              {(() => {
                const initials = (`${user.firstName?.[0] || ''}${user.lastName?.[0] || ''}`).toUpperCase() || (user.name || 'JD').slice(0,2).toUpperCase();
                return <span className="text-white font-bold text-2xl">{initials}</span>;
              })()}
            </div>
            <div>
              <h1 className="text-3xl font-bold text-gray-900 mb-2">
                {getGreeting()}, {user.firstName || 'John'}!
              </h1>
              <p className="text-gray-700 text-lg">
                {currentTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} • 
                Welcome to your health dashboard
              </p>
            </div>
          </div>

          {/* Upload Records Section */}
          <div className="bg-white/80 backdrop-blur-sm rounded-xl p-6 mb-8 border border-white/20 shadow-lg relative z-10">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-semibold text-gray-900 mb-2">Upload New Health Records</h2>
                <p className="text-gray-600">Keep your medical history updated by uploading new reports and documents</p>
              </div>
              <button
                onClick={() => setShowUploadModal(true)}
                className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-semibold transition-colors shadow-md hover:shadow-lg transform hover:-translate-y-0.5 transition-transform"
              >
                + Upload Record
              </button>
            </div>
          </div>

          {/* Health Records Section */}
          <section className="mb-8 relative z-10">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-gray-900">Your Health Records</h2>
                <div className="flex items-center space-x-3">
                  <span className="text-gray-500 bg-white/80 backdrop-blur-sm px-3 py-1 rounded-full">{records.length} records</span>
                  {recordsLoading && <span className="text-sm text-gray-500">Loading…</span>}
                  {recordsError && <span className="text-sm text-red-600">{recordsError}</span>}
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {records.map(record => (
                <div 
                  key={record.id}
                  className="bg-white/90 backdrop-blur-sm rounded-xl shadow-sm border border-white/20 p-5 hover:shadow-md transition-all duration-300 cursor-pointer hover:transform hover:-translate-y-1"
                >
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <h3 className="font-semibold text-gray-900 text-lg mb-1">{record.title}</h3>
                      <span className="inline-block px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-full">
                        {record.type}
                      </span>
                    </div>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      (record.status === 'Normal' || record.status === 'Uploaded')
                        ? 'bg-green-100 text-green-800'
                        : 'bg-yellow-100 text-yellow-800'
                    }`}>
                      {record.status}
                    </span>
                  </div>
                  
                  <div className="space-y-2 mb-4">
                    <div className="flex items-center text-sm text-gray-600">
                      <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                      </svg>
                      {record.date}
                    </div>
                    {record.symptoms && (
                      <div className="text-sm text-gray-700">
                        <strong>Symptoms:</strong> {record.symptoms}
                      </div>
                    )}
                  </div>

                  <div className="flex space-x-2">
                    <button className="flex-1 bg-blue-600 hover:bg-blue-700 text-white py-2 px-3 rounded-lg text-sm font-medium transition-colors">
                      View
                    </button>
                    <button className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors">
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z" />
                      </svg>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </section>

          {/* Quick Actions */}
          <section className="bg-white/90 backdrop-blur-sm rounded-xl shadow-sm border border-white/20 p-6 relative z-10">
            <h3 className="text-xl font-semibold text-gray-900 mb-4">Quick Actions</h3>
              <div className="flex flex-wrap gap-4">
              <Link to="/patient/ai-assistant">
                <button className="bg-green-600 hover:bg-green-700 text-white px-6 py-3 rounded-lg font-semibold transition-colors flex items-center space-x-2 hover:shadow-lg transform hover:-translate-y-0.5 transition-transform">
                  <span className="material-icons">smart_toy</span>
                  <span>AI Health Assistant</span>
                </button>
              </Link>
              
              <button onClick={() => setShowAppointmentModal(true)} className="bg-purple-600 hover:bg-purple-700 text-white px-6 py-3 rounded-lg font-semibold transition-colors flex items-center space-x-2 hover:shadow-lg transform hover:-translate-y-0.5 transition-transform">
                <span className="material-icons">event_available</span>
                <span>Make Appointment</span>
              </button>

              <button className="bg-orange-500 hover:bg-orange-600 text-white px-6 py-3 rounded-lg font-semibold transition-colors flex items-center space-x-2 hover:shadow-lg transform hover:-translate-y-0.5 transition-transform">
                <span className="material-icons">link</span>
                <span>Share Records</span>
              </button>

              <button className="bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-3 rounded-lg font-semibold transition-colors flex items-center space-x-2 hover:shadow-lg transform hover:-translate-y-0.5 transition-transform">
                <span className="material-icons">event</span>
                <span>Book Appointment</span>
              </button>
            </div>
          </section>

          {/* Appointment Modal */}
          {showAppointmentModal && (
            <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
              <div className="bg-white rounded-xl p-6 w-full max-w-xl mx-4">
                <h3 className="text-xl font-semibold text-gray-900 mb-4">Make Appointment</h3>

                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Doctor name or ID or Hospital</label>
                    <input type="text" value={appointmentForm.doctor} onChange={e => setAppointmentForm({...appointmentForm, doctor: e.target.value})} className="w-full px-3 py-2 border border-gray-300 rounded-lg" placeholder="Dr. Smith or ID or Hospital" />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Basic reason</label>
                    <textarea value={appointmentForm.reason} onChange={e => setAppointmentForm({...appointmentForm, reason: e.target.value})} className="w-full px-3 py-2 border border-gray-300 rounded-lg" rows={3} placeholder="Short reason for appointment"></textarea>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Which files to share with doctor</label>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-h-40 overflow-auto border rounded-md p-2">
                      {records.map(r => (
                        <label key={r.id} className="flex items-center space-x-2">
                          <input type="checkbox" checked={appointmentForm.fileIds.includes(r.id)} onChange={e => {
                            const checked = e.target.checked;
                            setAppointmentForm(prev => ({
                              ...prev,
                              fileIds: checked ? [...prev.fileIds, r.id] : prev.fileIds.filter(id => id !== r.id)
                            }))
                          }} />
                          <span className="text-sm">{r.title} • {r.date}</span>
                        </label>
                      ))}
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Share mode</label>
                    <div className="flex items-center space-x-4">
                      <label className="flex items-center space-x-2"><input type="radio" name="mode" value="view" checked={appointmentForm.mode === 'view'} onChange={e => setAppointmentForm({...appointmentForm, mode: e.target.value})} /> <span>View</span></label>
                      <label className="flex items-center space-x-2"><input type="radio" name="mode" value="edit" checked={appointmentForm.mode === 'edit'} onChange={e => setAppointmentForm({...appointmentForm, mode: e.target.value})} /> <span>Edit</span></label>
                    </div>
                  </div>
                </div>

                <div className="flex gap-3 mt-6">
                  <button onClick={() => setShowAppointmentModal(false)} className="flex-1 px-4 py-2 border border-gray-300 rounded-lg">Cancel</button>
                  <button onClick={() => {
                    // simple submit: store in-memory appointments and show confirmation
                    setAppointments(prev => ([...prev, { id: prev.length + 1, ...appointmentForm, createdAt: new Date().toISOString() }]));
                    setShowAppointmentModal(false);
                    setAppointmentForm({ doctor: '', hospital: '', reason: '', fileIds: [], mode: 'view' });
                    alert('Appointment requested — files will be shared with selected mode.');
                  }} className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg">Request Appointment</button>
                </div>
              </div>
            </div>
          )}

          {/* Upload Modal */}
          {showUploadModal && (
            <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
              <div className="bg-white rounded-xl p-6 w-full max-w-md mx-4">
                <h3 className="text-xl font-semibold text-gray-900 mb-4">Upload New Record</h3>
                
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Record Title</label>
                    <input
                      type="text"
                      value={newRecord.title}
                      onChange={(e) => setNewRecord({...newRecord, title: e.target.value})}
                      placeholder="e.g., Blood Test Results"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Record Type</label>
                    <select
                      value={newRecord.type}
                      onChange={(e) => setNewRecord({...newRecord, type: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    >
                      <option value="Lab Report">Lab Report</option>
                      <option value="Imaging">Imaging</option>
                      <option value="Test">Test</option>
                      <option value="Prescription">Prescription</option>
                      <option value="Other">Other</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Date</label>
                    <input
                      type="date"
                      value={newRecord.date}
                      onChange={(e) => setNewRecord({...newRecord, date: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Symptoms (optional)</label>
                    <textarea
                      value={newRecord.symptoms}
                      onChange={(e) => setNewRecord({...newRecord, symptoms: e.target.value})}
                      placeholder="Describe any symptoms related to this record (short notes)"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      rows={3}
                    />
                  </div>

                  <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
                    <svg className="w-12 h-12 text-gray-400 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                    </svg>
                    <p className="text-gray-600 mb-2">Drag and drop your file here or choose a file</p>
                    <input type="file" onChange={handleFileSelect} accept=".pdf,.jpg,.jpeg,.png,.doc,.docx" className="mx-auto" />
                    {newRecord.file && (
                      <p className="text-sm text-green-600 mt-2">Selected: {newRecord.file.name}</p>
                    )}
                    {uploadError && (
                      <p className="text-sm text-red-600 mt-2">{uploadError}</p>
                    )}
                    {uploadSuccess && (
                      <p className="text-sm text-green-600 mt-2">{uploadSuccess}</p>
                    )}
                    {uploadLoading && (
                      <p className="text-sm text-gray-600 mt-2">Uploading…</p>
                    )}
                  </div>
                </div>

                <div className="flex space-x-3 mt-6">
                  <button
                    onClick={() => setShowUploadModal(false)}
                    className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleUpload}
                    disabled={uploadLoading}
                    className={`flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors ${uploadLoading ? 'opacity-60 cursor-not-allowed' : ''}`}
                  >
                    {uploadLoading ? 'Uploading...' : 'Upload Record'}
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
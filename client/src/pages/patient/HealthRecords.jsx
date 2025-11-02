import React, { useMemo, useState, useEffect } from 'react';
import Navbar from '../../components/Navbar';
import Slidebar from '../../components/Slidebar';

// records will be fetched from the backend

const typeColors = {
  Lab: 'bg-green-100 text-green-800 border-green-200',
  Prescription: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  Imaging: 'bg-blue-100 text-blue-800 border-blue-200',
};

const typeIcons = {
  Lab: 'science',
  Prescription: 'medical_services',
  Imaging: 'image'
};

function formatDate(d) {
  return d;
}

export default function HealthRecords() {
  const [records, setRecords] = useState([]);
  const [recordsLoading, setRecordsLoading] = useState(false);
  const [recordsError, setRecordsError] = useState('');
  const [query, setQuery] = useState('');
  const [typeFilter, setTypeFilter] = useState('All');
  const [uploaderFilter, setUploaderFilter] = useState('All');
  const [viewMode, setViewMode] = useState('cards');
  const [selected, setSelected] = useState(null);
  const [shareModalOpen, setShareModalOpen] = useState(false);
  const [shareReport, setShareReport] = useState(null);
  const [doctorQuery, setDoctorQuery] = useState('');
  const [doctorResults, setDoctorResults] = useState([]);
  const [selectedDoctor, setSelectedDoctor] = useState(null);
  const [sharing, setSharing] = useState(false);
  const [shareError, setShareError] = useState('');
  const [shareSuccess, setShareSuccess] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [currentTime, setCurrentTime] = useState(new Date());
  const [downloadingId, setDownloadingId] = useState(null);

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 60000);
    return () => clearInterval(timer);
  }, []);

  const uploaders = useMemo(() => Array.from(new Set(records.map(r => r.uploader))), [records]);

  useEffect(() => {
    let mounted = true;
    const load = async () => {
      setRecordsLoading(true);
      setRecordsError('');
      try {
        const token = localStorage.getItem('token');
        const res = await fetch('http://localhost:5000/api/reports/me', {
          headers: token ? { Authorization: `Bearer ${token}` } : {}
        });
        const json = await res.json().catch(() => ({}));
        if (!res.ok) throw new Error(json.message || `Failed to load (${res.status})`);
        const items = (json.reports || json.data || json || []).map((r, idx) => ({
          id: r._id || r.id || idx + 1,
          date: (r.createdAt || r.date || '').slice(0,10) || new Date().toISOString().split('T')[0],
          type: r.type || 'Lab',
          uploader: r.uploader || r.uploaderName || 'Unknown',
          access: r.access || 'You',
          summary: r.summary || r.fileName || r.name || 'Report',
          size: r.size || r.fileSize || ''
        }));
        if (mounted) setRecords(items);
      } catch (err) {
        console.error('Failed to load records', err);
        if (mounted) setRecordsError(err.message || 'Failed to load records');
      } finally {
        if (mounted) setRecordsLoading(false);
      }
    };

    load();
    return () => { mounted = false; };
  }, []);

  // Download a report by id using the backend endpoint
  const handleDownload = async (report) => {
    if (!report || !report.id) return;
    setDownloadingId(report.id);
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`http://localhost:5000/api/reports/${report.id}/download`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {}
      });

      const contentType = res.headers.get('content-type') || '';

      // If backend returns JSON (current implementation returns { ipfsHash, fileName })
      if (contentType.includes('application/json')) {
        const json = await res.json().catch(() => ({}));
        if (!res.ok) throw new Error(json.message || `Download failed (${res.status})`);
        if (json.ipfsHash) {
          // Open the public IPFS gateway for the returned hash
          const url = `https://ipfs.io/ipfs/${json.ipfsHash}`;
          // open in a new tab (this is a user-initiated click so should be allowed)
          window.open(url, '_blank');
        } else {
          throw new Error('No file reference returned from server');
        }
      } else {
        // Assume binary/stream response — download as blob
        if (!res.ok) {
          const text = await res.text().catch(() => '');
          throw new Error(text || `Download failed (${res.status})`);
        }
        const blob = await res.blob();
        // Try to get filename from content-disposition header, fallback to report.summary
        const cd = res.headers.get('content-disposition') || '';
        let filename = report.summary || 'report';
        const match = cd.match(/filename\*=UTF-8''([^;\n]+)/) || cd.match(/filename="?([^";\n]+)"?/);
        if (match && match[1]) filename = decodeURIComponent(match[1]);

        const href = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = href;
        a.download = filename.replace(/\"/g, '');
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(href);
      }
    } catch (err) {
      console.error('Download error', err);
      setRecordsError(err.message || 'Failed to download report');
    } finally {
      setDownloadingId(null);
    }
  };

  // Open share modal for a report
  const openShareModal = (report) => {
    setShareReport(report);
    setShareModalOpen(true);
    setDoctorQuery('');
    setDoctorResults([]);
    setSelectedDoctor(null);
    setShareError('');
    setShareSuccess('');
    // Load full doctor list when opening modal
    loadDoctors();
  };

  const closeShareModal = () => {
    setShareModalOpen(false);
    setShareReport(null);
    setDoctorQuery('');
    setDoctorResults([]);
    setSelectedDoctor(null);
    setShareError('');
    setShareSuccess('');
  };

  // Try to search doctors from server (best-effort). If server doesn't support, allow manual id entry.
  const searchDoctors = async () => {
    setShareError('');
    setDoctorResults([]);
    if (!doctorQuery) return;
    try {
      const token = localStorage.getItem('token');
      const url = `http://localhost:5000/api/users?search=${encodeURIComponent(doctorQuery)}&role=doctor`;
      const res = await fetch(url, { headers: token ? { Authorization: `Bearer ${token}` } : {} });
      const json = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(json.message || `Search failed (${res.status})`);
      // Accept either json.users, json.data, or raw array
      const list = json.users || json.data || json || [];
      setDoctorResults(Array.isArray(list) ? list : []);
    } catch (err) {
      // Not fatal: show message and allow manual ID entry
      console.warn('Doctor search failed', err);
      setShareError('Search failed — you can still share using the doctor ID');
    }
  };

  // Load all doctors (used when opening the share modal)
  const loadDoctors = async () => {
    setShareError('');
    setDoctorResults([]);
    try {
      const token = localStorage.getItem('token');
      // best-effort endpoint: server should accept role=doctor to list doctors
      const url = `http://localhost:5000/api/users?role=doctor`;
      const res = await fetch(url, { headers: token ? { Authorization: `Bearer ${token}` } : {} });
      const json = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(json.message || `Failed to load doctors (${res.status})`);
      const list = json.users || json.data || json || [];
      setDoctorResults(Array.isArray(list) ? list : []);
    } catch (err) {
      console.warn('Failed to load doctors', err);
      setShareError('Unable to load doctors — you can still share using the doctor ID');
    }
  };

  const confirmShare = async () => {
    if (!shareReport) return;
    // Prefer the doctor's blockchain address. If user selected a doctor from the list,
    // that object should include `blockchainAddress` (populated by the server).
    let doctorAddress = '';
    if (selectedDoctor) doctorAddress = selectedDoctor.blockchainAddress || selectedDoctor._id || selectedDoctor.id || '';
    if (!doctorAddress && doctorQuery) doctorAddress = doctorQuery;

    // Basic validation: require an Ethereum-style address (0x...) when possible.
    const looksLikeAddress = typeof doctorAddress === 'string' && doctorAddress.startsWith('0x') && doctorAddress.length === 42;
    if (!doctorAddress || !looksLikeAddress) {
      setShareError('Please select a doctor from the list or enter their wallet address (0x...)');
      return;
    }
    setSharing(true);
    setShareError('');
    try {
      const token = localStorage.getItem('token');
      const res = await fetch('http://localhost:5000/api/reports/grant', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {})
        },
        body: JSON.stringify({ reportId: shareReport.id, doctorAddress })
      });
      const json = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(json.message || `Share failed (${res.status})`);

      // Update local UI to reflect sharing
      setRecords(prev => prev.map(r => r.id === shareReport.id ? { ...r, access: `Shared with ${selectedDoctor?.name || doctorAddress}` } : r));
      setShareSuccess('Report shared successfully');

      // Optionally close modal after a short delay
      setTimeout(() => {
        closeShareModal();
      }, 900);
    } catch (err) {
      console.error('Share error', err);
      setShareError(err.message || 'Failed to share report');
    } finally {
      setSharing(false);
    }
  };

  const filtered = useMemo(() => {
    return records.filter(r => {
      if (typeFilter !== 'All' && r.type !== typeFilter) return false;
      if (uploaderFilter !== 'All' && r.uploader !== uploaderFilter) return false;
      if (dateFrom && r.date < dateFrom) return false;
      if (dateTo && r.date > dateTo) return false;
      if (query) {
        const q = query.toLowerCase();
        if (!(r.summary.toLowerCase().includes(q) || r.uploader.toLowerCase().includes(q) || r.type.toLowerCase().includes(q))) return false;
      }
      return true;
    });
  }, [records, typeFilter, uploaderFilter, dateFrom, dateTo, query]);

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

  return (
    <div>
      <Navbar companyName="MedChain - Patient" />

      <div className="flex">
        <Slidebar role="patient" />

        <main className="flex-1 relative overflow-hidden">
          {/* Animated Background */}
          <div className={`absolute top-0 left-0 right-0 h-64 bg-gradient-to-br ${getTimeBasedGradient()} transition-all duration-1000 ease-in-out -z-10`}>
            {/* Floating medical icons */}
            <div className="absolute top-8 left-1/4 text-3xl opacity-20 animate-bounce">🏥</div>
            <div className="absolute top-16 right-1/3 text-2xl opacity-30 animate-pulse delay-300">💊</div>
            <div className="absolute top-24 left-2/3 text-3xl opacity-25 animate-bounce delay-700">🩺</div>
            <div className="absolute top-12 right-1/4 text-2xl opacity-20 animate-pulse delay-500">🧪</div>
            <div className="absolute top-32 left-1/3 text-3xl opacity-30 animate-bounce delay-1000">📋</div>
            
            {/* Animated pulse circles */}
            <div className="absolute top-20 left-10 w-4 h-4 bg-blue-300 rounded-full animate-ping opacity-20"></div>
            <div className="absolute top-8 right-20 w-3 h-3 bg-green-300 rounded-full animate-ping opacity-30 delay-300"></div>
            <div className="absolute top-40 left-20 w-2 h-2 bg-purple-300 rounded-full animate-ping opacity-25 delay-700"></div>
          </div>

          <div className="p-6 relative z-10">
            {/* Header Section */}
            <div className="flex items-center justify-between mb-8">
              <div>
                <h1 className="text-3xl font-bold text-gray-900">Health Records</h1>
                <p className="text-lg text-gray-600 mt-2">Manage and review all your medical reports and documents</p>
              </div>

              <div className="flex items-center space-x-3 bg-white/80 backdrop-blur-sm rounded-xl p-2 border border-white/20 shadow-sm">
                <button
                  onClick={() => setViewMode('cards')}
                  className={`px-4 py-2 rounded-lg transition-all duration-200 ${
                    viewMode === 'cards' 
                      ? 'bg-blue-600 text-white shadow-md' 
                      : 'text-gray-600 hover:bg-gray-100'
                  }`}
                >
                  <div className="flex items-center space-x-2">
                    <span className="material-icons">description</span>
                    <span>Cards</span>
                  </div>
                </button>
                <button
                  onClick={() => setViewMode('table')}
                  className={`px-4 py-2 rounded-lg transition-all duration-200 ${
                    viewMode === 'table' 
                      ? 'bg-blue-600 text-white shadow-md' 
                      : 'text-gray-600 hover:bg-gray-100'
                  }`}
                >
                  <div className="flex items-center space-x-2">
                    <span className="material-icons">table_chart</span>
                    <span>Table</span>
                  </div>
                </button>
              </div>
            </div>

            {/* Filters Section */}
            <div className="bg-white/80 backdrop-blur-sm rounded-2xl p-6 mb-8 border border-white/20 shadow-lg">
              <div className="flex flex-wrap gap-4 items-center">
                <div className="relative flex-1 min-w-72">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <span className="material-icons text-gray-400">search</span>
                  </div>
                  <input
                    type="search"
                    placeholder="Search records, uploaders, types..."
                    value={query}
                    onChange={e => setQuery(e.target.value)}
                    className="pl-10 pr-4 py-3 border border-gray-200 rounded-xl w-full focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all"
                  />
                </div>

                <select 
                  value={typeFilter} 
                  onChange={e => setTypeFilter(e.target.value)} 
                  className="px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all"
                >
                  <option>All Types</option>
                  <option>Lab</option>
                  <option>Imaging</option>
                  <option>Prescription</option>
                </select>

                <select 
                  value={uploaderFilter} 
                  onChange={e => setUploaderFilter(e.target.value)} 
                  className="px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all"
                >
                  <option>All Uploaders</option>
                  {uploaders.map(u => <option key={u}>{u}</option>)}
                </select>

                <div className="flex items-center space-x-3 bg-gray-50 rounded-xl p-2">
                  <div className="flex items-center space-x-2">
                    <label className="text-sm text-gray-600 font-medium">From</label>
                    <input 
                      type="date" 
                      value={dateFrom} 
                      onChange={e => setDateFrom(e.target.value)} 
                      className="px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-blue-500 transition-all" 
                    />
                  </div>
                  <div className="flex items-center space-x-2">
                    <label className="text-sm text-gray-600 font-medium">To</label>
                    <input 
                      type="date" 
                      value={dateTo} 
                      onChange={e => setDateTo(e.target.value)} 
                      className="px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-blue-500 transition-all" 
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Results Count */}
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-4">
                <p className="text-gray-600">
                  Showing <span className="font-semibold text-gray-900">{filtered.length}</span> of <span className="font-semibold text-gray-900">{records.length}</span> records
                </p>
                {recordsLoading && <span className="text-sm text-gray-500">Loading…</span>}
                {recordsError && <span className="text-sm text-red-600">{recordsError}</span>}
              </div>
            </div>

            {/* Content */}
            {viewMode === 'cards' ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {filtered.map(r => (
                  <article 
                    key={r.id} 
                    className="bg-white/90 backdrop-blur-sm rounded-2xl p-6 border border-white/20 shadow-sm hover:shadow-xl transition-all duration-300 hover:-translate-y-1 group"
                  >
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex items-center space-x-3">
                        <span className="material-icons text-2xl">{typeIcons[r.type]}</span>
                        <span className={`inline-block px-3 py-1 rounded-full text-xs font-medium border ${typeColors[r.type]}`}>
                          {r.type}
                        </span>
                      </div>
                      <span className="text-sm text-gray-500 bg-gray-100 px-2 py-1 rounded-lg">{r.size}</span>
                    </div>

                    <h3 className="font-semibold text-lg text-gray-900 mb-2 group-hover:text-blue-600 transition-colors">
                      {r.summary}
                    </h3>
                    
                    <div className="space-y-2 mb-4">
                      <p className="text-sm text-gray-600 flex items-center">
                        <span className="material-icons mr-2 text-base">calendar_today</span>
                        Uploaded {formatDate(r.date)}
                      </p>
                      <p className="text-sm text-gray-600 flex items-center">
                        <span className="material-icons mr-2 text-base">person</span>
                        {r.uploader}
                      </p>
                      <p className="text-sm text-gray-600 flex items-center">
                        <span className="material-icons mr-2 text-base">lock</span>
                        Access: {r.access}
                      </p>
                    </div>

                    <div className="flex space-x-2">
                      <button 
                        onClick={() => setSelected(r)} 
                        className="flex-1 bg-blue-600 hover:bg-blue-700 text-white py-2 px-3 rounded-lg text-sm font-medium transition-all duration-200 hover:shadow-md"
                      >
                        View Details
                      </button>
                      <button onClick={() => handleDownload(r)} className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors">
                        {downloadingId === r.id ? (
                          <span className="text-sm text-gray-600">Downloading…</span>
                        ) : (
                          <span className="material-icons">download</span>
                        )}
                      </button>
                      <button onClick={() => openShareModal(r)} className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors">
                        <span className="material-icons">link</span>
                      </button>
                    </div>
                  </article>
                ))}
              </div>
            ) : (
              <div className="bg-white/90 backdrop-blur-sm rounded-2xl border border-white/20 shadow-sm overflow-hidden">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900">Date</th>
                      <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900">Type</th>
                      <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900">Summary</th>
                      <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900">Uploaded by</th>
                      <th className="px-6 py-4 text-left text-sm font-semibold text-gray-900">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {filtered.map(r => (
                      <tr key={r.id} className="hover:bg-gray-50 transition-colors">
                        <td className="px-6 py-4 text-sm text-gray-700 font-medium">{formatDate(r.date)}</td>
                        <td className="px-6 py-4 text-sm">
                          <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium border ${typeColors[r.type]}`}>
                            <span className="material-icons text-sm mr-1">{typeIcons[r.type]}</span>
                            {r.type}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-900 font-medium">{r.summary}</td>
                        <td className="px-6 py-4 text-sm text-gray-700">{r.uploader}</td>
                        <td className="px-6 py-4 text-sm">
                          <div className="flex items-center gap-2">
                            <button 
                              onClick={() => setSelected(r)} 
                              className="px-3 py-2 rounded-lg bg-blue-600 text-white text-sm hover:bg-blue-700 transition-colors"
                            >
                              View
                            </button>
                            <button onClick={() => handleDownload(r)} className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors">
                              {downloadingId === r.id ? (
                                <span className="text-sm text-gray-600">Downloading…</span>
                              ) : (
                                <span className="material-icons">download</span>
                              )}
                            </button>
                            <button onClick={() => openShareModal(r)} className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors">
                              <span className="material-icons">link</span>
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {/* Empty State */}
            {filtered.length === 0 && (
              <div className="text-center py-12">
                <div className="text-6xl mb-4"><span className="material-icons">description</span></div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">No records found</h3>
                <p className="text-gray-600">Try adjusting your filters or search terms</p>
              </div>
            )}

            {/* Modal */}
            {selected && (
              <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
                <div className="bg-white rounded-2xl p-6 w-full max-w-2xl mx-4 shadow-2xl transform transition-all duration-300 scale-100">
                  <div className="flex justify-between items-start mb-6">
                    <div>
                      <div className="flex items-center space-x-3 mb-2">
                        <span className="material-icons text-2xl">{typeIcons[selected.type]}</span>
                        <span className={`inline-block px-3 py-1 rounded-full text-xs font-medium border ${typeColors[selected.type]}`}>
                          {selected.type}
                        </span>
                      </div>
                      <h2 className="text-2xl font-bold text-gray-900">{selected.summary}</h2>
                      <p className="text-sm text-gray-500 mt-1">
                        Uploaded {selected.date} by {selected.uploader} • {selected.size}
                      </p>
                    </div>
                    <button 
                      onClick={() => setSelected(null)} 
                      className="text-gray-400 hover:text-gray-600 text-2xl transition-colors"
                    >
                      <span className="material-icons">close</span>
                    </button>
                  </div>

                  <div className="mb-6">
                    <h3 className="font-semibold text-gray-900 mb-3">AI Summary</h3>
                    <div className="bg-blue-50 rounded-xl p-4 border border-blue-200">
                      <p className="text-sm text-gray-700">
                        This is a placeholder AI-generated summary for the selected record. Key findings and important 
                        medical information would be displayed here in an easy-to-understand format.
                      </p>
                    </div>
                  </div>

                  <div className="flex gap-3">
                    <button className="flex-1 bg-blue-600 hover:bg-blue-700 text-white py-3 px-4 rounded-xl font-semibold transition-colors flex items-center justify-center space-x-2">
                      <span className="material-icons">download</span>
                      <span>Download</span>
                    </button>
                    <button className="flex-1 bg-gray-100 hover:bg-gray-200 text-gray-700 py-3 px-4 rounded-xl font-semibold transition-colors flex items-center justify-center space-x-2">
                      <span className="material-icons">link</span>
                      <span>Share</span>
                    </button>
                  </div>
                </div>
              </div>
            )}

              {/* Share Modal */}
              {shareModalOpen && (
                <div className="fixed inset-0 z-60 flex items-center justify-center bg-black bg-opacity-50">
                  <div className="bg-white rounded-2xl p-6 w-full max-w-lg mx-4 shadow-2xl transform transition-all duration-300 scale-100">
                    <div className="flex justify-between items-center mb-4">
                      <h3 className="text-xl font-semibold">Share report with a doctor</h3>
                      <button onClick={closeShareModal} className="text-gray-400 hover:text-gray-600 text-2xl transition-colors">
                        <span className="material-icons">close</span>
                      </button>
                    </div>

                    <p className="text-sm text-gray-600 mb-4">Enter the doctor's ID or search by name/ID. The doctor will receive a notification when the report is shared.</p>

                    <div className="space-y-3">
                      <div>
                        <label className="text-sm font-medium text-gray-700">Search doctor</label>
                        <div className="flex mt-2">
                          <input
                            type="search"
                            value={doctorQuery}
                            onChange={e => { setDoctorQuery(e.target.value); setSelectedDoctor(null); setShareError(''); setShareSuccess(''); }}
                            placeholder="Doctor ID or name"
                            className="flex-1 px-4 py-3 border border-gray-200 rounded-l-xl focus:outline-none focus:ring-1 focus:ring-blue-500"
                          />
                          <button onClick={searchDoctors} className="px-4 py-3 bg-blue-600 text-white rounded-r-xl">Search</button>
                        </div>
                      </div>

                      {doctorResults.length > 0 && (
                        <div className="max-h-40 overflow-auto border border-gray-100 rounded-lg p-2">
                          {doctorResults.map(d => (
                            <div key={d.id || d._id} className={`p-2 rounded-lg hover:bg-gray-50 cursor-pointer flex items-center justify-between ${selectedDoctor && (selectedDoctor.id === (d._id || d.id) || selectedDoctor._id === (d._id || d.id)) ? 'bg-blue-50 border border-blue-100' : ''}`} onClick={() => setSelectedDoctor(d)}>
                              <div>
                                <div className="text-sm font-medium text-gray-900">{d.name || d.fullName || d.username || d._id}</div>
                                {/* <div className="text-xs text-gray-500">{d._id || d.id}</div> */}
                              </div>
                              <div className="text-sm text-gray-500">{d.specialty || ''}</div>
                            </div>
                          ))}
                        </div>
                      )}

                      <div className="text-sm text-gray-600">Or proceed with the entered ID: <span className="font-medium text-gray-900">{doctorQuery}</span></div>

                      {shareError && <div className="text-sm text-red-600">{shareError}</div>}
                      {shareSuccess && <div className="text-sm text-green-600">{shareSuccess}</div>}

                      <div className="flex items-center gap-3 mt-4">
                        <button onClick={confirmShare} disabled={sharing} className="flex-1 bg-blue-600 hover:bg-blue-700 text-white py-3 px-4 rounded-xl font-semibold transition-colors">
                          {sharing ? 'Sharing…' : 'Share Report'}
                        </button>
                        <button onClick={closeShareModal} className="px-4 py-3 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-xl">Cancel</button>
                      </div>
                    </div>
                  </div>
                </div>
              )}
          </div>
        </main>
      </div>
    </div>
  );
}
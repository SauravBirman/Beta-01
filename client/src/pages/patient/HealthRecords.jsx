import React, { useMemo, useState, useEffect } from 'react';
import Navbar from '../../components/Navbar';
import Slidebar from '../../components/Slidebar';

const DUMMY = [
  { id: 1, date: '2025-10-01', type: 'Lab', uploader: 'LabCorp', access: 'Dr. Smith', summary: 'Hemoglobin normal', size: '120KB' },
  { id: 2, date: '2025-09-18', type: 'Imaging', uploader: 'City Hospital', access: 'Dr. Jones', summary: 'No acute findings', size: '3.2MB' },
  { id: 3, date: '2025-08-20', type: 'Prescription', uploader: 'Dr. Smith', access: 'Pharmacy', summary: 'Amoxicillin 500mg', size: '8KB' },
  { id: 4, date: '2025-07-12', type: 'Lab', uploader: 'QuickLabs', access: 'Dr. Smith', summary: 'Elevated cholesterol', size: '95KB' },
  { id: 5, date: '2025-06-01', type: 'Imaging', uploader: 'Radiology Inc', access: 'Dr. Lee', summary: 'MRI - follow-up suggested', size: '4.6MB' },
];

const typeColors = {
  Lab: 'bg-green-100 text-green-800 border-green-200',
  Prescription: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  Imaging: 'bg-blue-100 text-blue-800 border-blue-200',
};

const typeIcons = {
  Lab: '🧪',
  Prescription: '💊',
  Imaging: '📷'
};

function formatDate(d) {
  return d;
}

export default function HealthRecords() {
  const [records] = useState(DUMMY);
  const [query, setQuery] = useState('');
  const [typeFilter, setTypeFilter] = useState('All');
  const [uploaderFilter, setUploaderFilter] = useState('All');
  const [viewMode, setViewMode] = useState('cards');
  const [selected, setSelected] = useState(null);
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [currentTime, setCurrentTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 60000);
    return () => clearInterval(timer);
  }, []);

  const uploaders = useMemo(() => Array.from(new Set(records.map(r => r.uploader))), [records]);

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
                    <span>📄</span>
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
                    <span>📊</span>
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
                    <span className="text-gray-400">🔍</span>
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
              <p className="text-gray-600">
                Showing <span className="font-semibold text-gray-900">{filtered.length}</span> of <span className="font-semibold text-gray-900">{records.length}</span> records
              </p>
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
                        <span className="text-2xl">{typeIcons[r.type]}</span>
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
                        <span className="mr-2">📅</span>
                        Uploaded {formatDate(r.date)}
                      </p>
                      <p className="text-sm text-gray-600 flex items-center">
                        <span className="mr-2">👤</span>
                        {r.uploader}
                      </p>
                      <p className="text-sm text-gray-600 flex items-center">
                        <span className="mr-2">🔒</span>
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
                      <button className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors">
                        <span className="text-lg">⬇️</span>
                      </button>
                      <button className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors">
                        <span className="text-lg">🔗</span>
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
                            {typeIcons[r.type]} {r.type}
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
                            <button className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors">
                              <span className="text-lg">⬇️</span>
                            </button>
                            <button className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors">
                              <span className="text-lg">🔗</span>
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
                <div className="text-6xl mb-4">📋</div>
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
                        <span className="text-2xl">{typeIcons[selected.type]}</span>
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
                      ✕
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
                      <span>⬇️</span>
                      <span>Download</span>
                    </button>
                    <button className="flex-1 bg-gray-100 hover:bg-gray-200 text-gray-700 py-3 px-4 rounded-xl font-semibold transition-colors flex items-center justify-center space-x-2">
                      <span>🔗</span>
                      <span>Share</span>
                    </button>
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
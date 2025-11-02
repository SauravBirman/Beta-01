import React, { useEffect, useState } from 'react';
import Navbar from '../components/Navbar';
import Slidebar from '../components/Slidebar';

const AIAssistant = () => {
  const [records, setRecords] = useState([]);
  const [loadingRecords, setLoadingRecords] = useState(false);
  const [selectedRecordId, setSelectedRecordId] = useState(null);
  const [symptomsInput, setSymptomsInput] = useState('');

  const [summary, setSummary] = useState('');
  const [analysis, setAnalysis] = useState(null);
  const [prediction, setPrediction] = useState(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState('');
  const [overallHealth, setOverallHealth] = useState({ score: 100, level: 'Good', note: 'No records yet' });

  // Fetch user's reports to allow selecting a record
  useEffect(() => {
    let mounted = true;
    const load = async () => {
      setLoadingRecords(true);
      try {
        const token = localStorage.getItem('token');
        const res = await fetch('http://localhost:5000/api/reports/me', {
          headers: token ? { Authorization: `Bearer ${token}` } : {}
        });
        const json = await res.json().catch(() => ({}));
        if (!res.ok) throw new Error(json.message || `Failed to load reports (${res.status})`);
        const items = (json.reports || json.data || json || []).map((r, idx) => ({
          id: r._id || r.id || idx + 1,
          title: r.fileName || r.name || r.summary || 'Report',
          date: (r.createdAt || r.date || '').slice(0,10) || new Date().toISOString().split('T')[0],
          type: r.type || 'Lab',
          symptoms: r.symptoms || r.notes || ''
        }));
        if (mounted) setRecords(items);
      } catch (err) {
        console.error('Failed to load reports for AI assistant', err);
        if (mounted) setError(err.message || 'Failed to load reports');
      } finally {
        if (mounted) setLoadingRecords(false);
      }
    };
    load();
    return () => { mounted = false; };
  }, []);

  // compute overall health from records (simple heuristic)
  useEffect(() => {
    const computeOverallHealth = (recs) => {
      if (!recs || recs.length === 0) return { score: 100, level: 'Good', note: 'No records yet' };
      const total = recs.length;
      let concerning = 0;
      const symptomKeywords = ['fever','cough','chest','pain','shortness','breath','dizzy','nausea','vomit','diarrhea','severe','urgent'];
      for (const r of recs) {
        if (r.status && !(r.status === 'Normal' || r.status === 'Uploaded')) concerning += 1;
        const s = (r.symptoms || '').toLowerCase();
        for (const k of symptomKeywords) {
          if (s.includes(k)) { concerning += 1; break; }
        }
      }
      const maxConcerning = Math.max(1, total * 2);
      const ratio = Math.min(concerning / maxConcerning, 1);
      const score = Math.max(20, Math.round(100 - ratio * 80));
      let level = 'Good';
      let note = 'Keep up the healthy habits.';
      if (score >= 80) { level = 'Good'; note = 'Overall health looks good.'; }
      else if (score >= 60) { level = 'Fair'; note = 'Some reports indicate minor issues — monitor symptoms and consult a doctor if needed.'; }
      else { level = 'Poor'; note = 'Multiple concerning findings — consider scheduling a doctor visit soon.'; }
      return { score, level, note };
    };
    const h = computeOverallHealth(records);
    setOverallHealth(h);
  }, [records]);

  const selectedRecord = records.find(r => String(r.id) === String(selectedRecordId));

  // Simple summarizer: produce a short summary from record metadata and/or symptoms
  const runSummarize = () => {
    setSummary('');
    setError('');
    setRunning(true);
    try {
      const source = selectedRecord ? `${selectedRecord.title} (${selectedRecord.type})` : (symptomsInput || 'No data');
      const sym = selectedRecord?.symptoms || symptomsInput;
      let s = `Summary: ${source}.`;
      if (sym) {
        const short = sym.length > 160 ? sym.slice(0,157) + '...' : sym;
        s += ` Key symptoms: ${short}`;
      } else {
        s += ` No symptom details provided.`;
      }
      setSummary(s);
    } catch (err) {
      setError('Failed to generate summary');
    } finally {
      setRunning(false);
    }
  };

  // Symptom analysis: send textarea value to server /api/analyze, fall back to local heuristic
  const runAnalysis = () => {
    setAnalysis(null);
    setError('');
    setRunning(true);

    (async () => {
      try {
        const textValue = (symptomsInput || '').trim();
        if (!textValue) {
          setError('Please enter symptoms in the textarea before analyzing');
          setRunning(false);
          return;
        }

        const payload = { symptoms: textValue };
        console.log('Sending /api/analyze payload ->', payload);

        try {
          const token = localStorage.getItem('token');
          const resp = await fetch('http://localhost:5000/api/ai/analyze', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              ...(token ? { Authorization: `Bearer ${token}` } : {})
            },
            body: JSON.stringify(payload)
          });

          const body = await resp.json().catch(() => ({}));
          console.log('Server /api/analyze response ->', resp.status, body);

          if (resp.ok && body) {
            // Expect shape: { message, categories, advice }
            if (body.categories || body.advice || body.message) {
              setAnalysis({ message: body.message || 'Analysis (server)', categories: body.categories || [], advice: body.advice || [] });
              setRunning(false);
              return;
            }
          } else {
            // Non-OK response: show message and fall back
            const msg = (body && body.message) ? body.message : `Server returned ${resp.status}`;
            console.warn('/api/analyze returned error:', msg);
            setError(msg);
          }
        } catch (netErr) {
          console.warn('Network/server error calling /api/analyze, falling back to local heuristic', netErr);
        }

        // Local heuristic fallback (same as previous logic)
        const text = textValue.toLowerCase();
        const categories = [];
        const kws = {
          respiratory: ['cough','sneez','shortness','breath','wheez','phlegm','sore throat'],
          cardiac: ['chest pain','palpit','heart','breathless','arrhythmia'],
          neuro: ['headache','dizzy','seizure','numb','weakness','confusion'],
          gastro: ['nausea','vomit','diarrhea','abdominal','stomach','pain'],
          fever: ['fever','temperature','chill']
        };
        for (const [cat, arr] of Object.entries(kws)) {
          for (const k of arr) {
            if (text.includes(k)) { categories.push(cat); break; }
          }
        }
        const advice = [];
        if (categories.includes('respiratory') || categories.includes('fever')) advice.push('Consider rest, fluids; seek medical review if breathing difficulty or high fever');
        if (categories.includes('cardiac')) advice.push('Seek urgent medical attention for chest pain or palpitations');
        if (categories.length === 0) advice.push('Symptoms are non-specific; monitor and seek advice if they worsen');

        setAnalysis({ message: 'Symptom analysis complete (client-side)', categories, advice });
      } catch (err) {
        console.error('Analysis error:', err);
        setError('Failed to analyze symptoms');
      } finally {
        setRunning(false);
      }
    })();
  };

  // Disease prediction: basic rule-based scoring
  const runPrediction = () => {
    setPrediction(null);
    setError('');
    setRunning(true);
    try {
      const text = (selectedRecord?.symptoms || symptomsInput || '').toLowerCase();
      if (!text) {
        setPrediction({ message: 'No symptoms provided', candidates: [] });
        setRunning(false);
        return;
      }
      const diseaseMap = {
        'Common Cold': ['cough','sneeze','sore throat','runny nose'],
        'Flu (Influenza)': ['fever','chill','body ache','fatigue','cough'],
        'COVID-19': ['loss of taste','loss of smell','fever','cough','shortness of breath'],
        'Gastroenteritis': ['nausea','vomit','diarrhea','stomach','abdominal'],
        'Migraine': ['headache','nausea','sensitivity to light','aura']
      };
      const scores = {};
      for (const [d, kws] of Object.entries(diseaseMap)) {
        let score = 0;
        for (const k of kws) if (text.includes(k)) score += 1;
        if (score > 0) scores[d] = score;
      }
      const total = Object.values(scores).reduce((a,b) => a+b, 0) || 1;
      const candidates = Object.entries(scores).sort((a,b)=>b[1]-a[1]).map(([d,s])=>({ disease: d, probability: Math.round((s/total)*100) }));
      setPrediction({ message: 'Prediction (heuristic)', candidates });
    } catch (err) {
      setError('Failed to predict diseases');
    } finally {
      setRunning(false);
    }
  };

  return (
    <div>
      {/* Use the site's Navbar and Slidebar for consistent layout */}
      <div>
        <Navbar companyName="MedChain - AI Assistant" />
        <div className="flex">
          <Slidebar role="patient" />

          <main className="flex-1 p-6 relative">
            <div className="bg-white/80 backdrop-blur-sm rounded-xl p-6 mb-6 border border-white/20 shadow-lg">
              <h2 className="text-2xl font-bold mb-2">AI Health Assistant</h2>
              <p className="text-gray-600 mb-4">Use simple AI tools to summarize reports, analyze symptoms, and get preliminary disease predictions. These are heuristics and not medical advice.</p>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-2">Select a report (optional)</label>
                  <select
                    value={selectedRecordId || ''}
                    onChange={e => {
                      const val = e.target.value;
                      setSelectedRecordId(val);
                      const rec = records.find(r => String(r.id) === String(val));
                      if (rec && rec.symptoms) setSymptomsInput(rec.symptoms);
                    }}
                    className="w-full px-3 py-2 border rounded-md mb-3"
                  >
                    <option value="">-- Use manual symptoms / choose a report --</option>
                    {records.map(r => (
                      <option key={r.id} value={r.id}>{r.title} • {r.date} • {r.type}</option>
                    ))}
                  </select>

                  <label className="block text-sm font-medium text-gray-700 mb-2">Or paste symptoms/notes</label>
                  <textarea value={symptomsInput} onChange={e => setSymptomsInput(e.target.value)} placeholder="e.g. Fever, cough and sore throat for 3 days" rows={6} className="w-full px-3 py-2 border rounded-md" />

                  <div className="flex gap-3 mt-4">
                    <button onClick={runSummarize} disabled={running} className="px-4 py-2 bg-blue-600 text-white rounded-md">Generate Summary</button>
                    <button onClick={runAnalysis} disabled={running} className="px-4 py-2 bg-green-600 text-white rounded-md">Analyze Symptoms</button>
                    <button onClick={runPrediction} disabled={running} className="px-4 py-2 bg-purple-600 text-white rounded-md">Predict Diseases</button>
                  </div>
                </div>

                <div className="bg-gray-50 p-4 rounded-md">
                  <h4 className="font-semibold mb-2">Quick info</h4>
                  {loadingRecords ? <p className="text-sm text-gray-500">Loading reports…</p> : (
                    <p className="text-sm text-gray-600">You have {records.length} reports. Selecting a report will prefill the symptoms if available.</p>
                  )}
                  {error && <p className="text-sm text-red-600 mt-2">{error}</p>}

                  {/* Overall Health Panel */}
                  <div className="mt-4 bg-white p-3 rounded-md border">
                    <h5 className="text-sm font-semibold">Overall Health</h5>
                    <div className="flex items-center justify-between mt-2">
                      <div>
                        <div className="text-xs text-gray-500">Score</div>
                        <div className="text-lg font-bold">{overallHealth.score}</div>
                        <div className="text-sm text-gray-600">{overallHealth.level}</div>
                      </div>
                      <div className="w-2/5">
                        <div className="h-3 bg-gray-200 rounded-full overflow-hidden">
                          <div style={{ width: `${overallHealth.score}%` }} className={`h-3 rounded-full ${overallHealth.score >= 80 ? 'bg-green-500' : overallHealth.score >= 60 ? 'bg-yellow-400' : 'bg-red-500'}`}></div>
                        </div>
                        <div className="text-xs text-gray-500 mt-1 text-right">Higher is better</div>
                      </div>
                    </div>
                    <p className="text-xs text-gray-500 mt-3">{overallHealth.note}</p>
                  </div>
                </div>
              </div>

            </div>

            {/* Results */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-white p-4 rounded-md border">
                <h4 className="font-semibold mb-2">Summary</h4>
                <p className="text-sm text-gray-700">{summary || 'No summary generated yet'}</p>
              </div>

              <div className="bg-white p-4 rounded-md border">
                <h4 className="font-semibold mb-2">Symptom Analysis</h4>
                {analysis ? (
                  <div>
                    <p className="text-sm text-gray-700 mb-2">{analysis.message}</p>
                    <p className="text-sm"><strong>Categories:</strong> {analysis.categories.length ? analysis.categories.join(', ') : 'None detected'}</p>
                    <ul className="mt-2 text-sm list-disc list-inside text-gray-600">
                      {analysis.advice && analysis.advice.map((a,i)=> <li key={i}>{a}</li>)}
                    </ul>
                  </div>
                ) : (
                  <p className="text-sm text-gray-500">No analysis yet</p>
                )}
              </div>

              <div className="bg-white p-4 rounded-md border">
                <h4 className="font-semibold mb-2">Disease Prediction</h4>
                {prediction ? (
                  <div>
                    {prediction.candidates && prediction.candidates.length ? (
                      <ul className="list-disc list-inside text-sm text-gray-700">
                        {prediction.candidates.map((c,i) => (
                          <li key={i}>{c.disease} — approx. {c.probability}%</li>
                        ))}
                      </ul>
                    ) : (
                      <p className="text-sm text-gray-500">No likely conditions detected</p>
                    )}
                  </div>
                ) : (
                  <p className="text-sm text-gray-500">No prediction yet</p>
                )}
              </div>
            </div>
          </main>
        </div>
      </div>
    </div>
  );
};

export default AIAssistant;

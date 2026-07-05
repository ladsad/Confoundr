'use client'

import { useState, useEffect } from 'react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function Dashboard() {
  const [file, setFile] = useState<File | null>(null)
  const [targetCol, setTargetCol] = useState('')
  const [treatmentCol, setTreatmentCol] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [history, setHistory] = useState<any[]>([])

  const fetchHistory = async () => {
    try {
      const res = await fetch(`${API_URL}/api/v1/history`)
      if (res.ok) {
        const data = await res.json()
        setHistory(data.history)
      }
    } catch (e) {
      console.error("Failed to fetch history", e)
    }
  }

  useEffect(() => {
    fetchHistory()
    const interval = setInterval(fetchHistory, 5000) // Poll every 5s for updates
    return () => clearInterval(interval)
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!file || !targetCol) return

    setLoading(true)
    setError('')

    const formData = new FormData()
    formData.append('file', file)
    formData.append('target_col', targetCol)
    if (treatmentCol) formData.append('treatment_col', treatmentCol)

    try {
      const res = await fetch(`${API_URL}/api/v1/async-check`, {
        method: 'POST',
        body: formData,
      })
      const data = await res.json()
      
      if (!res.ok) {
        throw new Error(data.detail || 'Failed to submit job')
      }
      
      // Reset form on success
      setFile(null)
      setTargetCol('')
      setTreatmentCol('')
      
      // Refresh history immediately
      fetchHistory()
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="container animate-in">
      <div style={{ marginBottom: '40px' }}>
        <h1 style={{ fontSize: '3rem', marginBottom: '8px' }}>
          Welcome to <span className="gradient-text">Confoundr</span>
        </h1>
        <p style={{ color: 'var(--text-muted)', fontSize: '1.1rem' }}>
          Upload a dataset to run automated causal validity diagnostics and AI-powered insights.
        </p>
      </div>

      <div className="grid grid-cols-2 delay-1 animate-in">
        
        {/* Upload Form */}
        <div className="glass-panel" style={{ height: 'fit-content' }}>
          <h2 style={{ marginBottom: '24px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '1.2rem' }}>⚡</span> Start a New Job
          </h2>
          
          {error && (
            <div style={{ background: 'rgba(239, 68, 68, 0.1)', border: '1px solid var(--danger)', padding: '12px', borderRadius: '8px', color: '#fca5a5', marginBottom: '20px' }}>
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit}>
            <div className="input-group">
              <label className="input-label">Dataset (CSV, Parquet, JSON)</label>
              <input 
                type="file" 
                className="input-field" 
                accept=".csv,.parquet,.json"
                onChange={(e) => setFile(e.target.files?.[0] || null)}
                required
              />
            </div>

            <div className="input-group">
              <label className="input-label">Target Column Name</label>
              <input 
                type="text" 
                className="input-field" 
                placeholder="e.g., converted"
                value={targetCol}
                onChange={(e) => setTargetCol(e.target.value)}
                required
              />
            </div>

            <div className="input-group">
              <label className="input-label">Treatment Column Name (Optional)</label>
              <input 
                type="text" 
                className="input-field" 
                placeholder="e.g., received_email"
                value={treatmentCol}
                onChange={(e) => setTreatmentCol(e.target.value)}
              />
            </div>

            <button type="submit" className="btn btn-primary" style={{ width: '100%', marginTop: '16px' }} disabled={loading || !file || !targetCol}>
              {loading ? 'Submitting...' : 'Run Diagnostics'}
            </button>
          </form>
        </div>

        {/* History List */}
        <div className="glass-panel">
          <h2 style={{ marginBottom: '24px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '1.2rem' }}>🕒</span> Recent Runs
          </h2>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {history.length === 0 ? (
              <p style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '40px 0' }}>No history found.</p>
            ) : history.map((job) => (
              <a href={`/job/${job.job_id}`} key={job.job_id} className="glass-panel interactive" style={{ padding: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <div style={{ fontWeight: 600, marginBottom: '4px' }}>{job.filename}</div>
                  <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Target: {job.target_col}</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '8px', opacity: 0.6 }}>{new Date(job.created_at).toLocaleString()}</div>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '8px' }}>
                  <span className={`badge ${job.status === 'finished' ? 'badge-pass' : job.status === 'failed' ? 'badge-fail' : 'badge-info'}`}>
                    {job.status}
                  </span>
                  {job.execution_time_seconds && (
                    <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{job.execution_time_seconds.toFixed(2)}s</span>
                  )}
                </div>
              </a>
            ))}
          </div>
        </div>

      </div>
    </div>
  )
}

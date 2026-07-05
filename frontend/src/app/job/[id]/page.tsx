'use client'

import { useState, useEffect } from 'react'
import { useParams } from 'next/navigation'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function JobDetails() {
  const { id } = useParams()
  const [job, setJob] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const fetchJob = async () => {
    try {
      const res = await fetch(`${API_URL}/api/v1/job/${id}`)
      const data = await res.json()
      
      if (!res.ok) throw new Error(data.detail || 'Failed to fetch job')
      
      setJob(data)
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchJob()
    const interval = setInterval(() => {
      if (job && (job.status === 'queued' || job.status === 'started')) {
        fetchJob()
      }
    }, 3000)
    return () => clearInterval(interval)
  }, [id, job?.status])

  if (loading && !job) {
    return <div className="container" style={{ textAlign: 'center', marginTop: '100px', color: 'var(--text-muted)' }}>Loading job details...</div>
  }

  if (error) {
    return <div className="container" style={{ textAlign: 'center', marginTop: '100px', color: 'var(--danger)' }}>Error: {error}</div>
  }

  const getBadgeClass = (status: string) => {
    switch(status.toLowerCase()) {
      case 'pass': return 'badge-pass'
      case 'fail': return 'badge-fail'
      case 'warn': return 'badge-warn'
      default: return 'badge-info'
    }
  }

  return (
    <div className="container animate-in">
      
      <div style={{ marginBottom: '32px', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <a href="/" style={{ color: 'var(--primary)', fontSize: '0.9rem', display: 'flex', alignItems: 'center', gap: '4px', marginBottom: '16px' }}>
            &larr; Back to Dashboard
          </a>
          <h1 style={{ fontSize: '2.5rem', marginBottom: '8px' }}>Job Report</h1>
          <p style={{ color: 'var(--text-muted)', fontFamily: 'monospace' }}>ID: {job.job_id}</p>
        </div>
        <div style={{ textAlign: 'right' }}>
          <div style={{ marginBottom: '8px' }}>
            Status: <span className={`badge ${job.status === 'finished' ? 'badge-pass' : job.status === 'failed' ? 'badge-fail' : 'badge-warn'}`}>{job.status}</span>
          </div>
          <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            Started: {job.started_at ? new Date(job.started_at).toLocaleString() : 'N/A'}<br/>
            Ended: {job.ended_at ? new Date(job.ended_at).toLocaleString() : 'N/A'}
          </div>
        </div>
      </div>

      {job.status === 'queued' || job.status === 'started' ? (
        <div className="glass-panel" style={{ textAlign: 'center', padding: '60px' }}>
          <div style={{ display: 'inline-block', width: '40px', height: '40px', borderRadius: '50%', border: '3px solid var(--border-color)', borderTopColor: 'var(--primary)', animation: 'spin 1s linear infinite', marginBottom: '24px' }} />
          <h3>Processing your dataset...</h3>
          <p style={{ color: 'var(--text-muted)', marginTop: '8px' }}>This may take a few moments depending on dataset size.</p>
          <style>{`@keyframes spin { 100% { transform: rotate(360deg); } }`}</style>
        </div>
      ) : job.error ? (
        <div className="glass-panel" style={{ borderColor: 'rgba(239, 68, 68, 0.3)' }}>
          <h2 style={{ color: 'var(--danger)', marginBottom: '16px' }}>Critical Execution Error</h2>
          <pre style={{ background: 'rgba(0,0,0,0.3)', padding: '16px', borderRadius: '8px', overflowX: 'auto', fontSize: '0.85rem' }}>{job.error}</pre>
        </div>
      ) : (
        <div className="grid">
          {job.results && job.results.map((res: any, idx: number) => (
            <div key={idx} className={`glass-panel delay-${idx+1} animate-in`} style={{ display: 'grid', gridTemplateColumns: res.ai_insight ? '1fr 1fr' : '1fr', gap: '24px' }}>
              
              {/* Technical Results Side */}
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                  <h2 style={{ fontSize: '1.25rem' }}>{res.check_name}</h2>
                  <span className={`badge ${getBadgeClass(res.status)}`}>{res.status}</span>
                </div>
                
                <p style={{ marginBottom: '16px', lineHeight: 1.6 }}>{res.explanation}</p>
                
                <div style={{ background: 'rgba(0,0,0,0.2)', padding: '16px', borderRadius: '8px' }}>
                  <div style={{ fontSize: '0.8rem', textTransform: 'uppercase', color: 'var(--text-muted)', letterSpacing: '0.05em', marginBottom: '12px' }}>Statistical Evidence</div>
                  <pre style={{ margin: 0, fontSize: '0.85rem', color: '#a5b4fc', overflowX: 'auto' }}>
                    {JSON.stringify(res.evidence, null, 2)}
                  </pre>
                </div>
              </div>

              {/* AI Insight Side */}
              {res.ai_insight && (
                <div style={{ background: 'linear-gradient(180deg, rgba(99, 102, 241, 0.1), rgba(139, 92, 246, 0.05))', borderRadius: '12px', padding: '24px', border: '1px solid rgba(139, 92, 246, 0.2)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
                    <span style={{ fontSize: '1.5rem' }}>✨</span>
                    <h3 style={{ margin: 0, color: '#e0e7ff' }}>AI Explainer</h3>
                  </div>
                  <div style={{ whiteSpace: 'pre-wrap', fontSize: '0.95rem', lineHeight: 1.6, color: '#f8fafc' }}>
                    {res.ai_insight}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

    </div>
  )
}

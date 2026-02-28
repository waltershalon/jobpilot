import React, { useState, useEffect, useCallback } from 'react'
import './App.css'

const API = '/api'

const STATUS_COLORS = {
  discovered: '#94a3b8',
  resume_ready: '#60a5fa',
  applied: '#fbbf24',
  response: '#34d399',
  interview: '#a78bfa',
  offer: '#2dd4bf',
  rejected: '#f87171',
  withdrawn: '#64748b',
  low_match: '#64748b',
}

// ── Dashboard Components ────────────────────────────────────────

function StatsCards({ stats }) {
  const cards = [
    { value: stats.total || 0, label: 'Total Applications', color: '#60a5fa', gradient: 'linear-gradient(135deg, #3b82f6, #60a5fa)' },
    { value: stats.by_status?.resume_ready || 0, label: 'Resumes Ready', color: '#34d399', gradient: 'linear-gradient(135deg, #10b981, #34d399)' },
    { value: stats.by_status?.applied || 0, label: 'Applied', color: '#fbbf24', gradient: 'linear-gradient(135deg, #f59e0b, #fbbf24)' },
    { value: stats.by_status?.interview || 0, label: 'Interviews', color: '#a78bfa', gradient: 'linear-gradient(135deg, #8b5cf6, #a78bfa)' },
    { value: stats.avg_ats_score ? `${Math.round(stats.avg_ats_score * 100)}%` : '-', label: 'Avg ATS Score', color: '#2dd4bf', gradient: 'linear-gradient(135deg, #14b8a6, #2dd4bf)' },
  ]

  return (
    <div className="stats-grid">
      {cards.map((card, i) => (
        <div key={i} className={`glass stat-card fade-slide-up stagger-${i + 1}`}
             style={{ '--stat-color': card.color }}>
          <div style={{
            position: 'absolute', top: -20, right: -20,
            width: 80, height: 80, borderRadius: '50%',
            background: card.gradient, opacity: 0.1,
          }} />
          <div className="stat-value" style={{ color: card.color }}>{card.value}</div>
          <div className="stat-label">{card.label}</div>
        </div>
      ))}
    </div>
  )
}

function ApplicationDetailModal({ app, onClose, onStatusChange }) {
  if (!app) return null
  const scoreColor = app.ats_score >= 0.7 ? '#34d399' : app.ats_score >= 0.5 ? '#fbbf24' : '#f87171'
  const matched = app.keywords_matched || []
  const missing = app.keywords_missing || []

  useEffect(() => {
    const handler = (e) => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [onClose])

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="glass-strong modal-content" onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 24 }}>
          <div>
            <h2 style={{ fontFamily: 'var(--font-heading)', fontSize: 22, fontWeight: 700, margin: 0 }}>
              {app.title}
            </h2>
            <div style={{ color: 'var(--text-secondary)', marginTop: 6, fontSize: 14 }}>
              {app.company} {app.location ? `· ${app.location}` : ''} · {app.created_at?.slice(0, 10)}
            </div>
            {app.url && (
              <a href={app.url} target="_blank" rel="noopener"
                 style={{ color: 'var(--accent-violet)', fontSize: 13, textDecoration: 'none', display: 'inline-block', marginTop: 6 }}>
                View job posting ↗
              </a>
            )}
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            {app.ats_score > 0 && (
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontFamily: 'var(--font-heading)', fontSize: 34, fontWeight: 700, color: scoreColor }}>
                  {Math.round(app.ats_score * 100)}%
                </div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>ATS Score</div>
              </div>
            )}
            <button className="close-btn" onClick={onClose}>✕</button>
          </div>
        </div>

        {/* Status */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 20 }}>
          <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>Status:</span>
          <select
            className="input"
            value={app.status}
            onChange={e => onStatusChange(app.id, e.target.value)}
            style={{ width: 'auto', padding: '6px 32px 6px 12px', fontSize: 13 }}
          >
            {Object.keys(STATUS_COLORS).map(s => (
              <option key={s} value={s}>{s.replace(/_/g, ' ')}</option>
            ))}
          </select>
        </div>

        {/* Keywords */}
        {(matched.length > 0 || missing.length > 0) && (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 20 }}>
            <div>
              <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--accent-green)', marginBottom: 8 }}>
                Keywords Matched ({matched.length})
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                {matched.map((kw, i) => <span key={i} className="tag tag-matched">{kw}</span>)}
              </div>
            </div>
            <div>
              <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--accent-red)', marginBottom: 8 }}>
                Keywords Missing ({missing.length})
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                {missing.map((kw, i) => <span key={i} className="tag tag-missing">{kw}</span>)}
              </div>
            </div>
          </div>
        )}

        {/* Download Buttons */}
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
          {app.resume_path && (
            <a href={`/api/files/${encodeURIComponent(app.resume_path.split('/').pop())}`} style={{ textDecoration: 'none' }}>
              <button className="btn btn-primary">Download PDF</button>
            </a>
          )}
          {app.cover_letter_path && (
            <a href={`/api/files/${encodeURIComponent(app.cover_letter_path.split('/').pop())}`} style={{ textDecoration: 'none' }}>
              <button className="btn btn-secondary">Cover Letter</button>
            </a>
          )}
        </div>
      </div>
    </div>
  )
}

function ApplicationsTable({ applications, onStatusChange, onSelectApp }) {
  if (!applications?.length) {
    return (
      <div className="glass empty-state fade-slide-up">
        <div className="empty-state-icon">✦</div>
        <p>No applications yet. Tailor your first resume to get started.</p>
      </div>
    )
  }

  return (
    <div className="glass table-container fade-slide-up" style={{ padding: 0 }}>
      <table>
        <thead>
          <tr>
            <th>Role</th>
            <th>Company</th>
            <th>Status</th>
            <th>ATS Score</th>
            <th>Date</th>
          </tr>
        </thead>
        <tbody>
          {applications.map(app => {
            const scoreColor = app.ats_score >= 0.7 ? '#34d399' : app.ats_score >= 0.5 ? '#fbbf24' : '#f87171'
            return (
              <tr key={app.id} onClick={() => onSelectApp(app)}>
                <td><span style={{ fontWeight: 600 }}>{app.title}</span></td>
                <td>{app.company}</td>
                <td>
                  <span className="badge" style={{
                    background: (STATUS_COLORS[app.status] || '#94a3b8') + '18',
                    color: STATUS_COLORS[app.status] || '#94a3b8',
                    borderColor: (STATUS_COLORS[app.status] || '#94a3b8') + '30',
                  }}>
                    {app.status?.replace(/_/g, ' ')}
                  </span>
                </td>
                <td>
                  {app.ats_score > 0 ? (
                    <div>
                      <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 4, color: scoreColor }}>
                        {Math.round(app.ats_score * 100)}%
                      </div>
                      <div className="progress-track">
                        <div className="progress-fill" style={{
                          width: `${app.ats_score * 100}%`,
                          background: scoreColor,
                        }} />
                      </div>
                    </div>
                  ) : <span style={{ color: 'var(--text-muted)' }}>-</span>}
                </td>
                <td style={{ color: 'var(--text-muted)', fontSize: 13 }}>
                  {app.created_at?.slice(0, 10)}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

// ── Profile Upload ──────────────────────────────────────────────

function ProfileUpload({ onProfileSet, currentProfile }) {
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState(null)

  const handleUpload = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    setUploading(true)
    setError(null)
    try {
      const formData = new FormData()
      formData.append('file', file)
      const res = await fetch(`${API}/profile/upload`, { method: 'POST', body: formData })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || 'Upload failed')
      }
      const data = await res.json()
      onProfileSet({
        user_id: data.user_id,
        name: data.name,
        email: data.email,
        stats: { education: data.education_count, work: data.work_experience_count, research: data.research_experience_count, projects: data.projects_count }
      })
    } catch (e) {
      setError(e.message)
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="glass fade-slide-up" style={{ padding: 24, marginBottom: 20 }}>
      <h3 className="card-title">Your Profile</h3>
      {currentProfile ? (
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <div style={{ fontWeight: 600, fontSize: 16 }}>{currentProfile.name}</div>
            <div style={{ color: 'var(--text-secondary)', fontSize: 13, marginTop: 4 }}>
              {currentProfile.email}
              <span style={{ marginLeft: 12, color: 'var(--text-muted)' }}>
                {currentProfile.stats.work} work · {currentProfile.stats.research} research · {currentProfile.stats.projects} projects · {currentProfile.stats.education} education
              </span>
            </div>
          </div>
          <label className="btn btn-secondary" style={{ cursor: 'pointer' }}>
            {uploading ? 'Uploading...' : 'Switch Profile'}
            <input type="file" accept=".pdf" onChange={handleUpload} style={{ display: 'none' }} />
          </label>
        </div>
      ) : (
        <div className="profile-upload-area">
          <div style={{ fontSize: 40, marginBottom: 12, opacity: 0.4 }}>◎</div>
          <p>Upload your resume PDF to get started. AI will parse it into a profile for tailoring.</p>
          <label className="btn btn-primary btn-lg" style={{ cursor: 'pointer' }}>
            {uploading ? 'Parsing resume...' : 'Upload Resume PDF'}
            <input type="file" accept=".pdf" onChange={handleUpload} style={{ display: 'none' }} />
          </label>
          <div style={{ marginTop: 14 }}>
            <button
              className="btn btn-secondary btn-sm"
              onClick={() => onProfileSet({ user_id: null, name: 'Default Profile', email: '', stats: { education: 0, work: 0, research: 0, projects: 0 } })}
            >
              Use default profile instead
            </button>
          </div>
        </div>
      )}
      {error && <div className="error-box">{error}</div>}
    </div>
  )
}

// ── Interactive Resume Editor ───────────────────────────────────

function BulletSuggestionRow({ bullet, index, decision, onDecision }) {
  const [editing, setEditing] = useState(false)
  const [editText, setEditText] = useState(bullet.suggested || bullet.original || '')
  const action = decision?.action || 'accept'

  const handleEdit = () => {
    setEditing(true)
    setEditText(decision?.text || bullet.suggested || bullet.original || '')
  }

  const saveEdit = () => {
    onDecision({ action: 'edit', text: editText })
    setEditing(false)
  }

  const charCount = action === 'edit' ? editText.length : (action === 'reject' ? (bullet.original||'').length : (bullet.suggested||bullet.original||'').length)

  return (
    <div className="bullet-row">
      {/* Original */}
      <div style={{ display: 'flex', gap: 8, alignItems: 'flex-start', marginBottom: 6 }}>
        <span className="bullet-label" style={{ color: 'var(--text-muted)' }}>Original</span>
        <div className="bullet-text" style={{ color: 'var(--text-secondary)' }}>
          {bullet.original}
        </div>
      </div>

      {/* Suggestion */}
      {bullet.action !== 'keep' && bullet.suggested && bullet.suggested !== bullet.original && (
        <div style={{ display: 'flex', gap: 8, alignItems: 'flex-start', marginBottom: 6 }}>
          <span className="bullet-label" style={{ color: 'var(--accent-green)' }}>AI</span>
          <div className="bullet-text bullet-ai-box">
            {bullet.suggested}
          </div>
        </div>
      )}

      {/* Reason */}
      {bullet.reason && (
        <div style={{ fontSize: 11, color: 'var(--text-muted)', marginLeft: 60, marginBottom: 6, fontStyle: 'italic' }}>
          {bullet.reason}
          {bullet.keywords_added?.length > 0 && (
            <span> — Keywords: {bullet.keywords_added.map((kw, i) => (
              <span key={i} className="tag tag-matched" style={{ fontSize: 10, padding: '1px 6px' }}>{kw}</span>
            ))}</span>
          )}
        </div>
      )}

      {/* Edit mode */}
      {editing && (
        <div style={{ marginLeft: 60, marginBottom: 6 }}>
          <textarea
            className="textarea"
            value={editText}
            onChange={e => setEditText(e.target.value)}
            style={{ minHeight: 60, fontSize: 13 }}
          />
          <div style={{ display: 'flex', gap: 8, marginTop: 6, alignItems: 'center' }}>
            <button className="btn btn-primary btn-sm" onClick={saveEdit}>Save</button>
            <button className="btn btn-secondary btn-sm" onClick={() => setEditing(false)}>Cancel</button>
            <span style={{ fontSize: 11, color: editText.length > 120 ? 'var(--accent-red)' : 'var(--text-muted)' }}>
              {editText.length}/120 chars
            </span>
          </div>
        </div>
      )}

      {/* Action buttons */}
      <div style={{ display: 'flex', gap: 6, marginLeft: 60, alignItems: 'center' }}>
        {bullet.action !== 'keep' && bullet.suggested && (
          <button
            className={`action-btn accept ${action === 'accept' ? 'active' : ''}`}
            onClick={() => onDecision({ action: 'accept' })}
          >Accept</button>
        )}
        <button
          className={`action-btn reject ${action === 'reject' ? 'active' : ''}`}
          onClick={() => onDecision({ action: 'reject' })}
        >Keep Original</button>
        <button
          className={`action-btn edit ${action === 'edit' ? 'active' : ''}`}
          onClick={handleEdit}
        >Edit</button>
        <span style={{ fontSize: 11, color: charCount > 120 ? 'var(--accent-red)' : 'var(--text-muted)', marginLeft: 8 }}>
          {charCount} chars
        </span>
      </div>
    </div>
  )
}

function ExperienceCard({ exp, selected, onToggle, bulletDecisions, onBulletDecision }) {
  const [expanded, setExpanded] = useState(selected)
  const scoreColor = exp.relevance_score >= 7 ? '#34d399' : exp.relevance_score >= 4 ? '#fbbf24' : '#f87171'

  return (
    <div className={`glass exp-card ${selected ? 'selected' : 'excluded'}`}
         style={{ borderLeftColor: selected ? scoreColor : undefined }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, flex: 1, cursor: 'pointer' }}
             onClick={() => setExpanded(!expanded)}>
          <div>
            <div style={{ fontWeight: 600, fontSize: 15 }}>{exp.title}</div>
            <div style={{ color: 'var(--text-secondary)', fontSize: 13 }}>
              {exp.company} · {exp.start_date} — {exp.end_date}
            </div>
          </div>
          <span className="badge" style={{
            background: scoreColor + '18',
            color: scoreColor,
            borderColor: scoreColor + '30',
          }}>{exp.relevance_score}/10</span>
          <span style={{ fontSize: 12, color: 'var(--text-muted)', fontStyle: 'italic' }}>{exp.relevance_reason}</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
            {expanded ? '▾' : '▸'} {exp.bullets?.length || 0} bullets
          </span>
          <button
            className={`btn btn-sm ${selected ? 'btn-teal' : 'btn-secondary'}`}
            onClick={() => onToggle(!selected)}
            style={{ minWidth: 80 }}
          >
            {selected ? '✓ Included' : 'Excluded'}
          </button>
        </div>
      </div>

      {/* Bullets */}
      {expanded && selected && (
        <div style={{ marginTop: 14 }}>
          {(exp.bullets || []).map((bullet, i) => (
            <BulletSuggestionRow
              key={i}
              bullet={bullet}
              index={i}
              decision={bulletDecisions?.[String(i)]}
              onDecision={(dec) => onBulletDecision(String(i), dec)}
            />
          ))}
        </div>
      )}
    </div>
  )
}

function MissingKeywordsBar({ keywords, suggestions }) {
  if (!keywords?.length && !suggestions?.length) return null
  const allMissing = new Set([
    ...(keywords || []),
    ...(suggestions || []).map(s => s.keyword)
  ])

  return (
    <div className="missing-kw-bar fade-slide-up">
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 10 }}>
        <span style={{ fontSize: 14, fontWeight: 600, color: 'var(--accent-red)' }}>
          {allMissing.size} Missing Keywords
        </span>
        <span className="section-subtitle">
          AI has suggestions for where to add some of these
        </span>
      </div>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginBottom: suggestions?.length ? 12 : 0 }}>
        {[...allMissing].map((kw, i) => <span key={i} className="tag tag-missing">{kw}</span>)}
      </div>
      {suggestions?.length > 0 && (
        <div style={{ marginTop: 8 }}>
          {suggestions.slice(0, 5).map((s, i) => (
            <div key={i} style={{ fontSize: 12, padding: '5px 0', borderTop: i > 0 ? '1px solid rgba(255,255,255,0.04)' : 'none' }}>
              <span className="tag tag-missing">{s.keyword}</span>
              <span style={{ color: 'var(--text-secondary)', marginLeft: 8 }}>→ {s.suggestion}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function SuggestionsEditor({ suggestions, sessionId, userId, onFinalized }) {
  const [selectedExps, setSelectedExps] = useState(() => {
    const initial = {}
    ;(suggestions.experiences || []).forEach(exp => { initial[exp.id] = exp.selected })
    return initial
  })
  const [bulletDecisions, setBulletDecisions] = useState({})
  const [selectedProjects, setSelectedProjects] = useState(() => {
    const initial = {}
    ;(suggestions.projects || []).forEach(proj => { initial[proj.id] = proj.selected })
    return initial
  })
  const [projectBulletDecisions, setProjectBulletDecisions] = useState({})
  const [generating, setGenerating] = useState(false)
  const [error, setError] = useState(null)

  const selectedExpCount = Object.values(selectedExps).filter(Boolean).length
  const selectedProjCount = Object.values(selectedProjects).filter(Boolean).length
  const totalBullets = (suggestions.experiences || [])
    .filter(e => selectedExps[e.id])
    .reduce((sum, e) => sum + (e.bullets || []).length, 0)
  const estPages = selectedExpCount <= 4 && totalBullets <= 16 && selectedProjCount <= 2 ? 1 : 2

  const handleFinalize = async () => {
    setGenerating(true)
    setError(null)
    try {
      const res = await fetch(`${API}/tailor/finalize`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          user_edits: {
            selected_experiences: selectedExps,
            bullet_decisions: bulletDecisions,
            selected_projects: selectedProjects,
            project_bullet_decisions: projectBulletDecisions,
            skills: suggestions.skills,
          }
        }),
      })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || 'Finalization failed')
      }
      const data = await res.json()
      onFinalized(data)
    } catch (e) {
      setError(e.message)
    } finally {
      setGenerating(false)
    }
  }

  const acceptAll = () => {
    const bd = {}
    ;(suggestions.experiences || []).forEach(exp => {
      bd[exp.id] = {}
      ;(exp.bullets || []).forEach((b, i) => { bd[exp.id][String(i)] = { action: 'accept' } })
    })
    setBulletDecisions(bd)
  }

  const rejectAll = () => {
    const bd = {}
    ;(suggestions.experiences || []).forEach(exp => {
      bd[exp.id] = {}
      ;(exp.bullets || []).forEach((b, i) => { bd[exp.id][String(i)] = { action: 'reject' } })
    })
    setBulletDecisions(bd)
  }

  const missingKeywords = (suggestions.job?.keywords || []).filter(kw => {
    const allText = (suggestions.experiences || [])
      .flatMap(e => (e.bullets || []).map(b => (b.suggested || b.original || '').toLowerCase()))
      .join(' ')
    return !allText.includes(kw.toLowerCase())
  })

  return (
    <div>
      {/* Job Header */}
      <div className="glass fade-slide-up" style={{ padding: 24, marginBottom: 20 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <h3 style={{ fontFamily: 'var(--font-heading)', fontSize: 22, fontWeight: 700, marginBottom: 4 }}>
              {suggestions.job?.title}
            </h3>
            <div style={{ color: 'var(--text-secondary)' }}>
              {suggestions.job?.company} · {suggestions.job?.industry}
            </div>
          </div>
          <div className={`page-badge ${estPages === 1 ? 'ok' : 'warn'}`}>
            <div style={{
              fontFamily: 'var(--font-heading)', fontSize: 20, fontWeight: 700,
              color: estPages === 1 ? 'var(--accent-green)' : 'var(--accent-red)',
            }}>
              ~{estPages} page{estPages > 1 ? 's' : ''}
            </div>
            <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>
              {selectedExpCount} exp · {totalBullets} bullets · {selectedProjCount} proj
            </div>
          </div>
        </div>
      </div>

      <MissingKeywordsBar keywords={missingKeywords} suggestions={suggestions.keyword_suggestions} />

      {/* Action Bar */}
      <div className="fade-slide-up stagger-2" style={{ display: 'flex', gap: 8, marginBottom: 16, alignItems: 'center', flexWrap: 'wrap' }}>
        <button className="btn btn-primary" onClick={handleFinalize} disabled={generating}>
          {generating ? '⟳ Generating PDF...' : '✦ Generate Final PDF'}
        </button>
        <button className="btn btn-secondary" onClick={acceptAll}>Accept All AI</button>
        <button className="btn btn-secondary" onClick={rejectAll}>Keep All Originals</button>
        {estPages > 1 && (
          <span style={{ fontSize: 12, color: 'var(--accent-red)', marginLeft: 8 }}>
            Content may exceed 1 page — consider excluding some experiences
          </span>
        )}
      </div>

      {error && <div className="error-box">{error}</div>}

      {/* Work Experience */}
      {(suggestions.experiences || []).filter(e => e.source === 'work_experience').length > 0 && (
        <div className="fade-slide-up stagger-3">
          <h3 className="section-title">Work Experience</h3>
          {(suggestions.experiences || [])
            .filter(e => e.source === 'work_experience')
            .sort((a, b) => (b.relevance_score || 0) - (a.relevance_score || 0))
            .map(exp => (
              <ExperienceCard
                key={exp.id}
                exp={exp}
                selected={selectedExps[exp.id] || false}
                onToggle={(val) => setSelectedExps(prev => ({ ...prev, [exp.id]: val }))}
                bulletDecisions={bulletDecisions[exp.id]}
                onBulletDecision={(idx, dec) => setBulletDecisions(prev => ({
                  ...prev, [exp.id]: { ...(prev[exp.id] || {}), [idx]: dec }
                }))}
              />
            ))}
        </div>
      )}

      {/* Research Experience */}
      {(suggestions.experiences || []).filter(e => e.source === 'research_experience').length > 0 && (
        <div className="fade-slide-up stagger-4">
          <h3 className="section-title" style={{ marginTop: 28 }}>Research Experience</h3>
          {(suggestions.experiences || [])
            .filter(e => e.source === 'research_experience')
            .sort((a, b) => (b.relevance_score || 0) - (a.relevance_score || 0))
            .map(exp => (
              <ExperienceCard
                key={exp.id}
                exp={exp}
                selected={selectedExps[exp.id] || false}
                onToggle={(val) => setSelectedExps(prev => ({ ...prev, [exp.id]: val }))}
                bulletDecisions={bulletDecisions[exp.id]}
                onBulletDecision={(idx, dec) => setBulletDecisions(prev => ({
                  ...prev, [exp.id]: { ...(prev[exp.id] || {}), [idx]: dec }
                }))}
              />
            ))}
        </div>
      )}

      {/* Projects */}
      {(suggestions.projects || []).length > 0 && (
        <div className="fade-slide-up stagger-5">
          <h3 className="section-title" style={{ marginTop: 28 }}>Projects</h3>
          {(suggestions.projects || [])
            .sort((a, b) => (b.relevance_score || 0) - (a.relevance_score || 0))
            .map(proj => (
              <ExperienceCard
                key={proj.id}
                exp={{ ...proj, start_date: proj.date, end_date: '', company: proj.institution, source: 'project' }}
                selected={selectedProjects[proj.id] || false}
                onToggle={(val) => setSelectedProjects(prev => ({ ...prev, [proj.id]: val }))}
                bulletDecisions={projectBulletDecisions[proj.id]}
                onBulletDecision={(idx, dec) => setProjectBulletDecisions(prev => ({
                  ...prev, [proj.id]: { ...(prev[proj.id] || {}), [idx]: dec }
                }))}
              />
            ))}
        </div>
      )}

      {/* Skills Preview */}
      {suggestions.skills && (
        <div className="glass fade-slide-up" style={{ marginTop: 24, padding: 24 }}>
          <h3 className="card-title">Skills (reordered for this JD)</h3>
          {Object.entries(suggestions.skills).map(([category, items]) => (
            <div key={category} style={{ marginBottom: 8 }}>
              <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'capitalize' }}>
                {category.replace(/_/g, ' ')}:
              </span>
              <span style={{ fontSize: 13, color: 'var(--text-secondary)', marginLeft: 8 }}>
                {(items || []).join(', ')}
              </span>
            </div>
          ))}
        </div>
      )}

      {/* Bottom action */}
      <div style={{ display: 'flex', gap: 8, marginTop: 24 }}>
        <button className="btn btn-primary btn-lg" onClick={handleFinalize} disabled={generating}>
          {generating ? '⟳ Generating PDF...' : '✦ Generate Final PDF'}
        </button>
      </div>
    </div>
  )
}

// ── Tailor Panel (phased) ───────────────────────────────────────

function TailorPanel({ userId }) {
  const [mode, setMode] = useState('url')
  const [jdUrl, setJdUrl] = useState('')
  const [jdText, setJdText] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [phase, setPhase] = useState('input')
  const [suggestions, setSuggestions] = useState(null)
  const [sessionId, setSessionId] = useState(null)
  const [result, setResult] = useState(null)

  const handleGetSuggestions = async () => {
    setLoading(true)
    setError(null)
    try {
      const body = mode === 'url' ? { jd_url: jdUrl } : { jd_text: jdText }
      if (userId) body.user_id = userId
      const res = await fetch(`${API}/tailor/suggestions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || 'Failed to generate suggestions')
      }
      const data = await res.json()
      setSuggestions(data)
      setSessionId(data.session_id)
      setPhase('suggestions')
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  const handleFinalized = (data) => { setResult(data); setPhase('result') }
  const handleReset = () => { setPhase('input'); setSuggestions(null); setSessionId(null); setResult(null); setError(null) }

  if (phase === 'input') {
    return (
      <div className="glass fade-slide-up" style={{ padding: 28 }}>
        <h3 style={{ fontFamily: 'var(--font-heading)', fontSize: 22, fontWeight: 700, marginBottom: 6 }}>
          Tailor your resume
        </h3>
        <p style={{ color: 'var(--text-secondary)', fontSize: 14, marginBottom: 20, lineHeight: 1.5 }}>
          Paste a job posting URL or description and let AI optimize your resume for it.
        </p>

        <div style={{ display: 'flex', gap: 4, marginBottom: 16 }}>
          <button className={`nav-btn ${mode === 'url' ? 'active' : ''}`}
                  onClick={() => setMode('url')}>Paste URL</button>
          <button className={`nav-btn ${mode === 'text' ? 'active' : ''}`}
                  onClick={() => setMode('text')}>Paste JD Text</button>
        </div>

        {mode === 'url' ? (
          <input className="input" placeholder="https://boards.greenhouse.io/company/jobs/12345"
                 value={jdUrl} onChange={e => setJdUrl(e.target.value)}
                 onKeyDown={e => e.key === 'Enter' && handleGetSuggestions()} />
        ) : (
          <textarea className="textarea" placeholder="Paste the full job description here..."
                    value={jdText} onChange={e => setJdText(e.target.value)} />
        )}

        <div style={{ marginTop: 18, display: 'flex', alignItems: 'center', gap: 12 }}>
          <button className="btn btn-primary btn-lg" onClick={handleGetSuggestions} disabled={loading}>
            {loading ? '⟳ Analyzing JD...' : '✦ Get AI Suggestions'}
          </button>
          {loading && (
            <span style={{ color: 'var(--text-muted)', fontSize: 13 }}>
              Parsing JD and generating suggestions... ~30s
            </span>
          )}
        </div>
        {error && <div className="error-box">{error}</div>}
      </div>
    )
  }

  if (phase === 'suggestions' && suggestions) {
    return (
      <div>
        <div className="fade-slide-up" style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
          <button className="btn btn-secondary" onClick={handleReset}>← Back</button>
          <span className="section-subtitle">Review AI suggestions, then generate your PDF</span>
        </div>
        <SuggestionsEditor suggestions={suggestions} sessionId={sessionId} userId={userId} onFinalized={handleFinalized} />
      </div>
    )
  }

  if (phase === 'result' && result) {
    return (
      <div>
        <div className="fade-slide-up" style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
          <button className="btn btn-secondary" onClick={handleReset}>← New Tailoring</button>
          <button className="btn btn-secondary" onClick={() => setPhase('suggestions')}>← Back to Editor</button>
        </div>
        <TailorResult result={result} />
      </div>
    )
  }

  return null
}

function TailorResult({ result }) {
  const { job, ats, files, cover_letter, pages } = result
  const scoreColor = ats.overall_score >= 0.7 ? '#34d399' : ats.overall_score >= 0.5 ? '#fbbf24' : '#f87171'

  return (
    <div>
      {/* Job summary card */}
      <div className="glass fade-slide-up" style={{ padding: 28, marginBottom: 20 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div style={{ flex: 1 }}>
            <h3 style={{ fontFamily: 'var(--font-heading)', fontSize: 22, fontWeight: 700, marginBottom: 4 }}>{job.title}</h3>
            <div style={{ color: 'var(--text-secondary)' }}>
              {job.company} · {job.location} · {job.seniority} · {job.industry}
            </div>
            <p style={{ color: 'var(--text-secondary)', marginTop: 10, fontSize: 14, lineHeight: 1.6 }}>{job.summary}</p>
          </div>
          <div style={{ textAlign: 'center', minWidth: 120 }}>
            <div style={{ fontFamily: 'var(--font-heading)', fontSize: 40, fontWeight: 800, color: scoreColor, lineHeight: 1 }}>
              {Math.round(ats.overall_score * 100)}%
            </div>
            <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 4 }}>ATS Match</div>
            {pages > 0 && (
              <div style={{
                fontSize: 12, marginTop: 8, fontWeight: 600,
                color: pages === 1 ? 'var(--accent-green)' : 'var(--accent-red)',
              }}>
                {pages === 1 ? '1 page' : `${pages} pages`}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Downloads */}
      <div className="glass fade-slide-up stagger-1" style={{ display: 'flex', gap: 10, padding: 20, flexWrap: 'wrap', alignItems: 'center', marginBottom: 20 }}>
        <a href={files.pdf} style={{ textDecoration: 'none' }}>
          <button className="btn btn-primary">Download PDF</button>
        </a>
        <a href={files.tex} style={{ textDecoration: 'none' }}>
          <button className="btn btn-secondary">Download .tex</button>
        </a>
        <a href={files.docx} style={{ textDecoration: 'none' }}>
          <button className="btn btn-secondary">Download DOCX</button>
        </a>
        <a href={files.cover_letter} style={{ textDecoration: 'none' }}>
          <button className="btn btn-secondary">Cover Letter</button>
        </a>
      </div>

      {/* Keywords */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 20 }}>
        <div className="glass fade-slide-up stagger-2" style={{ padding: 22 }}>
          <h4 className="card-title">Keywords Matched</h4>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
            {(ats.matched_required || []).concat(ats.matched_tech || []).map((kw, i) => (
              <span key={i} className="tag tag-matched">{kw}</span>
            ))}
            {!(ats.matched_required?.length || ats.matched_tech?.length) && (
              <span style={{ color: 'var(--text-muted)' }}>No keywords matched</span>
            )}
          </div>
        </div>
        <div className="glass fade-slide-up stagger-3" style={{ padding: 22 }}>
          <h4 className="card-title">Keywords Missing</h4>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
            {(ats.missing_required || []).concat(ats.missing_tech || []).map((kw, i) => (
              <span key={i} className="tag tag-missing">{kw}</span>
            ))}
            {!(ats.missing_required?.length || ats.missing_tech?.length) && (
              <span style={{ color: 'var(--accent-green)' }}>All keywords covered!</span>
            )}
          </div>
        </div>
      </div>

      {/* Cover Letter Preview */}
      <div className="glass fade-slide-up stagger-4" style={{ padding: 24 }}>
        <h4 className="card-title">Cover Letter Preview</h4>
        <div className="cover-letter-preview">{cover_letter}</div>
      </div>
    </div>
  )
}

// ── Scraper Panel ───────────────────────────────────────────────

function ScraperPanel() {
  const [source, setSource] = useState('all')
  const [query, setQuery] = useState('AI ML Engineer')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [boardUrl, setBoardUrl] = useState('')

  const handleScrape = async () => {
    setLoading(true)
    try {
      const res = await fetch(`${API}/scrape`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ source, query }),
      })
      setResult(await res.json())
    } catch (e) { console.error(e) }
    finally { setLoading(false) }
  }

  const handleBoardScrape = async () => {
    if (!boardUrl) return
    setLoading(true)
    try {
      const res = await fetch(`${API}/scrape/board`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: boardUrl }),
      })
      setResult(await res.json())
    } catch (e) { console.error(e) }
    finally { setLoading(false) }
  }

  return (
    <div>
      <div className="glass fade-slide-up" style={{ padding: 28, marginBottom: 20 }}>
        <h3 style={{ fontFamily: 'var(--font-heading)', fontSize: 22, fontWeight: 700, marginBottom: 6 }}>
          Discover jobs
        </h3>
        <p style={{ color: 'var(--text-secondary)', fontSize: 14, marginBottom: 20 }}>
          Search across job boards or scrape company career pages.
        </p>

        <div style={{ display: 'flex', gap: 12, marginBottom: 16 }}>
          <input className="input" style={{ flex: 1 }} placeholder="Search query (e.g., AI ML Engineer)"
                 value={query} onChange={e => setQuery(e.target.value)} />
          <select className="input" style={{ width: 160 }} value={source} onChange={e => setSource(e.target.value)}>
            <option value="all">All Sources</option>
            <option value="linkedin">LinkedIn</option>
            <option value="indeed">Indeed</option>
          </select>
          <button className="btn btn-primary" onClick={handleScrape} disabled={loading}>
            {loading ? '⟳ Searching...' : 'Search Jobs'}
          </button>
        </div>

        <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
          <input className="input" style={{ flex: 1 }}
                 placeholder="Greenhouse/Lever board URL (e.g., https://boards.greenhouse.io/openai)"
                 value={boardUrl} onChange={e => setBoardUrl(e.target.value)} />
          <button className="btn btn-secondary" onClick={handleBoardScrape} disabled={loading}>Scrape Board</button>
        </div>
      </div>

      {result && (
        <div className="glass fade-slide-up" style={{ padding: 24 }}>
          <h4 className="card-title">Found {result.total_found} jobs ({result.new_added} new)</h4>
          <div style={{ maxHeight: 500, overflow: 'auto' }}>
            {result.jobs?.map((job, i) => (
              <div key={i} style={{
                padding: '14px 0',
                borderBottom: '1px solid rgba(255,255,255,0.04)',
                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              }}>
                <div>
                  <div style={{ fontWeight: 600 }}>{job.title}</div>
                  <div style={{ color: 'var(--text-secondary)', fontSize: 13 }}>{job.company} · {job.location}</div>
                </div>
                <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                  <span className="tag">{job.source}</span>
                  {job.url && (
                    <a href={job.url} target="_blank" rel="noopener"
                       style={{ color: 'var(--accent-violet)', fontSize: 13, textDecoration: 'none' }}>View ↗</a>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

// ── Main App ────────────────────────────────────────────────────

export default function App() {
  const [page, setPage] = useState('tailor')
  const [stats, setStats] = useState({})
  const [applications, setApplications] = useState([])
  const [apiStatus, setApiStatus] = useState(null)
  const [profile, setProfile] = useState(null)
  const [selectedApp, setSelectedApp] = useState(null)

  const loadData = useCallback(async () => {
    try {
      const [statsRes, appsRes, healthRes] = await Promise.all([
        fetch(`${API}/applications/stats`),
        fetch(`${API}/applications`),
        fetch(`${API}/health`),
      ])
      if (statsRes.ok) setStats(await statsRes.json())
      if (appsRes.ok) setApplications(await appsRes.json())
      if (healthRes.ok) setApiStatus(await healthRes.json())
    } catch (e) {
      console.error('API not running:', e)
      setApiStatus({ status: 'offline' })
    }
  }, [])

  useEffect(() => {
    loadData()
    const interval = setInterval(loadData, 30000)
    return () => clearInterval(interval)
  }, [loadData])

  const handleStatusChange = async (appId, newStatus) => {
    await fetch(`${API}/applications/${appId}/status`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: newStatus }),
    })
    loadData()
    if (selectedApp && selectedApp.id === appId) {
      setSelectedApp(prev => ({ ...prev, status: newStatus }))
    }
  }

  return (
    <div className="app-container">
      {/* Animated background */}
      <div className="app-bg">
        <div className="app-bg-orb3" />
      </div>

      {/* Header */}
      <header className="header">
        <div className="logo">
          <div className="logo-icon">◉</div>
          <span>JobPilot</span>
        </div>

        <nav className="nav">
          <button className={`nav-btn ${page === 'dashboard' ? 'active' : ''}`}
                  onClick={() => setPage('dashboard')}>Dashboard</button>
          <button className={`nav-btn ${page === 'tailor' ? 'active' : ''}`}
                  onClick={() => setPage('tailor')}>Tailor Resume</button>
          <button className={`nav-btn ${page === 'scrape' ? 'active' : ''}`}
                  onClick={() => setPage('scrape')}>Find Jobs</button>
        </nav>

        <div className="api-status">
          {apiStatus?.status === 'ok' ? (
            <>
              <span className="status-dot online" />
              <span style={{ color: 'var(--accent-green)' }}>
                Connected {apiStatus.api_key_set ? '' : '(no key)'}
              </span>
            </>
          ) : (
            <>
              <span className="status-dot offline" />
              <span style={{ color: 'var(--accent-red)' }}>Offline — run: python api.py</span>
            </>
          )}
        </div>
      </header>

      {/* Main */}
      <main className="main-content">
        {page === 'dashboard' && (
          <>
            <StatsCards stats={stats} />
            <h3 className="section-title fade-slide-up stagger-3">Applications</h3>
            <ApplicationsTable
              applications={applications}
              onStatusChange={handleStatusChange}
              onSelectApp={setSelectedApp}
            />
          </>
        )}
        {page === 'tailor' && (
          <>
            <ProfileUpload onProfileSet={setProfile} currentProfile={profile} />
            {profile && <TailorPanel userId={profile.user_id} />}
          </>
        )}
        {page === 'scrape' && <ScraperPanel />}
      </main>

      {/* Modal */}
      {selectedApp && (
        <ApplicationDetailModal
          app={selectedApp}
          onClose={() => setSelectedApp(null)}
          onStatusChange={handleStatusChange}
        />
      )}
    </div>
  )
}

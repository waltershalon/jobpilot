import React, { useState, useEffect, useCallback } from 'react'

const API = '/api'

// ── Styles ──────────────────────────────────────────────────────
const styles = {
  app: {
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    background: '#0f1117',
    color: '#e1e4e8',
    minHeight: '100vh',
  },
  header: {
    background: 'linear-gradient(135deg, #1a1f35 0%, #0d1117 100%)',
    borderBottom: '1px solid #21262d',
    padding: '16px 32px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  logo: {
    fontSize: '22px',
    fontWeight: '700',
    color: '#58a6ff',
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
  },
  nav: {
    display: 'flex',
    gap: '4px',
  },
  navBtn: (active) => ({
    padding: '8px 18px',
    border: 'none',
    borderRadius: '8px',
    background: active ? '#21262d' : 'transparent',
    color: active ? '#58a6ff' : '#8b949e',
    cursor: 'pointer',
    fontSize: '14px',
    fontWeight: active ? '600' : '400',
    transition: 'all 0.15s',
  }),
  main: {
    maxWidth: '1200px',
    margin: '0 auto',
    padding: '24px 32px',
  },
  card: {
    background: '#161b22',
    border: '1px solid #21262d',
    borderRadius: '12px',
    padding: '24px',
    marginBottom: '20px',
  },
  cardTitle: {
    fontSize: '16px',
    fontWeight: '600',
    marginBottom: '16px',
    color: '#e1e4e8',
  },
  statsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
    gap: '16px',
    marginBottom: '24px',
  },
  statCard: (color) => ({
    background: '#161b22',
    border: '1px solid #21262d',
    borderRadius: '12px',
    padding: '20px',
    borderLeft: `3px solid ${color}`,
  }),
  statValue: {
    fontSize: '28px',
    fontWeight: '700',
    color: '#e1e4e8',
  },
  statLabel: {
    fontSize: '13px',
    color: '#8b949e',
    marginTop: '4px',
  },
  input: {
    width: '100%',
    padding: '12px 16px',
    background: '#0d1117',
    border: '1px solid #30363d',
    borderRadius: '8px',
    color: '#e1e4e8',
    fontSize: '14px',
    outline: 'none',
    boxSizing: 'border-box',
  },
  textarea: {
    width: '100%',
    padding: '12px 16px',
    background: '#0d1117',
    border: '1px solid #30363d',
    borderRadius: '8px',
    color: '#e1e4e8',
    fontSize: '14px',
    outline: 'none',
    minHeight: '120px',
    resize: 'vertical',
    fontFamily: 'inherit',
    boxSizing: 'border-box',
  },
  btn: (variant = 'primary') => ({
    padding: '10px 24px',
    border: 'none',
    borderRadius: '8px',
    fontSize: '14px',
    fontWeight: '600',
    cursor: 'pointer',
    transition: 'all 0.15s',
    ...(variant === 'primary' ? {
      background: 'linear-gradient(135deg, #238636 0%, #2ea043 100%)',
      color: '#fff',
    } : variant === 'secondary' ? {
      background: '#21262d',
      color: '#e1e4e8',
      border: '1px solid #30363d',
    } : variant === 'danger' ? {
      background: '#da3633',
      color: '#fff',
    } : {
      background: '#1f6feb',
      color: '#fff',
    }),
  }),
  badge: (color) => ({
    display: 'inline-block',
    padding: '3px 10px',
    borderRadius: '12px',
    fontSize: '12px',
    fontWeight: '600',
    background: color + '22',
    color: color,
    border: `1px solid ${color}44`,
  }),
  table: {
    width: '100%',
    borderCollapse: 'collapse',
  },
  th: {
    textAlign: 'left',
    padding: '10px 12px',
    borderBottom: '1px solid #21262d',
    color: '#8b949e',
    fontSize: '12px',
    fontWeight: '600',
    textTransform: 'uppercase',
  },
  td: {
    padding: '12px',
    borderBottom: '1px solid #21262d',
    fontSize: '14px',
  },
  progressBar: () => ({
    width: '100%',
    height: '8px',
    background: '#21262d',
    borderRadius: '4px',
    overflow: 'hidden',
    position: 'relative',
  }),
  progressFill: (pct, color) => ({
    width: `${pct}%`,
    height: '100%',
    background: color,
    borderRadius: '4px',
    transition: 'width 0.5s ease',
  }),
  tag: {
    display: 'inline-block',
    padding: '2px 8px',
    borderRadius: '4px',
    fontSize: '12px',
    background: '#21262d',
    color: '#8b949e',
    marginRight: '4px',
    marginBottom: '4px',
  },
  matchedTag: {
    display: 'inline-block',
    padding: '2px 8px',
    borderRadius: '4px',
    fontSize: '12px',
    background: '#23863622',
    color: '#3fb950',
    marginRight: '4px',
    marginBottom: '4px',
    border: '1px solid #23863644',
  },
  missingTag: {
    display: 'inline-block',
    padding: '2px 8px',
    borderRadius: '4px',
    fontSize: '12px',
    background: '#f8514922',
    color: '#f85149',
    marginRight: '4px',
    marginBottom: '4px',
    border: '1px solid #f8514944',
  },
  modal: {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    background: 'rgba(0,0,0,0.7)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 1000,
    padding: '24px',
  },
  modalContent: {
    background: '#161b22',
    border: '1px solid #30363d',
    borderRadius: '16px',
    width: '100%',
    maxWidth: '800px',
    maxHeight: '85vh',
    overflow: 'auto',
    padding: '32px',
  },
}

const STATUS_COLORS = {
  discovered: '#8b949e',
  resume_ready: '#58a6ff',
  applied: '#d29922',
  response: '#3fb950',
  interview: '#a371f7',
  offer: '#238636',
  rejected: '#f85149',
  withdrawn: '#6e7681',
  low_match: '#6e7681',
}

// ── Dashboard Components ────────────────────────────────────────

function StatsCards({ stats }) {
  return (
    <div style={styles.statsGrid}>
      <div style={styles.statCard('#58a6ff')}>
        <div style={styles.statValue}>{stats.total || 0}</div>
        <div style={styles.statLabel}>Total Applications</div>
      </div>
      <div style={styles.statCard('#3fb950')}>
        <div style={styles.statValue}>{stats.by_status?.resume_ready || 0}</div>
        <div style={styles.statLabel}>Resumes Ready</div>
      </div>
      <div style={styles.statCard('#d29922')}>
        <div style={styles.statValue}>{stats.by_status?.applied || 0}</div>
        <div style={styles.statLabel}>Applied</div>
      </div>
      <div style={styles.statCard('#a371f7')}>
        <div style={styles.statValue}>{stats.by_status?.interview || 0}</div>
        <div style={styles.statLabel}>Interviews</div>
      </div>
      <div style={styles.statCard('#238636')}>
        <div style={styles.statValue}>
          {stats.avg_ats_score ? `${Math.round(stats.avg_ats_score * 100)}%` : '-'}
        </div>
        <div style={styles.statLabel}>Avg ATS Score</div>
      </div>
    </div>
  )
}

function ApplicationDetailModal({ app, onClose, onStatusChange }) {
  if (!app) return null
  const scoreColor = app.ats_score >= 0.7 ? '#3fb950' : app.ats_score >= 0.5 ? '#d29922' : '#f85149'
  const matched = app.keywords_matched || []
  const missing = app.keywords_missing || []

  useEffect(() => {
    const handler = (e) => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [onClose])

  return (
    <div style={styles.modal} onClick={onClose}>
      <div style={styles.modalContent} onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '24px' }}>
          <div>
            <h2 style={{ fontSize: '22px', fontWeight: '700', margin: 0, color: '#e1e4e8' }}>
              {app.title}
            </h2>
            <div style={{ color: '#8b949e', marginTop: '6px', fontSize: '14px' }}>
              {app.company} {app.location ? `· ${app.location}` : ''} · Applied {app.created_at?.slice(0, 10)}
            </div>
            {app.url && (
              <a href={app.url} target="_blank" rel="noopener"
                 style={{ color: '#58a6ff', fontSize: '13px', textDecoration: 'none', display: 'inline-block', marginTop: '4px' }}>
                View job posting
              </a>
            )}
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            {app.ats_score > 0 && (
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '32px', fontWeight: '700', color: scoreColor }}>
                  {Math.round(app.ats_score * 100)}%
                </div>
                <div style={{ fontSize: '11px', color: '#8b949e' }}>ATS Score</div>
              </div>
            )}
            <button onClick={onClose} style={{
              background: 'none', border: 'none', color: '#8b949e', cursor: 'pointer',
              fontSize: '24px', lineHeight: 1, padding: '4px',
            }}>x</button>
          </div>
        </div>

        {/* Status */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '20px' }}>
          <span style={{ fontSize: '13px', color: '#8b949e' }}>Status:</span>
          <select
            value={app.status}
            onChange={e => onStatusChange(app.id, e.target.value)}
            style={{ ...styles.input, width: 'auto', padding: '6px 12px', fontSize: '13px' }}
          >
            {Object.keys(STATUS_COLORS).map(s => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </div>

        {/* Keywords */}
        {(matched.length > 0 || missing.length > 0) && (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '20px' }}>
            <div>
              <div style={{ fontSize: '13px', fontWeight: '600', color: '#3fb950', marginBottom: '8px' }}>
                Keywords Matched ({matched.length})
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                {matched.map((kw, i) => (
                  <span key={i} style={styles.matchedTag}>{kw}</span>
                ))}
              </div>
            </div>
            <div>
              <div style={{ fontSize: '13px', fontWeight: '600', color: '#f85149', marginBottom: '8px' }}>
                Keywords Missing ({missing.length})
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                {missing.map((kw, i) => (
                  <span key={i} style={styles.missingTag}>{kw}</span>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Download Buttons */}
        <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
          {app.resume_path && (
            <a href={`/api/files/${encodeURIComponent(app.resume_path.split('/').pop())}`}
               style={{ textDecoration: 'none' }}>
              <button style={styles.btn('primary')}>Download PDF</button>
            </a>
          )}
          {app.cover_letter_path && (
            <a href={`/api/files/${encodeURIComponent(app.cover_letter_path.split('/').pop())}`}
               style={{ textDecoration: 'none' }}>
              <button style={styles.btn('secondary')}>Cover Letter</button>
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
      <div style={{ ...styles.card, textAlign: 'center', color: '#8b949e', padding: '48px' }}>
        No applications yet. Tailor your first resume to get started!
      </div>
    )
  }

  return (
    <div style={{ ...styles.card, padding: '0', overflow: 'auto' }}>
      <table style={styles.table}>
        <thead>
          <tr>
            <th style={styles.th}>Role</th>
            <th style={styles.th}>Company</th>
            <th style={styles.th}>Status</th>
            <th style={styles.th}>ATS Score</th>
            <th style={styles.th}>Date</th>
          </tr>
        </thead>
        <tbody>
          {applications.map(app => (
            <tr key={app.id}
                style={{ transition: 'background 0.15s', cursor: 'pointer' }}
                onClick={() => onSelectApp(app)}
                onMouseEnter={e => e.currentTarget.style.background = '#1c2128'}
                onMouseLeave={e => e.currentTarget.style.background = 'transparent'}>
              <td style={styles.td}>
                <div style={{ fontWeight: '600' }}>{app.title}</div>
              </td>
              <td style={styles.td}>{app.company}</td>
              <td style={styles.td}>
                <span style={styles.badge(STATUS_COLORS[app.status] || '#8b949e')}>
                  {app.status}
                </span>
              </td>
              <td style={styles.td}>
                {app.ats_score > 0 ? (
                  <div>
                    <div style={{ fontWeight: '600', marginBottom: '4px' }}>
                      {Math.round(app.ats_score * 100)}%
                    </div>
                    <div style={styles.progressBar()}>
                      <div style={styles.progressFill(
                        app.ats_score * 100,
                        app.ats_score >= 0.7 ? '#3fb950' : app.ats_score >= 0.5 ? '#d29922' : '#f85149'
                      )} />
                    </div>
                  </div>
                ) : '-'}
              </td>
              <td style={{ ...styles.td, color: '#8b949e', fontSize: '13px' }}>
                {app.created_at?.slice(0, 10)}
              </td>
            </tr>
          ))}
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
    <div style={styles.card}>
      <h3 style={styles.cardTitle}>Your Profile</h3>
      {currentProfile ? (
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <div style={{ fontWeight: '600', fontSize: '16px' }}>{currentProfile.name}</div>
            <div style={{ color: '#8b949e', fontSize: '13px', marginTop: '4px' }}>
              {currentProfile.email}
              <span style={{ marginLeft: '12px' }}>
                {currentProfile.stats.work} work · {currentProfile.stats.research} research · {currentProfile.stats.projects} projects · {currentProfile.stats.education} education
              </span>
            </div>
          </div>
          <label style={{ ...styles.btn('secondary'), cursor: 'pointer', display: 'inline-block' }}>
            {uploading ? 'Uploading...' : 'Switch Profile'}
            <input type="file" accept=".pdf" onChange={handleUpload} style={{ display: 'none' }} />
          </label>
        </div>
      ) : (
        <div style={{ textAlign: 'center', padding: '24px' }}>
          <p style={{ color: '#8b949e', marginBottom: '16px' }}>
            Upload your resume PDF to get started. AI will parse it into a profile for tailoring.
          </p>
          <label style={{ ...styles.btn('primary'), cursor: 'pointer', display: 'inline-block' }}>
            {uploading ? 'Parsing resume...' : 'Upload Resume PDF'}
            <input type="file" accept=".pdf" onChange={handleUpload} style={{ display: 'none' }} />
          </label>
          <div style={{ marginTop: '12px' }}>
            <button
              style={{ ...styles.btn('secondary'), fontSize: '12px' }}
              onClick={() => onProfileSet({ user_id: null, name: 'Default Profile', email: '', stats: { education: 0, work: 0, research: 0, projects: 0 } })}
            >
              Use default profile instead
            </button>
          </div>
        </div>
      )}
      {error && (
        <div style={{ marginTop: '12px', padding: '12px 16px', background: '#f8514922', border: '1px solid #f8514944', borderRadius: '8px', color: '#f85149', fontSize: '14px' }}>
          {error}
        </div>
      )}
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
    <div style={{ padding: '10px 0', borderBottom: '1px solid #21262d' }}>
      {/* Original */}
      <div style={{ display: 'flex', gap: '8px', alignItems: 'flex-start', marginBottom: '6px' }}>
        <span style={{ fontSize: '10px', color: '#8b949e', minWidth: '50px', paddingTop: '2px' }}>Original</span>
        <div style={{ fontSize: '13px', color: '#8b949e', lineHeight: '1.5', flex: 1 }}>
          {bullet.original}
        </div>
      </div>

      {/* Suggestion (if different from original) */}
      {bullet.action !== 'keep' && bullet.suggested && bullet.suggested !== bullet.original && (
        <div style={{ display: 'flex', gap: '8px', alignItems: 'flex-start', marginBottom: '6px' }}>
          <span style={{ fontSize: '10px', color: '#3fb950', minWidth: '50px', paddingTop: '2px' }}>AI</span>
          <div style={{ fontSize: '13px', color: '#c9d1d9', lineHeight: '1.5', flex: 1, background: '#23863611', padding: '4px 8px', borderRadius: '4px', border: '1px solid #23863633' }}>
            {bullet.suggested}
          </div>
        </div>
      )}

      {/* Reason */}
      {bullet.reason && (
        <div style={{ fontSize: '11px', color: '#8b949e', marginLeft: '58px', marginBottom: '6px', fontStyle: 'italic' }}>
          {bullet.reason}
          {bullet.keywords_added?.length > 0 && (
            <span> — Keywords: {bullet.keywords_added.map((kw, i) => (
              <span key={i} style={{ ...styles.matchedTag, fontSize: '10px', padding: '1px 5px' }}>{kw}</span>
            ))}</span>
          )}
        </div>
      )}

      {/* Edit mode */}
      {editing && (
        <div style={{ marginLeft: '58px', marginBottom: '6px' }}>
          <textarea
            value={editText}
            onChange={e => setEditText(e.target.value)}
            style={{ ...styles.textarea, minHeight: '60px', fontSize: '13px' }}
          />
          <div style={{ display: 'flex', gap: '8px', marginTop: '4px', alignItems: 'center' }}>
            <button style={{ ...styles.btn('primary'), padding: '4px 12px', fontSize: '12px' }} onClick={saveEdit}>Save</button>
            <button style={{ ...styles.btn('secondary'), padding: '4px 12px', fontSize: '12px' }} onClick={() => setEditing(false)}>Cancel</button>
            <span style={{ fontSize: '11px', color: editText.length > 120 ? '#f85149' : '#8b949e' }}>{editText.length}/120 chars</span>
          </div>
        </div>
      )}

      {/* Action buttons */}
      <div style={{ display: 'flex', gap: '6px', marginLeft: '58px', alignItems: 'center' }}>
        {bullet.action !== 'keep' && bullet.suggested && (
          <button
            onClick={() => onDecision({ action: 'accept' })}
            style={{
              padding: '3px 10px', borderRadius: '4px', fontSize: '11px', fontWeight: '600', cursor: 'pointer', border: 'none',
              background: action === 'accept' ? '#238636' : '#21262d',
              color: action === 'accept' ? '#fff' : '#8b949e',
            }}
          >Accept</button>
        )}
        <button
          onClick={() => onDecision({ action: 'reject' })}
          style={{
            padding: '3px 10px', borderRadius: '4px', fontSize: '11px', fontWeight: '600', cursor: 'pointer', border: 'none',
            background: action === 'reject' ? '#da3633' : '#21262d',
            color: action === 'reject' ? '#fff' : '#8b949e',
          }}
        >Keep Original</button>
        <button
          onClick={handleEdit}
          style={{
            padding: '3px 10px', borderRadius: '4px', fontSize: '11px', fontWeight: '600', cursor: 'pointer', border: 'none',
            background: action === 'edit' ? '#1f6feb' : '#21262d',
            color: action === 'edit' ? '#fff' : '#8b949e',
          }}
        >Edit</button>
        <span style={{ fontSize: '11px', color: charCount > 120 ? '#f85149' : '#6e7681', marginLeft: '8px' }}>
          {charCount} chars
        </span>
      </div>
    </div>
  )
}

function ExperienceCard({ exp, selected, onToggle, bulletDecisions, onBulletDecision }) {
  const [expanded, setExpanded] = useState(selected)
  const scoreColor = exp.relevance_score >= 7 ? '#3fb950' : exp.relevance_score >= 4 ? '#d29922' : '#f85149'

  return (
    <div style={{
      ...styles.card,
      borderLeft: `3px solid ${selected ? scoreColor : '#30363d'}`,
      opacity: selected ? 1 : 0.6,
      marginBottom: '12px',
    }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flex: 1, cursor: 'pointer' }}
             onClick={() => setExpanded(!expanded)}>
          <div>
            <div style={{ fontWeight: '600', fontSize: '15px' }}>{exp.title}</div>
            <div style={{ color: '#8b949e', fontSize: '13px' }}>
              {exp.company} · {exp.start_date} — {exp.end_date}
            </div>
          </div>
          <span style={styles.badge(scoreColor)}>{exp.relevance_score}/10</span>
          <span style={{ fontSize: '12px', color: '#8b949e', fontStyle: 'italic' }}>{exp.relevance_reason}</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '12px', color: '#8b949e' }}>{expanded ? '▼' : '▶'} {exp.bullets?.length || 0} bullets</span>
          <button
            onClick={() => onToggle(!selected)}
            style={{
              padding: '4px 12px', borderRadius: '6px', fontSize: '12px', fontWeight: '600', cursor: 'pointer', border: 'none',
              background: selected ? '#238636' : '#21262d',
              color: selected ? '#fff' : '#8b949e',
            }}
          >
            {selected ? 'Included' : 'Excluded'}
          </button>
        </div>
      </div>

      {/* Bullets */}
      {expanded && selected && (
        <div style={{ marginTop: '12px' }}>
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
    <div style={{
      ...styles.card,
      background: '#f8514911',
      border: '1px solid #f8514933',
      padding: '16px 20px',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
        <span style={{ fontSize: '14px', fontWeight: '600', color: '#f85149' }}>
          {allMissing.size} Missing Keywords
        </span>
        <span style={{ fontSize: '12px', color: '#8b949e' }}>
          AI has suggestions for where to add some of these
        </span>
      </div>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', marginBottom: suggestions?.length ? '12px' : 0 }}>
        {[...allMissing].map((kw, i) => (
          <span key={i} style={styles.missingTag}>{kw}</span>
        ))}
      </div>
      {suggestions?.length > 0 && (
        <div style={{ marginTop: '8px' }}>
          {suggestions.slice(0, 5).map((s, i) => (
            <div key={i} style={{ fontSize: '12px', color: '#c9d1d9', padding: '4px 0', borderTop: i > 0 ? '1px solid #21262d' : 'none' }}>
              <span style={styles.missingTag}>{s.keyword}</span>
              <span style={{ color: '#8b949e', marginLeft: '8px' }}>
                → {s.suggestion}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function SuggestionsEditor({ suggestions, sessionId, userId, onFinalized }) {
  // State for user decisions
  const [selectedExps, setSelectedExps] = useState(() => {
    const initial = {}
    ;(suggestions.experiences || []).forEach(exp => {
      initial[exp.id] = exp.selected
    })
    return initial
  })
  const [bulletDecisions, setBulletDecisions] = useState({})
  const [selectedProjects, setSelectedProjects] = useState(() => {
    const initial = {}
    ;(suggestions.projects || []).forEach(proj => {
      initial[proj.id] = proj.selected
    })
    return initial
  })
  const [projectBulletDecisions, setProjectBulletDecisions] = useState({})
  const [generating, setGenerating] = useState(false)
  const [error, setError] = useState(null)

  // Page estimate
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
    // Accept all AI suggestions
    const bd = {}
    ;(suggestions.experiences || []).forEach(exp => {
      bd[exp.id] = {}
      ;(exp.bullets || []).forEach((b, i) => {
        bd[exp.id][String(i)] = { action: 'accept' }
      })
    })
    setBulletDecisions(bd)
  }

  const rejectAll = () => {
    // Keep all originals
    const bd = {}
    ;(suggestions.experiences || []).forEach(exp => {
      bd[exp.id] = {}
      ;(exp.bullets || []).forEach((b, i) => {
        bd[exp.id][String(i)] = { action: 'reject' }
      })
    })
    setBulletDecisions(bd)
  }

  // Collect all missing keywords from keyword_suggestions
  const missingKeywords = (suggestions.job?.keywords || []).filter(kw => {
    const allText = (suggestions.experiences || [])
      .flatMap(e => (e.bullets || []).map(b => (b.suggested || b.original || '').toLowerCase()))
      .join(' ')
    return !allText.includes(kw.toLowerCase())
  })

  return (
    <div>
      {/* Job Header */}
      <div style={styles.card}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <h3 style={{ ...styles.cardTitle, fontSize: '20px', marginBottom: '4px' }}>
              {suggestions.job?.title}
            </h3>
            <div style={{ color: '#8b949e' }}>
              {suggestions.job?.company} · {suggestions.job?.industry}
            </div>
          </div>
          <div style={{
            textAlign: 'center', padding: '8px 16px', borderRadius: '8px',
            background: estPages === 1 ? '#23863622' : '#f8514922',
            border: `1px solid ${estPages === 1 ? '#23863644' : '#f8514944'}`,
          }}>
            <div style={{ fontSize: '18px', fontWeight: '700', color: estPages === 1 ? '#3fb950' : '#f85149' }}>
              ~{estPages} page{estPages > 1 ? 's' : ''}
            </div>
            <div style={{ fontSize: '11px', color: '#8b949e' }}>
              {selectedExpCount} exp · {totalBullets} bullets · {selectedProjCount} proj
            </div>
          </div>
        </div>
      </div>

      {/* Missing Keywords */}
      <MissingKeywordsBar
        keywords={missingKeywords}
        suggestions={suggestions.keyword_suggestions}
      />

      {/* Action Bar */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '16px', alignItems: 'center' }}>
        <button style={{ ...styles.btn('primary'), opacity: generating ? 0.6 : 1 }}
                onClick={handleFinalize} disabled={generating}>
          {generating ? 'Generating PDF...' : 'Generate Final PDF'}
        </button>
        <button style={styles.btn('secondary')} onClick={acceptAll}>Accept All AI</button>
        <button style={styles.btn('secondary')} onClick={rejectAll}>Keep All Originals</button>
        {estPages > 1 && (
          <span style={{ fontSize: '12px', color: '#f85149', marginLeft: '8px' }}>
            Content may exceed 1 page — consider excluding some experiences
          </span>
        )}
      </div>

      {error && (
        <div style={{ marginBottom: '16px', padding: '12px 16px', background: '#f8514922', border: '1px solid #f8514944', borderRadius: '8px', color: '#f85149', fontSize: '14px' }}>
          {error}
        </div>
      )}

      {/* Work Experience */}
      {(suggestions.experiences || []).filter(e => e.source === 'work_experience').length > 0 && (
        <>
          <h3 style={{ ...styles.cardTitle, marginBottom: '12px' }}>Work Experience</h3>
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
                  ...prev,
                  [exp.id]: { ...(prev[exp.id] || {}), [idx]: dec }
                }))}
              />
            ))}
        </>
      )}

      {/* Research Experience */}
      {(suggestions.experiences || []).filter(e => e.source === 'research_experience').length > 0 && (
        <>
          <h3 style={{ ...styles.cardTitle, marginBottom: '12px', marginTop: '24px' }}>Research Experience</h3>
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
                  ...prev,
                  [exp.id]: { ...(prev[exp.id] || {}), [idx]: dec }
                }))}
              />
            ))}
        </>
      )}

      {/* Projects */}
      {(suggestions.projects || []).length > 0 && (
        <>
          <h3 style={{ ...styles.cardTitle, marginBottom: '12px', marginTop: '24px' }}>Projects</h3>
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
                  ...prev,
                  [proj.id]: { ...(prev[proj.id] || {}), [idx]: dec }
                }))}
              />
            ))}
        </>
      )}

      {/* Skills Preview */}
      {suggestions.skills && (
        <div style={{ ...styles.card, marginTop: '24px' }}>
          <h3 style={styles.cardTitle}>Skills (reordered for this JD)</h3>
          {Object.entries(suggestions.skills).map(([category, items]) => (
            <div key={category} style={{ marginBottom: '8px' }}>
              <span style={{ fontSize: '12px', fontWeight: '600', color: '#8b949e', textTransform: 'capitalize' }}>
                {category.replace(/_/g, ' ')}:
              </span>
              <span style={{ fontSize: '13px', color: '#c9d1d9', marginLeft: '8px' }}>
                {(items || []).join(', ')}
              </span>
            </div>
          ))}
        </div>
      )}

      {/* Bottom action bar */}
      <div style={{ display: 'flex', gap: '8px', marginTop: '20px' }}>
        <button style={{ ...styles.btn('primary'), opacity: generating ? 0.6 : 1, padding: '12px 32px', fontSize: '15px' }}
                onClick={handleFinalize} disabled={generating}>
          {generating ? 'Generating PDF...' : 'Generate Final PDF'}
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

  // Phased flow: input → suggestions → result
  const [phase, setPhase] = useState('input') // input | suggestions | result
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

  const handleFinalized = (data) => {
    setResult(data)
    setPhase('result')
  }

  const handleReset = () => {
    setPhase('input')
    setSuggestions(null)
    setSessionId(null)
    setResult(null)
    setError(null)
  }

  // Phase: Input
  if (phase === 'input') {
    return (
      <div>
        <div style={styles.card}>
          <h3 style={styles.cardTitle}>Tailor Resume to Job</h3>
          <div style={{ display: 'flex', gap: '8px', marginBottom: '16px' }}>
            <button style={styles.navBtn(mode === 'url')} onClick={() => setMode('url')}>Paste URL</button>
            <button style={styles.navBtn(mode === 'text')} onClick={() => setMode('text')}>Paste JD Text</button>
          </div>
          {mode === 'url' ? (
            <input style={styles.input} placeholder="https://boards.greenhouse.io/company/jobs/12345"
                   value={jdUrl} onChange={e => setJdUrl(e.target.value)}
                   onKeyDown={e => e.key === 'Enter' && handleGetSuggestions()} />
          ) : (
            <textarea style={styles.textarea} placeholder="Paste the full job description here..."
                      value={jdText} onChange={e => setJdText(e.target.value)} />
          )}
          <div style={{ marginTop: '16px', display: 'flex', alignItems: 'center', gap: '12px' }}>
            <button style={{ ...styles.btn('primary'), opacity: loading ? 0.6 : 1, minWidth: '200px' }}
                    onClick={handleGetSuggestions} disabled={loading}>
              {loading ? 'Analyzing JD...' : 'Get AI Suggestions'}
            </button>
            {loading && (
              <span style={{ color: '#8b949e', fontSize: '13px' }}>
                Parsing JD, generating suggestions for each experience... ~30s
              </span>
            )}
          </div>
          {error && (
            <div style={{ marginTop: '16px', padding: '12px 16px', background: '#f8514922', border: '1px solid #f8514944', borderRadius: '8px', color: '#f85149', fontSize: '14px' }}>
              {error}
            </div>
          )}
        </div>
      </div>
    )
  }

  // Phase: Suggestions Editor
  if (phase === 'suggestions' && suggestions) {
    return (
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
          <button style={styles.btn('secondary')} onClick={handleReset}>← Back to Input</button>
          <span style={{ color: '#8b949e', fontSize: '13px' }}>Review AI suggestions, then generate your PDF</span>
        </div>
        <SuggestionsEditor
          suggestions={suggestions}
          sessionId={sessionId}
          userId={userId}
          onFinalized={handleFinalized}
        />
      </div>
    )
  }

  // Phase: Result
  if (phase === 'result' && result) {
    return (
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
          <button style={styles.btn('secondary')} onClick={handleReset}>← New Tailoring</button>
          <button style={styles.btn('secondary')} onClick={() => setPhase('suggestions')}>← Back to Editor</button>
        </div>
        <TailorResult result={result} />
      </div>
    )
  }

  return null
}

function TailorResult({ result }) {
  const { job, ats, files, cover_letter, pages } = result
  const scoreColor = ats.overall_score >= 0.7 ? '#3fb950'
    : ats.overall_score >= 0.5 ? '#d29922' : '#f85149'

  return (
    <div>
      <div style={styles.card}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <h3 style={{ ...styles.cardTitle, fontSize: '20px', marginBottom: '4px' }}>{job.title}</h3>
            <div style={{ color: '#8b949e' }}>
              {job.company} · {job.location} · {job.seniority} · {job.industry}
            </div>
            <p style={{ color: '#c9d1d9', marginTop: '8px', fontSize: '14px', lineHeight: '1.5' }}>{job.summary}</p>
          </div>
          <div style={{ textAlign: 'center', minWidth: '120px' }}>
            <div style={{ fontSize: '36px', fontWeight: '700', color: scoreColor }}>
              {Math.round(ats.overall_score * 100)}%
            </div>
            <div style={{ fontSize: '12px', color: '#8b949e' }}>ATS Match</div>
            {pages > 0 && (
              <div style={{ fontSize: '12px', marginTop: '6px', color: pages === 1 ? '#3fb950' : '#f85149', fontWeight: '600' }}>
                {pages === 1 ? '1 page' : `${pages} pages`}
              </div>
            )}
          </div>
        </div>
      </div>

      <div style={{ ...styles.card, display: 'flex', gap: '12px', flexWrap: 'wrap', alignItems: 'center' }}>
        <a href={files.pdf} style={{ textDecoration: 'none' }}><button style={styles.btn('primary')}>Download PDF</button></a>
        <a href={files.tex} style={{ textDecoration: 'none' }}><button style={styles.btn('secondary')}>Download .tex</button></a>
        <a href={files.docx} style={{ textDecoration: 'none' }}><button style={styles.btn('secondary')}>Download DOCX</button></a>
        <a href={files.cover_letter} style={{ textDecoration: 'none' }}><button style={styles.btn('secondary')}>Cover Letter</button></a>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
        <div style={styles.card}>
          <h4 style={styles.cardTitle}>Keywords Matched</h4>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
            {(ats.matched_required || []).concat(ats.matched_tech || []).map((kw, i) => (
              <span key={i} style={styles.matchedTag}>{kw}</span>
            ))}
            {!(ats.matched_required?.length || ats.matched_tech?.length) && (
              <span style={{ color: '#8b949e' }}>No keywords matched</span>
            )}
          </div>
        </div>
        <div style={styles.card}>
          <h4 style={styles.cardTitle}>Keywords Missing</h4>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
            {(ats.missing_required || []).concat(ats.missing_tech || []).map((kw, i) => (
              <span key={i} style={styles.missingTag}>{kw}</span>
            ))}
            {!(ats.missing_required?.length || ats.missing_tech?.length) && (
              <span style={{ color: '#3fb950' }}>All keywords covered!</span>
            )}
          </div>
        </div>
      </div>

      <div style={styles.card}>
        <h4 style={styles.cardTitle}>Cover Letter Preview</h4>
        <div style={{ background: '#0d1117', padding: '20px', borderRadius: '8px', fontSize: '14px', lineHeight: '1.7', color: '#c9d1d9', whiteSpace: 'pre-wrap' }}>
          {cover_letter}
        </div>
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
      <div style={styles.card}>
        <h3 style={styles.cardTitle}>Job Discovery</h3>
        <div style={{ display: 'flex', gap: '12px', marginBottom: '16px' }}>
          <input style={{ ...styles.input, flex: 1 }} placeholder="Search query (e.g., AI ML Engineer)"
                 value={query} onChange={e => setQuery(e.target.value)} />
          <select style={{ ...styles.input, width: '150px' }} value={source} onChange={e => setSource(e.target.value)}>
            <option value="all">All Sources</option>
            <option value="linkedin">LinkedIn</option>
            <option value="indeed">Indeed</option>
          </select>
          <button style={styles.btn('primary')} onClick={handleScrape} disabled={loading}>
            {loading ? 'Searching...' : 'Search Jobs'}
          </button>
        </div>
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <input style={{ ...styles.input, flex: 1 }}
                 placeholder="Greenhouse/Lever board URL (e.g., https://boards.greenhouse.io/openai)"
                 value={boardUrl} onChange={e => setBoardUrl(e.target.value)} />
          <button style={styles.btn('secondary')} onClick={handleBoardScrape} disabled={loading}>Scrape Board</button>
        </div>
      </div>
      {result && (
        <div style={styles.card}>
          <h4 style={styles.cardTitle}>Found {result.total_found} jobs ({result.new_added} new)</h4>
          <div style={{ maxHeight: '500px', overflow: 'auto' }}>
            {result.jobs?.map((job, i) => (
              <div key={i} style={{ padding: '12px 0', borderBottom: '1px solid #21262d', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <div style={{ fontWeight: '600' }}>{job.title}</div>
                  <div style={{ color: '#8b949e', fontSize: '13px' }}>{job.company} · {job.location}</div>
                </div>
                <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                  <span style={styles.tag}>{job.source}</span>
                  {job.url && <a href={job.url} target="_blank" rel="noopener" style={{ color: '#58a6ff', fontSize: '13px' }}>View</a>}
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
    // Update modal if open
    if (selectedApp && selectedApp.id === appId) {
      setSelectedApp(prev => ({ ...prev, status: newStatus }))
    }
  }

  return (
    <div style={styles.app}>
      <header style={styles.header}>
        <div style={styles.logo}>
          <span style={{ fontSize: '26px' }}>🚀</span>
          <span>JobPilot</span>
        </div>
        <nav style={styles.nav}>
          <button style={styles.navBtn(page === 'dashboard')} onClick={() => setPage('dashboard')}>Dashboard</button>
          <button style={styles.navBtn(page === 'tailor')} onClick={() => setPage('tailor')}>Tailor Resume</button>
          <button style={styles.navBtn(page === 'scrape')} onClick={() => setPage('scrape')}>Find Jobs</button>
        </nav>
        <div style={{ fontSize: '12px', color: '#8b949e' }}>
          {apiStatus?.status === 'ok' ? (
            <span style={{ color: '#3fb950' }}>API Connected {apiStatus.api_key_set ? '' : '(no API key)'}</span>
          ) : (
            <span style={{ color: '#f85149' }}>API Offline — start with: python api.py</span>
          )}
        </div>
      </header>

      <main style={styles.main}>
        {page === 'dashboard' && (
          <>
            <StatsCards stats={stats} />
            <h3 style={{ ...styles.cardTitle, marginBottom: '12px' }}>Applications</h3>
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

      {/* Application Detail Modal */}
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

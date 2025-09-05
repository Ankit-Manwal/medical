import React from 'react'

function SettingsPanel({ targetConfidence, maxIterations, onChangeConfidence, onChangeIterations }) {
  return (
    <div className="card-panel" style={{ background: '#fff' }}>
      <h3 style={{ marginBottom: 8 }}>Settings</h3>
      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
        <div style={{ minWidth: 220 }}>
          <label style={{ fontSize: 12, color: 'var(--muted)' }}>Target confidence (%)</label>
          <input type="number" min={1} max={100} value={targetConfidence} onChange={e => onChangeConfidence(Number(e.target.value))} />
        </div>
        <div style={{ minWidth: 220 }}>
          <label style={{ fontSize: 12, color: 'var(--muted)' }}>Max iterations</label>
          <input type="number" min={1} max={20} value={maxIterations} onChange={e => onChangeIterations(Number(e.target.value))} />
        </div>
      </div>
    </div>
  )
}

export default SettingsPanel



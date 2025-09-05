import React from 'react'

function Sidebar({
  activeTab,
  onNavigate,
  availableTests = {},
  addTestSelect = '',
  onChangeAddTest,
  onAddTest,
  showSymptoms = false,
  onToggleSymptoms,
  currentSymptoms = [],
  symptomsRemoved = [],
  bottomSlot,
}) {
  return (
    <div className="sidebar card-panel" style={{ height: '100%' }}>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        <nav style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          <button style={{ background: activeTab==='home' ? '#e2e8f0' : '#fff', color: '#0f172a', borderColor: '#e2e8f0' }} onClick={() => onNavigate('home')}>Home</button>
          <button style={{ background: activeTab==='general' ? '#e2e8f0' : '#fff', color: '#0f172a', borderColor: '#e2e8f0' }} onClick={() => onNavigate('general')}>General Predictor</button>
          <button style={{ background: activeTab==='tests' ? '#e2e8f0' : '#fff', color: '#0f172a', borderColor: '#e2e8f0' }} onClick={() => onNavigate('tests')}>Specific Tests</button>
        </nav>

        <div style={{ height: 1, background: 'var(--border)', margin: '8px 0' }} />

        <div>
          <h4 style={{ marginBottom: 8 }}>Select a Test</h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            <select value={addTestSelect} onChange={e => onChangeAddTest(e.target.value)}>
              <option value="">Select a test</option>
              {Object.keys(availableTests).map(name => (
                <option key={name} value={name}>{name} ({availableTests[name]})</option>
              ))}
            </select>
            <button onClick={onAddTest} disabled={!addTestSelect}>Add Test</button>
          </div>
        </div>

        <div>
          <button onClick={onToggleSymptoms}>{showSymptoms ? 'Hide' : 'Show'} Symptoms</button>
          {showSymptoms && (
            <div style={{ marginTop: 8 }}>
              <div>
                <b>Identified:</b>
                <div style={{ fontSize: 13, color: '#333' }}>{currentSymptoms.length ? currentSymptoms.sort().join(', ') : 'None'}</div>
              </div>
              <div style={{ marginTop: 8 }}>
                <b>Removed:</b>
                <div style={{ fontSize: 13, color: '#333' }}>{symptomsRemoved.length ? Array.from(new Set(symptomsRemoved)).sort().join(', ') : 'None'}</div>
              </div>
            </div>
          )}
        </div>

        {bottomSlot && (
          <div style={{ marginTop: 'auto' }}>
            {bottomSlot}
          </div>
        )}
      </div>
    </div>
  )
}

export default Sidebar



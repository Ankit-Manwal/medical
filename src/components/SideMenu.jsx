import React from 'react'

function SideMenu({
  availableTests = {},
  addTestSelect = '',
  onChangeAddTest,
  onAddTest,
  showSymptoms = false,
  onToggleSymptoms,
  currentSymptoms = [],
  symptomsRemoved = []
}) {
  return (
    <div style={{ borderRight: '1px solid #ddd', paddingRight: 12 }}>
      <h4>Tests</h4>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        <select value={addTestSelect} onChange={e => onChangeAddTest(e.target.value)}>
          <option value="">Select a test</option>
          {Object.keys(availableTests).map(name => (
            <option key={name} value={name}>{name} ({availableTests[name]})</option>
          ))}
        </select>
        <button onClick={onAddTest} disabled={!addTestSelect}>Add Test</button>
      </div>

      <div style={{ marginTop: 16 }}>
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
    </div>
  )
}

export default SideMenu



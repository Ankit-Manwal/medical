import React, { useState } from 'react'

function TestPanel({
  activeTest,
  availableTests = {},
  userTests = [],
  recommendedTests = [],
  testDone = {},
  onSelectTest,
  children,
  headerExtra
}) {
  const [collapsed, setCollapsed] = useState(false)
  if (!activeTest) return null
  return (
    <div className="card-panel sticky" style={{ marginBottom: 12 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12 }}>
        <h3 style={{ margin: 0 }}>Test Panel • {activeTest} ({availableTests[activeTest]})</h3>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          {headerExtra}
          <button onClick={() => setCollapsed(c => !c)} style={{ background: '#fff', color: '#0f172a', borderColor: 'var(--border)' }}>
            {collapsed ? 'Expand' : 'Collapse'}
          </button>
        </div>
      </div>

      {!collapsed && (
        <div style={{ marginTop: 12 }}>
          {children}
        </div>
      )}
    </div>
  )
}

export default TestPanel



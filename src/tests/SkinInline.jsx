import React, { useState } from 'react'

function SkinInline({ name, onDone }) {
  const [file, setFile] = useState(null)
  const [loading, setLoading] = useState(false)

  const run = async () => {
    if (!file) { alert('Please select an image'); return }
    setLoading(true)
    try {
      const formData = new FormData()
      formData.append('file', file)
      const res = await fetch('/api/skin/predict', { method: 'POST', body: formData })
      const data = await res.json()
      if (data && data.predicted_class) onDone(data)
      else onDone({ error: 'Failed to get test result' })
    } catch (e) {
      onDone({ error: String(e) })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ marginTop: 8 }}>
      <h4>{name} Image Upload</h4>
      <input type="file" accept="image/*" onChange={e => setFile(e.target.files?.[0] ?? null)} />
      <div style={{ marginTop: 8 }}>
        <button onClick={run} disabled={!file || loading}>{loading ? 'Analyzing...' : `Run ${name} Test`}</button>
      </div>
    </div>
  )
}

export default SkinInline



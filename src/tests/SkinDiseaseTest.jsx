import React, { useState } from 'react'

function SkinDiseaseTest({ name='Skin Disease', onDone }) {
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
      if (onDone) onDone(data)
    } catch (e) {
      if (onDone) onDone({ error: String(e) })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="card-panel">
      <h4 style={{ marginBottom: 8 }}>{name} Image Upload</h4>
      <input type="file" accept="image/*" onChange={e => setFile(e.target.files?.[0] ?? null)} />
      <div style={{ marginTop: 8 }}>
        <button onClick={run} disabled={!file || loading}>{loading ? 'Analyzing...' : `Run ${name} Test`}</button>
      </div>
    </div>
  )
}

export default SkinDiseaseTest



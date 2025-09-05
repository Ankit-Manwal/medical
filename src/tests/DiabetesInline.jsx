import React, { useState } from 'react'

function DiabetesInline({ name, onDone }) {
  const [form, setForm] = useState({
    pregnancies: 0, glucose: 0, blood_pressure: 0, skin_thickness: 0,
    insulin: 0, bmi: 0, diabetes_pedigree_function: 0, age: 0,
  })
  const [loading, setLoading] = useState(false)

  const setField = (k, v) => setForm(prev => ({ ...prev, [k]: v }))

  const run = async () => {
    if ([form.glucose, form.blood_pressure, form.skin_thickness, form.insulin, form.bmi, form.diabetes_pedigree_function, form.age].every(v => Number(v) === 0)) {
      alert('Please enter valid parameters (all values cannot be 0)')
      return
    }
    setLoading(true)
    try {
      const res = await fetch('/api/diabetes/predict', {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(form)
      })
      const data = await res.json()
      if (data && data.predicted_class) {
        onDone(data)
      } else {
        onDone({ error: 'Failed to get test result' })
      }
    } catch (e) {
      onDone({ error: String(e) })
    } finally {
      setLoading(false)
    }
  }

  const NumberInput = ({ label, field }) => (
    <div style={{ display: 'flex', flexDirection: 'column', marginBottom: 8 }}>
      <label>{label}</label>
      <input type="number" value={form[field]} onChange={e => setField(field, Number(e.target.value))} />
    </div>
  )

  return (
    <div style={{ marginTop: 8 }}>
      <h4>{name} Test Parameters</h4>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
        <NumberInput label="Pregnancies" field="pregnancies" />
        <NumberInput label="Glucose" field="glucose" />
        <NumberInput label="Blood Pressure" field="blood_pressure" />
        <NumberInput label="Skin Thickness" field="skin_thickness" />
        <NumberInput label="Insulin" field="insulin" />
        <NumberInput label="BMI" field="bmi" />
        <NumberInput label="Diabetes Pedigree Function" field="diabetes_pedigree_function" />
        <NumberInput label="Age" field="age" />
      </div>
      <div style={{ marginTop: 8 }}>
        <button onClick={run} disabled={loading}>{loading ? 'Running...' : `Run ${name} Test`}</button>
      </div>
    </div>
  )
}

export default DiabetesInline



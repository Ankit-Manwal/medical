import { useState, useEffect } from 'react'
import './App.css'
import Sidebar from './components/Sidebar'
import TestPanel from './components/TestPanel'
import ChatWindow from './components/ChatWindow'
import SettingsPanel from './components/SettingsPanel'
import DiabetesTest from './tests/DiabetesTest'
import SkinDiseaseTest from './tests/SkinDiseaseTest'

function App() {
  const [activeTab, setActiveTab] = useState('general')

  return (
    <div style={{ padding: 24 }}>
      <h1 style={{ marginBottom: 8 }}>Medical Condition Detector</h1>
      <p style={{ marginBottom: 16 }}>AI-assisted symptom analysis and specific tests</p>
      {activeTab === 'general' && <GeneralPredictor onNavigate={setActiveTab} />}
    </div>
  )
}

function GeneralPredictor({ onNavigate }) {
  // Conversation state
  const [chat, setChat] = useState([]) // {type:'user'|'assistant'|'prediction'|'test', content:string}
  const [userInput, setUserInput] = useState('')
  const [loading, setLoading] = useState(false)

  // Symptom management
  const [currentSymptoms, setCurrentSymptoms] = useState([]) // array of strings
  const [symptomsRemoved, setSymptomsRemoved] = useState([]) // array of strings

  // Follow-up questions
  const [followUps, setFollowUps] = useState([]) // [{question, symptoms:[]}]
  const [analysisRunning, setAnalysisRunning] = useState(false)
  const [analysisIteration, setAnalysisIteration] = useState(0)
  const [targetConfidence, setTargetConfidence] = useState(80) // percent
  const [maxIterations, setMaxIterations] = useState(5)

  // LLM processing is handled internally in sendToLLM and processLLMData functions

  // Tests
  const [availableTests, setAvailableTests] = useState({}) // { diseaseName: modelName }
  const [userTests, setUserTests] = useState([]) // tests explicitly asked by user
  const [recommendedTests, setRecommendedTests] = useState([]) // tests we recommend
  const [activeTest, setActiveTest] = useState(null) // which test panel is open
  const [testDone, setTestDone] = useState({}) // { testName: true if done at least once }
  const [testResults, setTestResults] = useState({}) // { testName: result }

  // UI toggles
  const [showSymptoms, setShowSymptoms] = useState(false)
  const [addTestSelect, setAddTestSelect] = useState('')

  // skip follow-ups
  const [skipped_follow, setSkipped_follow] = useState(false)
  

  // Load available tests on mount
  useEffect(() => {
    (async () => {
      try {
        const res = await fetch('/api/tests/available')
        const data = await res.json()
        setAvailableTests(data.available_tests || {})
      } catch (e) {
        console.error(e)
      }
    })()
  }, [])



  const sendToLLM = async () => {
    const message = userInput.trim()
    if (!message) return
    setLoading(true)
    try {
      setChat(prev => [...prev, { type: 'user', content: message }])
      const res = await fetch('/api/llm/parse', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message })
      })
      const data = await res.json()
      if (data.error) throw new Error(data.error)
      console.log("\n", data)
      processLLMData(data)
    } 
    catch (e) {
      console.error(e)
      setChat(prev => [...prev, { type: 'assistant', content: 'I had trouble understanding. Please try again.' }])
    } 
    finally {
      setUserInput('')
      setLoading(false)
    }
  }
  // # {
  //   #   "raw": {
  //   #     "symptoms_to_add": "high_fever",
  //   #     "symptoms_to_removed": "",
  //   #     "specific_tests_to_run": "",
  //   #     "specific_diseases_detail": "",
  //   #     "invalid_input": ""
  //   #   },
  //   #   "normalized": {
  //   #     "symptoms_to_add": ["high_fever"],
  //   #     "symptoms_to_removed": [],
  //   #     "specific_tests_to_run": [],
  //   #     "specific_diseases_detail": [],
  //   #     "invalid_input": "",
  //   #   }
  //   # }
    


  const mapSuggestedTests = (requested_tests=[]) => {
    const mapped = []
    for (const name of requested_tests) {
      if (availableTests[name]) mapped.push(name)
    }
    if (mapped.length) {
      // user explicitly asked
      setUserTests(prev => Array.from(new Set([...(prev || []), ...mapped])))
      setChat(prev => [...prev, { type: 'assistant', content: 'Recommended tests based on your input:\n' + mapped.map(t => `- ${t}`).join('\n') }])
    } else {
      setChat(prev => [...prev, { type: 'assistant', content: 'No specific tests available for your input.' }])
    }
  }

  // Handles normalized LLM data (symptoms add/remove + chat update)
  const processLLMData = (data) => {
    if (!data || !data.normalized) return

    const { symptoms_to_add = [], symptoms_to_removed = [] } = data.normalized

    // Update symptoms using your central update function and get updated symptoms
    const updatedSymptoms = updateSymptoms(symptoms_to_add, symptoms_to_removed)

    // Build assistant response
    const parts = []
    if (symptoms_to_add.length) {
      parts.push(`I recognized these new symptoms: ${symptoms_to_add.join(', ')}`)
    }
    if (symptoms_to_removed.length) {
      parts.push(`You indicated you do not have: ${symptoms_to_removed.join(', ')}`)
    }
    
    parts.push(
      `Current symptoms: ${updatedSymptoms.length ? updatedSymptoms.sort().join(', ') : 'None'}`
    )

    // Add to chat if anything meaningful changed
    if (symptoms_to_add.length || symptoms_to_removed.length) {
      setChat(prev => [...prev, { type: 'assistant', content: parts.join('\n') }])
    }
    if ((data.normalized.specific_tests_to_run || []).length > 0) {
      mapSuggestedTests(data.normalized.specific_tests_to_run)
    }
  }



  const updateSymptoms = (symptomsToAdd = [], symptomsToRemove = []) => {

    console.log("\n\nUpdating symptoms. To add:", symptomsToAdd, "To remove:", symptomsToRemove,"\n\n")
    // Create sets for efficient updates
    const addSet = new Set(currentSymptoms)
    symptomsToAdd.forEach(s => addSet.add(s))

    const removeSet = new Set(symptomsRemoved)
    symptomsToRemove.forEach(s => removeSet.add(s))

    // Build next current symptoms list (exclude removed)
    const nextCurrent = [...addSet].filter(s => !removeSet.has(s))

    // Update state
    setCurrentSymptoms(nextCurrent)
    setSymptomsRemoved([...removeSet])
    
    // Return the updated symptoms for immediate use
    return nextCurrent
  }

  // Helper function to get current symptoms including removed ones
  const getAllSymptoms = () => {
    return {
      current: currentSymptoms,
      removed: symptomsRemoved,
      all: [...new Set([...currentSymptoms, ...symptomsRemoved])]
    }
  }

  // Reset function that uses updateSymptoms for consistency
  const resetAll = () => {
    console.log("\nResetting all state to initial.\n")
    setChat([])
    setCurrentSymptoms([])
    setSymptomsRemoved([])
    setFollowUps([])
    setUserTests([])
    setRecommendedTests([])
    setActiveTest(null)
    setTestDone({})
    setTestResults({})
    setAnalysisRunning(false)
    setAnalysisIteration(0)
    setSkipped_follow(false)
  }


  
  // const applySymptoms = () => {
  //   if (!llm) return
  //   const { symptoms_to_add, symptoms_to_removed } = llm
  //   const addSet = new Set(currentSymptoms)
  //   for (const s of symptoms_to_add || []) addSet.add(s)
  //   const removeSet = new Set(symptomsRemoved)
  //   for (const s of symptoms_to_removed || []) removeSet.add(s)
  //   // Remove from current if marked removed
  //   const nextCurrent = [...addSet].filter(s => !removeSet.has(s))
  //   setCurrentSymptoms(nextCurrent)
  //   setSymptomsRemoved([...removeSet])
  //   const parts = []
  //   if (symptoms_to_add?.length) parts.push(`I recognized these new symptoms: ${symptoms_to_add.join(', ')}`)
  //   if (symptoms_to_removed?.length) parts.push(`You indicated you do not have: ${symptoms_to_removed.join(', ')}`)
  //   parts.push(`Current symptoms: ${nextCurrent.length ? nextCurrent.sort().join(', ') : 'None'}`)
  //   setChat(prev => [...prev, { type: 'assistant', content: parts.join('\n') }])
  //   // Prepare follow-up
  //   setLlm(null)
  //   setAnalysisIteration(0)
  //   setAnalysisRunning(true)
  //   generateFollowUps(nextCurrent, [...removeSet])
  // }


  const startSymptomsAnalysis = () => {
    // if (!llm) return
    // const { symptoms_to_add, symptoms_to_removed } = llm
    // if (symptoms_to_add.length || symptoms_to_removed.length) {
    //   updateSymptoms(symptoms_to_add, symptoms_to_removed)
    // }
    console.log("\n\nStarting symptom analysis with current symptoms:", currentSymptoms, "and removed symptoms:", symptomsRemoved,"\n\n")
    setAnalysisIteration(0)
    setAnalysisRunning(true)
    SymptomsAnalysis_checkpoint(true) // Pass true to indicate analysis should be running
  }

 const getTopConfidence = async (curr) => {
  console.log("\n\nGetting topooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooo confidence for symptoms:", curr,"\n")
    try {
      const res = await fetch('/api/general/top_predictions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ symptoms: curr.join(' ') })
      })
      const data = await res.json()
      const preds = data.predictions || []
      console.log("\nTop predictions received from API:", preds,"\n")
      
      if (!Array.isArray(preds) || preds.length === 0) return []
      
      // Return the full predictions array with normalized confidence scores
      return preds.map(pred => ({
        disease: pred.disease,
        confidence: Number(pred.confidence || pred.confidence_score || 0) <= 1 
          ? Number(pred.confidence || pred.confidence_score || 0) * 100 
          : Number(pred.confidence || pred.confidence_score || 0)
      }))
    } catch (e) {
      console.error(e)
      return []
    }
  }
//   [
//     {"disease": "Flu", "confidence": 0.82},
//     {"disease": "Common Cold", "confidence": 0.10},
//     {"disease": "COVID-19", "confidence": 0.05}
// ]


  const getDiseaseDetails = async (diseases=[]) => {
    if (!diseases.length) return []
    try {
      const res = await fetch('/api/general/disease_info', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ diseases })   // ✅ send list, not symptoms
      })

      const data = await res.json()
      const results = data.results || []
      console.log("\nDisease details fetched:", results,"\n")

      return results
    } catch (e) {
      console.error(e)
      return []
    }
  }

// {
//   "results": [
//     {
//       "disease": "Flu",
//       "description": "Flu is a viral infection...",
//       "recommendations": ["Rest", "Drink fluids", "Consult a doctor"]
//     },
//     {
//       "disease": "Diabetes",
//       "description": "A condition with high sugar levels.",
//       "recommendations": ["Exercise daily", "Monitor blood sugar"]
//     }
//   ],
//   "suggested_tests": [
//     {
//       "disease": "Flu",
//       "model": "flu_test_model",
//       "test_name": "Flu"
//     },
//     {
//       "disease": "Diabetes",
//       "model": "diabetes_test_model",
//       "test_name": "Diabetes"
//     }
//   ]
// }


  
const SymptomsAnalysis_checkpoint = async (forceRunning = false) => {
  setFollowUps([])
  console.log("\nSymptoms analysis checkpoint. Iteration:", analysisIteration, "Current symptoms:", currentSymptoms, "Removed symptoms:", symptomsRemoved,"\n")

  if (!currentSymptoms || currentSymptoms.length === 0) {
    console.log("\nNo current symptoms available. Stopping analysis.\n")
    setAnalysisRunning(false)
    setAnalysisIteration(0)
    return
  }

  try {
    console.log("\nFetching top predictions+++++++++2465455555555555555555 for current symptoms:", currentSymptoms,"\n")
    const topPredictions = await getTopConfidence(currentSymptoms)
    if (!topPredictions || topPredictions.length === 0) {
      setAnalysisRunning(false)
      console.log("\nNo predictions received. Stopping analysis.\n")
      setAnalysisIteration(0)
      return
    }
    console.log("\nTop predictions received:", topPredictions,"\n")

    const topDisease = topPredictions[0]
    const nextIter = analysisIteration + 1
    setAnalysisIteration(nextIter)
    const reachedConfidence = topDisease.confidence >= Number(targetConfidence || 0)
    const reachedIterations = nextIter >= Number(maxIterations || 0)

    // Use forceRunning parameter or current analysisRunning state
    const isAnalysisRunning = forceRunning || analysisRunning

    if (!isAnalysisRunning || reachedConfidence || reachedIterations || skipped_follow) 
    {
      // Get disease details and suggested tests
      const diseaseDetails = await getDiseaseDetails([topDisease.disease])
      const diseaseDetail = diseaseDetails[0] || {}

      console.log("\nFinalizing analysis. Reached confidence:", reachedConfidence, "Reached iterations:", reachedIterations, "Skipped follow-ups:", skipped_follow,"\n")

      // Use the prediction data we already have from getTopConfidence
      if (topDisease) {
        let text = `Final Prediction: ${topDisease.disease}\nConfidence: ${Number(topDisease.confidence).toFixed(1)}%\n`
        
        // Add description and recommendations from disease details
        if (diseaseDetail.description) {
          text += `Description: ${diseaseDetail.description}\n\n`
        }
        if (Array.isArray(diseaseDetail.recommendations) && diseaseDetail.recommendations.length) {
          text += 'Recommen888dations:\n' + diseaseDetail.recommendations.map(x => `• ${x}`).join('\n')
        }
        
        // Check if there's a suggested test for this disease
        if (availableTests[topDisease.disease]) {
          const suggestedTest = {
            disease: topDisease.disease,
            model: availableTests[topDisease.disease],
            test_name: topDisease.disease
          }
          text += `\n\nSpecific Test Availahhble: ${suggestedTest.model} for ${suggestedTest.disease}`
          // add to recommended tests list
          setRecommendedTests(prev => Array.from(new Set([...(prev || []), suggestedTest.test_name])))
        }
        console.log("\nPrediction details added to chat:", text,"\n")

        setChat(prev => [...prev, { type: 'prediction', content: text }])
        
      }
      // #check due to which condition we are exiting
      if (!isAnalysisRunning || reachedConfidence || reachedIterations || skipped_follow) 
        console.log("\nExiting analysis loop. Reason - Analysis running:", !isAnalysisRunning, "Reached confidence:", reachedConfidence, "Reached iterations:", reachedIterations, "Skipped follow-ups:", skipped_follow,"\n")

      setAnalysisIteration(0)
      setAnalysisRunning(false)
      setSkipped_follow(false)
    } 
    else {
      generateFollowUps(currentSymptoms, [...symptomsRemoved])
    }
  }
  catch (e) {
    console.error(e)
    setAnalysisRunning(false)
    setAnalysisIteration(0)
  }
}









  // {
  //   "current_symptoms": ["fever", "cough"],
  //   "symptoms_removed": ["headache"],
  //   "max_per_disease": 3,
  //   "max_total": 10
  // }  
  const generateFollowUps = async (curr, removed) => {
    console.log("\nGenerating follow-ups for current symptoms:", curr, "and removed symptoms:", removed,"\n")
    try {
      const res = await fetch('/api/general/followup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ current_symptoms: curr, symptoms_removed: removed, max_per_disease: 3, max_total: 10 })
      })
      const data = await res.json()
      setFollowUps(data.follow_up_questions || [])
      console.log("\nFollow-up questions received:", data.follow_up_questions || [],"\n")
    } 
    catch (e) {
      console.error(e)
      setFollowUps([])
    }
  }
//   [
//     {
//         "disease": "Flu",
//         "symptoms": ["muscle pain", "chills"],
//         "question": "For Flu (confidence: 0.82%), do you have: muscle pain, chills?",
//         "confidence": 0.82
//     },
//     ...
// ]






  const submitFollowUps = async (responses) => {
    // responses: { [symptom]: boolean }
    const toAdd = []
    const toRemove = []
    console.log("\nSubmitting follow-up responses:", responses,"\n")
    for (const [symptom, checked] of Object.entries(responses)) {
      if (checked) toAdd.push(symptom)
      else toRemove.push(symptom)
    }
    
    // Update symptoms using the central function and get updated symptoms
    const updatedSymptoms = updateSymptoms(toAdd, toRemove)
    console.log("\nUpdated symptoms after follow-ups. To add:", toAdd, "To remove:", toRemove, "Resulting symptoms:", updatedSymptoms,"\n")

    if (toAdd.length || toRemove.length) {
      setChat(prev => [
        ...prev,
        { type: 'user', content: `Additional symptoms: ${toAdd.join(', ')}\nRemoved symptoms: ${toRemove.join(', ')}\nCurrent symptoms: ${updatedSymptoms.sort().join(', ')}` }
      ])
    }
    SymptomsAnalysis_checkpoint(false) // Continue analysis with current state
  }



  
  const skipFollowUps = () => {
    console.log("\nSkipping follow-up questions as per user request.\n")
    setSkipped_follow(true)
    SymptomsAnalysis_checkpoint(false) // Continue analysis with current state
  }

  



  const onTestCompleted = (name, result, sourceLabel) => {
    setTestDone(prev => ({ ...prev, [name]: true }))
    setTestResults(prev => ({ ...prev, [name]: result }))
    // Post to chat
    if (result) {
      const confidence = Number(result.confidence || 0)
      const confidencePercent = confidence <= 1 ? (confidence * 100).toFixed(5) : confidence.toFixed(1)
      const content = `(${sourceLabel}) ${name} Test Result:\n• Prediction: ${result.predicted_class ?? 'Unknown'}\n• Confidence: ${confidencePercent}%\n• Status: Completed`
      setChat(prev => [...prev, { type: 'test', content }])
    }
  }

  return (
    <div>
      <div style={{ display: 'grid', gridTemplateColumns: '260px 1fr', gap: 16, alignItems: 'start' }}>
        <Sidebar
          activeTab={'general'}
          onNavigate={onNavigate}
          availableTests={availableTests}
          addTestSelect={addTestSelect}
          onChangeAddTest={(val) => setAddTestSelect(val)}
          onAddTest={() => { if (addTestSelect) { setUserTests(prev => Array.from(new Set([...(prev || []), addTestSelect]))); setAddTestSelect(''); setActiveTest(addTestSelect) } }}
          showSymptoms={showSymptoms}
          onToggleSymptoms={() => setShowSymptoms(s => !s)}
          currentSymptoms={currentSymptoms}
          symptomsRemoved={symptomsRemoved}
          bottomSlot={(
            <SettingsPanel
              targetConfidence={targetConfidence}
              maxIterations={maxIterations}
              onChangeConfidence={setTargetConfidence}
              onChangeIterations={setMaxIterations}
            />
          )}
        />

                <div>
          <TestPanel
            activeTest={activeTest}
            availableTests={availableTests}
            userTests={userTests}
            recommendedTests={recommendedTests}
            testDone={testDone}
            onSelectTest={setActiveTest}
            headerExtra={activeTest && testResults[activeTest] ? (
              <div style={{ fontSize: 13, color: '#333' }}>
                <b>Last Result:</b> {testResults[activeTest]?.predicted_class ?? '—'} ({(() => {
                  const c = Number(testResults[activeTest]?.confidence || 0)
                  return c <= 1 ? (c * 100).toFixed(1) : c.toFixed(1)
                })()}%)
                </div>
            ) : null}
          >
            {activeTest && availableTests[activeTest] === 'Diabetes' && (
              <DiabetesTest name={activeTest} onDone={(res) => onTestCompleted(activeTest, res, (userTests||[]).includes(activeTest) ? 'User-asked' : 'Recommended')} />
            )}
            {activeTest && availableTests[activeTest] === 'Skin Diseases' && (
              <SkinDiseaseTest name={activeTest} onDone={(res) => onTestCompleted(activeTest, res, (userTests||[]).includes(activeTest) ? 'User-asked' : 'Recommended')} />
            )}
            {activeTest && testResults[activeTest] && (
              <div style={{ marginTop: 8, background: '#f9f9f9', padding: 8, borderRadius: 6 }}>
                <div><b>Prediction:</b> {testResults[activeTest].predicted_class ?? 'Unknown'}</div>
                <div><b>Confidence:</b> {(() => { const c = Number(testResults[activeTest].confidence || 0); return c <= 1 ? (c * 100).toFixed(1) : c.toFixed(1) })()}%</div>
              </div>
            )}
          </TestPanel>

          <div className="card-panel" style={{ marginBottom: 12 }}>
      <textarea rows={3} style={{ width: '100%' }} placeholder="Describe your symptoms..."
        value={userInput} onChange={e => setUserInput(e.target.value)} />
      <div style={{ marginTop: 8, display: 'flex', gap: 8 }}>
        <button onClick={sendToLLM} disabled={!userInput.trim() || loading}>{loading ? 'Analyzing...' : 'Send'}</button>
              <button onClick={resetAll} style={{ background: '#fff', color: '#0f172a', borderColor: 'var(--border)' }}>Start New</button>
        {analysisRunning && (
                <div style={{ fontSize: 12, color: '#555', marginLeft: 'auto' }}>Analysis running • Iteration {analysisIteration + 1}</div>
        )}
      </div>
          </div>

          {chat.length > 0 && (
            <div style={{ marginTop: 12 }}>
              <ChatWindow chat={chat} />
        </div>
      )}
      
      {currentSymptoms?.length > 0 && (
        <div style={{ marginTop: 16 }}>
          <h3>Available Actions</h3>
          <div style={{ display: 'flex', gap: 12 }}>
            <button onClick={startSymptomsAnalysis}>Start Symptom Analysis</button>
                <button onClick={skipFollowUps} style={{ background: '#fff', color: '#0f172a', borderColor: 'var(--border)' }}>Skip Follow-up Questions</button>
          </div>
        </div>
      )}

      {followUps.length > 0 && (
        <FollowUpsUI followUps={followUps} onSubmit={submitFollowUps} onSkip={skipFollowUps} />
      )}
        </div>
      </div>
    </div>
  )
}

function FollowUpsUI({ followUps, onSubmit, onSkip }) {
  const [responses, setResponses] = useState({})
  const toggle = (sym, checked) => setResponses(prev => ({ ...prev, [sym]: checked }))
  return (
    <div style={{ marginTop: 16 }}>
      <h3>Follow-up Questions</h3>
      {followUps.map((q, i) => (
        <div key={i} style={{ marginBottom: 12 }}>
          <b>{q.question}</b>
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            {(q.symptoms || []).map((s) => (
              <label key={s} style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                <input type="checkbox" checked={Boolean(responses[s])} onChange={e => toggle(s, e.target.checked)} />
                Yes, I have {s}
              </label>
            ))}
          </div>
          <hr />
        </div>
      ))}
      <div style={{ display: 'flex', gap: 12 }}>
        <button onClick={() => onSubmit(responses)}>Submit Follow-up Responses</button>
        <button onClick={onSkip}>Skip Follow-up Questions</button>
      </div>
    </div>
  )
}
export default App

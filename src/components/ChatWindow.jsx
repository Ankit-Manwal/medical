import React from 'react'

function ChatMessage({ type, content }) {
  const isUser = type === 'user'
  const isPrediction = type === 'prediction' || type === 'test'
  return (
    <div style={{ display: 'flex', justifyContent: isUser ? 'flex-end' : 'flex-start' }}>
      <div
        className="card-panel"
        style={{
          maxWidth: 740,
          background: isUser ? '#e0f2fe' : '#fff',
          borderColor: isUser ? '#bae6fd' : 'var(--border)',
          borderRadius: 16,
          padding: 12,
          boxShadow: isPrediction ? '0 2px 10px rgba(2,6,23,.06)' : undefined,
        }}
      >
        <b style={{ color: '#0f172a' }}>
          {isUser ? 'You' : isPrediction ? (type === 'test' ? 'Test Result' : 'Prediction') : 'Assistant'}:
        </b>
        <div style={{ whiteSpace: 'pre-wrap', marginTop: 6 }}>{content}</div>
      </div>
    </div>
  )
}

function ChatWindow({ chat = [] }) {
  return (
    <div className="card-panel" style={{ background: '#fff' }}>
      <h3>Conversation</h3>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 10, maxHeight: 520, overflow: 'auto', paddingRight: 4 }}>
        {chat.map((m, i) => (
          <ChatMessage key={i} type={m.type} content={m.content} />
        ))}
      </div>
    </div>
  )
}

export default ChatWindow



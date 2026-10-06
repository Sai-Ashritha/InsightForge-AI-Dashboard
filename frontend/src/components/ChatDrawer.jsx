import { Bot, Send, Sparkles, Cpu } from 'lucide-react'

const PROMPT_SUGGESTIONS = [
  'Summarize this dataset',
  'Which fields show a trend?',
  'What anomalies were detected?',
  'What actions does the data support?',
]

function ChatDrawer({
  messages = [],
  input = '',
  loading = false,
  provider = '',
  onInputChange,
  onSendMessage,
  onSend,
  onSelectPrompt,
  kpis,
}) {
  const sendHandler = onSendMessage || onSend

  const handleSendClick = (queryToSend = input) => {
    if (sendHandler) {
      sendHandler(queryToSend)
    }
  }

  const handlePromptClick = (suggestion) => {
    if (onSelectPrompt) {
      onSelectPrompt(suggestion)
    } else if (onInputChange) {
      onInputChange(suggestion)
      if (sendHandler) {
        sendHandler(suggestion)
      }
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      if (input.trim() && !loading) {
        handleSendClick(input)
      }
    }
  }

  return (
    <section className="panel chatbot-panel glass-panel" aria-label="Ask AI assistant">
      <div className="panel-heading-row">
        <div className="chat-title-group">
          <div className="ai-badge-icon">
            <Bot size={18} aria-hidden="true" />
          </div>
          <div>
            <p className="section-kicker">Operational Intelligence</p>
            <h3>InsightForge AI Assistant</h3>
          </div>
        </div>
        {provider && (
          <span className="provider-pill">
            <Cpu size={12} /> {provider === 'ollama' ? 'Ollama Llama-3.2' : provider === 'gemini' ? 'Gemini 1.5 Pro' : 'InsightForge Engine'}
          </span>
        )}
      </div>

      <div className="prompt-suggestions-row">
        <span className="suggestions-label">
          <Sparkles size={13} /> Quick questions:
        </span>
        <div className="suggestions-list">
          {PROMPT_SUGGESTIONS.map((suggestion, idx) => (
            <button
              key={idx}
              type="button"
              className="suggestion-chip"
              onClick={() => handlePromptClick(suggestion)}
              disabled={loading}
            >
              {suggestion}
            </button>
          ))}
        </div>
      </div>

      <div className="chat-container">
        <div className="chat-messages">
          {messages.length === 0 ? (
            <div className="chat-welcome glass-card">
              <p className="welcome-headline">InsightForge AI Analyst</p>
              <p className="welcome-body">
                I analyze the columns in your uploaded dataset and report only findings supported by its data.
              </p>
              <p className="welcome-cta">
                Choose a question above or ask for a summary, trend, anomaly, or recommendation.
              </p>
            </div>
          ) : (
            messages.map((message, index) => (
              <div className={`chat-message ${message.role}`} key={`${message.role}-${index}`}>
                <div className="chat-avatar">
                  {message.role === 'user' ? '👤' : '🤖'}
                </div>
                <div className="chat-content-box">
                  <span className="chat-role">
                    {message.role === 'user' ? 'You' : 'InsightForge AI Advisor'}
                  </span>
                  <div className="chat-text">
                    {message.content.split('\n').map((paragraph, pIdx) => {
                      if (!paragraph.trim()) return <br key={pIdx} />
                      // Simple render bold markdown
                      const parts = paragraph.split(/(\*\*.*?\*\*)/g)
                      return (
                        <p key={pIdx} className="chat-paragraph">
                          {parts.map((part, partIdx) => {
                            if (part.startsWith('**') && part.endsWith('**')) {
                              return <strong key={partIdx}>{part.slice(2, -2)}</strong>
                            }
                            return part
                          })}
                        </p>
                      )
                    })}
                  </div>
                </div>
              </div>
            ))
          )}
          {loading && (
            <div className="chat-message ai streaming">
              <div className="chat-avatar">🤖</div>
              <div className="chat-content-box">
                <span className="chat-role">InsightForge AI Advisor</span>
                <p className="thinking-indicator">
                  <span className="dot" />
                  <span className="dot" />
                  <span className="dot" />
                  <span>Synthesizing operational context & ML models...</span>
                </p>
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="chat-input-box">
        <input
          value={input}
          onChange={(e) => onInputChange(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask about the uploaded dataset..."
          disabled={loading}
          aria-label="Ask a question"
        />
        <button
          type="button"
          onClick={onSend}
          disabled={loading || !input.trim()}
          aria-label="Send question"
          className="send-button"
        >
          <Send size={15} aria-hidden="true" />
          <span>Send</span>
        </button>
      </div>
    </section>
  )
}

export default ChatDrawer

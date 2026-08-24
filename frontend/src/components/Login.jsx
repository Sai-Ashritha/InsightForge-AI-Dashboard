import { useState } from 'react'
import { LogIn, UserPlus, ShieldCheck, Factory, KeyRound, Mail, Sparkles } from 'lucide-react'

function Login({ email, password, message, loading, onEmailChange, onPasswordChange, onSignIn, onRegister, isStepScreen = true }) {
  const [isRegisterMode, setIsRegisterMode] = useState(false)

  const handleQuickDemo = () => {
    onEmailChange('analyst@insightforge.ai')
    onPasswordChange('Project@123')
  }

  const handleSubmit = (e) => {
    e?.preventDefault()
    if (isRegisterMode) {
      onRegister()
    } else {
      onSignIn()
    }
  }

  if (!isStepScreen) {
    return (
      <div className="auth-inline-box">
        <input aria-label="Email" type="email" placeholder="Email" value={email} onChange={(e) => onEmailChange(e.target.value)} />
        <input aria-label="Password" type="password" placeholder="Password" value={password} onChange={(e) => onPasswordChange(e.target.value)} />
        <button className="auth-button" onClick={onSignIn} disabled={loading}>
          <LogIn size={14} aria-hidden="true" /> Sign in
        </button>
        <button className="auth-link" onClick={onRegister} disabled={loading}>
          <UserPlus size={14} aria-hidden="true" /> Register
        </button>
        {message && <span className="auth-message">{message}</span>}
      </div>
    )
  }

  return (
    <div className="login-step-container">
      <div className="login-card glass-panel">
        <div className="login-header">
          <div className="brand-badge">
            <Factory size={26} className="brand-icon" />
          </div>
          <h2>InsightForge AI</h2>
          <p className="login-subtitle">Predictive Manufacturing Intelligence Platform</p>
          <div className="step-indicator-pill">
            <ShieldCheck size={12} /> Secure Access Portal
          </div>
        </div>

        <div className="auth-mode-tabs">
          <button
            type="button"
            className={`auth-tab ${!isRegisterMode ? 'active' : ''}`}
            onClick={() => setIsRegisterMode(false)}
          >
            <LogIn size={16} /> Sign In
          </button>
          <button
            type="button"
            className={`auth-tab ${isRegisterMode ? 'active' : ''}`}
            onClick={() => setIsRegisterMode(true)}
          >
            <UserPlus size={16} /> Create Account
          </button>
        </div>

        <form onSubmit={handleSubmit} className="auth-form">
          <div className="input-group">
            <label htmlFor="auth-email">
              <Mail size={15} /> Work Email
            </label>
            <input
              id="auth-email"
              type="email"
              placeholder="e.g. analyst@insightforge.ai"
              value={email}
              onChange={(e) => onEmailChange(e.target.value)}
              required
              autoFocus
            />
          </div>

          <div className="input-group">
            <label htmlFor="auth-password">
              <KeyRound size={15} /> Password
            </label>
            <input
              id="auth-password"
              type="password"
              placeholder="••••••••••••"
              value={password}
              onChange={(e) => onPasswordChange(e.target.value)}
              required
            />
          </div>

          {message && (
            <div className={`auth-alert ${message.toLowerCase().includes('success') || message.toLowerCase().includes('created') ? 'success' : 'error'}`}>
              <span>{message}</span>
            </div>
          )}

          <button type="submit" className="auth-submit-btn" disabled={loading}>
            {loading ? (
              <span className="spinner-label">Authenticating...</span>
            ) : isRegisterMode ? (
              <>
                <UserPlus size={18} /> Register & Continue
              </>
            ) : (
              <>
                <LogIn size={18} /> Sign In with JWT
              </>
            )}
          </button>

          <div className="demo-credentials-box">
            <div className="demo-header">
              <Sparkles size={14} className="sparkle-icon" />
              <span>Quick Test Credentials</span>
            </div>
            <button
              type="button"
              className="quick-fill-btn"
              onClick={handleQuickDemo}
            >
              Fill Demo Credentials (analyst@insightforge.ai)
            </button>
          </div>

          <div className="auth-footer-security">
            <ShieldCheck size={14} />
            <span>Secured with JWT authentication & SQLAlchemy ORM</span>
          </div>
        </form>
      </div>
    </div>
  )
}

export default Login

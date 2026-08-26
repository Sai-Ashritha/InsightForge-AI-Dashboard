import { useState, useRef, useEffect } from 'react'
import {
  KeyRound,
  Mail,
  ArrowRight,
  ShieldCheck,
  Lock,
  ArrowLeft,
  CheckCircle2,
  Sparkles,
} from 'lucide-react'

function ForgotPassword({ onBackToLogin, onResetSuccess, API_BASE }) {
  const [step, setStep] = useState('request') // 'request' | 'reset' | 'success'
  const [email, setEmail] = useState('')
  const [digits, setDigits] = useState(['', '', '', '', '', ''])
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [infoMessage, setInfoMessage] = useState('')

  const inputRefs = useRef([])

  // Auto-focus first input when entering 'reset' step
  useEffect(() => {
    if (step === 'reset') {
      inputRefs.current[0]?.focus()
    }
  }, [step])

  const handleRequestOTP = async (e) => {
    e?.preventDefault()
    if (!email.trim()) {
      setError('Please enter your work email.')
      return
    }

    setLoading(true)
    setError('')
    setInfoMessage('')

    try {
      const res = await fetch(`${API_BASE}/auth/forgot-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email.trim() }),
      })
      const data = await res.json()

      if (!res.ok) throw new Error(data.detail || 'Failed to send reset code')

      setInfoMessage('Password reset code sent! Please check your email inbox.')
      setStep('reset')
    } catch (err) {
      setError(err.message || 'Unable to process request.')
    } finally {
      setLoading(false)
    }
  }

  const handleDigitChange = (index, value) => {
    if (!/^\d*$/.test(value)) return
    const char = value.slice(-1)
    const newDigits = [...digits]
    newDigits[index] = char
    setDigits(newDigits)
    setError('')

    if (char && index < 5) {
      inputRefs.current[index + 1]?.focus()
    }
  }

  const handleKeyDown = (index, e) => {
    if (e.key === 'Backspace') {
      if (!digits[index] && index > 0) {
        const newDigits = [...digits]
        newDigits[index - 1] = ''
        setDigits(newDigits)
        inputRefs.current[index - 1]?.focus()
      } else {
        const newDigits = [...digits]
        newDigits[index] = ''
        setDigits(newDigits)
      }
    } else if (e.key === 'ArrowLeft' && index > 0) {
      inputRefs.current[index - 1]?.focus()
    } else if (e.key === 'ArrowRight' && index < 5) {
      inputRefs.current[index + 1]?.focus()
    }
  }

  const handlePaste = (e) => {
    e.preventDefault()
    const pastedData = e.clipboardData.getData('text').trim()
    if (/^\d{6}$/.test(pastedData)) {
      setDigits(pastedData.split(''))
      inputRefs.current[5]?.focus()
    }
  }

  const handleResetPassword = async (e) => {
    e?.preventDefault()
    const code = digits.join('')
    if (code.length !== 6) {
      setError('Please enter the full 6-digit reset code.')
      return
    }
    if (!newPassword || newPassword.length < 6) {
      setError('New password must be at least 6 characters.')
      return
    }
    if (newPassword !== confirmPassword) {
      setError('Passwords do not match.')
      return
    }

    setLoading(true)
    setError('')

    try {
      const res = await fetch(`${API_BASE}/auth/reset-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: email.trim(),
          code,
          new_password: newPassword,
          confirm_password: confirmPassword,
        }),
      })
      const data = await res.json()

      if (!res.ok) throw new Error(data.detail || 'Reset failed')

      setStep('success')
    } catch (err) {
      setError(err.message || 'Invalid reset code or password update failed.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-step-container">
      <div className="login-card glass-panel forgot-pw-card">
        {/* Step 1: Enter Email */}
        {step === 'request' && (
          <form onSubmit={handleRequestOTP}>
            <div className="login-header">
              <div className="brand-badge">
                <KeyRound size={26} className="brand-icon" />
              </div>
              <h2>Forgot Password</h2>
              <p className="login-subtitle">
                Enter your work email to receive a 6-digit password reset code.
              </p>
            </div>

            <div className="auth-form" style={{ marginTop: '16px' }}>
              <div className="input-group">
                <label htmlFor="reset-email">
                  <Mail size={15} /> Work Email
                </label>
                <input
                  id="reset-email"
                  type="email"
                  placeholder="analyst@insightforge.ai"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  autoFocus
                />
              </div>

              {error && (
                <div className="auth-alert error">
                  <span>{error}</span>
                </div>
              )}

              <button type="submit" className="auth-submit-btn" disabled={loading}>
                {loading ? (
                  <span className="spinner-label">Sending Reset Code...</span>
                ) : (
                  <>
                    <KeyRound size={17} /> Send Reset Code <ArrowRight size={16} />
                  </>
                )}
              </button>

              <button
                type="button"
                className="otp-link-btn text-muted"
                onClick={onBackToLogin}
                style={{ textAlign: 'center', marginTop: '10px' }}
              >
                <ArrowLeft size={13} /> Back to Sign In
              </button>
            </div>
          </form>
        )}

        {/* Step 2: Enter OTP + New Password */}
        {step === 'reset' && (
          <form onSubmit={handleResetPassword}>
            <div className="login-header">
              <div className="brand-badge">
                <ShieldCheck size={26} className="text-primary-accent" />
              </div>
              <h2>Set New Password</h2>
              <p className="login-subtitle">
                Enter the 6-digit code sent to <strong>{email}</strong>
              </p>
            </div>

            <div className="auth-form" style={{ marginTop: '16px' }}>
              <label style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                6-Digit Reset Code
              </label>
              <div className="otp-inputs-wrapper" onPaste={handlePaste} style={{ marginBottom: '14px' }}>
                {digits.map((digit, idx) => (
                  <input
                    key={idx}
                    ref={(el) => (inputRefs.current[idx] = el)}
                    type="text"
                    inputMode="numeric"
                    maxLength={1}
                    value={digit}
                    onChange={(e) => handleDigitChange(idx, e.target.value)}
                    onKeyDown={(e) => handleKeyDown(idx, e)}
                    className={`otp-digit-input ${digit ? 'filled' : ''}`}
                    disabled={loading}
                    aria-label={`Digit ${idx + 1}`}
                  />
                ))}
              </div>

              <div className="input-group">
                <label htmlFor="new-pw">
                  <Lock size={15} /> New Password
                </label>
                <input
                  id="new-pw"
                  type="password"
                  placeholder="Min 6 characters"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  required
                />
              </div>

              <div className="input-group">
                <label htmlFor="confirm-new-pw">
                  <Lock size={15} /> Confirm New Password
                </label>
                <input
                  id="confirm-new-pw"
                  type="password"
                  placeholder="Re-enter new password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                />
              </div>

              {error && (
                <div className="auth-alert error">
                  <span>{error}</span>
                </div>
              )}
              {infoMessage && (
                <div className="auth-alert success">
                  <span>{infoMessage}</span>
                </div>
              )}

              <button type="submit" className="auth-submit-btn" disabled={loading}>
                {loading ? (
                  <span className="spinner-label">Updating Password...</span>
                ) : (
                  <>
                    <KeyRound size={17} /> Update Password &amp; Sign In
                  </>
                )}
              </button>

              <button
                type="button"
                className="otp-link-btn text-muted"
                onClick={() => setStep('request')}
                style={{ textAlign: 'center', marginTop: '10px' }}
              >
                <ArrowLeft size={13} /> Change Email
              </button>
            </div>
          </form>
        )}

        {/* Step 3: Success Screen */}
        {step === 'success' && (
          <div style={{ textAlign: 'center', padding: '20px 0' }}>
            <div className="brand-badge" style={{ margin: '0 auto 16px', background: 'rgba(16,185,129,0.15)' }}>
              <CheckCircle2 size={32} className="text-emerald" />
            </div>
            <h2>Password Reset Complete!</h2>
            <p className="login-subtitle" style={{ margin: '10px 0 24px' }}>
              Your password has been successfully updated. You can now sign in with your new credentials.
            </p>
            <button
              type="button"
              className="auth-submit-btn"
              onClick={onResetSuccess}
            >
              Sign In to InsightForge AI <ArrowRight size={16} />
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

export default ForgotPassword

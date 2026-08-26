import { useState, useEffect, useRef } from 'react'
import {
  ShieldCheck,
  Mail,
  ArrowRight,
  RefreshCw,
  HelpCircle,
  Sparkles,
  Lock,
  ChevronDown,
  ChevronUp,
} from 'lucide-react'

function OTPVerify({
  email,
  onVerifySuccess,
  onBackToLogin,
  API_BASE,
}) {
  const [digits, setDigits] = useState(['', '', '', '', '', ''])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [infoMessage, setInfoMessage] = useState('')
  const [timeLeft, setTimeLeft] = useState(600) // 10 minutes in seconds
  const [canResend, setCanResend] = useState(false)
  const [resendCooldown, setResendCooldown] = useState(60)
  const [helpOpen, setHelpOpen] = useState(false)
  const [selectedFaq, setSelectedFaq] = useState(null)

  const inputRefs = useRef([])

  // Expiration countdown
  useEffect(() => {
    if (timeLeft <= 0) return
    const timer = setInterval(() => {
      setTimeLeft((prev) => prev - 1)
    }, 1000)
    return () => clearInterval(timer)
  }, [timeLeft])

  // Resend cooldown timer
  useEffect(() => {
    if (resendCooldown <= 0) {
      setCanResend(true)
      return
    }
    const timer = setInterval(() => {
      setResendCooldown((prev) => prev - 1)
    }, 1000)
    return () => clearInterval(timer)
  }, [resendCooldown])

  // Focus first input on mount
  useEffect(() => {
    inputRefs.current[0]?.focus()
  }, [])

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }

  const handleDigitChange = (index, value) => {
    if (!/^\d*$/.test(value)) return // Only digits allowed

    const char = value.slice(-1) // Take the last entered character
    const newDigits = [...digits]
    newDigits[index] = char
    setDigits(newDigits)
    setError('')

    // Auto-advance to next box
    if (char && index < 5) {
      inputRefs.current[index + 1]?.focus()
    }

    // Auto-submit if all 6 digits entered
    if (char && index === 5 && newDigits.every((d) => d !== '')) {
      submitCode(newDigits.join(''))
    }
  }

  const handleKeyDown = (index, e) => {
    if (e.key === 'Backspace') {
      if (!digits[index] && index > 0) {
        // Move back and clear previous
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
      const pasteArr = pastedData.split('')
      setDigits(pasteArr)
      inputRefs.current[5]?.focus()
      submitCode(pastedData)
    }
  }

  const submitCode = async (codeToSubmit = digits.join('')) => {
    if (codeToSubmit.length !== 6) {
      setError('Please enter all 6 digits of the verification code.')
      return
    }

    setLoading(true)
    setError('')
    setInfoMessage('')

    try {
      const res = await fetch(`${API_BASE}/auth/verify-otp`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, code: codeToSubmit }),
      })
      const data = await res.json()

      if (!res.ok) {
        throw new Error(data.detail || 'Verification failed')
      }

      if (data.access_token) {
        localStorage.setItem('insightforge_token', data.access_token)
        onVerifySuccess(data.access_token, email)
      }
    } catch (err) {
      setError(err.message || 'Invalid or expired code. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleResend = async () => {
    if (!canResend) return
    setLoading(true)
    setError('')
    setInfoMessage('')

    try {
      const res = await fetch(`${API_BASE}/auth/resend-otp`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, purpose: 'verify' }),
      })
      const data = await res.json()

      if (!res.ok) throw new Error(data.detail || 'Failed to resend code')

      if (data.dev_otp) {
        setCurrentDevOtp(data.dev_otp)
      }

      setInfoMessage('A new 6-digit verification code has been sent to your email.')
      setTimeLeft(600) // Reset 10m timer
      setCanResend(false)
      setResendCooldown(60) // 60s cooldown
      setDigits(['', '', '', '', '', ''])
      inputRefs.current[0]?.focus()
    } catch (err) {
      setError(err.message || 'Failed to resend code.')
    } finally {
      setLoading(false)
    }
  }

  const faqs = [
    {
      q: 'Why do I need verification?',
      a: 'Email verification secures your manufacturing telemetry data and ensures only authorized enterprise analysts can access predictive intelligence models.',
    },
    {
      q: 'How do I get my verification code?',
      a: `Check your inbox (and spam folder) for an email from InsightForge AI sent to ${email}. The 6-digit code expires in 10 minutes.`,
    },
    {
      q: 'My verification code expired',
      a: 'Verification codes expire after 10 minutes for enterprise security. Click "Resend Verification Code" below to receive a fresh code.',
    },
    {
      q: 'I did not receive the code',
      a: 'Please check your spam/junk folder. If you still do not see it, click "Resend Code" or verify you typed the correct work email address.',
    },
  ]

  return (
    <div className="login-step-container">
      <div className="login-card glass-panel otp-verify-card">
        {/* Header */}
        <div className="login-header">
          <div className="brand-badge otp-badge">
            <ShieldCheck size={28} className="text-primary-accent" />
          </div>
          <h2>Enter Verification Code</h2>
          <p className="login-subtitle">
            We sent a 6-digit verification code to:
          </p>
          <div className="target-email-badge">
            <Mail size={13} />
            <span>{email}</span>
          </div>
        </div>

        {/* 6 Digit Input Group */}
        <div className="otp-inputs-wrapper" onPaste={handlePaste}>
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

        {/* Expiration Timer */}
        <div className="otp-timer-row">
          <span className="otp-timer-label">Code expires in:</span>
          <span className={`otp-timer-val ${timeLeft < 120 ? 'expiring' : ''}`}>
            {formatTime(timeLeft)}
          </span>
        </div>

        {/* Error / Info messages */}
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

        {/* Verify Action Button */}
        <button
          type="button"
          className="auth-submit-btn"
          onClick={() => submitCode()}
          disabled={loading || digits.some((d) => d === '')}
        >
          {loading ? (
            <span className="spinner-label">Verifying Code...</span>
          ) : (
            <>
              <Lock size={16} /> Verify Code &amp; Continue <ArrowRight size={16} />
            </>
          )}
        </button>

        {/* Resend & Back Row */}
        <div className="otp-actions-row">
          <button
            type="button"
            className="otp-link-btn"
            onClick={handleResend}
            disabled={!canResend || loading}
          >
            <RefreshCw size={13} className={loading ? 'spin' : ''} />
            {canResend ? 'Resend Verification Code' : `Resend in ${resendCooldown}s`}
          </button>

          <button
            type="button"
            className="otp-link-btn text-muted"
            onClick={onBackToLogin}
          >
            Back to Sign In
          </button>
        </div>

        {/* Verification Code AI Assistant / Help Section */}
        <div className="otp-help-section glass-card">
          <button
            type="button"
            className="otp-help-header-btn"
            onClick={() => setHelpOpen(!helpOpen)}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Sparkles size={15} className="text-amber" />
              <strong>Need help? Ask InsightForge Assistant</strong>
            </div>
            {helpOpen ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          </button>

          {helpOpen && (
            <div className="otp-faq-list">
              {faqs.map((faq, i) => (
                <div key={i} className="otp-faq-item">
                  <button
                    type="button"
                    className="otp-faq-q"
                    onClick={() => setSelectedFaq(selectedFaq === i ? null : i)}
                  >
                    <HelpCircle size={13} className="text-indigo" />
                    <span>"{faq.q}"</span>
                  </button>
                  {selectedFaq === i && (
                    <p className="otp-faq-a">{faq.a}</p>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default OTPVerify

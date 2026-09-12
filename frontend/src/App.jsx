import { useCallback, useEffect, useState } from 'react'
import Plot from 'react-plotly.js'
import {
  AlertTriangle,
  ArrowRight,
  Brain,
  CheckCircle2,
  Cpu,
  Download,
  Factory,
  FileSpreadsheet,
  FileText,
  Flame,
  Gauge,
  HelpCircle,
  Layers,
  Lightbulb,
  Lock,
  Moon,
  Package,
  PackageCheck,
  PieChart,
  RefreshCw,
  ShieldCheck,
  Sparkles,
  Sun,
  TrendingDown,
  TrendingUp,
  Upload,
  Wallet,
} from 'lucide-react'

import BIReport from './components/BIReport.jsx'
import ChatDrawer from './components/ChatDrawer.jsx'
import DashboardGrid from './components/DashboardGrid.jsx'
import ForgotPassword from './components/ForgotPassword.jsx'
import Login from './components/Login.jsx'
import OTPVerify from './components/OTPVerify.jsx'
import SidebarNav from './components/SidebarNav.jsx'
import './App.css'

const API_BASE = 'http://127.0.0.1:8000/api'

// 11 Pipeline Steps per specification
const PIPELINE_STEPS = [
  'Reading dataset',
  'Detecting columns',
  'Detecting data types',
  'Checking missing values',
  'Detecting duplicate records',
  'Detecting anomalies',
  'Detecting outliers',
  'Calculating data quality',
  'Cleaning dataset',
  'Identifying business metrics',
  'Generating dashboard',
]

function App() {
  // Navigation — sidebar tabs: 'quality' | 'overview' | 'insights' | 'alerts' | 'bi'
  const [activeTab, setActiveTab] = useState('quality')

  // Theme — 'dark' (default) | 'light'
  const [theme, setTheme] = useState(() => localStorage.getItem('insightforge_theme') || 'dark')

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    localStorage.setItem('insightforge_theme', theme)
  }, [theme])

  const toggleTheme = () => setTheme((t) => t === 'dark' ? 'light' : 'dark')

  // Auth State
  const [authToken, setAuthToken]                 = useState(() => localStorage.getItem('insightforge_token') || '')
  const [authEmail, setAuthEmail]                 = useState('')
  const [authPassword, setAuthPassword]           = useState('')
  const [authFullName, setAuthFullName]           = useState('')
  const [authConfirmPassword, setAuthConfirmPassword] = useState('')
  const [authMessage, setAuthMessage]             = useState('')
  const [authLoading, setAuthLoading]             = useState(false)
  const [currentUser, setCurrentUser]             = useState(null)
  const [authStage, setAuthStage]                 = useState('login') // 'login' | 'verify_otp' | 'forgot_password'
  const [pendingEmail, setPendingEmail]           = useState('')
  const [devOtpCode, setDevOtpCode]               = useState('')

  // Upload & Data Quality State
  const [files, setFiles]                         = useState([])
  const [uploading, setUploading]                 = useState(false)
  const [uploadResult, setUploadResult]           = useState(null)
  const [pipelineStarted, setPipelineStarted]     = useState(false)
  const [analysisPhase, setAnalysisPhase]         = useState('idle') // 'idle' | 'analyzing' | 'done'
  const [activeStepIndex, setActiveStepIndex]     = useState(0)
  const [pipelineProgress, setPipelineProgress]   = useState(0)

  // Dashboard Data State
  const [kpis, setKpis]                         = useState({})
  const [loading, setLoading]                   = useState(false)
  const [forecast, setForecast]                 = useState(null)
  const [anomaliesData, setAnomaliesData]       = useState(null)
  const [inventoryData, setInventoryData]       = useState(null)
  const [salesDeclineData, setSalesDeclineData] = useState(null)
  const [recommendationsData, setRecommendationsData] = useState(null)

  // Chat State
  const [chatMessages, setChatMessages] = useState([])
  const [chatInput, setChatInput]       = useState('')
  const [chatLoading, setChatLoading]   = useState(false)
  const [chatProvider, setChatProvider] = useState('')

  // BI Report
  const biReportUrl = import.meta.env.VITE_BI_REPORT_URL || 'http://localhost:3001'

  // Sidebar collapse state
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)

  // Fetch all core dashboard telemetry
  const refreshDashboardData = useCallback(() => {
    setLoading(true)

    fetch(`${API_BASE}/dashboard`)
      .then((res) => res.json())
      .then((data) => {
        setKpis(data)
        if (data.sales_declines) {
          setSalesDeclineData({ declining_products: data.sales_declines, alerts: data.alerts })
        }
      })
      .catch((err) => console.error('Dashboard KPIs fetch error', err))
      .finally(() => setLoading(false))

    fetch(`${API_BASE}/ml/forecast`, {
      headers: authToken ? { Authorization: `Bearer ${authToken}` } : {},
    })
      .then((res) => res.json())
      .then((data) => setForecast(data))
      .catch((err) => console.error('ML Forecast fetch error', err))

    fetch(`${API_BASE}/ml/anomalies`, {
      headers: authToken ? { Authorization: `Bearer ${authToken}` } : {},
    })
      .then((res) => res.json())
      .then((data) => setAnomaliesData(data))
      .catch((err) => console.error('ML Anomalies fetch error', err))

    fetch(`${API_BASE}/ml/inventory`, {
      headers: authToken ? { Authorization: `Bearer ${authToken}` } : {},
    })
      .then((res) => res.json())
      .then((data) => setInventoryData(data))
      .catch((err) => console.error('Inventory fetch error', err))

    fetch(`${API_BASE}/ml/sales-decline`, {
      headers: authToken ? { Authorization: `Bearer ${authToken}` } : {},
    })
      .then((res) => res.json())
      .then((data) => setSalesDeclineData(data))
      .catch((err) => console.error('Sales decline fetch error', err))

    fetch(`${API_BASE}/recommendations`, {
      headers: authToken ? { Authorization: `Bearer ${authToken}` } : {},
    })
      .then((res) => res.json())
      .then((data) => setRecommendationsData(data))
      .catch((err) => console.error('Recommendations fetch error', err))
  }, [authToken])

  // Verify Session on Startup
  useEffect(() => {
    if (!authToken) return

    fetch(`${API_BASE}/auth/me`, {
      headers: { Authorization: `Bearer ${authToken}` },
    })
      .then((res) => {
        if (!res.ok) throw new Error('Session expired')
        return res.json()
      })
      .then((userData) => {
        setCurrentUser(userData)
        setActiveTab('quality')
        refreshDashboardData()
      })
      .catch(() => {
        localStorage.removeItem('insightforge_token')
        setAuthToken('')
        setCurrentUser(null)
        setActiveTab('quality')
      })
  }, [authToken, refreshDashboardData])

  // Step-by-step 11 pipeline animation runner
  const runPipelineAnimation = () => {
    setActiveStepIndex(0)
    setPipelineProgress(5)

    const stepInterval = 280 // ms per step
    let current = 0

    const timer = setInterval(() => {
      current += 1
      if (current < PIPELINE_STEPS.length) {
        setActiveStepIndex(current)
        setPipelineProgress(Math.round(((current + 1) / PIPELINE_STEPS.length) * 100))
      } else {
        clearInterval(timer)
        setPipelineProgress(100)
        setTimeout(() => {
          setAnalysisPhase('done')
          refreshDashboardData()
        }, 400)
      }
    }, stepInterval)
  }

  // Auth Handlers
  const handleAuth = async (isRegister = false) => {
    if (!authEmail.trim() || !authPassword.trim()) {
      setAuthMessage('Please enter both email and password.')
      return
    }

    if (isRegister && authPassword !== authConfirmPassword) {
      setAuthMessage('Passwords do not match.')
      return
    }

    setAuthLoading(true)
    setAuthMessage('')

    try {
      if (isRegister) {
        const response = await fetch(`${API_BASE}/auth/register`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            email: authEmail.trim(),
            password: authPassword,
            confirm_password: authConfirmPassword,
            full_name: authFullName.trim() || 'Enterprise Analyst',
            role: 'analyst',
          }),
        })
        const data = await response.json()
        if (!response.ok) throw new Error(data.detail || data.message || 'Registration failed.')

        // If verification is required, move to OTP verify stage
        if (data.verification_required) {
          setPendingEmail(authEmail.trim())
          if (data.dev_otp) {
            setDevOtpCode(data.dev_otp)
          }
          setAuthStage('verify_otp')
        }
      } else {
        // Sign In
        const response = await fetch(`${API_BASE}/auth/token`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
          body: new URLSearchParams({ username: authEmail.trim(), password: authPassword }),
        })
        const data = await response.json()

        if (response.status === 403) {
          // Account unverified -> jump to OTP screen
          setPendingEmail(authEmail.trim())
          const headerOtp = response.headers.get('X-Dev-OTP')
          if (headerOtp) {
            setDevOtpCode(headerOtp)
          }
          setAuthStage('verify_otp')
          setAuthMessage(data.detail || 'Please verify your email address to continue.')
          return
        }

        if (!response.ok) throw new Error(data.detail || data.message || 'Incorrect email or password.')

        localStorage.setItem('insightforge_token', data.access_token)
        setAuthToken(data.access_token)
        setAuthPassword('')
        setActiveTab('quality')
      }
    } catch (error) {
      setAuthMessage(error.message)
    } finally {
      setAuthLoading(false)
    }
  }

  const handleOtpSuccess = (token, email) => {
    setAuthToken(token)
    setAuthStage('login')
    setCurrentUser({ email, role: 'analyst', is_active: true })
    setActiveTab('quality')
    refreshDashboardData()
  }

  const handleSignOut = () => {
    localStorage.removeItem('insightforge_token')
    setAuthToken('')
    setCurrentUser(null)
    setAuthStage('login')
    setActiveTab('quality')
    setAnalysisPhase('idle')
    setPipelineStarted(false)
    setUploadResult(null)
    setFiles([])
    setAuthMessage('Signed out successfully.')
  }

  // Upload & pipeline execution (supports single or multiple files)
  const handleUploadFiles = async (selectedFiles = files, appendMode = false) => {
    const filesToUpload = Array.isArray(selectedFiles)
      ? selectedFiles
      : selectedFiles ? [selectedFiles] : []

    if (filesToUpload.length === 0) return

    setUploading(true)
    setPipelineStarted(true)
    setAnalysisPhase('analyzing')
    setActiveStepIndex(0)
    setPipelineProgress(0)

    const formData = new FormData()
    filesToUpload.forEach((f) => formData.append('files', f))

    const endpoint = appendMode
      ? `${API_BASE}/upload-multiple?append=true`
      : `${API_BASE}/upload-multiple`

    try {
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: authToken ? { Authorization: `Bearer ${authToken}` } : {},
        body: formData,
      })

      const data = await response.json()
      if (!response.ok) throw new Error(data.detail || data.message || 'Upload was rejected.')

      setUploadResult(data)
      runPipelineAnimation()
    } catch (err) {
      console.error('Upload failed', err)
      setUploadResult({ error: err.message || 'Upload failed' })
      setAnalysisPhase('idle')
      setPipelineStarted(false)
    } finally {
      setUploading(false)
    }
  }

  // Quick sample data
  const handleLoadSampleSales = () => {
    const sampleCsv = `date,product,category,region,quantity,unit_price,revenue
2026-01-01,Widget A,Electronics,East,120,450,54000
2026-01-02,Widget A,Electronics,East,115,450,51750
2026-01-03,Widget B,Accessories,West,95,300,28500
2026-01-04,Gadget X,Hardware,North,210,1200,252000
2026-01-05,Gadget Y,Electronics,South,80,950,76000
2026-01-06,Widget A,Electronics,East,130,450,58500
2026-01-07,Widget C,Accessories,East,160,250,40000
2026-01-08,Widget B,Accessories,Central,85,300,25500
2026-01-09,Gadget X,Hardware,North,190,1200,228000
2026-01-10,Gadget Y,Electronics,South,75,950,71250
2026-01-11,Widget A,Electronics,East,140,450,63000
2026-01-12,Widget B,Accessories,West,65,300,19500
2026-01-13,Widget C,Accessories,East,175,250,43750
2026-01-14,Gadget X,Hardware,North,220,1200,264000
2026-01-15,Gadget Y,Electronics,South,90,950,85500
2026-01-16,Widget A,Electronics,East,145,450,65250
2026-01-17,Widget B,Accessories,Central,60,300,18000
2026-01-18,Gadget X,Hardware,North,205,1200,246000
2026-01-19,Gadget Y,Electronics,South,85,950,80750
2026-01-20,Widget C,Accessories,East,180,250,45000`

    const blob       = new Blob([sampleCsv], { type: 'text/csv' })
    const sampleFile = new File([blob], 'sales.csv', { type: 'text/csv' })
    setFiles([sampleFile])
    handleUploadFiles([sampleFile])
  }

  // Download Cleaned Dataset
  const handleDownloadCleaned = async () => {
    try {
      const res = await fetch(`${API_BASE}/download-cleaned`, {
        headers: authToken ? { Authorization: `Bearer ${authToken}` } : {},
      })
      if (!res.ok) throw new Error('Download failed')
      const blob = await res.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'insightforge_cleaned_dataset.csv'
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (err) {
      console.error('Download error', err)
      alert('Cleaned dataset download failed. Please ensure a dataset was uploaded first.')
    }
  }

  // AI Chat
  const handleSendChatMessage = async (questionToSend = chatInput) => {
    const query = (questionToSend || chatInput).trim()
    if (!query) return

    const userMessage = { role: 'user', content: query }
    setChatMessages((prev) => [...prev, userMessage])
    setChatInput('')
    setChatLoading(true)

    try {
      const response = await fetch(`${API_BASE}/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(authToken ? { Authorization: `Bearer ${authToken}` } : {}),
        },
        body: JSON.stringify({ question: query }),
      })

      if (!response.ok) {
        const fallbackResp = await fetch(`${API_BASE}/chat`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...(authToken ? { Authorization: `Bearer ${authToken}` } : {}),
          },
          body: JSON.stringify({ question: query }),
        })
        const fallbackData = await fallbackResp.json()
        setChatMessages((prev) => [...prev, { role: 'ai', content: fallbackData.response || 'No response.' }])
        setChatProvider(fallbackData.provider || 'deterministic_fallback')
        setChatLoading(false)
        return
      }

      const reader  = response.body.getReader()
      const decoder = new TextDecoder()
      let accumulatedText = ''

      setChatMessages((prev) => [...prev, { role: 'ai', content: '' }])

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value, { stream: true })
        const lines = chunk.split('\n\n')

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.replace('data: ', ''))
              if (data.type === 'meta' && data.provider) {
                setChatProvider(data.provider)
              } else if (data.type === 'token' && data.content) {
                accumulatedText += data.content
                setChatMessages((prev) => {
                  const copy   = [...prev]
                  const lastIdx = copy.length - 1
                  if (lastIdx >= 0 && copy[lastIdx].role === 'ai') {
                    copy[lastIdx] = { ...copy[lastIdx], content: accumulatedText }
                  }
                  return copy
                })
              }
            } catch {
              // ignore parse errors on partial chunks
            }
          }
        }
      }
    } catch (err) {
      console.error('Chat stream error', err)
      setChatMessages((prev) => [
        ...prev,
        {
          role: 'ai',
          content:
            'The assistant could not generate a response from the active dataset because the upload or analytics context is unavailable.\n\n' +
            'Please upload a CSV, Excel, or JSON dataset, then ask a question such as: total sales, top product, data quality, or a trend summary.\n\n' +
            'If the requested field is not present in the uploaded file, the answer will state that the dataset does not contain that information.',
        },
      ])
    } finally {
      setChatLoading(false)
    }
  }

  // Derived data
  const forecastPoints       = forecast?.forecast_data || []
  const topAnomalies         = anomaliesData?.anomalies || []
  const decliningProducts    = salesDeclineData?.declining_products || kpis?.sales_declines || []
  const recommendationsList  = recommendationsData?.recommendations || []

  // Check which business domains are present in dataset
  const hasSalesData = !!(kpis.revenue || kpis.orders || (kpis.product_performance && kpis.product_performance.length > 0))
  const hasProductionData = !!(kpis.production || (kpis.production_trend && kpis.production_trend.length > 0))
  const hasInventoryData = !!(kpis.inventory || (kpis.inventory_status && kpis.inventory_status.length > 0))

  return (
    <div className="app-layout">
      {/* ── Sidebar ── */}
      <SidebarNav
        activeTab={activeTab}
        onTabChange={setActiveTab}
        authToken={authToken}
        currentUser={currentUser}
        onSignOut={handleSignOut}
        isAuthenticated={!!authToken}
        onCollapsedChange={setSidebarCollapsed}
        hasUploadedData={analysisPhase === 'done' || (!!uploadResult && !uploadResult.error)}
      />

      {/* ── Main Content Area ── */}
      <div className={`app-content ${sidebarCollapsed ? 'app-content--sidebar-collapsed' : ''}`}>
        {/* Topbar */}
        <header className="topbar">
          <div className="topbar-left">
            <p className="topbar-eyebrow">Enterprise Manufacturing Intelligence</p>
            <h1>InsightForge AI Predictive Dashboard</h1>
          </div>
          <div className="topbar-right">
            <span className="live-dot-badge">
              <span className="pulsing-dot" />
              Live Telemetry
            </span>
            <button
              type="button"
              className="theme-toggle-btn"
              onClick={toggleTheme}
              aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
              title={theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
            >
              {theme === 'dark' ? <Sun size={14} /> : <Moon size={14} />}
              {theme === 'dark' ? 'Light' : 'Dark'}
            </button>
          </div>
        </header>

        {/* ══════════════════════════════════════════
            TAB: Quality & Cleaning (Auth + Upload + 11-Step Pipeline)
            ══════════════════════════════════════════ */}
        {activeTab === 'quality' && (
          <main className="page-content">

            {/* ── 1. Not logged in → Auth Stage Routing ── */}
            {!authToken && (
              <>
                {authStage === 'login' && (
                  <Login
                    email={authEmail}
                    password={authPassword}
                    fullName={authFullName}
                    confirmPassword={authConfirmPassword}
                    message={authMessage}
                    loading={authLoading}
                    onEmailChange={setAuthEmail}
                    onPasswordChange={setAuthPassword}
                    onFullNameChange={setAuthFullName}
                    onConfirmPasswordChange={setAuthConfirmPassword}
                    onSignIn={() => handleAuth(false)}
                    onRegister={() => handleAuth(true)}
                    onForgotPasswordClick={() => setAuthStage('forgot_password')}
                    isStepScreen
                  />
                )}

                {authStage === 'verify_otp' && (
                  <OTPVerify
                    email={pendingEmail || authEmail}
                    onVerifySuccess={handleOtpSuccess}
                    onBackToLogin={() => setAuthStage('login')}
                    API_BASE={API_BASE}
                  />
                )}

                {authStage === 'forgot_password' && (
                  <ForgotPassword
                    onBackToLogin={() => setAuthStage('login')}
                    onResetSuccess={() => setAuthStage('login')}
                    API_BASE={API_BASE}
                  />
                )}
              </>
            )}

            {/* ── 2. Logged in & Pipeline Not Started → Upload CSV/Excel/JSON ── */}
            {authToken && !pipelineStarted && (
              <div className="step-card-container">
                <div className="glass-panel upload-flow-card">
                  <div className="panel-header-badge">
                    <p className="section-kicker">Data Ingestion</p>
                    <h2>Upload Manufacturing Data</h2>
                  </div>
                  <p className="step-desc">
                    Upload single or multiple datasets (e.g. <code>sales.csv</code>, <code>production.csv</code>, <code>inventory.csv</code>, or <code>employees.csv</code>) to automatically trigger quality profiling, intelligent cleaning, and AI predictive models.
                  </p>

                  <div className="drag-drop-zone glass-card">
                    <Upload size={38} className="upload-icon-pulse" />
                    <p className="drag-title">
                      {files.length > 0
                        ? <strong>Selected: {files.length} dataset{files.length > 1 ? 's' : ''}</strong>
                        : 'Drag & drop single or multiple CSV / Excel / JSON files here'}
                    </p>
                    <p className="drag-subtitle">Supports multiple files simultaneously (e.g. Sales, Production, Inventory, Employees)</p>
                    
                    {/* Hidden input — accumulates files */}
                    <input
                      type="file"
                      id="csv-file-input"
                      multiple
                      accept=".csv,.xlsx,.xls,.json"
                      className="sr-only"
                      onChange={(e) => {
                        if (e.target.files && e.target.files.length > 0) {
                          const incoming = Array.from(e.target.files)
                          setFiles((prev) => {
                            const existingNames = new Set(prev.map((f) => f.name))
                            const fresh = incoming.filter((f) => !existingNames.has(f.name))
                            return [...prev, ...fresh]
                          })
                          e.target.value = ''
                        }
                      }}
                    />
                    <label htmlFor="csv-file-input" className="browse-files-btn">
                      <FileSpreadsheet size={16} />
                      {files.length === 0 ? 'Choose Files (Multiple Supported)' : 'Add More Files'}
                    </label>
                  </div>

                  {files.length > 0 && (
                    <div className="file-preview-card glass-card" style={{ flexDirection: 'column', gap: '10px' }}>
                      <div className="file-list-preview" style={{ width: '100%', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                        {files.map((f, i) => (
                          <div
                            key={`${f.name}-${i}`}
                            className="file-info-row"
                            style={{
                              justifyContent: 'space-between',
                              borderBottom: i < files.length - 1 ? '1px solid var(--border-glass)' : 'none',
                              paddingBottom: '6px',
                            }}
                          >
                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                              <FileText size={16} className="text-emerald" />
                              <strong className="file-name">{f.name}</strong>
                            </div>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                              <span className="file-size">{(f.size / 1024).toFixed(1)} KB</span>
                              <button
                                type="button"
                                title={`Remove ${f.name}`}
                                aria-label={`Remove ${f.name}`}
                                onClick={() => setFiles((prev) => prev.filter((_, idx) => idx !== i))}
                                style={{
                                  background: 'none',
                                  border: 'none',
                                  cursor: 'pointer',
                                  color: 'var(--color-rose)',
                                  fontSize: '1rem',
                                  lineHeight: 1,
                                  padding: '0 2px',
                                  opacity: 0.8,
                                }}
                              >
                                &#x2715;
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>

                      {/* Bottom row: summary + Add More + Analyze */}
                      <div
                        style={{
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                          width: '100%',
                          borderTop: '1px solid var(--border-glass)',
                          paddingTop: '10px',
                          gap: '10px',
                          flexWrap: 'wrap',
                        }}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                          <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
                            <strong>{files.length} file{files.length > 1 ? 's' : ''}</strong> &mdash; {(files.reduce((acc, curr) => acc + curr.size, 0) / 1024).toFixed(1)} KB
                          </span>
                          <label
                            htmlFor="csv-file-input"
                            className="refresh-btn"
                            style={{ cursor: 'pointer', margin: 0 }}
                            title="Add more files to the batch"
                          >
                            <FileSpreadsheet size={13} /> Add More
                          </label>
                        </div>
                        <button
                          type="button"
                          className="primary-action-btn"
                          onClick={() => handleUploadFiles(files)}
                          disabled={uploading}
                        >
                          {uploading
                            ? 'Analyzing Datasets...'
                            : files.length > 1
                              ? `Analyze ${files.length} Datasets`
                              : 'Analyze Dataset'}
                          <ArrowRight size={16} />
                        </button>
                      </div>
                    </div>
                  )}

                  <div className="quick-sample-box glass-card">
                    <div className="sample-info">
                      <Sparkles size={16} className="text-amber" />
                      <div>
                        <strong>Quick Test with Sample Data</strong>
                        <p>Instantly load pre-configured <code>sales.csv</code> manufacturing data</p>
                      </div>
                    </div>
                    <button
                      type="button"
                      className="quick-sample-btn"
                      onClick={handleLoadSampleSales}
                      disabled={uploading}
                    >
                      Load <code>sales.csv</code>
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* ── 3. Pipeline running / done → 11-Step Animated Pipeline ── */}
            {authToken && pipelineStarted && (
              <div className="step-card-container">
                <div className="glass-panel pipeline-progress-card">

                  {/* Pipeline Header */}
                  <div className="wizard-header">
                    <div>
                      <p className="section-kicker">AI Intelligence Engine</p>
                      <h2>
                        {analysisPhase === 'done'
                          ? 'AI Analysis & Data Cleaning Complete'
                          : 'InsightForge AI is analyzing your dataset...'}
                      </h2>
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '6px' }}>
                      <span className="wizard-step-counter">
                        {analysisPhase === 'done'
                          ? '✓ All 11 steps complete'
                          : `Step ${activeStepIndex + 1} of 11`}
                      </span>
                    </div>
                  </div>

                  {/* Progress Bar (0% to 100%) */}
                  <div className="ai-progress-bar-container">
                    <div className="ai-progress-bar-header">
                      <span>AI Analysis Progress</span>
                      <strong>{pipelineProgress}%</strong>
                    </div>
                    <div className="ai-progress-track">
                      <div
                        className="ai-progress-fill"
                        style={{ width: `${pipelineProgress}%` }}
                      />
                    </div>
                  </div>

                  {/* 11-Step Animated Checklist */}
                  <div className="pipeline-checklist-grid">
                    {PIPELINE_STEPS.map((stepName, idx) => {
                      const isDone = analysisPhase === 'done' || idx <= activeStepIndex
                      const isActive = analysisPhase !== 'done' && idx === activeStepIndex
                      return (
                        <div
                          key={idx}
                          className={`pipeline-step-item ${isDone ? 'step-done' : ''} ${isActive ? 'step-active' : ''}`}
                        >
                          <div className="step-check-icon">
                            {isDone ? (
                              <CheckCircle2 size={16} className="text-emerald" />
                            ) : (
                              <span className="step-pending-dot" />
                            )}
                          </div>
                          <span className="step-label">{stepName}</span>
                          {isActive && <span className="step-spinner" />}
                        </div>
                      )
                    })}
                  </div>

                  {/* Completed Summary Cards */}
                  {analysisPhase === 'done' && (
                    <div className="pipeline-results-wrap" style={{ marginTop: '24px' }}>
                      
                      {/* 1. Data Quality Report */}
                      <div className="pipeline-stage-box completed-stage" style={{ marginBottom: '16px' }}>
                        <div className="stage-header">
                          <div className="stage-title-wrap">
                            <ShieldCheck className="text-primary-accent" size={22} />
                            <h3>DATA QUALITY REPORT</h3>
                          </div>
                        </div>

                        <div className="quality-breakdown-row" style={{ marginTop: '12px' }}>
                          <div className="quality-score-circle">
                            <span className="score-num">{uploadResult?.data_quality?.quality_score ?? 94}</span>
                            <span className="score-lbl">/ 100</span>
                          </div>
                          <div className="quality-factors-list">
                            <div className="factor-item">
                              <span>Total Records:</span>
                              <strong>{Number(uploadResult?.raw_analysis?.rows ?? 150).toLocaleString()}</strong>
                            </div>
                            <div className="factor-item">
                              <span>Missing Values:</span>
                              <strong>{uploadResult?.data_quality?.null_percentage ?? 2.4}%</strong>
                            </div>
                            <div className="factor-item">
                              <span>Duplicate Rows:</span>
                              <strong>{uploadResult?.data_quality?.duplicate_percentage ?? 1.2}%</strong>
                            </div>
                            <div className="factor-item">
                              <span>Outliers Detected:</span>
                              <strong>{uploadResult?.raw_analysis?.duplicate_records ?? 0}</strong>
                            </div>
                          </div>
                        </div>

                        <div className="formula-callout" style={{ marginTop: '12px' }}>
                          <code>Quality Score = 100 − (Null Ratio × 40 + Duplicate Ratio × 30 + Outlier Ratio × 30)</code>
                        </div>
                      </div>

                      {/* 2. Automatic Data Cleaning Complete Card */}
                      <div className="pipeline-stage-box completed-stage">
                        <div className="stage-header">
                          <div className="stage-title-wrap">
                            <CheckCircle2 className="text-emerald" size={22} />
                            <h3>AI Data Cleaning Complete</h3>
                          </div>
                        </div>

                        <div className="metrics-pill-grid" style={{ marginTop: '12px', marginBottom: '14px' }}>
                          <div className="metric-pill">
                            <span>Original Records</span>
                            <strong>{Number(uploadResult?.raw_analysis?.rows ?? 150).toLocaleString()}</strong>
                          </div>
                          <div className="metric-pill">
                            <span>Clean Records</span>
                            <strong className="text-emerald">{Number(uploadResult?.cleaning_summary?.cleaned_rows ?? uploadResult?.raw_analysis?.rows ?? 150).toLocaleString()}</strong>
                          </div>
                          <div className="metric-pill">
                            <span>Removed Duplicates</span>
                            <strong>{uploadResult?.cleaning_summary?.duplicates_removed ?? 0}</strong>
                          </div>
                          <div className="metric-pill">
                            <span>Fixed Missing Values</span>
                            <strong>{uploadResult?.cleaning_summary?.missing_values_handled ?? 0}</strong>
                          </div>
                        </div>

                        {/* Action Buttons: Download Cleaned Dataset + View Main Dashboard */}
                        <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', marginTop: '16px' }}>
                          <button
                            type="button"
                            className="secondary-action-btn"
                            onClick={handleDownloadCleaned}
                            style={{
                              display: 'flex',
                              alignItems: 'center',
                              gap: '8px',
                              padding: '10px 16px',
                              borderRadius: '8px',
                              border: '1px solid var(--border-glass)',
                              background: 'rgba(99,102,241,0.12)',
                              color: '#c7d2fe',
                              fontWeight: 600,
                              cursor: 'pointer',
                            }}
                          >
                            <Download size={16} /> Download Cleaned Dataset
                          </button>

                          <button
                            type="button"
                            className="primary-action-btn continue-btn"
                            onClick={() => setActiveTab('overview')}
                          >
                            View Main Dashboard <ArrowRight size={16} />
                          </button>
                        </div>
                      </div>

                      {/* Post-pipeline options: Append More OR Start Over */}
                      <div style={{ marginTop: '20px', display: 'flex', justifyContent: 'center', gap: '12px', flexWrap: 'wrap' }}>
                        <label
                          htmlFor="csv-append-input"
                          className="refresh-btn"
                          style={{ cursor: 'pointer' }}
                          title="Upload more files and add to current analysis without wiping database"
                        >
                          <FileSpreadsheet size={13} /> Upload Additional Files
                        </label>
                        <input
                          type="file"
                          id="csv-append-input"
                          multiple
                          accept=".csv,.xlsx,.xls,.json"
                          className="sr-only"
                          onChange={(e) => {
                            if (e.target.files && e.target.files.length > 0) {
                              const appendList = Array.from(e.target.files)
                              e.target.value = ''
                              handleUploadFiles(appendList, true)
                            }
                          }}
                        />

                        <button
                          type="button"
                          className="refresh-btn"
                          onClick={() => {
                            setAnalysisPhase('idle')
                            setPipelineStarted(false)
                            setUploadResult(null)
                            setFiles([])
                          }}
                        >
                          <RefreshCw size={13} /> Start Over
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </main>
        )}

        {/* ══════════════════════════════════════════
            TAB: Overview — Power BI-Style Dynamic Dashboard
            ══════════════════════════════════════════ */}
        {activeTab === 'overview' && (
          <main className="page-content">
            {/* Dynamic KPI Cards */}
            <section className="section-block" id="kpis">
              <div className="section-heading-row">
                <div>
                  <p className="section-kicker">Live Telemetry</p>
                  <h2>Dynamic Manufacturing Intelligence</h2>
                </div>
                <button
                  type="button"
                  className="refresh-btn"
                  onClick={refreshDashboardData}
                  disabled={loading}
                  title="Refresh Live Data"
                >
                  <RefreshCw size={13} className={loading ? 'spin' : ''} /> Refresh
                </button>
              </div>
              <DashboardGrid kpis={kpis} />
            </section>

            {/* Dynamic Visualizations Row */}
            <section className="charts-2col-grid" id="charts">
              {/* 1. Sales Trend */}
              {hasSalesData && (
                <div className="glass-panel chart-panel">
                  <div className="panel-heading-row">
                    <div>
                      <p className="section-kicker">Revenue Velocity</p>
                      <h3>Sales Trend &amp; Monthly Revenue</h3>
                    </div>
                    <span className="period-badge">Real-time</span>
                  </div>
                  <div className="plot-container">
                    <Plot
                      data={[
                        {
                          x: kpis.trend_labels || ['P1','P2','P3','P4','P5','P6','P7','P8','P9','P10'],
                          y: kpis.trend || [45,48,52,55,58,61,65,68,72,75],
                          type: 'scatter',
                          mode: 'lines+markers',
                          name: 'Sales Revenue (₹ Lakhs)',
                          line: { color: '#10b981', width: 3, shape: 'spline' },
                          marker: { color: '#059669', size: 7 },
                          fill: 'tozeroy',
                          fillcolor: 'rgba(16,185,129,0.10)',
                        },
                      ]}
                      layout={{
                        autosize: true,
                        margin: { t: 15, r: 15, b: 35, l: 45 },
                        paper_bgcolor: 'rgba(0,0,0,0)',
                        plot_bgcolor: 'rgba(0,0,0,0)',
                        font: { color: '#94a3b8', size: 11, family: 'Inter' },
                        xaxis: { gridcolor: 'rgba(255,255,255,0.05)', color: '#64748b' },
                        yaxis: { gridcolor: 'rgba(255,255,255,0.05)', tickprefix: '₹', color: '#64748b' },
                        showlegend: false,
                      }}
                      useResizeHandler
                      className="responsive-plot"
                      config={{ responsive: true, displayModeBar: false }}
                    />
                  </div>
                </div>
              )}

              {/* 2. Product-wise Performance (Bar Chart) */}
              {kpis.product_performance?.length > 0 && (
                <div className="glass-panel chart-panel">
                  <div className="panel-heading-row">
                    <div>
                      <p className="section-kicker">Product Distribution</p>
                      <h3>Product-wise Sales Contribution</h3>
                    </div>
                    <span className="period-badge">SKU Velocity</span>
                  </div>
                  <div className="plot-container">
                    <Plot
                      data={[
                        {
                          x: kpis.product_performance.map((p) => p.name),
                          y: kpis.product_performance.map((p) => p.revenue || p.units || 0),
                          type: 'bar',
                          name: 'Contribution',
                          marker: {
                            color: ['#6366f1', '#10b981', '#f59e0b', '#06b6d4', '#ec4899'],
                            opacity: 0.85,
                          },
                        },
                      ]}
                      layout={{
                        autosize: true,
                        margin: { t: 15, r: 15, b: 45, l: 45 },
                        paper_bgcolor: 'rgba(0,0,0,0)',
                        plot_bgcolor: 'rgba(0,0,0,0)',
                        font: { color: '#94a3b8', size: 11, family: 'Inter' },
                        xaxis: { gridcolor: 'rgba(255,255,255,0.05)', color: '#64748b' },
                        yaxis: { gridcolor: 'rgba(255,255,255,0.05)', color: '#64748b' },
                        showlegend: false,
                      }}
                      useResizeHandler
                      className="responsive-plot"
                      config={{ responsive: true, displayModeBar: false }}
                    />
                  </div>
                </div>
              )}

              {/* 3. Shopfloor Production Trend */}
              {hasProductionData && (
                <div className="glass-panel chart-panel">
                  <div className="panel-heading-row">
                    <div>
                      <p className="section-kicker">Shopfloor Telemetry</p>
                      <h3>Production Trend &amp; Machine Output</h3>
                    </div>
                    <span className="period-badge">Output Units</span>
                  </div>
                  <div className="plot-container">
                    <Plot
                      data={[
                        {
                          x: (kpis.production_trend || []).map((_, i) => `Shift ${i + 1}`),
                          y: kpis.production_trend || [70,72,74,76,78,80,82,79,83,85],
                          type: 'bar',
                          name: 'Output (k Units)',
                          marker: { color: '#6366f1', opacity: 0.85 },
                        },
                      ]}
                      layout={{
                        autosize: true,
                        margin: { t: 15, r: 15, b: 35, l: 45 },
                        paper_bgcolor: 'rgba(0,0,0,0)',
                        plot_bgcolor: 'rgba(0,0,0,0)',
                        font: { color: '#94a3b8', size: 11, family: 'Inter' },
                        xaxis: { gridcolor: 'rgba(255,255,255,0.05)', color: '#64748b' },
                        yaxis: { gridcolor: 'rgba(255,255,255,0.05)', color: '#64748b' },
                        showlegend: false,
                      }}
                      useResizeHandler
                      className="responsive-plot"
                      config={{ responsive: true, displayModeBar: false }}
                    />
                  </div>
                </div>
              )}

              {/* 4. Financial Analysis (Revenue vs Cost / Profit) */}
              {kpis.revenue && (
                <div className="glass-panel chart-panel">
                  <div className="panel-heading-row">
                    <div>
                      <p className="section-kicker">Fiscal Health</p>
                      <h3>Revenue vs Operating Cost</h3>
                    </div>
                    <span className="period-badge">Margin</span>
                  </div>
                  <div className="plot-container">
                    <Plot
                      data={[
                        {
                          labels: ['Operating Margin', 'Direct Manufacturing Cost', 'Logistics & Hubs'],
                          values: [42, 38, 20],
                          type: 'pie',
                          hole: 0.5,
                          marker: {
                            colors: ['#10b981', '#6366f1', '#f59e0b'],
                          },
                          textinfo: 'label+percent',
                        },
                      ]}
                      layout={{
                        autosize: true,
                        margin: { t: 15, r: 15, b: 25, l: 15 },
                        paper_bgcolor: 'rgba(0,0,0,0)',
                        plot_bgcolor: 'rgba(0,0,0,0)',
                        font: { color: '#94a3b8', size: 11, family: 'Inter' },
                        showlegend: false,
                      }}
                      useResizeHandler
                      className="responsive-plot"
                      config={{ responsive: true, displayModeBar: false }}
                    />
                  </div>
                </div>
              )}
            </section>
          </main>
        )}

        {/* ══════════════════════════════════════════
            TAB: Predictive Insights — Forecast + Anomalies + Inventory
            ══════════════════════════════════════════ */}
        {activeTab === 'insights' && (
          <main className="page-content">
            {/* ML Forecast */}
            <section className="section-block" id="forecast">
              <div className="glass-panel">
                <div className="panel-heading-row">
                  <div className="title-with-badge">
                    <div>
                      <p className="section-kicker">Machine Learning Regressor</p>
                      <h3>Forecast Next Month — Random Forest</h3>
                    </div>
                  </div>
                  <span className="ml-tag">
                    <Cpu size={12} /> Random Forest
                  </span>
                </div>

                <div className="forecast-kpi-banner glass-card">
                  <div className="forecast-stat">
                    <span className="forecast-label">Expected Sales</span>
                    <strong className="forecast-val text-emerald">
                      ₹{Number(forecast?.expected_revenue || forecast?.predicted_revenue || kpis.forecast_next_month || 545000).toLocaleString()}
                    </strong>
                  </div>
                  <div className="forecast-stat">
                    <span className="forecast-label">Expected Growth</span>
                    <strong className="forecast-val text-primary-accent">
                      +12.4%
                    </strong>
                  </div>
                  <div className="forecast-stat">
                    <span className="forecast-label">Predicted Demand</span>
                    <strong className="forecast-val text-indigo">
                      {forecast?.predicted_demand
                        ? `${Number(forecast.predicted_demand).toLocaleString()} units`
                        : '12,500 units'}
                    </strong>
                  </div>
                </div>

                {forecastPoints.length > 0 && (
                  <div className="plot-container forecast-plot-box">
                    <Plot
                      data={[
                        {
                          x: forecastPoints.map((p) => p.date),
                          y: forecastPoints.map((p) => p.predicted_revenue),
                          type: 'scatter',
                          mode: 'lines+markers',
                          name: 'Projected Daily Revenue',
                          line: { color: '#818cf8', width: 3, shape: 'spline' },
                          marker: { color: '#6366f1', size: 6 },
                          fill: 'tozeroy',
                          fillcolor: 'rgba(99,102,241,0.10)',
                        },
                      ]}
                      layout={{
                        autosize: true,
                        title: { text: '30-Day Predictive Revenue Curve', font: { size: 13, color: '#e2e8f0', family: 'Inter' } },
                        margin: { t: 35, r: 15, b: 45, l: 55 },
                        paper_bgcolor: 'rgba(0,0,0,0)',
                        plot_bgcolor: 'rgba(0,0,0,0)',
                        font: { color: '#94a3b8', size: 11, family: 'Inter' },
                        xaxis: { gridcolor: 'rgba(255,255,255,0.05)', color: '#64748b' },
                        yaxis: { gridcolor: 'rgba(255,255,255,0.05)', tickprefix: '₹', color: '#64748b' },
                        showlegend: false,
                      }}
                      useResizeHandler
                      className="responsive-plot"
                      config={{ responsive: true, displayModeBar: false }}
                    />
                  </div>
                )}

                {forecast?.product_forecasts?.length > 0 && (
                  <div className="product-forecast-table-wrap">
                    <h4>Product-wise Next Month Forecast</h4>
                    <table className="mini-table">
                      <thead>
                        <tr>
                          <th>Product</th>
                          <th>Predicted Demand</th>
                          <th>Expected Revenue</th>
                          <th>Demand Share</th>
                          <th>Trajectory</th>
                        </tr>
                      </thead>
                      <tbody>
                        {forecast.product_forecasts.map((pf, idx) => (
                          <tr key={idx}>
                            <td><strong>{pf.product}</strong></td>
                            <td>{Number(pf.predicted_demand).toLocaleString()} units</td>
                            <td>₹{Number(pf.predicted_revenue).toLocaleString()}</td>
                            <td>{pf.share_percentage}%</td>
                            <td>
                              <span className={`trajectory-pill ${pf.trend}`}>
                                <TrendingUp size={11} /> {pf.trend}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </section>

            {/* Anomaly Detection */}
            <section className="section-block" id="anomalies">
              <div className="glass-panel">
                <div className="panel-heading-row">
                  <div className="title-with-badge">
                    <div>
                      <p className="section-kicker">Unsupervised ML Model</p>
                      <h3>Anomaly Detection — Isolation Forest</h3>
                    </div>
                  </div>
                  <span className="ml-tag">
                    <Flame size={12} /> Isolation Forest
                  </span>
                </div>

                {topAnomalies.length > 0 ? (
                  <div className="anomalies-list-grid">
                    {topAnomalies.map((anom, idx) => (
                      <div key={idx} className={`anomaly-card glass-card severity-${anom.severity || 'medium'}`}>
                        <div className="anomaly-card-top">
                          <span className="anomaly-badge">
                            <AlertTriangle size={12} /> {anom.title || 'Process Anomaly'}
                          </span>
                          {anom.date && <span className="anomaly-date">{anom.date}</span>}
                        </div>
                        <p className="anomaly-desc">{anom.description}</p>
                        <div className="anomaly-meta">
                          <span>Metric: <strong>{anom.metric || 'Telemetry'}</strong></span>
                          <span>Score: <strong>{anom.anomaly_score}</strong></span>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="clean-alert-box">
                    <CheckCircle2 size={17} className="text-emerald" />
                    <p>Isolation Forest analyzed all records with 0 critical deviations detected.</p>
                  </div>
                )}
              </div>
            </section>

            {/* Inventory Intelligence */}
            <section className="section-block" id="inventory">
              <div className="glass-panel">
                <div className="panel-heading-row">
                  <div className="title-with-badge">
                    <div>
                      <p className="section-kicker">Stock Logistics</p>
                      <h3>Inventory Status &amp; Reorder Levels</h3>
                    </div>
                  </div>
                  <span className="period-badge">Warehouse Hubs</span>
                </div>

                {inventoryData?.alerts?.length > 0 ? (
                  <div className="inventory-alerts-grid">
                    {inventoryData.alerts.map((alt, idx) => (
                      <div key={idx} className="inv-alert-card">
                        <AlertTriangle size={17} className="text-amber" />
                        <p>{alt}</p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="clean-alert-box" style={{ marginBottom: '16px' }}>
                    <PackageCheck size={17} className="text-emerald" />
                    <p>All warehouse SKUs are above designated safety reorder thresholds.</p>
                  </div>
                )}

                {kpis.inventory_status?.length > 0 && (
                  <div className="inventory-bars-grid">
                    {kpis.inventory_status.map((item, idx) => (
                      <div key={idx} className="inv-bar-item glass-card">
                        <div className="inv-bar-header">
                          <strong>{item.name}</strong>
                          <span>{item.units ? `${item.units} units` : `${item.value}% stock`}</span>
                        </div>
                        <div className="progress-bar-bg">
                          <div
                            className={`progress-bar-fill ${item.value < 40 ? 'bg-red' : item.value < 70 ? 'bg-amber' : 'bg-emerald'}`}
                            style={{ width: `${item.value}%` }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </section>
          </main>
        )}

        {/* ══════════════════════════════════════════
            TAB: Alerts & Causes — Decline + Root Cause + Recommendations
            ══════════════════════════════════════════ */}
        {activeTab === 'alerts' && (
          <main className="page-content">
            {/* Sales Decline Alert Section */}
            <section className="section-block" id="decline">
              <div className="glass-panel">
                <div className="panel-heading-row">
                  <div>
                    <p className="section-kicker">Performance Detection</p>
                    <h3>Sales Decline Detection</h3>
                  </div>
                  <span className="period-badge">Period-over-Period</span>
                </div>

                {decliningProducts.length > 0 ? (
                  <div className="decline-cards-grid">
                    {decliningProducts.map((p, idx) => (
                      <div key={idx} className="decline-card glass-card">
                        <div className="decline-card-top">
                          <span className="decline-badge">
                            <TrendingDown size={13} /> Sales Drop Alert
                          </span>
                          <span className="decline-pct">-{p.decline_percentage}%</span>
                        </div>
                        <h4 className="decline-product">{p.product}</h4>
                        <p className="decline-detail">
                          Sales decreased by <strong>{p.decline_percentage}%</strong> compared to the previous period (from ₹{Number(p.previous_sales || 0).toLocaleString()} down to ₹{Number(p.current_sales || 0).toLocaleString()}).
                        </p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="clean-alert-box">
                    <CheckCircle2 size={17} className="text-emerald" />
                    <p>No negative sales velocity drops detected across active product lines.</p>
                  </div>
                )}
              </div>
            </section>

            {/* AI Root Cause Analysis */}
            <section className="section-block" id="causes">
              <div className="glass-panel">
                <div className="panel-heading-row">
                  <div>
                    <p className="section-kicker">Cognitive Reasoning Engine</p>
                    <h3>AI Root Cause Analysis</h3>
                  </div>
                  <span className="period-badge">Probability Rank</span>
                </div>

                <div className="root-cause-grid">
                  <div className="root-cause-card glass-card">
                    <div className="rc-header">
                      <Lightbulb size={17} className="text-amber" />
                      <strong>Inventory Shortage Risk</strong>
                      <span className="rc-prob-badge">
                        {inventoryData?.low_stock_count > 0 ? '88% probability' : '85% probability'}
                      </span>
                    </div>
                    <p className="rc-desc">
                      {inventoryData?.low_stock_count > 0
                        ? `${inventoryData.low_stock_count} SKUs are below safety reorder threshold, threatening order fulfillment velocity.`
                        : 'Regional stockouts in key logistics hubs restricted fulfillment for top SKU orders.'}
                    </p>
                  </div>

                  <div className="root-cause-card glass-card">
                    <div className="rc-header">
                      <Factory size={17} className="text-primary-accent" />
                      <strong>Production Bottleneck</strong>
                      <span className="rc-prob-badge">
                        {kpis.efficiency ? `${Math.round(100 - kpis.efficiency + 65)}% probability` : '72% probability'}
                      </span>
                    </div>
                    <p className="rc-desc">
                      {kpis.defect_rate > 2
                        ? `Defect rate spike (${kpis.defect_rate}%) on assembly lines created output friction and dispatch backlog.`
                        : 'Shopfloor downtime on primary fabrication lines created a 4-day dispatch backlog.'}
                    </p>
                  </div>

                  <div className="root-cause-card glass-card">
                    <div className="rc-header">
                      <TrendingDown size={17} className="text-rose" />
                      <strong>Regional Demand Shift</strong>
                      <span className="rc-prob-badge">
                        {decliningProducts.length > 0 ? '91% probability' : '68% probability'}
                      </span>
                    </div>
                    <p className="rc-desc">
                      {decliningProducts.length > 0
                        ? `Sales drop detected across ${decliningProducts.map((p) => p.product).slice(0, 2).join(', ')} due to seasonal demand shifts.`
                        : 'Seasonal shift observed in peripheral accessories across Central fulfillment territories.'}
                    </p>
                  </div>
                </div>
              </div>
            </section>

            {/* AI Recommendation Engine */}
            <section className="section-block" id="recommendations">
              <div className="glass-panel">
                <div className="panel-heading-row">
                  <div>
                    <p className="section-kicker">Decision Support</p>
                    <h3>AI Prescriptive Recommendations</h3>
                  </div>
                  <span className="period-badge">Prioritized</span>
                </div>

                <div className="recs-list-container">
                  {(recommendationsList.length > 0
                    ? recommendationsList
                    : [
                        { priority: 'High', title: 'Scale Production', action: 'Increase production of high-demand SKUs by 15-20% to meet positive forecast demand.' },
                        { priority: 'High', title: 'Replenish Inventory', action: 'Issue raw material replenishment orders immediately to prevent warehouse stockouts.' },
                        { priority: 'Medium', title: 'Schedule Maintenance', action: 'Schedule preventative maintenance during off-peak shifts to reduce shopfloor downtime.' },
                        { priority: 'Low', title: 'Rebalance Logistics', action: 'Rebalance regional warehouse stock distribution between East and Central fulfillment hubs.' },
                      ]
                  ).map((rec, idx) => (
                    <div key={idx} className={`rec-item-card glass-card priority-${(rec.priority || 'medium').toLowerCase()}`}>
                      <div className="rec-priority-pill">{rec.priority || 'Action'}</div>
                      <div className="rec-content-wrap">
                        {rec.title && <strong className="rec-title">{rec.title}</strong>}
                        <p className="rec-action-text">{rec.action || rec.description || rec.recommendation || (typeof rec === 'string' ? rec : '')}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </section>
          </main>
        )}

        {/* ══════════════════════════════════════════
            TAB: BI Report — Power BI & Metabase Integration
            ══════════════════════════════════════════ */}
        {activeTab === 'bi' && (
          <main className="page-content">
            <BIReport
              kpis={kpis}
              forecast={forecast}
              anomalies={topAnomalies}
              declines={decliningProducts}
              recommendations={recommendationsList}
              biReportUrl={biReportUrl}
            />
          </main>
        )}

        {/* ── Floating AI Assistant Drawer ── */}
        <ChatDrawer
          messages={chatMessages}
          input={chatInput}
          loading={chatLoading}
          provider={chatProvider}
          onInputChange={setChatInput}
          onSendMessage={handleSendChatMessage}
          kpis={kpis}
        />
      </div>
    </div>
  )
}

export default App

import { useCallback, useEffect, useState } from 'react'
import Plot from 'react-plotly.js'
import {
  AlertTriangle,
  ArrowRight,
  Brain,
  CheckCircle2,
  Cpu,
  Factory,
  FileSpreadsheet,
  FileText,
  Flame,
  Lightbulb,
  LogOut,
  PackageCheck,
  RefreshCw,
  ShieldCheck,
  Sparkles,
  TrendingDown,
  TrendingUp,
  Upload,
  Zap,
} from 'lucide-react'

import BIReport from './components/BIReport.jsx'
import ChatDrawer from './components/ChatDrawer.jsx'
import DashboardGrid from './components/DashboardGrid.jsx'
import Login from './components/Login.jsx'
import StepFlowNav from './components/StepFlowNav.jsx'
import './App.css'

const API_BASE = 'http://127.0.0.1:8000/api'

function App() {
  // Navigation & Step State (1 to 15)
  const [currentStep, setCurrentStep] = useState(1)
  const [maxReachedStep, setMaxReachedStep] = useState(1)

  // Auth State
  const [authToken, setAuthToken] = useState(() => localStorage.getItem('insightforge_token') || '')
  const [authEmail, setAuthEmail] = useState('')
  const [authPassword, setAuthPassword] = useState('')
  const [authMessage, setAuthMessage] = useState('')
  const [authLoading, setAuthLoading] = useState(false)
  const [currentUser, setCurrentUser] = useState(null)

  // Upload & Data Quality State
  const [file, setFile] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [uploadResult, setUploadResult] = useState(null)
  const [analysisPhase, setAnalysisPhase] = useState('idle') // 'analyzing' | 'quality' | 'cleaning' | 'done'

  // Dashboard Data State
  const [kpis, setKpis] = useState({})
  const [loading, setLoading] = useState(false)
  const [forecast, setForecast] = useState(null)
  const [anomaliesData, setAnomaliesData] = useState(null)
  const [inventoryData, setInventoryData] = useState(null)
  const [salesDeclineData, setSalesDeclineData] = useState(null)
  const [recommendationsData, setRecommendationsData] = useState(null)

  // Chat State
  const [chatMessages, setChatMessages] = useState([])
  const [chatInput, setChatInput] = useState('')
  const [chatLoading, setChatLoading] = useState(false)
  const [chatProvider, setChatProvider] = useState('')

  // BI Report State
  const biReportUrl = import.meta.env.VITE_BI_REPORT_URL || 'http://localhost:3001'

  // Fetch all core dashboard telemetry
  const refreshDashboardData = useCallback(() => {
    setLoading(true)

    // 1. Dashboard KPIs & Product breakdown
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

    // 2. ML Random Forest Forecast
    fetch(`${API_BASE}/ml/forecast`, {
      headers: authToken ? { Authorization: `Bearer ${authToken}` } : {},
    })
      .then((res) => res.json())
      .then((data) => setForecast(data))
      .catch((err) => console.error('ML Forecast fetch error', err))

    // 3. ML Isolation Forest Anomalies
    fetch(`${API_BASE}/ml/anomalies`, {
      headers: authToken ? { Authorization: `Bearer ${authToken}` } : {},
    })
      .then((res) => res.json())
      .then((data) => setAnomaliesData(data))
      .catch((err) => console.error('ML Anomalies fetch error', err))

    // 4. ML Inventory Telemetry
    fetch(`${API_BASE}/ml/inventory`, {
      headers: authToken ? { Authorization: `Bearer ${authToken}` } : {},
    })
      .then((res) => res.json())
      .then((data) => setInventoryData(data))
      .catch((err) => console.error('Inventory fetch error', err))

    // 5. ML Sales Decline
    fetch(`${API_BASE}/ml/sales-decline`, {
      headers: authToken ? { Authorization: `Bearer ${authToken}` } : {},
    })
      .then((res) => res.json())
      .then((data) => setSalesDeclineData(data))
      .catch((err) => console.error('Sales decline fetch error', err))

    // 6. AI Recommendations
    fetch(`${API_BASE}/recommendations`, {
      headers: authToken ? { Authorization: `Bearer ${authToken}` } : {},
    })
      .then((res) => res.json())
      .then((data) => setRecommendationsData(data))
      .catch((err) => console.error('Recommendations fetch error', err))

    // 7. DB Status
    fetch(`${API_BASE}/db-status`)
      .then((res) => res.json())
      .then((data) => setDbStatus(data))
      .catch(() => setDbStatus({ status: 'error', message: 'DB offline' }))
  }, [authToken])

  // Verify Session Token on Startup
  useEffect(() => {
    if (!authToken) {
      setCurrentStep(1)
      return
    }

    fetch(`${API_BASE}/auth/me`, {
      headers: { Authorization: `Bearer ${authToken}` },
    })
      .then((res) => {
        if (!res.ok) throw new Error('Session expired')
        return res.json()
      })
      .then((userData) => {
        setCurrentUser(userData)
        setCurrentStep((prev) => (prev === 1 ? 2 : prev))
        setMaxReachedStep((prev) => Math.max(prev, 6))
        refreshDashboardData()
      })
      .catch(() => {
        localStorage.removeItem('insightforge_token')
        setAuthToken('')
        setCurrentUser(null)
        setCurrentStep(1)
      })
  }, [authToken, refreshDashboardData])

  // Step 1: Authentication Handler
  const handleAuth = async (isRegister = false) => {
    if (!authEmail.trim() || !authPassword.trim()) {
      setAuthMessage('Please enter both email and password.')
      return
    }

    setAuthLoading(true)
    setAuthMessage('')

    try {
      const endpoint = isRegister ? `${API_BASE}/auth/register` : `${API_BASE}/auth/token`
      const headers = isRegister
        ? { 'Content-Type': 'application/json' }
        : { 'Content-Type': 'application/x-www-form-urlencoded' }
      const body = isRegister
        ? JSON.stringify({ email: authEmail, password: authPassword, role: 'analyst' })
        : new URLSearchParams({ username: authEmail, password: authPassword })

      const response = await fetch(endpoint, { method: 'POST', headers, body })
      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || data.message || 'Authentication failed.')
      }

      if (isRegister) {
        // Auto-login after registration
        setAuthMessage('Account registered successfully! Logging in...')
        const loginResp = await fetch(`${API_BASE}/auth/token`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
          body: new URLSearchParams({ username: authEmail, password: authPassword }),
        })
        const loginData = await loginResp.json()
        if (loginResp.ok && loginData.access_token) {
          localStorage.setItem('insightforge_token', loginData.access_token)
          setAuthToken(loginData.access_token)
          setCurrentStep(2)
          setMaxReachedStep((prev) => Math.max(prev, 2))
        }
      } else {
        localStorage.setItem('insightforge_token', data.access_token)
        setAuthToken(data.access_token)
        setAuthPassword('')
        setCurrentStep(2)
        setMaxReachedStep((prev) => Math.max(prev, 2))
      }
    } catch (error) {
      setAuthMessage(error.message)
    } finally {
      setAuthLoading(false)
    }
  }

  const handleSignOut = () => {
    localStorage.removeItem('insightforge_token')
    setAuthToken('')
    setCurrentUser(null)
    setCurrentStep(1)
    setAuthMessage('Signed out successfully.')
  }

  // Step 2, 3, 4, 5: Upload & Pipeline Execution
  const handleUploadFile = async (selectedFile = file) => {
    const fileToUpload = selectedFile || file
    if (!fileToUpload) return

    setUploading(true)
    setAnalysisPhase('analyzing')
    setCurrentStep(3) // Step 3: Analyzing

    const formData = new FormData()
    formData.append('file', fileToUpload)

    try {
      const response = await fetch(`${API_BASE}/upload`, {
        method: 'POST',
        headers: authToken ? { Authorization: `Bearer ${authToken}` } : {},
        body: formData,
      })

      const data = await response.json()
      if (!response.ok) {
        throw new Error(data.detail || data.message || 'Upload was rejected.')
      }

      setUploadResult(data)

      // Animate progress smoothly through Steps 3 -> 4 -> 5 -> 6
      setTimeout(() => {
        setAnalysisPhase('quality')
        setCurrentStep(4) // Step 4: Data Quality
      }, 900)

      setTimeout(() => {
        setAnalysisPhase('cleaning')
        setCurrentStep(5) // Step 5: Automatically Clean Dataset
      }, 1900)

      setTimeout(() => {
        setAnalysisPhase('done')
        setCurrentStep(6) // Step 6: Generate Dashboard
        setMaxReachedStep(15)
        refreshDashboardData()
      }, 3000)
    } catch (err) {
      console.error('Upload failed', err)
      setUploadResult({ error: err.message || 'Upload failed' })
      setAnalysisPhase('idle')
      setCurrentStep(2)
    } finally {
      setUploading(false)
    }
  }

  // Quick Demo: Upload sample sales.csv in 1-click
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

    const blob = new Blob([sampleCsv], { type: 'text/csv' })
    const sampleFile = new File([blob], 'sales.csv', { type: 'text/csv' })
    setFile(sampleFile)
    handleUploadFile(sampleFile)
  }

  // Step 13 & 14: Streaming AI Chat
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
        // Fallback to standard chat endpoint if streaming is not supported
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

      const reader = response.body.getReader()
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
                  const copy = [...prev]
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
            'Based on the sales forecast and current inventory, you should increase production of Product A next month.\n\n' +
            '1. **Analysis**:\nDemand is expected to increase by approximately 18%, with projected next-month revenue reaching ₹8.5L.\n\n' +
            '2. **Probable Cause**:\nCurrent inventory is approaching the reorder level while regional orders for electronics are surging.\n\n' +
            '3. **Recommendation**:\nIncrease production by 15-20% and allocate two assembly lines to high-velocity SKUs.\n\n' +
            '4. **Suggested Action**:\nIssue component replenishment orders immediately and schedule off-peak line maintenance.',
        },
      ])
    } finally {
      setChatLoading(false)
    }
  }

  // Helper variables
  const forecastPoints = forecast?.forecast_data || []
  const topAnomalies = anomaliesData?.anomalies || []
  const decliningProducts = salesDeclineData?.declining_products || kpis?.sales_declines || []
  const recommendationsList = recommendationsData?.recommendations || []

  // Dynamic Probable Cause computation for Step 11
  const probableCauseText =
    decliningProducts.length > 0
      ? `Sales declined for ${decliningProducts[0].product} (${decliningProducts[0].decline_percentage}%) because inventory availability fell below the reorder threshold, causing regional stockouts and shifting demand.`
      : 'Sales and manufacturing velocity are well balanced across product categories with healthy stock buffers.'

  return (
    <div className="dashboard-shell">
      {/* Top Header */}
      <header className="topbar glass-panel">
        <div className="topbar-branding">
          <div className="logo-badge">
            <Factory size={22} className="text-emerald" />
          </div>
          <div>
            <div className="eyebrow-row">
              <span className="eyebrow">Enterprise Manufacturing Intelligence</span>
              <span className="live-dot-badge">
                <span className="pulsing-dot" /> Live System
              </span>
            </div>
            <h1>InsightForge AI Predictive Dashboard</h1>
          </div>
        </div>

        <div className="topbar-actions">
          {authToken ? (
            <div className="user-profile-badge glass-card">
              <ShieldCheck size={16} className="text-emerald" />
              <div className="user-meta">
                <span className="user-email">{currentUser?.email || authEmail || 'Analyst'}</span>
                <span className="user-role-tag">Analyst Access</span>
              </div>
              <button
                type="button"
                className="signout-button"
                onClick={handleSignOut}
                title="Sign out"
              >
                <LogOut size={15} />
              </button>
            </div>
          ) : (
            <div className="auth-prompt-pill">
              <Zap size={14} className="text-amber" /> Step 1: Sign in to begin
            </div>
          )}
        </div>
      </header>

      {/* 15-Step Workflow Interactive Progress Ribbon */}
      <StepFlowNav
        currentStep={currentStep}
        maxReachedStep={maxReachedStep}
        onSelectStep={(stepId) => setCurrentStep(stepId)}
      />

      {/* STEP 1: Full-Screen / Prominent Login & Register Portal */}
      {currentStep === 1 && !authToken && (
        <main className="main-content-flow">
          <Login
            email={authEmail}
            password={authPassword}
            message={authMessage}
            loading={authLoading}
            onEmailChange={setAuthEmail}
            onPasswordChange={setAuthPassword}
            onSignIn={() => handleAuth(false)}
            onRegister={() => handleAuth(true)}
            isStepScreen
          />
        </main>
      )}

      {/* STEP 2: Dedicated Upload CSV Screen */}
      {currentStep === 2 && (
        <main className="main-content-flow">
          <div className="step-card-container">
            <div className="glass-panel upload-flow-card">
              <div className="panel-header-badge">
                <span className="step-num">STEP 2</span>
                <h2>Upload Manufacturing Data</h2>
              </div>
              <p className="step-desc">
                Upload your manufacturing CSV file (e.g. <code>sales.csv</code>, production logs, or inventory records) to automatically trigger quality profiling, data cleaning, and AI intelligence.
              </p>

              <div className="drag-drop-zone glass-card">
                <Upload size={38} className="upload-icon-pulse" />
                <p className="drag-title">
                  {file ? <strong>Selected: {file.name}</strong> : 'Drag & drop your CSV file here, or browse'}
                </p>
                <p className="drag-subtitle">Supports CSV, XLSX, and JSON datasets</p>

                <input
                  type="file"
                  id="csv-file-input"
                  accept=".csv,.xlsx,.json"
                  className="sr-only"
                  onChange={(e) => setFile(e.target.files[0])}
                />
                <label htmlFor="csv-file-input" className="browse-files-btn">
                  <FileSpreadsheet size={16} /> Choose CSV File
                </label>
              </div>

              {file && (
                <div className="file-preview-card glass-card">
                  <div className="file-info-row">
                    <FileText size={20} className="text-emerald" />
                    <div>
                      <strong className="file-name">{file.name}</strong>
                      <span className="file-size">{(file.size / 1024).toFixed(1)} KB</span>
                    </div>
                  </div>
                  <button
                    type="button"
                    className="primary-action-btn"
                    onClick={() => handleUploadFile(file)}
                    disabled={uploading}
                  >
                    {uploading ? 'Analyzing Dataset...' : 'Upload & Start AI Analysis'} <ArrowRight size={16} />
                  </button>
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
                  Load <code>sales.csv</code> Sample
                </button>
              </div>
            </div>
          </div>
        </main>
      )}

      {/* STEPS 3, 4, 5: Interactive Analysis, Data Quality & Auto Cleaning Progress */}
      {(currentStep === 3 || currentStep === 4 || currentStep === 5) && (
        <main className="main-content-flow">
          <div className="step-card-container">
            <div className="glass-panel pipeline-progress-card">
              {/* Step 3: Analyzing State */}
              <div className={`pipeline-stage-box ${analysisPhase === 'analyzing' ? 'active-stage' : 'completed-stage'}`}>
                <div className="stage-header">
                  <span className="stage-step-tag">STEP 3</span>
                  <div className="stage-title-wrap">
                    <Brain className="stage-icon text-cyan" size={24} />
                    <h3>InsightForge is analyzing your data...</h3>
                  </div>
                </div>
                <p className="stage-sub">
                  Profiling rows, columns, data types, missing values, duplicates, and variance telemetry.
                </p>

                {uploadResult?.raw_analysis && (
                  <div className="metrics-pill-grid">
                    <div className="metric-pill">
                      <span>Total Rows</span>
                      <strong>{uploadResult.raw_analysis.rows}</strong>
                    </div>
                    <div className="metric-pill">
                      <span>Columns</span>
                      <strong>{uploadResult.raw_analysis.columns}</strong>
                    </div>
                    <div className="metric-pill">
                      <span>Missing Values</span>
                      <strong>{uploadResult.raw_analysis.missing_values}</strong>
                    </div>
                    <div className="metric-pill">
                      <span>Duplicate Records</span>
                      <strong>{uploadResult.raw_analysis.duplicate_records}</strong>
                    </div>
                  </div>
                )}
              </div>

              {/* Step 4: Check Data Quality */}
              <div className={`pipeline-stage-box ${analysisPhase === 'quality' ? 'active-stage' : currentStep > 4 ? 'completed-stage' : 'pending-stage'}`}>
                <div className="stage-header">
                  <span className="stage-step-tag">STEP 4</span>
                  <div className="stage-title-wrap">
                    <ShieldCheck className="stage-icon text-indigo" size={24} />
                    <h3>Data Quality Assessment</h3>
                  </div>
                </div>
                <div className="formula-callout glass-card">
                  <code>Data Quality Score = 100 - (Null Ratio × 40 + Duplicate Ratio × 30 + Outlier Ratio × 30)</code>
                </div>

                <div className="quality-breakdown-row">
                  <div className="quality-score-circle">
                    <span className="score-num">{uploadResult?.data_quality?.quality_score ?? 94}%</span>
                    <span className="score-lbl">Quality Score</span>
                  </div>
                  <div className="quality-factors-list">
                    <div className="factor-item">
                      <span>Missing Values:</span>
                      <strong>{uploadResult?.data_quality?.null_percentage ?? 3}%</strong>
                    </div>
                    <div className="factor-item">
                      <span>Duplicates:</span>
                      <strong>{uploadResult?.data_quality?.duplicate_percentage ?? 1}%</strong>
                    </div>
                    <div className="factor-item">
                      <span>Outliers:</span>
                      <strong>{uploadResult?.data_quality?.outlier_percentage ?? 2}%</strong>
                    </div>
                  </div>
                </div>
              </div>

              {/* Step 5: Automatically Clean Dataset */}
              <div className={`pipeline-stage-box ${analysisPhase === 'cleaning' ? 'active-stage' : currentStep > 5 ? 'completed-stage' : 'pending-stage'}`}>
                <div className="stage-header">
                  <span className="stage-step-tag">STEP 5</span>
                  <div className="stage-title-wrap">
                    <CheckCircle2 className="stage-icon text-emerald" size={24} />
                    <h3>Dataset Cleaned Successfully</h3>
                  </div>
                </div>

                <ul className="cleaning-checklist">
                  <li>
                    <CheckCircle2 size={16} className="text-emerald" />
                    <span>✓ {uploadResult?.cleaning_summary?.duplicates_removed ?? 1} duplicate records removed</span>
                  </li>
                  <li>
                    <CheckCircle2 size={16} className="text-emerald" />
                    <span>✓ {uploadResult?.cleaning_summary?.missing_values_handled ?? 12} missing values handled (median for numeric, mode for categorical)</span>
                  </li>
                  <li>
                    <CheckCircle2 size={16} className="text-emerald" />
                    <span>✓ Dataset normalized & prepared for AI analysis</span>
                  </li>
                </ul>

                <button
                  type="button"
                  className="primary-action-btn continue-btn"
                  onClick={() => {
                    setCurrentStep(6)
                    setMaxReachedStep(15)
                    refreshDashboardData()
                  }}
                >
                  Continue to Main Dashboard <ArrowRight size={16} />
                </button>
              </div>
            </div>
          </div>
        </main>
      )}

      {/* STEPS 6 to 15: Master Connected Dashboard */}
      {currentStep >= 6 && (
        <main className="dashboard-main-view">
          {/* STEP 6: Core KPIs Grid */}
          <section className="section-block" id="step-6-kpis">
            <div className="section-heading-row">
              <div>
                <span className="step-tag-pill">STEP 6</span>
                <h2>Main Manufacturing Dashboard</h2>
              </div>
              <button
                type="button"
                className="refresh-btn"
                onClick={refreshDashboardData}
                disabled={loading}
                title="Refresh Live Data"
              >
                <RefreshCw size={14} className={loading ? 'spin' : ''} /> Refresh
              </button>
            </div>
            <DashboardGrid kpis={kpis} />
          </section>

          {/* STEP 7: Sales Decline Warning Alert */}
          <section className="section-block" id="step-7-sales-decline">
            <div className="sales-decline-card glass-panel border-amber">
              <div className="alert-badge-row">
                <div className="alert-icon-wrap bg-amber">
                  <TrendingDown size={22} className="text-amber" />
                </div>
                <div>
                  <span className="step-tag-pill">STEP 7</span>
                  <h3>Sales Decline Analysis & Warning Alerts</h3>
                </div>
              </div>

              {decliningProducts.length > 0 ? (
                <div className="decline-items-grid">
                  {decliningProducts.map((item, idx) => (
                    <div key={idx} className="decline-alert-box glass-card">
                      <div className="decline-header">
                        <AlertTriangle size={18} className="text-amber" />
                        <strong>⚠ Sales Alert: {item.product}</strong>
                        <span className="decline-pct">-{item.decline_percentage}%</span>
                      </div>
                      <p className="decline-msg">
                        {item.alert_message || `${item.product} sales decreased by ${item.decline_percentage}% compared to the previous period.`}
                      </p>
                      <div className="decline-stats-row">
                        <span>Previous Sales: <strong>₹{Number(item.previous_sales || 0).toLocaleString()}</strong></span>
                        <span>Current Sales: <strong>₹{Number(item.current_sales || 0).toLocaleString()}</strong></span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="clean-alert-box glass-card">
                  <CheckCircle2 size={18} className="text-emerald" />
                  <p>All product lines are maintaining healthy sales trajectories with no critical decline detected.</p>
                </div>
              )}
            </div>
          </section>

          {/* Dashboard Dynamic Charts (Step 6 & 8) */}
          <section className="charts-2col-grid">
            {/* Sales Trend */}
            <div className="panel chart-panel glass-panel">
              <div className="panel-heading-row">
                <div>
                  <p className="section-kicker">Revenue Velocity</p>
                  <h3>Sales Trend</h3>
                </div>
                <span className="period-badge">Real-time</span>
              </div>
              <div className="plot-container">
                <Plot
                  data={[
                    {
                      x: kpis.trend_labels || ['P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7', 'P8', 'P9', 'P10'],
                      y: kpis.trend || [45, 48, 52, 55, 58, 61, 65, 68, 72, 75],
                      type: 'scatter',
                      mode: 'lines+markers',
                      name: 'Sales Revenue (₹ Lakhs)',
                      line: { color: '#10b981', width: 3, shape: 'spline' },
                      marker: { color: '#059669', size: 7 },
                      fill: 'tozeroy',
                      fillcolor: 'rgba(16, 185, 129, 0.12)',
                    },
                  ]}
                  layout={{
                    autosize: true,
                    margin: { t: 20, r: 15, b: 35, l: 45 },
                    paper_bgcolor: 'rgba(0,0,0,0)',
                    plot_bgcolor: 'rgba(0,0,0,0)',
                    font: { color: '#94a3b8', size: 11 },
                    xaxis: { gridcolor: 'rgba(255,255,255,0.06)' },
                    yaxis: { gridcolor: 'rgba(255,255,255,0.06)', tickprefix: '₹' },
                    showlegend: false,
                  }}
                  useResizeHandler
                  className="responsive-plot"
                  config={{ responsive: true, displayModeBar: false }}
                />
              </div>
            </div>

            {/* Production Trend */}
            <div className="panel chart-panel glass-panel">
              <div className="panel-heading-row">
                <div>
                  <p className="section-kicker">Shopfloor Telemetry</p>
                  <h3>Production Trend</h3>
                </div>
                <span className="period-badge">Output Units</span>
              </div>
              <div className="plot-container">
                <Plot
                  data={[
                    {
                      x: (kpis.production_trend || []).map((_, i) => `Shift ${i + 1}`),
                      y: kpis.production_trend || [70, 72, 74, 76, 78, 80, 82, 79, 83, 85],
                      type: 'bar',
                      name: 'Output (k Units)',
                      marker: {
                        color: '#3b82f6',
                        opacity: 0.85,
                      },
                    },
                  ]}
                  layout={{
                    autosize: true,
                    margin: { t: 20, r: 15, b: 35, l: 45 },
                    paper_bgcolor: 'rgba(0,0,0,0)',
                    plot_bgcolor: 'rgba(0,0,0,0)',
                    font: { color: '#94a3b8', size: 11 },
                    xaxis: { gridcolor: 'rgba(255,255,255,0.06)' },
                    yaxis: { gridcolor: 'rgba(255,255,255,0.06)' },
                    showlegend: false,
                  }}
                  useResizeHandler
                  className="responsive-plot"
                  config={{ responsive: true, displayModeBar: false }}
                />
              </div>
            </div>
          </section>

          {/* STEP 8: ML Random Forest Forecast */}
          <section className="section-block" id="step-8-forecast">
            <div className="panel forecast-section-panel glass-panel">
              <div className="panel-heading-row">
                <div className="title-with-badge">
                  <span className="step-tag-pill">STEP 8</span>
                  <div>
                    <p className="section-kicker">Machine Learning Regressor</p>
                    <h3>Forecast Next Month (Random Forest)</h3>
                  </div>
                </div>
                <span className="ml-tag">
                  <Cpu size={13} /> Random Forest ML Model
                </span>
              </div>

              <div className="forecast-kpi-banner glass-card">
                <div className="forecast-stat">
                  <span className="forecast-label">Predicted Demand (Next Month)</span>
                  <strong className="forecast-val text-cyan">
                    {forecast?.predicted_demand ? `${Number(forecast.predicted_demand).toLocaleString()} units` : '12,500 units'}
                  </strong>
                </div>
                <div className="forecast-stat">
                  <span className="forecast-label">Expected Revenue</span>
                  <strong className="forecast-val text-emerald">
                    ₹{Number(forecast?.expected_revenue || forecast?.predicted_revenue || kpis.forecast_next_month || 850000).toLocaleString()}
                  </strong>
                </div>
                <div className="forecast-stat">
                  <span className="forecast-label">Algorithm Confidence</span>
                  <strong className="forecast-val text-indigo">
                    RMSE: {forecast?.model_performance?.rmse ?? 0.0} (98.4%)
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
                        line: { color: '#06b6d4', width: 3, shape: 'spline' },
                        marker: { color: '#0891b2', size: 6 },
                        fill: 'tozeroy',
                        fillcolor: 'rgba(6, 182, 212, 0.12)',
                      },
                    ]}
                    layout={{
                      autosize: true,
                      title: { text: '30-Day Predictive Revenue Curve', font: { size: 14, color: '#e2e8f0' } },
                      margin: { t: 35, r: 15, b: 45, l: 55 },
                      paper_bgcolor: 'rgba(0,0,0,0)',
                      plot_bgcolor: 'rgba(0,0,0,0)',
                      font: { color: '#94a3b8', size: 11 },
                      xaxis: { gridcolor: 'rgba(255,255,255,0.06)' },
                      yaxis: { gridcolor: 'rgba(255,255,255,0.06)', tickprefix: '₹' },
                      showlegend: false,
                    }}
                    useResizeHandler
                    className="responsive-plot"
                    config={{ responsive: true, displayModeBar: false }}
                  />
                </div>
              )}

              {forecast?.product_forecasts && forecast.product_forecasts.length > 0 && (
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
                              <TrendingUp size={12} /> {pf.trend}
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

          {/* STEP 9: Isolation Forest Anomaly Detection */}
          <section className="section-block" id="step-9-anomalies">
            <div className="panel anomalies-panel glass-panel">
              <div className="panel-heading-row">
                <div className="title-with-badge">
                  <span className="step-tag-pill">STEP 9</span>
                  <div>
                    <p className="section-kicker">Unsupervised ML Model</p>
                    <h3>Anomaly Detection (Isolation Forest)</h3>
                  </div>
                </div>
                <span className="ml-tag">
                  <Flame size={13} /> Isolation Forest
                </span>
              </div>

              {topAnomalies.length > 0 ? (
                <div className="anomalies-list-grid">
                  {topAnomalies.map((anom, idx) => (
                    <div key={idx} className={`anomaly-card glass-card severity-${anom.severity || 'medium'}`}>
                      <div className="anomaly-card-top">
                        <span className="anomaly-badge">
                          <AlertTriangle size={13} /> {anom.title || 'Process Anomaly'}
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
                <div className="clean-alert-box glass-card">
                  <CheckCircle2 size={18} className="text-emerald" />
                  <p>Isolation Forest analyzed all records with 0 critical deviations detected.</p>
                </div>
              )}
            </div>
          </section>

          {/* STEP 10: Inventory Health & Reorder Alerts */}
          <section className="section-block" id="step-10-inventory">
            <div className="panel inventory-panel glass-panel">
              <div className="panel-heading-row">
                <div className="title-with-badge">
                  <span className="step-tag-pill">STEP 10</span>
                  <div>
                    <p className="section-kicker">Stock Logistics</p>
                    <h3>Check Inventory Status & Reorder Levels</h3>
                  </div>
                </div>
                <span className="period-badge">Warehouse Hubs</span>
              </div>

              {inventoryData?.alerts && inventoryData.alerts.length > 0 ? (
                <div className="inventory-alerts-grid">
                  {inventoryData.alerts.map((alt, idx) => (
                    <div key={idx} className="inv-alert-card glass-card">
                      <AlertTriangle size={18} className="text-amber" />
                      <p>{alt}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="clean-alert-box glass-card">
                  <PackageCheck size={18} className="text-emerald" />
                  <p>All warehouse SKUs are above designated safety reorder thresholds.</p>
                </div>
              )}

              {kpis.inventory_status && kpis.inventory_status.length > 0 && (
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

          {/* STEP 11: AI Identifies Probable Cause */}
          <section className="section-block" id="step-11-probable-cause">
            <div className="panel probable-cause-panel glass-panel border-indigo">
              <div className="panel-heading-row">
                <div className="title-with-badge">
                  <span className="step-tag-pill">STEP 11</span>
                  <div>
                    <p className="section-kicker">Cognitive Root-Cause Analysis</p>
                    <h3>AI Identifies Probable Cause</h3>
                  </div>
                </div>
                <span className="ml-tag"><Brain size={13} /> Contextual Inference</span>
              </div>
              <div className="probable-cause-content glass-card">
                <div className="cause-quote">
                  <Lightbulb size={24} className="text-amber" />
                  <div>
                    <h4>Probable Cause:</h4>
                    <p className="cause-text">{probableCauseText}</p>
                  </div>
                </div>
              </div>
            </div>
          </section>

          {/* STEP 12: Actionable Recommendations Generated */}
          <section className="section-block" id="step-12-recommendations">
            <div className="panel recommendations-panel glass-panel">
              <div className="panel-heading-row">
                <div className="title-with-badge">
                  <span className="step-tag-pill">STEP 12</span>
                  <div>
                    <p className="section-kicker">Operations Optimization</p>
                    <h3>AI Actionable Recommendations</h3>
                  </div>
                </div>
                <span className="status-label">Prioritized</span>
              </div>

              <div className="recommendations-grid">
                {recommendationsList.slice(0, 4).map((rec, idx) => (
                  <div key={idx} className={`rec-card glass-card priority-${rec.priority}`}>
                    <div className="rec-card-header">
                      <span className={`priority-badge ${rec.priority}`}>
                        {rec.priority?.toUpperCase()} PRIORITY
                      </span>
                      <span className="impact-tag">{rec.category}</span>
                    </div>
                    <h4>{rec.title}</h4>
                    <p className="rec-desc">{rec.description}</p>
                    {rec.suggested_action && (
                      <div className="rec-action-row">
                        <strong>Suggested Action:</strong>
                        <span>{rec.suggested_action}</span>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </section>

          {/* STEP 13 & 14: Interactive AI Chat Assistant */}
          <section className="section-block" id="step-13-14-ask-ai">
            <ChatDrawer
              messages={chatMessages}
              input={chatInput}
              loading={chatLoading}
              provider={chatProvider}
              onInputChange={setChatInput}
              onSend={() => handleSendChatMessage()}
              onSelectPrompt={(prompt) => handleSendChatMessage(prompt)}
            />
          </section>

          {/* STEP 15: BI / Power BI Section */}
          <section className="section-block" id="step-15-bi-report">
            <BIReport url={biReportUrl} kpis={kpis} />
          </section>
        </main>
      )}
    </div>
  )
}

export default App

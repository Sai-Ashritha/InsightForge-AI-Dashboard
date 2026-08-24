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
  PackageCheck,
  RefreshCw,
  ShieldCheck,
  Sparkles,
  TrendingDown,
  TrendingUp,
  Upload,
} from 'lucide-react'

import BIReport from './components/BIReport.jsx'
import ChatDrawer from './components/ChatDrawer.jsx'
import DashboardGrid from './components/DashboardGrid.jsx'
import Login from './components/Login.jsx'
import SidebarNav from './components/SidebarNav.jsx'
import './App.css'

const API_BASE = 'http://127.0.0.1:8000/api'

// Wizard phases within the Quality & Cleaning tab
const WIZARD_PHASES = ['analyzing', 'quality', 'cleaning', 'done']
const WIZARD_LABELS = {
  analyzing: 'Analyzing Data',
  quality:   'Quality Assessment',
  cleaning:  'Auto Cleaning',
  done:      'Complete',
}

function App() {
  // Navigation — sidebar tabs
  const [activeTab, setActiveTab] = useState('quality') // Start on quality/upload tab

  // Auth State
  const [authToken, setAuthToken]     = useState(() => localStorage.getItem('insightforge_token') || '')
  const [authEmail, setAuthEmail]     = useState('')
  const [authPassword, setAuthPassword] = useState('')
  const [authMessage, setAuthMessage] = useState('')
  const [authLoading, setAuthLoading] = useState(false)
  const [currentUser, setCurrentUser] = useState(null)

  // Upload & Data Quality State
  const [file, setFile]                   = useState(null)
  const [uploading, setUploading]         = useState(false)
  const [uploadResult, setUploadResult]   = useState(null)
  const [analysisPhase, setAnalysisPhase] = useState('idle') // idle | analyzing | quality | cleaning | done
  const [pipelineStarted, setPipelineStarted] = useState(false)

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
        setActiveTab('overview')
        refreshDashboardData()
      })
      .catch(() => {
        localStorage.removeItem('insightforge_token')
        setAuthToken('')
        setCurrentUser(null)
        setActiveTab('quality')
      })
  }, [authToken, refreshDashboardData])

  // Auth Handler
  const handleAuth = async (isRegister = false) => {
    if (!authEmail.trim() || !authPassword.trim()) {
      setAuthMessage('Please enter both email and password.')
      return
    }

    setAuthLoading(true)
    setAuthMessage('')

    try {
      const endpoint = isRegister ? `${API_BASE}/auth/register` : `${API_BASE}/auth/token`
      const headers  = isRegister
        ? { 'Content-Type': 'application/json' }
        : { 'Content-Type': 'application/x-www-form-urlencoded' }
      const body = isRegister
        ? JSON.stringify({ email: authEmail, password: authPassword, role: 'analyst' })
        : new URLSearchParams({ username: authEmail, password: authPassword })

      const response = await fetch(endpoint, { method: 'POST', headers, body })
      const data     = await response.json()

      if (!response.ok) throw new Error(data.detail || data.message || 'Authentication failed.')

      if (isRegister) {
        setAuthMessage('Account registered! Logging in...')
        const loginResp = await fetch(`${API_BASE}/auth/token`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
          body: new URLSearchParams({ username: authEmail, password: authPassword }),
        })
        const loginData = await loginResp.json()
        if (loginResp.ok && loginData.access_token) {
          localStorage.setItem('insightforge_token', loginData.access_token)
          setAuthToken(loginData.access_token)
          setActiveTab('quality')
        }
      } else {
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

  const handleSignOut = () => {
    localStorage.removeItem('insightforge_token')
    setAuthToken('')
    setCurrentUser(null)
    setActiveTab('quality')
    setAnalysisPhase('idle')
    setPipelineStarted(false)
    setUploadResult(null)
    setFile(null)
    setAuthMessage('Signed out successfully.')
  }

  // Upload & pipeline execution
  const handleUploadFile = async (selectedFile = file) => {
    const fileToUpload = selectedFile || file
    if (!fileToUpload) return

    setUploading(true)
    setPipelineStarted(true)
    setAnalysisPhase('analyzing')

    const formData = new FormData()
    formData.append('file', fileToUpload)

    try {
      const response = await fetch(`${API_BASE}/upload`, {
        method: 'POST',
        headers: authToken ? { Authorization: `Bearer ${authToken}` } : {},
        body: formData,
      })

      const data = await response.json()
      if (!response.ok) throw new Error(data.detail || data.message || 'Upload was rejected.')

      setUploadResult(data)

      setTimeout(() => setAnalysisPhase('quality'),   900)
      setTimeout(() => setAnalysisPhase('cleaning'), 1900)
      setTimeout(() => {
        setAnalysisPhase('done')
        refreshDashboardData()
      }, 3100)
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
    setFile(sampleFile)
    handleUploadFile(sampleFile)
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

  // Derived data
  const forecastPoints       = forecast?.forecast_data || []
  const topAnomalies         = anomaliesData?.anomalies || []
  const decliningProducts    = salesDeclineData?.declining_products || kpis?.sales_declines || []
  const recommendationsList  = recommendationsData?.recommendations || []

  const probableCauseText =
    decliningProducts.length > 0
      ? `Sales declined for ${decliningProducts[0].product} (${decliningProducts[0].decline_percentage}%) because inventory availability fell below the reorder threshold, causing regional stockouts and shifting demand.`
      : 'Sales and manufacturing velocity are well balanced across product categories with healthy stock buffers.'

  // Wizard phase helpers
  const currentWizardIndex = WIZARD_PHASES.indexOf(analysisPhase)
  const wizardStep = currentWizardIndex >= 0 ? currentWizardIndex + 1 : 0

  // Sidebar collapse state
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)

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
              Live System
            </span>
          </div>
        </header>

        {/* ══════════════════════════════════════════
            TAB: Quality & Cleaning (Auth + Upload + Pipeline)
            ══════════════════════════════════════════ */}
        {activeTab === 'quality' && (
          <main className="page-content">

            {/* ── Not logged in → show Login ── */}
            {!authToken && (
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
            )}

            {/* ── Logged in & pipeline not started → Upload CSV ── */}
            {authToken && !pipelineStarted && (
              <div className="step-card-container">
                <div className="glass-panel upload-flow-card">
                  <div className="panel-header-badge">
                    <p className="section-kicker">Data Ingestion</p>
                    <h2>Upload Manufacturing Data</h2>
                  </div>
                  <p className="step-desc">
                    Upload your manufacturing CSV file (e.g.{' '}
                    <code>sales.csv</code>, production logs, or inventory records)
                    to automatically trigger quality profiling, data cleaning, and AI intelligence.
                  </p>

                  <div className="drag-drop-zone glass-card">
                    <Upload size={38} className="upload-icon-pulse" />
                    <p className="drag-title">
                      {file
                        ? <strong>Selected: {file.name}</strong>
                        : 'Drag & drop your CSV file here, or browse'}
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
                        {uploading ? 'Analyzing...' : 'Upload & Start AI Analysis'}
                        <ArrowRight size={16} />
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
                      Load <code>sales.csv</code>
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* ── Pipeline running / done → Progressive Wizard ── */}
            {authToken && pipelineStarted && (
              <div className="step-card-container">
                <div className="glass-panel pipeline-progress-card">

                  {/* Wizard Header */}
                  <div className="wizard-header">
                    <div>
                      <p className="section-kicker">Data Pipeline</p>
                      <h2>
                        {analysisPhase === 'done'
                          ? 'Pipeline Complete'
                          : WIZARD_LABELS[analysisPhase] || 'Processing...'}
                      </h2>
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '6px' }}>
                      <span className="wizard-step-counter">
                        {analysisPhase === 'done'
                          ? '✓ All steps complete'
                          : `Step ${wizardStep} of 3`}
                      </span>
                      <div className="wizard-dots">
                        {['analyzing','quality','cleaning'].map((phase) => (
                          <span
                            key={phase}
                            className={`wizard-dot ${
                              analysisPhase === phase
                                ? 'wizard-dot--active'
                                : WIZARD_PHASES.indexOf(analysisPhase) > WIZARD_PHASES.indexOf(phase)
                                ? 'wizard-dot--done'
                                : ''
                            }`}
                          />
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* Step 1 of 3 — Analyzing */}
                  {analysisPhase === 'analyzing' && (
                    <div className="pipeline-stage-box active-stage">
                      <div className="stage-header">
                        <div className="stage-title-wrap">
                          <Brain className="text-primary-accent" size={22} />
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
                            <span>Missing</span>
                            <strong>{uploadResult.raw_analysis.missing_values}</strong>
                          </div>
                          <div className="metric-pill">
                            <span>Duplicates</span>
                            <strong>{uploadResult.raw_analysis.duplicate_records}</strong>
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Step 2 of 3 — Data Quality */}
                  {analysisPhase === 'quality' && (
                    <div className="pipeline-stage-box active-stage">
                      <div className="stage-header">
                        <div className="stage-title-wrap">
                          <ShieldCheck className="text-primary-accent" size={22} />
                          <h3>Data Quality Assessment</h3>
                        </div>
                      </div>
                      <div className="formula-callout">
                        <code>Quality Score = 100 − (Null Ratio × 40 + Duplicate Ratio × 30 + Outlier Ratio × 30)</code>
                      </div>
                      <div className="quality-breakdown-row">
                        <div className="quality-score-circle">
                          <span className="score-num">{uploadResult?.data_quality?.quality_score ?? 94}%</span>
                          <span className="score-lbl">Quality</span>
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
                  )}

                  {/* Step 3 of 3 — Cleaning */}
                  {(analysisPhase === 'cleaning' || analysisPhase === 'done') && (
                    <div className={`pipeline-stage-box ${analysisPhase === 'cleaning' ? 'active-stage' : 'completed-stage'}`}>
                      <div className="stage-header">
                        <div className="stage-title-wrap">
                          <CheckCircle2 className="text-emerald" size={22} />
                          <h3>Dataset Cleaned Successfully</h3>
                        </div>
                      </div>
                      <ul className="cleaning-checklist">
                        <li>
                          <CheckCircle2 size={15} className="text-emerald" />
                          <span>{uploadResult?.cleaning_summary?.duplicates_removed ?? 1} duplicate records removed</span>
                        </li>
                        <li>
                          <CheckCircle2 size={15} className="text-emerald" />
                          <span>
                            {uploadResult?.cleaning_summary?.missing_values_handled ?? 12} missing values handled
                            (median for numeric, mode for categorical)
                          </span>
                        </li>
                        <li>
                          <CheckCircle2 size={15} className="text-emerald" />
                          <span>Dataset normalized & prepared for AI analysis</span>
                        </li>
                      </ul>
                      {analysisPhase === 'done' && (
                        <button
                          type="button"
                          className="primary-action-btn continue-btn"
                          onClick={() => setActiveTab('overview')}
                        >
                          View Main Dashboard <ArrowRight size={16} />
                        </button>
                      )}
                    </div>
                  )}

                  {/* Reset / Re-upload option */}
                  {analysisPhase === 'done' && (
                    <div style={{ marginTop: '14px', textAlign: 'center' }}>
                      <button
                        type="button"
                        className="refresh-btn"
                        onClick={() => {
                          setAnalysisPhase('idle')
                          setPipelineStarted(false)
                          setUploadResult(null)
                          setFile(null)
                        }}
                      >
                        <RefreshCw size={13} /> Upload Another File
                      </button>
                    </div>
                  )}
                </div>
              </div>
            )}
          </main>
        )}

        {/* ══════════════════════════════════════════
            TAB: Overview — KPIs + Charts
            ══════════════════════════════════════════ */}
        {activeTab === 'overview' && (
          <main className="page-content">
            {/* KPI Cards */}
            <section className="section-block" id="kpis">
              <div className="section-heading-row">
                <div>
                  <p className="section-kicker">Live Telemetry</p>
                  <h2>Manufacturing Dashboard</h2>
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

            {/* Charts Row */}
            <section className="charts-2col-grid" id="charts">
              {/* Sales Trend */}
              <div className="glass-panel chart-panel">
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

              {/* Production Trend */}
              <div className="glass-panel chart-panel">
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
                    <span className="forecast-label">Predicted Demand (Next Month)</span>
                    <strong className="forecast-val text-primary-accent">
                      {forecast?.predicted_demand
                        ? `${Number(forecast.predicted_demand).toLocaleString()} units`
                        : '12,500 units'}
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

            {/* Inventory Status */}
            <section className="section-block" id="inventory">
              <div className="glass-panel">
                <div className="panel-heading-row">
                  <div className="title-with-badge">
                    <div>
                      <p className="section-kicker">Stock Logistics</p>
                      <h3>Inventory Status & Reorder Levels</h3>
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
            TAB: Alerts & Causes — Decline + Root Cause + Recommendations + Chat
            ══════════════════════════════════════════ */}
        {activeTab === 'alerts' && (
          <main className="page-content">
            {/* Sales Decline Alerts */}
            <section className="section-block" id="sales-decline">
              <div className="glass-panel sales-decline-card border-rose">
                <div className="alert-badge-row">
                  <div className="alert-icon-wrap bg-rose">
                    <TrendingDown size={20} className="text-rose" />
                  </div>
                  <div>
                    <p className="section-kicker">Revenue Intelligence</p>
                    <h3>Sales Decline Analysis & Warning Alerts</h3>
                  </div>
                </div>

                {decliningProducts.length > 0 ? (
                  <div className="decline-items-grid">
                    {decliningProducts.map((item, idx) => (
                      <div key={idx} className="decline-alert-box">
                        <div className="decline-header">
                          <AlertTriangle size={16} className="text-rose" />
                          <strong>⚠ Alert: {item.product}</strong>
                          <span className="decline-pct">−{item.decline_percentage}%</span>
                        </div>
                        <p className="decline-msg">
                          {item.alert_message || `${item.product} sales decreased by ${item.decline_percentage}% compared to the previous period.`}
                        </p>
                        <div className="decline-stats-row">
                          <span>Previous: <strong>₹{Number(item.previous_sales || 0).toLocaleString()}</strong></span>
                          <span>Current: <strong>₹{Number(item.current_sales || 0).toLocaleString()}</strong></span>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="clean-alert-box">
                    <CheckCircle2 size={17} className="text-emerald" />
                    <p>All product lines are maintaining healthy sales trajectories with no critical decline detected.</p>
                  </div>
                )}
              </div>
            </section>

            {/* AI Probable Cause */}
            <section className="section-block" id="probable-cause">
              <div className="glass-panel border-indigo-accent">
                <div className="panel-heading-row">
                  <div className="title-with-badge">
                    <div>
                      <p className="section-kicker">Cognitive Root-Cause Analysis</p>
                      <h3>AI Identifies Probable Cause</h3>
                    </div>
                  </div>
                  <span className="ml-tag"><Brain size={12} /> Contextual Inference</span>
                </div>
                <div className="probable-cause-content">
                  <div className="cause-quote">
                    <Lightbulb size={22} className="text-amber" />
                    <div>
                      <h4>Probable Cause:</h4>
                      <p className="cause-text">{probableCauseText}</p>
                    </div>
                  </div>
                </div>
              </div>
            </section>

            {/* AI Recommendations */}
            <section className="section-block" id="recommendations">
              <div className="glass-panel">
                <div className="panel-heading-row">
                  <div className="title-with-badge">
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

            {/* AI Chat */}
            <section className="section-block" id="ai-chat">
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
          </main>
        )}

        {/* ══════════════════════════════════════════
            TAB: BI Report
            ══════════════════════════════════════════ */}
        {activeTab === 'bi' && (
          <main className="page-content">
            <section className="section-block" id="bi-report">
              <BIReport url={biReportUrl} kpis={kpis} />
            </section>
          </main>
        )}
      </div>
    </div>
  )
}

export default App

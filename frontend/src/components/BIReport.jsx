import { useState } from 'react'
import { LayoutDashboard, ExternalLink, Globe, BarChart2, PieChart, Layers } from 'lucide-react'

function BIReport({ url, kpis }) {
  const [activeTab, setActiveTab] = useState('interactive')
  const [iframeError, setIframeError] = useState(false)
  const biUrl = url || 'http://localhost:3001'

  const products = kpis?.product_performance || [
    { name: 'Widget A', revenue: 1450000, quantity: 850, share: 38.5 },
    { name: 'Widget B', revenue: 1120000, quantity: 620, share: 29.8 },
    { name: 'Gadget X', revenue: 890000, quantity: 410, share: 23.7 },
    { name: 'Gadget Y', revenue: 300000, quantity: 180, share: 8.0 },
  ]

  const regions = [
    { region: 'East Coast', share: 34, revenue: '₹41.8L', status: 'High Growth' },
    { region: 'North Territory', share: 28, revenue: '₹34.4L', status: 'Stable' },
    { region: 'West Hub', share: 22, revenue: '₹27.1L', status: 'Expanding' },
    { region: 'South Central', share: 16, revenue: '₹19.7L', status: 'Target Area' },
  ]

  return (
    <section className="panel bi-panel glass-panel" aria-label="Business Intelligence Report">
      <div className="panel-heading-row">
        <div className="bi-heading-group">
          <div className="bi-icon-wrapper">
            <LayoutDashboard size={20} />
          </div>
          <div>
            <p className="section-kicker">Enterprise Analytics</p>
            <h3>STEP 15 — Business Intelligence (Power BI / Metabase)</h3>
          </div>
        </div>
        <div className="bi-tab-controls">
          <button
            type="button"
            className={`bi-tab-btn ${activeTab === 'interactive' ? 'active' : ''}`}
            onClick={() => setActiveTab('interactive')}
          >
            <BarChart2 size={14} /> Interactive BI View
          </button>
          <button
            type="button"
            className={`bi-tab-btn ${activeTab === 'embedded' ? 'active' : ''}`}
            onClick={() => setActiveTab('embedded')}
          >
            <Globe size={14} /> Embedded Iframe (Power BI / Superset)
          </button>
        </div>
      </div>

      {activeTab === 'interactive' ? (
        <div className="bi-interactive-container">
          <div className="bi-stats-banner glass-card">
            <div className="bi-stat-item">
              <span className="bi-stat-label">Enterprise Health Score</span>
              <strong className="bi-stat-val text-emerald">
                {kpis?.efficiency ? Math.round((kpis.efficiency * 0.6) + (kpis.quality_score * 0.4)) : 94}/100
              </strong>
              <span className="bi-stat-badge">Optimal</span>
            </div>
            <div className="bi-stat-item">
              <span className="bi-stat-label">Target Revenue Attainment</span>
              <strong className="bi-stat-val text-blue">104.2%</strong>
              <span className="bi-stat-badge">Above Target</span>
            </div>
            <div className="bi-stat-item">
              <span className="bi-stat-label">Defect Tolerance Compliance</span>
              <strong className="bi-stat-val text-indigo">{kpis?.defect_rate ?? 1.8}%</strong>
              <span className="bi-stat-badge">Pass</span>
            </div>
            <div className="bi-stat-item">
              <span className="bi-stat-label">Fulfillment Velocity</span>
              <strong className="bi-stat-val text-cyan">98.6%</strong>
              <span className="bi-stat-badge">On Time</span>
            </div>
          </div>

          <div className="bi-grid-2col">
            <div className="bi-card glass-card">
              <div className="bi-card-title">
                <PieChart size={16} />
                <h4>Regional Market Penetration</h4>
              </div>
              <div className="bi-table-wrapper">
                <table className="bi-table">
                  <thead>
                    <tr>
                      <th>Region</th>
                      <th>Sales Share</th>
                      <th>Revenue</th>
                      <th>Performance</th>
                    </tr>
                  </thead>
                  <tbody>
                    {regions.map((reg, idx) => (
                      <tr key={idx}>
                        <td><strong>{reg.region}</strong></td>
                        <td>
                          <div className="progress-cell">
                            <div className="progress-bar-bg">
                              <div className="progress-bar-fill" style={{ width: `${reg.share}%` }} />
                            </div>
                            <span>{reg.share}%</span>
                          </div>
                        </td>
                        <td>{reg.revenue}</td>
                        <td><span className="badge-pill">{reg.status}</span></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="bi-card glass-card">
              <div className="bi-card-title">
                <Layers size={16} />
                <h4>Product Portfolio Revenue Contribution</h4>
              </div>
              <div className="bi-portfolio-list">
                {products.map((p, idx) => (
                  <div key={idx} className="portfolio-item">
                    <div className="portfolio-item-header">
                      <span className="portfolio-name">{p.name}</span>
                      <span className="portfolio-rev">
                        ₹{(p.revenue / 100000).toFixed(1)}L ({p.share}%)
                      </span>
                    </div>
                    <div className="progress-bar-bg">
                      <div
                        className={`progress-bar-fill fill-${idx % 4}`}
                        style={{ width: `${Math.min(100, p.share * 2)}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="bi-embedded-container">
          <div className="bi-iframe-info-bar">
            <span>
              Connected URL: <code>{biUrl}</code> (Configurable via <code>VITE_BI_REPORT_URL</code>)
            </span>
            <a
              href={biUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="open-external-link"
            >
              <ExternalLink size={13} /> Open in new tab
            </a>
          </div>

          <div className="bi-iframe-wrapper">
            <iframe
              title="InsightForge Embedded Power BI / Metabase Report"
              src={biUrl}
              className="bi-frame"
              loading="lazy"
              onError={() => setIframeError(true)}
            />
            {iframeError && (
              <div className="iframe-fallback-overlay glass-card">
                <p>
                  ℹ️ Embedded BI Server at <code>{biUrl}</code> is not currently active.
                </p>
                <p>
                  To view live external dashboards, start your Power BI service, Apache Superset, or Metabase container on port 3001.
                </p>
                <button
                  type="button"
                  className="auth-button"
                  onClick={() => setActiveTab('interactive')}
                >
                  Switch to Built-in Interactive BI View
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </section>
  )
}

export default BIReport

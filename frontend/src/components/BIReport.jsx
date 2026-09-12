import { LayoutDashboard, BarChart2, PieChart, Layers } from 'lucide-react'

function BIReport({ kpis }) {

  const products = Array.isArray(kpis?.product_performance) && kpis.product_performance.length > 0
    ? kpis.product_performance
    : []

  const summaryMetrics = [
    {
      label: 'Current dataset',
      value: kpis?.data_source === 'active_dataset' ? 'Uploaded dataset' : 'No active dataset',
      status: kpis?.data_source === 'active_dataset' ? 'Ready' : 'Awaiting upload',
    },
    {
      label: 'Total records',
      value: Number(kpis?.total_records ?? 0).toLocaleString(),
      status: 'Records',
    },
    {
      label: 'Quality score',
      value: `${Number(kpis?.quality_score ?? 0).toFixed(1)}%`,
      status: 'Data quality',
    },
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
            <h3>Business Intelligence Report</h3>
          </div>
        </div>
        <div className="bi-tab-controls">
          <button type="button" className="bi-tab-btn active" disabled>
            <BarChart2 size={14} /> Interactive BI View
          </button>
        </div>
      </div>

      <div className="bi-interactive-container">
        <div className="bi-stats-banner glass-card">
          {summaryMetrics.map((metric) => (
            <div className="bi-stat-item" key={metric.label}>
              <span className="bi-stat-label">{metric.label}</span>
              <strong className="bi-stat-val text-emerald">{metric.value}</strong>
              <span className="bi-stat-badge">{metric.status}</span>
            </div>
          ))}
        </div>

        <div className="bi-grid-2col">
          <div className="bi-card glass-card">
            <div className="bi-card-title">
              <PieChart size={16} />
              <h4>Dataset summary</h4>
            </div>
            <div className="bi-table-wrapper">
              <table className="bi-table">
                <thead>
                  <tr>
                    <th>Metric</th>
                    <th>Value</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td>Revenue</td>
                    <td>{kpis?.revenue ? `₹${Number(kpis.revenue).toLocaleString()}` : 'Not available'}</td>
                  </tr>
                  <tr>
                    <td>Production</td>
                    <td>{kpis?.production ? Number(kpis.production).toLocaleString() : 'Not available'}</td>
                  </tr>
                  <tr>
                    <td>Inventory</td>
                    <td>{kpis?.inventory ? Number(kpis.inventory).toLocaleString() : 'Not available'}</td>
                  </tr>
                  <tr>
                    <td>Defect rate</td>
                    <td>{kpis?.defect_rate ? `${Number(kpis.defect_rate).toFixed(2)}%` : 'Not available'}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <div className="bi-card glass-card">
            <div className="bi-card-title">
              <Layers size={16} />
              <h4>Top category contribution</h4>
            </div>
            <div className="bi-portfolio-list">
              {products.length > 0 ? products.map((p, idx) => (
                <div key={idx} className="portfolio-item">
                  <div className="portfolio-item-header">
                    <span className="portfolio-name">{p.name}</span>
                    <span className="portfolio-rev">
                      {Number(p.revenue ?? 0).toLocaleString()} ({p.share ?? 0}%)
                    </span>
                  </div>
                  <div className="progress-bar-bg">
                    <div
                      className={`progress-bar-fill fill-${idx % 4}`}
                      style={{ width: `${Math.min(100, Number(p.share ?? 0) * 2)}%` }}
                    />
                  </div>
                </div>
              )) : (
                <p className="empty-state-small">Upload a dataset with category and metric columns to populate this report.</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}

export default BIReport

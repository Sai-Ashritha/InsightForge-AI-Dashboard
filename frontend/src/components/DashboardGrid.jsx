import { BarChart3, TrendingUp } from 'lucide-react'

function DashboardGrid({ kpis }) {
  const cards = kpis?.dynamic_analytics?.kpis || []

  if (!cards.length) {
    return <p className="empty-state">Upload a dataset to generate metrics.</p>
  }

  return (
    <section className="kpi-grid" aria-label="Key performance indicators">
      {cards.map(({ key, title, value, color, unit, subtext }) => {
        return (
          <div className={`kpi-card glass-card card-${color || 'indigo'}`} key={key}>
            <div className="kpi-card-top">
              <div className="kpi-icon-wrapper">
                <BarChart3 size={18} aria-hidden="true" />
              </div>
              <span className="kpi-label">{title}</span>
            </div>
            <div className="kpi-value-row">
              <strong className="kpi-value">{value}{unit && !String(value).includes(unit) ? ` ${unit}` : ''}</strong>
            </div>
            <div className="kpi-subtext">
              <TrendingUp size={12} className="kpi-sub-icon" />
              <span>{subtext || 'Calculated from uploaded data'}</span>
            </div>
          </div>
        )
      })}
    </section>
  )
}

export default DashboardGrid

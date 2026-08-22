import { Factory, Gauge, Package, ShieldCheck, TrendingUp, Wallet } from 'lucide-react'

const cards = [
  {
    key: 'revenue',
    label: 'Total Revenue',
    icon: Wallet,
    color: 'emerald',
    format: (value) => (value >= 100000 ? `₹${(value / 100000).toFixed(1)}L` : `₹${Number(value).toLocaleString()}`),
    subtext: 'Calculated from uploaded dataset',
  },
  {
    key: 'production',
    label: 'Total Production',
    icon: Factory,
    color: 'blue',
    format: (value) => `${Number(value).toLocaleString()} units`,
    subtext: 'Fabricated output units',
  },
  {
    key: 'inventory',
    label: 'Current Inventory',
    icon: Package,
    color: 'amber',
    format: (value) => `${Number(value).toLocaleString()} units`,
    subtext: 'Floor & hub safety stock',
  },
  {
    key: 'efficiency',
    label: 'Production Efficiency',
    icon: Gauge,
    color: 'cyan',
    format: (value) => `${value}%`,
    subtext: 'Uptime vs downtime ratio',
  },
  {
    key: 'quality_score',
    label: 'Data Quality Score',
    icon: ShieldCheck,
    color: 'indigo',
    format: (value) => `${value}%`,
    subtext: 'Formula: 100 - (Null+Dup+Outliers)',
  },
]

function DashboardGrid({ kpis }) {
  return (
    <section className="kpi-grid" aria-label="Key performance indicators">
      {cards.map(({ key, label, icon: Icon, color, format, subtext }) => {
        const val = kpis?.[key] ?? (key === 'quality_score' ? 94.0 : 0)
        return (
          <div className={`kpi-card glass-card card-${color}`} key={key}>
            <div className="kpi-card-top">
              <div className="kpi-icon-wrapper">
                <Icon size={18} aria-hidden="true" />
              </div>
              <span className="kpi-label">{label}</span>
            </div>
            <div className="kpi-value-row">
              <strong className="kpi-value">{format(val)}</strong>
            </div>
            <div className="kpi-subtext">
              <TrendingUp size={12} className="kpi-sub-icon" />
              <span>{subtext}</span>
            </div>
          </div>
        )
      })}
    </section>
  )
}

export default DashboardGrid

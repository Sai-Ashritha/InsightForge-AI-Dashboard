import { useState } from 'react'
import {
  Activity,
  AlertTriangle,
  BarChart3,
  Brain,
  ChevronLeft,
  ChevronRight,
  Factory,
  LayoutDashboard,
  LogOut,
  Menu,
  ShieldCheck,
  Sparkles,
  X,
  Zap,
} from 'lucide-react'

const NAV_TABS = [
  {
    id: 'quality',
    label: 'Quality & Cleaning',
    icon: ShieldCheck,
    description: 'Data upload & pipeline',
  },
  {
    id: 'overview',
    label: 'Overview',
    icon: LayoutDashboard,
    description: 'KPIs & live charts',
  },
  {
    id: 'insights',
    label: 'Predictive Insights',
    icon: Brain,
    description: 'ML forecast & anomalies',
  },
  {
    id: 'alerts',
    label: 'Alerts & Causes',
    icon: AlertTriangle,
    description: 'Declines & recommendations',
  },
  {
    id: 'bi',
    label: 'BI Report',
    icon: BarChart3,
    description: 'Business intelligence',
  },
]

function SidebarNav({ activeTab, onTabChange, authToken, currentUser, onSignOut, isAuthenticated, onCollapsedChange, hasUploadedData = false }) {
  const [collapsed, setCollapsed] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)

  const handleCollapse = (val) => {
    setCollapsed(val)
    if (onCollapsedChange) onCollapsedChange(val)
  }

  return (
    <>
      {/* Mobile overlay */}
      {mobileOpen && (
        <div
          className="sidebar-overlay"
          onClick={() => setMobileOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Mobile toggle button */}
      <button
        type="button"
        className="sidebar-mobile-toggle"
        onClick={() => setMobileOpen(!mobileOpen)}
        aria-label="Toggle navigation"
      >
        <Menu size={20} />
      </button>

      {/* Sidebar */}
      <aside
        className={`sidebar ${collapsed ? 'sidebar--collapsed' : ''} ${mobileOpen ? 'sidebar--mobile-open' : ''}`}
        aria-label="Main navigation"
      >
        {/* Brand Header */}
        <div className="sidebar-brand">
          <div className="sidebar-logo">
            <Factory size={20} />
          </div>
          {!collapsed && (
            <div className="sidebar-brand-text">
              <span className="sidebar-brand-name">InsightForge</span>
              <span className="sidebar-brand-sub">AI Manufacturing</span>
            </div>
          )}
          <button
            type="button"
            className="sidebar-collapse-btn"
            onClick={() => handleCollapse(!collapsed)}
            aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {collapsed ? <ChevronRight size={15} /> : <ChevronLeft size={15} />}
          </button>
        </div>

        {/* Live Status */}
        {!collapsed && (
          <div className="sidebar-live-status">
            <span className="pulsing-dot" />
            <span className="sidebar-live-label">Live System</span>
          </div>
        )}

        {/* Navigation */}
        <nav className="sidebar-nav" aria-label="Dashboard sections">
          {NAV_TABS.map((tab) => {
            const Icon = tab.icon
            const isActive = activeTab === tab.id
            const isQualityTab = tab.id === 'quality'
            const isDisabled = isQualityTab ? false : (!isAuthenticated || !hasUploadedData)

            const tooltipText = isQualityTab 
              ? (collapsed ? tab.label : undefined)
              : !isAuthenticated 
                ? 'Sign in first' 
                : !hasUploadedData 
                  ? 'Upload dataset in Quality & Cleaning to unlock' 
                  : (collapsed ? tab.label : undefined)

            return (
              <button
                key={tab.id}
                type="button"
                className={`nav-item ${isActive ? 'nav-item--active' : ''} ${isDisabled ? 'nav-item--disabled' : ''}`}
                onClick={() => {
                  if (!isDisabled) {
                    onTabChange(tab.id)
                    setMobileOpen(false)
                  }
                }}
                disabled={isDisabled}
                title={tooltipText}
                aria-current={isActive ? 'page' : undefined}
              >
                <span className="nav-item-icon">
                  <Icon size={18} aria-hidden="true" />
                </span>
                {!collapsed && (
                  <span className="nav-item-text">
                    <span className="nav-item-label">
                      {tab.label}
                      {isDisabled && !isQualityTab && (
                        <span className="nav-item-lock-pill">Upload Required</span>
                      )}
                    </span>
                    <span className="nav-item-desc">
                      {isDisabled && !isQualityTab ? 'Locked until data is uploaded' : tab.description}
                    </span>
                  </span>
                )}
                {isActive && !collapsed && <span className="nav-item-indicator" aria-hidden="true" />}
              </button>
            )
          })}
        </nav>

        {/* Bottom user section */}
        <div className="sidebar-footer">
          {isAuthenticated ? (
            <div className="sidebar-user">
              {!collapsed && (
                <div className="sidebar-user-info">
                  <ShieldCheck size={14} className="sidebar-user-icon" />
                  <div>
                    <span className="sidebar-user-email">
                      {currentUser?.email || 'Analyst'}
                    </span>
                    <span className="sidebar-user-role">Analyst Access</span>
                  </div>
                </div>
              )}
              <button
                type="button"
                className="sidebar-signout-btn"
                onClick={onSignOut}
                title="Sign out"
                aria-label="Sign out"
              >
                <LogOut size={14} />
                {!collapsed && <span>Sign Out</span>}
              </button>
            </div>
          ) : (
            <div className={`sidebar-auth-cta ${collapsed ? 'sidebar-auth-cta--collapsed' : ''}`}>
              {!collapsed ? (
                <>
                  <Zap size={14} className="sidebar-cta-icon" />
                  <span>Sign in to unlock all features</span>
                </>
              ) : (
                <Sparkles size={16} className="sidebar-cta-icon" />
              )}
            </div>
          )}
        </div>
      </aside>
    </>
  )
}

export default SidebarNav

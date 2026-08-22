import { CheckCircle2, ChevronRight } from 'lucide-react'

const WORKFLOW_STEPS = [
  { id: 1, label: 'Login / Register', short: 'Auth' },
  { id: 2, label: 'Upload CSV', short: 'Upload' },
  { id: 3, label: 'Analyze Data', short: 'Analyze' },
  { id: 4, label: 'Data Quality', short: 'Quality' },
  { id: 5, label: 'Auto Cleaning', short: 'Clean' },
  { id: 6, label: 'Dashboard KPIs', short: 'Dashboard' },
  { id: 7, label: 'Sales Decline', short: 'Decline' },
  { id: 8, label: 'ML Forecast', short: 'Forecast' },
  { id: 9, label: 'Anomaly Detection', short: 'Anomalies' },
  { id: 10, label: 'Inventory Check', short: 'Inventory' },
  { id: 11, label: 'AI Probable Cause', short: 'Causes' },
  { id: 12, label: 'Recommendations', short: 'Actions' },
  { id: 13, label: 'Ask AI Chat', short: 'Chat' },
  { id: 14, label: 'AI Recommendations', short: 'Advisor' },
  { id: 15, label: 'BI Report', short: 'BI Report' },
]

function StepFlowNav({ currentStep, onSelectStep, maxReachedStep = 1 }) {
  return (
    <nav className="step-flow-bar" aria-label="Workflow progress">
      <div className="step-flow-scroll">
        {WORKFLOW_STEPS.map((step, idx) => {
          const isCompleted = currentStep > step.id || (currentStep >= 6 && step.id <= 5)
          const isCurrent = currentStep === step.id
          const isAccessible = step.id <= Math.max(maxReachedStep, 6)

          return (
            <div key={step.id} className="step-node-wrapper">
              <button
                type="button"
                className={`step-node ${isCurrent ? 'active' : ''} ${isCompleted ? 'completed' : ''} ${isAccessible ? 'accessible' : 'locked'}`}
                onClick={() => isAccessible && onSelectStep && onSelectStep(step.id)}
                disabled={!isAccessible}
                title={`Step ${step.id}: ${step.label}`}
              >
                <span className="step-circle">
                  {isCompleted ? (
                    <CheckCircle2 size={14} className="step-check-icon" />
                  ) : (
                    <span className="step-number">{step.id}</span>
                  )}
                </span>
                <span className="step-text">{step.short}</span>
              </button>
              {idx < WORKFLOW_STEPS.length - 1 && (
                <ChevronRight size={13} className="step-arrow-divider" aria-hidden="true" />
              )}
            </div>
          )
        })}
      </div>
    </nav>
  )
}

export default StepFlowNav

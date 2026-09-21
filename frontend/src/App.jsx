import { useState } from 'react'
import './App.css'

// a real app would use a per-user token here, not a key baked into the JS
const API_KEY = 'demo-setu-8f3k29xz'
const API_HEADERS = { 'X-API-Key': API_KEY }

const SAMPLE_APPLICANT = {
  applicant_id: 'DEMO001',
  days_active: 10,
  recharge_freq_per_month: 6,
  recharge_regularity: 0.7,
  tenure_months_on_number: 24,
  utility_pct_on_time: 0.8,
  utility_avg_days_late: 2,
  txn_freq_per_month: 18,
  txn_regularity: 0.65,
  merchant_diversity: 6,
  platform_tenure_days: 90,
  kyc_complete: 1,
}

const BAND_LABEL = {
  low_risk: 'Low risk',
  medium_risk: 'Medium risk',
  high_risk: 'High risk',
}

const FIELD_LABELS = {
  applicant_id: 'Applicant ID',
  days_active: 'Days as a customer',
  recharge_freq_per_month: 'Mobile recharges per month',
  recharge_regularity: 'Recharge regularity (0-1)',
  tenure_months_on_number: 'Months on this phone number',
  utility_pct_on_time: 'Utility bills paid on time (0-1)',
  utility_avg_days_late: 'Average days late on utility bills',
  txn_freq_per_month: 'Transactions per month',
  txn_regularity: 'Transaction regularity (0-1)',
  merchant_diversity: 'Number of different merchants used',
  platform_tenure_days: 'Days using this platform',
  kyc_complete: 'KYC verified',
}

const FIELD_INFO = {
  applicant_id: 'Unique ID for this applicant, used to track consent and score history.',
  days_active: "How long they've been a customer. Decides whether the score uses a cohort-only estimate, their own personal model, or a blend of both.",
  recharge_freq_per_month: 'How often they top up their phone each month. Frequent, steady recharging suggests stable income.',
  recharge_regularity: 'How consistent the timing of recharges is, 0 = erratic to 1 = very regular. A proxy for financial discipline.',
  tenure_months_on_number: "How long they've kept the same phone number. People in financial distress tend to change numbers more often.",
  utility_pct_on_time: 'Share of utility bills paid on time, 0 to 1. A direct signal of bill-paying discipline.',
  utility_avg_days_late: 'When bills are late, how late on average. Captures severity, not just whether they are ever late.',
  txn_freq_per_month: 'How many digital (UPI or wallet) transactions per month. Reflects overall financial activity.',
  txn_regularity: 'How consistent transaction patterns are over time, 0 to 1. Erratic patterns can signal instability.',
  merchant_diversity: 'Number of different merchants they transact with. Broader spending suggests broader participation in the economy.',
  platform_tenure_days: "Total days using this platform. More days means more of the applicant's own history to score from.",
  kyc_complete: 'Whether identity verification is complete. A regulatory requirement, and incomplete KYC is itself a risk flag.',
}

export default function App() {
  const [applicant, setApplicant] = useState(SAMPLE_APPLICANT)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const [consentGiven, setConsentGiven] = useState(false)
  const [consenting, setConsenting] = useState(false)

  const [fairnessReport, setFairnessReport] = useState(null)
  const [fairnessLoading, setFairnessLoading] = useState(false)

  const handleChange = (key, value) => {
    setApplicant((prev) => ({ ...prev, [key]: value }))
    setConsentGiven(false) // a changed applicant_id needs consent recorded again
    setResult(null)
  }

  const handleConsent = async () => {
    setConsenting(true)
    setError(null)
    try {
      const res = await fetch('/api/consent', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...API_HEADERS },
        body: JSON.stringify({ applicant_id: applicant.applicant_id, consent_given: true }),
      })
      if (!res.ok) throw new Error(`Consent request failed: ${res.status}`)
      setConsentGiven(true)
    } catch (err) {
      setError(err.message)
    } finally {
      setConsenting(false)
    }
  }

  const handleScore = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch('/api/score', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...API_HEADERS },
        body: JSON.stringify(applicant),
      })
      const data = await res.json().catch(() => null)
      if (!res.ok) {
        throw new Error(data ? JSON.stringify(data) : `Request failed: ${res.status}`)
      }
      setResult(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleFairnessReport = async () => {
    setFairnessLoading(true)
    setError(null)
    try {
      const res = await fetch('/api/fairness-report', { headers: API_HEADERS })
      if (!res.ok) throw new Error(`Fairness report request failed: ${res.status}`)
      setFairnessReport(await res.json())
    } catch (err) {
      setError(err.message)
    } finally {
      setFairnessLoading(false)
    }
  }

  const handleErase = async () => {
    await fetch(`/api/applicants/${encodeURIComponent(applicant.applicant_id)}`, {
      method: 'DELETE',
      headers: API_HEADERS,
    })
    setConsentGiven(false)
    setResult(null)
  }

  return (
    <div className="setu-app">
      <div className="setu-header">
        <span className="setu-mark" aria-hidden="true">
          <span></span><span></span><span></span>
        </span>
        <h1>Setu</h1>
      </div>
      <p className="setu-tagline">
        Progressive trust scoring for underbanked applicants. Starts as a cold-start cohort
        estimate and sharpens into a personal score as history accumulates.
      </p>

      <div className="setu-container">
        <section className="setu-card">
          <h2><span className="setu-step-label">1</span>Consent</h2>
          <p>
            We use your mobile recharge, utility payment, and transaction data to assess risk.
            No social media, social network, or demographic data is used. You can withdraw
            this data at any time.
          </p>
          <div className="setu-actions">
            <button
              className="setu-btn setu-btn-primary"
              onClick={handleConsent}
              disabled={consenting || consentGiven}
            >
              {consentGiven ? 'Consent recorded ✓' : consenting ? 'Recording…' : 'I consent'}
            </button>
          </div>
        </section>

        <section className="setu-card">
          <h2><span className="setu-step-label">2</span>Applicant signals</h2>
          <p>Demo values. Edit any field to see the score respond.</p>
          <div className="setu-grid">
            {Object.entries(applicant).map(([key, value]) => (
              <div className="setu-field" key={key}>
                <label htmlFor={key}>
                  {FIELD_LABELS[key] || key}
                  {FIELD_INFO[key] && (
                    <span className="setu-info" tabIndex={0} title={FIELD_INFO[key]}>i</span>
                  )}
                </label>
                {key === 'kyc_complete' ? (
                  <select
                    id={key}
                    value={value ? 'yes' : 'no'}
                    onChange={(e) => handleChange(key, e.target.value === 'yes' ? 1 : 0)}
                  >
                    <option value="yes">Yes</option>
                    <option value="no">No</option>
                  </select>
                ) : (
                  <input
                    id={key}
                    type={key === 'applicant_id' ? 'text' : 'number'}
                    value={value}
                    onChange={(e) =>
                      handleChange(key, key === 'applicant_id' ? e.target.value : Number(e.target.value))
                    }
                  />
                )}
              </div>
            ))}
          </div>
          <div className="setu-actions">
            <button
              className="setu-btn setu-btn-primary"
              onClick={handleScore}
              disabled={loading || !consentGiven}
              title={!consentGiven ? 'Give consent first' : undefined}
            >
              {loading ? 'Scoring…' : 'Get risk score'}
            </button>
            <button className="setu-btn setu-btn-secondary" onClick={handleErase}>
              Erase my data
            </button>
          </div>
        </section>

        {error && <p className="setu-error">Error: {error}</p>}

        {result && (
          <section className="setu-card">
            <span className={`setu-result-band band-${result.risk_band}`}>
              {BAND_LABEL[result.risk_band] || result.risk_band}
            </span>
            <div className="setu-result-score">{result.risk_score}</div>
            <div className="setu-gauge">
              <div className="setu-gauge-track">
                <div
                  className="setu-gauge-marker"
                  style={{ left: `${Math.min(100, Math.max(0, result.risk_score * 100))}%` }}
                />
              </div>
              <div className="setu-gauge-labels">
                <span>High risk</span>
                <span>Medium risk</span>
                <span>Low risk</span>
              </div>
            </div>
            <p className="setu-result-meta">
              {result.applicant_id} · {result.method} estimate · cohort weight {result.cohort_weight}
            </p>
            <div className="setu-explanation">{result.explanation}</div>
            {result.top_factors?.length > 0 && (
              <ul className="setu-factors">
                {result.top_factors.map((f) => (
                  <li key={f.feature}>
                    <span className={`factor-dot ${f.direction}`}></span>
                    {FIELD_LABELS[f.feature] || f.feature}: {f.direction} (magnitude {f.magnitude})
                  </li>
                ))}
              </ul>
            )}
          </section>
        )}

        <section className="setu-card">
          <h2>Fairness audit</h2>
          <p>
            Checks whether the trained model's own predictions are disparate across
            gender/region, even though neither is a model feature.
          </p>
          <div className="setu-actions">
            <button className="setu-btn setu-btn-secondary" onClick={handleFairnessReport} disabled={fairnessLoading}>
              {fairnessLoading ? 'Loading…' : 'View fairness report'}
            </button>
          </div>
          {fairnessReport && (
            <div className="setu-fairness-stats">
              <div className="setu-stat">
                <div className="setu-stat-value">{fairnessReport.disparity_ratio_gender}</div>
                <div className="setu-stat-label">Gender disparity ratio</div>
              </div>
              <div className="setu-stat">
                <div className="setu-stat-value">{fairnessReport.disparity_ratio_region}</div>
                <div className="setu-stat-label">Region disparity ratio</div>
              </div>
            </div>
          )}
        </section>
      </div>
    </div>
  )
}

import { useState } from 'react'
import './App.css'

// Demo simplification: the backend's API-key auth (ApiKeyFilter.java) is a
// single shared key, not per-user identity, and this is where the frontend
// would normally read a user's own token instead of a value baked into the
// shipped JS. A real deployment would use OAuth2/JWT issued per signed-in
// user; a static client-side key only proves the server-side check is real,
// not that this is how production auth should look.
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
        Progressive trust scoring for underbanked applicants — a cold-start cohort estimate
        that sharpens into a personal score as history accumulates.
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
          <p>Demo values — edit any field to see the score respond.</p>
          <div className="setu-grid">
            {Object.entries(applicant).map(([key, value]) => (
              <div className="setu-field" key={key}>
                <label htmlFor={key}>{key.replace(/_/g, ' ')}</label>
                <input
                  id={key}
                  type={key === 'applicant_id' ? 'text' : 'number'}
                  value={value}
                  onChange={(e) =>
                    handleChange(key, key === 'applicant_id' ? e.target.value : Number(e.target.value))
                  }
                />
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
            <p className="setu-result-meta">
              {result.applicant_id} · {result.method} estimate · cohort weight {result.cohort_weight}
            </p>
            <div className="setu-explanation">{result.explanation}</div>
            {result.top_factors?.length > 0 && (
              <ul className="setu-factors">
                {result.top_factors.map((f) => (
                  <li key={f.feature}>
                    <span className={`factor-dot ${f.direction}`}></span>
                    {f.feature.replace(/_/g, ' ')} — {f.direction} (magnitude {f.magnitude})
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

import { useState } from 'react'

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

  return (
    <div style={{ fontFamily: 'system-ui, sans-serif', maxWidth: 640, margin: '2rem auto', padding: '0 1rem' }}>
      <h1>Setu</h1>
      <p>Progressive trust scoring for underbanked applicants — a cold-start cohort estimate that sharpens into a personal score as history accumulates.</p>

      <div style={{ padding: '1rem', border: '1px solid #ccc', borderRadius: 8, marginBottom: '1rem' }}>
        <h2 style={{ marginTop: 0 }}>Step 1 — Consent</h2>
        <p style={{ fontSize: '0.9rem' }}>
          We use your mobile recharge, utility payment, and transaction data to assess risk.
          No social media, social network, or demographic data is used. You can withdraw
          this data at any time (see "Erase my data" below).
        </p>
        <button onClick={handleConsent} disabled={consenting || consentGiven}>
          {consentGiven ? 'Consent recorded ✓' : consenting ? 'Recording…' : 'I consent — give consent'}
        </button>
      </div>

      <h2>Step 2 — Applicant signals (demo values, editable)</h2>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
        {Object.entries(applicant).map(([key, value]) => (
          <label key={key} style={{ display: 'flex', flexDirection: 'column', fontSize: '0.85rem' }}>
            {key}
            <input
              type={key === 'applicant_id' ? 'text' : 'number'}
              value={value}
              onChange={(e) =>
                handleChange(key, key === 'applicant_id' ? e.target.value : Number(e.target.value))
              }
            />
          </label>
        ))}
      </div>

      <button
        onClick={handleScore}
        disabled={loading || !consentGiven}
        title={!consentGiven ? 'Give consent first' : undefined}
        style={{ marginTop: '1rem', padding: '0.5rem 1rem' }}
      >
        {loading ? 'Scoring…' : 'Get risk score'}
      </button>

      <button
        onClick={async () => {
          await fetch(`/api/applicants/${encodeURIComponent(applicant.applicant_id)}`, {
            method: 'DELETE',
            headers: API_HEADERS,
          })
          setConsentGiven(false)
          setResult(null)
        }}
        style={{ marginTop: '1rem', marginLeft: '0.5rem', padding: '0.5rem 1rem' }}
      >
        Erase my data
      </button>

      {error && <p style={{ color: 'crimson' }}>Error: {error}</p>}

      {result && (
        <div style={{ marginTop: '1.5rem', padding: '1rem', border: '1px solid #ccc', borderRadius: 8 }}>
          <h3>Result for {result.applicant_id}</h3>
          <p><strong>Risk band:</strong> {result.risk_band} ({result.risk_score})</p>
          <p><strong>Method:</strong> {result.method} (cohort weight: {result.cohort_weight})</p>
          <p><strong>Why:</strong> {result.explanation}</p>
          {result.top_factors?.length > 0 && (
            <>
              <p><strong>Top factors:</strong></p>
              <ul>
                {result.top_factors.map((f) => (
                  <li key={f.feature}>{f.feature}: {f.direction} (magnitude {f.magnitude})</li>
                ))}
              </ul>
            </>
          )}
        </div>
      )}

      <div style={{ marginTop: '2rem', padding: '1rem', border: '1px solid #ccc', borderRadius: 8 }}>
        <h2 style={{ marginTop: 0 }}>Fairness audit</h2>
        <p style={{ fontSize: '0.9rem' }}>
          Checks whether the trained model's own predictions are disparate across gender/region,
          even though neither is a model feature.
        </p>
        <button onClick={handleFairnessReport} disabled={fairnessLoading}>
          {fairnessLoading ? 'Loading…' : 'View fairness report'}
        </button>
        {fairnessReport && (
          <div style={{ marginTop: '1rem', fontSize: '0.9rem' }}>
            <p><strong>Overall model approval rate:</strong> {fairnessReport.overall_model_approval_rate}</p>
            <p><strong>By gender:</strong> {JSON.stringify(fairnessReport.by_gender)}</p>
            <p><strong>By region:</strong> {JSON.stringify(fairnessReport.by_region)}</p>
            <p>
              <strong>Disparity ratios:</strong> gender {fairnessReport.disparity_ratio_gender}, region{' '}
              {fairnessReport.disparity_ratio_region} <em>(four-fifths rule flags below 0.8 — both clear it)</em>
            </p>
          </div>
        )}
      </div>
    </div>
  )
}

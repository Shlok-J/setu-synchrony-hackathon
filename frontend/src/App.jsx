import { useState } from 'react'

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

  const handleChange = (key, value) => {
    setApplicant((prev) => ({ ...prev, [key]: value }))
  }

  const handleScore = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch('/api/score', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
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

  return (
    <div style={{ fontFamily: 'system-ui, sans-serif', maxWidth: 640, margin: '2rem auto', padding: '0 1rem' }}>
      <h1>Setu</h1>
      <p>Progressive trust scoring for underbanked applicants — a cold-start cohort estimate that sharpens into a personal score as history accumulates.</p>

      <h2>Applicant signals (demo values, editable)</h2>
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

      <button onClick={handleScore} disabled={loading} style={{ marginTop: '1rem', padding: '0.5rem 1rem' }}>
        {loading ? 'Scoring…' : 'Get risk score'}
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
    </div>
  )
}

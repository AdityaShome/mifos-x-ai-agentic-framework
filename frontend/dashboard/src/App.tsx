import { useEffect, useMemo, useState } from 'react';
import { getDecision, getHealth, getPortfolioHealth, submitDecisionFeedback } from './api';
import type {
  DecisionDetail,
  HealthResponse,
  PortfolioHealthItem,
  PortfolioHealthResponse,
} from './types';

const defaultLimit = 25;

function formatPercent(part: number, total: number): string {
  if (total === 0) return '0%';
  return `${Math.round((part / total) * 100)}%`;
}

function tierClass(tier: PortfolioHealthItem['risk_tier']): string {
  return tier.toLowerCase().replace(/\s+/g, '-');
}

function prettyValue(value: unknown): string {
  if (value === null || value === undefined) {
    return '—';
  }
  if (typeof value === 'string') {
    return value;
  }
  if (typeof value === 'number' || typeof value === 'boolean') {
    return String(value);
  }
  return JSON.stringify(value, null, 2);
}

function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [portfolio, setPortfolio] = useState<PortfolioHealthResponse | null>(null);
  const [limit, setLimit] = useState(defaultLimit);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedLoanId, setSelectedLoanId] = useState<string | null>(null);
  const [decision, setDecision] = useState<DecisionDetail | null>(null);
  const [decisionLoading, setDecisionLoading] = useState(false);
  const [decisionError, setDecisionError] = useState<string | null>(null);
  const [feedbackComment, setFeedbackComment] = useState('');
  const [feedbackReviewer, setFeedbackReviewer] = useState('');
  const [feedbackMessage, setFeedbackMessage] = useState<string | null>(null);
  const [feedbackSubmitting, setFeedbackSubmitting] = useState(false);

  useEffect(() => {
    let active = true;

    async function load() {
      setLoading(true);
      setError(null);
      try {
        const [healthResponse, portfolioResponse] = await Promise.all([
          getHealth(),
          getPortfolioHealth(limit),
        ]);

        if (!active) {
          return;
        }

        setHealth(healthResponse);
        setPortfolio(portfolioResponse);
      } catch (err) {
        if (!active) {
          return;
        }
        setError(err instanceof Error ? err.message : 'Unable to load dashboard data');
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    load();

    return () => {
      active = false;
    };
  }, [limit]);

  const summary = portfolio?.summary;
  const atRiskItems = useMemo(
    () =>
      portfolio?.items
        .filter((item) => item.risk_score >= 31)
        .slice(0, 8) ?? [],
    [portfolio],
  );

  useEffect(() => {
    if (!selectedLoanId) {
      setDecision(null);
      setDecisionError(null);
      setFeedbackMessage(null);
      return;
    }

    const loanId = selectedLoanId;

    let active = true;

    async function loadDecision() {
      setDecisionLoading(true);
      setDecisionError(null);
      setFeedbackMessage(null);
      try {
        const response = await getDecision(loanId);
        if (!active) {
          return;
        }
        setDecision(response);
        setFeedbackComment('');
        setFeedbackReviewer('');
      } catch (err) {
        if (!active) {
          return;
        }
        setDecisionError(err instanceof Error ? err.message : 'Unable to load decision details');
      } finally {
        if (active) {
          setDecisionLoading(false);
        }
      }
    }

    loadDecision();

    return () => {
      active = false;
    };
  }, [selectedLoanId]);

  async function sendFeedback(feedback: 'approve' | 'reject') {
    if (!selectedLoanId) {
      return;
    }

    setFeedbackSubmitting(true);
    setFeedbackMessage(null);
    try {
      const response = await submitDecisionFeedback(selectedLoanId, {
        feedback,
        comment: feedbackComment.trim() || null,
        reviewer: feedbackReviewer.trim() || null,
      });
      setFeedbackMessage(`Stored ${response.feedback} feedback for loan ${response.loan_id}.`);
    } catch (err) {
      setFeedbackMessage(err instanceof Error ? err.message : 'Unable to store feedback');
    } finally {
      setFeedbackSubmitting(false);
    }
  }

  return (
    <div className="shell">
      <div className="ambient ambient-left" />
      <div className="ambient ambient-right" />

      <header className="hero">
        <div>
          <p className="eyebrow">Portfolio Health Agent</p>
          <h1>Loan risk, policy actions, and agent explanations in one place.</h1>
          <p className="subhead">
            Live data from the FastAPI backend, with transparent decisions and a compact view of the portfolio.
          </p>
        </div>

        <div className="hero-panel">
          <div className="hero-panel__row">
            <span>Backend</span>
            <strong>{health?.service ?? 'Loading...'}</strong>
          </div>
          <div className="hero-panel__row">
            <span>Status</span>
            <strong className={health?.status === 'ok' ? 'status-ok' : ''}>{health?.status ?? 'Loading...'}</strong>
          </div>
          <div className="hero-panel__row">
            <span>Version</span>
            <strong>{health?.version ?? '—'}</strong>
          </div>
        </div>
      </header>

      <main className="content">
        <section className="controls card">
          <div>
            <p className="section-label">Portfolio fetch size</p>
            <h2>Control how many loans the dashboard requests</h2>
          </div>
          <div className="control-row">
            <label htmlFor="limit">Limit</label>
            <input
              id="limit"
              type="range"
              min={10}
              max={100}
              step={5}
              value={limit}
              onChange={(event) => setLimit(Number(event.target.value))}
            />
            <span>{limit}</span>
          </div>
        </section>

        {error ? (
          <section className="card error-card">
            <p className="section-label">Load error</p>
            <p>{error}</p>
          </section>
        ) : null}

        <section className="stats-grid">
          <article className="stat card">
            <span>Total loans</span>
            <strong>{summary?.total_loans ?? '—'}</strong>
          </article>
          <article className="stat card healthy">
            <span>Healthy</span>
            <strong>{summary?.healthy_loans ?? '—'}</strong>
            <small>{summary ? formatPercent(summary.healthy_loans, summary.total_loans) : ''}</small>
          </article>
          <article className="stat card watch">
            <span>Watch</span>
            <strong>{summary?.watch_loans ?? '—'}</strong>
            <small>{summary ? formatPercent(summary.watch_loans, summary.total_loans) : ''}</small>
          </article>
          <article className="stat card at-risk">
            <span>At risk</span>
            <strong>{summary?.at_risk_loans ?? '—'}</strong>
            <small>{summary ? formatPercent(summary.at_risk_loans, summary.total_loans) : ''}</small>
          </article>
          <article className="stat card critical">
            <span>Critical</span>
            <strong>{summary?.critical_loans ?? '—'}</strong>
            <small>{summary ? formatPercent(summary.critical_loans, summary.total_loans) : ''}</small>
          </article>
        </section>

        <section className="grid-two">
          <article className="card pane">
            <div className="pane-head">
              <div>
                <p className="section-label">Portfolio composition</p>
                <h2>Risk mix</h2>
              </div>
              <span>{loading ? 'Refreshing…' : 'Live'}</span>
            </div>
            <div className="bar-stack" aria-label="risk mix chart">
              <div className="bar-row">
                <span>Healthy</span>
                <div className="bar-track"><div className="bar healthy" style={{ width: `${summary && summary.total_loans ? (summary.healthy_loans / summary.total_loans) * 100 : 0}%` }} /></div>
              </div>
              <div className="bar-row">
                <span>Watch</span>
                <div className="bar-track"><div className="bar watch" style={{ width: `${summary && summary.total_loans ? (summary.watch_loans / summary.total_loans) * 100 : 0}%` }} /></div>
              </div>
              <div className="bar-row">
                <span>At Risk</span>
                <div className="bar-track"><div className="bar at-risk" style={{ width: `${summary && summary.total_loans ? (summary.at_risk_loans / summary.total_loans) * 100 : 0}%` }} /></div>
              </div>
              <div className="bar-row">
                <span>Critical</span>
                <div className="bar-track"><div className="bar critical" style={{ width: `${summary && summary.total_loans ? (summary.critical_loans / summary.total_loans) * 100 : 0}%` }} /></div>
              </div>
            </div>
          </article>

          <article className="card pane">
            <div className="pane-head">
              <div>
                <p className="section-label">Top attention needed</p>
                <h2>At-risk loans</h2>
              </div>
              <span>{atRiskItems.length} shown</span>
            </div>

            <div className="risk-list">
              {atRiskItems.length === 0 ? (
                <p className="empty-state">No at-risk loans in the current sample.</p>
              ) : (
                atRiskItems.map((item) => (
                  <button
                    type="button"
                    className="risk-item risk-item-button"
                    key={item.loan_id}
                    onClick={() => setSelectedLoanId(item.loan_id)}
                  >
                    <div>
                      <strong>{item.client_name ?? `Client ${item.client_id}`}</strong>
                      <p>Loan {item.loan_id} · {item.policy_decision}</p>
                    </div>
                    <span className={`pill ${tierClass(item.risk_tier)}`}>{item.risk_tier}</span>
                  </button>
                ))
              )}
            </div>
          </article>
        </section>

        <section className="card ledger">
          <div className="pane-head">
            <div>
              <p className="section-label">Decision feed</p>
              <h2>Latest loan reviews</h2>
            </div>
            <span>{portfolio?.items.length ?? 0} rows</span>
          </div>

          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Loan</th>
                  <th>Client</th>
                  <th>Risk score</th>
                  <th>Tier</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {portfolio?.items.map((item) => (
                  <tr
                    key={item.loan_id}
                    className="clickable-row"
                    tabIndex={0}
                    role="button"
                    onClick={() => setSelectedLoanId(item.loan_id)}
                    onKeyDown={(event) => {
                      if (event.key === 'Enter' || event.key === ' ') {
                        event.preventDefault();
                        setSelectedLoanId(item.loan_id);
                      }
                    }}
                  >
                    <td>{item.loan_id}</td>
                    <td>{item.client_name ?? item.client_id}</td>
                    <td>{item.risk_score}</td>
                    <td><span className={`pill ${tierClass(item.risk_tier)}`}>{item.risk_tier}</span></td>
                    <td>{item.recommended_action}</td>
                  </tr>
                )) ?? null}
              </tbody>
            </table>
          </div>
        </section>
      </main>

      {selectedLoanId ? (
        <div className="modal-backdrop" onClick={() => setSelectedLoanId(null)} role="presentation">
          <aside className="modal-card" onClick={(event) => event.stopPropagation()} role="dialog" aria-modal="true" aria-label="Decision details">
            <div className="pane-head modal-head">
              <div>
                <p className="section-label">Decision details</p>
                <h2>Loan {selectedLoanId}</h2>
              </div>
              <button type="button" className="ghost-button" onClick={() => setSelectedLoanId(null)}>
                Close
              </button>
            </div>

            {decisionLoading ? <p className="empty-state">Loading decision details…</p> : null}
            {decisionError ? <p className="empty-state error-text">{decisionError}</p> : null}

            {decision ? (
              <div className="detail-grid">
                <section className="detail-card">
                  <h3>Summary</h3>
                  <dl>
                    <div><dt>Client</dt><dd>{decision.client_name ?? decision.client_id}</dd></div>
                    <div><dt>Risk score</dt><dd>{decision.risk_score}</dd></div>
                    <div><dt>Tier</dt><dd><span className={`pill ${tierClass(decision.risk_tier)}`}>{decision.risk_tier}</span></dd></div>
                    <div><dt>Action</dt><dd>{decision.recommended_action}</dd></div>
                    <div><dt>Policy</dt><dd>{decision.policy_decision}</dd></div>
                    <div><dt>Model</dt><dd>{decision.model_name}</dd></div>
                    <div><dt>Created</dt><dd>{decision.created_at ?? decision.timestamp ?? '—'}</dd></div>
                  </dl>
                </section>

                <section className="detail-card">
                  <h3>Explanation</h3>
                  <p className="detail-copy">{decision.explanation}</p>
                </section>

                <section className="detail-card detail-card-wide">
                  <h3>Evidence</h3>
                  <div className="evidence-list">
                    {Object.entries(decision.evidence ?? {}).length === 0 ? (
                      <p className="empty-state">No evidence recorded.</p>
                    ) : (
                      Object.entries(decision.evidence).map(([key, value]) => (
                        <div key={key} className="evidence-item">
                          <span>{key}</span>
                          <pre>{prettyValue(value)}</pre>
                        </div>
                      ))
                    )}
                  </div>
                </section>

                <section className="detail-card detail-card-wide">
                  <h3>Reviewer feedback</h3>
                  <div className="form-grid">
                    <label>
                      Reviewer
                      <input value={feedbackReviewer} onChange={(event) => setFeedbackReviewer(event.target.value)} placeholder="Optional name" />
                    </label>
                    <label className="form-grid-wide">
                      Comment
                      <textarea value={feedbackComment} onChange={(event) => setFeedbackComment(event.target.value)} placeholder="Optional note for audit trail" rows={4} />
                    </label>
                  </div>
                  <div className="feedback-actions">
                    <button type="button" className="approve-button" disabled={feedbackSubmitting} onClick={() => void sendFeedback('approve')}>
                      Approve
                    </button>
                    <button type="button" className="reject-button" disabled={feedbackSubmitting} onClick={() => void sendFeedback('reject')}>
                      Reject
                    </button>
                  </div>
                  {feedbackMessage ? <p className="feedback-message">{feedbackMessage}</p> : null}
                </section>
              </div>
            ) : null}
          </aside>
        </div>
      ) : null}
    </div>
  );
}

export default App;
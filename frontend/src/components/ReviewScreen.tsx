import { useEffect, useState } from 'react'
import axios from 'axios'
import { addHeading, getReview, rejectHeading, undoReject } from '../api'
import type { ReviewData } from '../types'

const FACETS = [
  'topical',
  'geographic',
  'form_genre',
  'personal',
  'corporate',
  'event',
  'chronological',
]

interface Props {
  runId: number
}

// Self-contained review screen for one run: fetches its own data,
// owns its mutations, always refetches after mutating (the server is
// the only authority on the final list).
function ReviewScreen({ runId }: Props) {
  const [review, setReview] = useState<ReviewData | null>(null)
  const [newLabel, setNewLabel] = useState('')
  const [newFacet, setNewFacet] = useState('')
  const [addError, setAddError] = useState<string | null>(null)
  const [adding, setAdding] = useState(false)

  useEffect(() => {
    setReview(null)
    setAddError(null)
    getReview(runId).then(setReview)
  }, [runId])

  async function refresh() {
    setReview(await getReview(runId))
  }

  async function onReject(fastId: string) {
    await rejectHeading(runId, fastId)
    await refresh()
  }

  async function onUndo(fastId: string) {
    await undoReject(runId, fastId)
    await refresh()
  }

  async function onAdd(e: React.SubmitEvent) {
    e.preventDefault()
    if (!newLabel.trim()) return
    setAddError(null)
    setAdding(true)
    try {
      await addHeading(runId, newLabel.trim(), newFacet)
      setNewLabel('')
      await refresh()
    } catch (err) {
      if (axios.isAxiosError(err) && err.response) {
        setAddError(err.response.data.detail ?? 'could not add heading')
      } else {
        setAddError('network error')
      }
    } finally {
      setAdding(false)
    }
  }

  if (!review) {
    return (
      <p className="status-line">
        <span className="spinner" /> loading review…
      </p>
    )
  }

  return (
    <section>
      <header className="review-head">
        <h2>
          {review.title ?? '(untitled)'}{' '}
          <span className="isbn">{review.isbn13}</span>
        </h2>
        {review.metadata_source && (
          <p className="status-line">
            metadata via <span className="badge">{review.metadata_source}</span>
            {review.metadata_source.includes('web_search') && (
              <span className="badge tier-fuzzy">
                web-sourced — verify it matches the book in hand
              </span>
            )}
          </p>
        )}
        {review.description ? (
          <details>
            <summary>description</summary>
            <p>{review.description}</p>
          </details>
        ) : (
          <p className="status-line">
            no description found, headings were generated from the title alone
          </p>
        )}
      </header>

      <div className="columns">
        <div className="card">
          <h3>Proposals</h3>
          {Object.entries(review.proposals).map(([model, headings]) => (
            <div key={model}>
              <h4 className="model-name">{model}</h4>
              <ul className="rows">
                {headings.map((h) => (
                  <li key={h.id}>
                    <span className="grow">
                      {h.proposed_label}
                      {h.label && h.label !== h.proposed_label && (
                        <>
                          {' '}
                          → <strong>{h.label}</strong>
                        </>
                      )}
                      {!h.label && (
                        <>
                          {' '}
                          → <em className="muted">no match</em>
                        </>
                      )}
                    </span>
                    <span className={`badge tier-${h.tier}`}>{h.tier}</span>
                    <span className="badge">{h.facet}</span>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="card">
          <h3>Final list</h3>
          <ul className="rows">
            {review.final.map((entry) => (
              <li key={entry.fast_id} className={entry.rejected ? 'rejected' : undefined}>
                <span className="grow">
                  <strong className="label">{entry.label}</strong>{' '}
                  <span className="muted">by {entry.source_models.join(', ')}</span>
                </span>
                <span className="badge">{entry.facet}</span>
                {entry.rejected ? (
                  <button onClick={() => onUndo(entry.fast_id)}>undo</button>
                ) : (
                  <button onClick={() => onReject(entry.fast_id)} title="reject">
                    ✗
                  </button>
                )}
              </li>
            ))}
          </ul>

          <form className="add-form" onSubmit={onAdd}>
            <input
              value={newLabel}
              onChange={(e) => setNewLabel(e.target.value)}
              placeholder="Add a heading…"
            />
            <select value={newFacet} onChange={(e) => setNewFacet(e.target.value)}>
              <option value="">any facet</option>
              {FACETS.map((f) => (
                <option key={f} value={f}>
                  {f}
                </option>
              ))}
            </select>
            <button type="submit" className="primary" disabled={adding}>
              {adding ? 'authorizing…' : 'add'}
            </button>
          </form>
          {addError && <p className="status-line error">{addError}</p>}
        </div>
      </div>
    </section>
  )
}

export default ReviewScreen

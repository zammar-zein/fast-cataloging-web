import { useEffect, useState } from 'react'
import { getRuns } from '../api'
import type { RunPage } from '../types'

interface Props {
  onOpen: (runId: number) => void
}

// Flat, chronological runs table (newest first), 25 per page.
function History({ onOpen }: Props) {
  const [page, setPage] = useState(1)
  const [data, setData] = useState<RunPage | null>(null)

  useEffect(() => {
    getRuns(page).then(setData)
  }, [page])

  if (!data) {
    return (
      <p className="status-line">
        <span className="spinner" /> loading history…
      </p>
    )
  }
  if (data.total === 0) return <p className="status-line">nothing cataloged yet</p>

  const lastPage = Math.max(1, Math.ceil(data.total / data.page_size))

  return (
    <section className="card">
      <table className="sheet">
        <thead>
          <tr>
            <th>run</th>
            <th>title</th>
            <th>ISBN</th>
            <th>status</th>
            <th>when</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {data.items.map((r) => (
            <tr key={r.id}>
              <td className="num">#{r.id}</td>
              <td className="title-cell">{r.title ?? <em>(untitled)</em>}</td>
              <td className="num">{r.isbn13}</td>
              <td>
                <span className={`badge status-${r.status}`}>{r.status}</span>
              </td>
              <td>{new Date(r.created_at).toLocaleString()}</td>
              <td>
                {r.status === 'succeeded' && (
                  <button onClick={() => onOpen(r.id)}>open review</button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <footer className="pager">
        <button onClick={() => setPage((p) => p - 1)} disabled={page <= 1}>
          ← newer
        </button>
        <span>
          page {data.page} of {lastPage} · {data.total} runs
        </span>
        <button onClick={() => setPage((p) => p + 1)} disabled={page >= lastPage}>
          older →
        </button>
      </footer>
    </section>
  )
}

export default History

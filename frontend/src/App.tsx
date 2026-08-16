import { useEffect, useState } from 'react'
import './App.css'
import axios from 'axios'
import { createWork, getRun } from './api'
import type { WorkCreated, RunStatus } from './types'
import ReviewScreen from './components/ReviewScreen'
import History from './components/History'

type View = 'catalog' | 'history'

function App() {
  const [view, setView] = useState<View>('catalog')

  // catalog flow
  const [isbn, setIsbn] = useState('')
  const [result, setResult] = useState<WorkCreated | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [run, setRun] = useState<RunStatus | null>(null)

  // which run's review is on screen (from a fresh run OR from history)
  const [openRunId, setOpenRunId] = useState<number | null>(null)

  useEffect(() => {
    if (!result) return // nothing queued yet

    const timer = setInterval(async () => {
      const status = await getRun(result.run_id)
      setRun(status)
      if (status.status === 'succeeded' || status.status === 'failed') {
        clearInterval(timer)
      }
      if (status.status === 'succeeded') {
        setOpenRunId(result.run_id)
      }
    }, 2000)

    return () => clearInterval(timer)
  }, [result])

  async function submit(e: React.SubmitEvent) {
    e.preventDefault()
    setRun(null)
    setError(null)
    setResult(null)
    setOpenRunId(null)

    try {
      setResult(await createWork(isbn))
    } catch (err) {
      if (axios.isAxiosError(err) && err.response) {
        setError(err.response.data.detail ?? 'something went wrong')
      } else {
        setError('network error')
      }
    }
  }

  function openFromHistory(runId: number) {
    setOpenRunId(runId)
    setView('catalog') // review renders on the catalog view
    setResult(null)
    setRun(null)
    setError(null)
  }

  const working = run && (run.status === 'queued' || run.status === 'running')

  return (
    <div className="shell">
      <header className="topbar">
        <h1 className="brand">
          <span>FAST</span> Cataloging
        </h1>
        <nav className="tabs">
          <button onClick={() => setView('catalog')} disabled={view === 'catalog'}>
            catalog
          </button>
          <button onClick={() => setView('history')} disabled={view === 'history'}>
            history
          </button>
        </nav>
      </header>

      <main>
        {view === 'catalog' && (
          <>
            <form className="catalog-form" onSubmit={submit}>
              <input
                value={isbn}
                onChange={(e) => setIsbn(e.target.value)}
                placeholder="Paste an ISBN…"
              />
              <button type="submit" className="primary" disabled={!!working}>
                Catalog it
              </button>
            </form>

            {error && <p className="status-line error">{error}</p>}
            {working && (
              <p className="status-line">
                <span className="spinner" />
                cataloging — fetching metadata, asking the model, authorizing
                headings…
              </p>
            )}
            {run?.status === 'failed' && (
              <p className="status-line error">{run.error}</p>
            )}

            {openRunId !== null && <ReviewScreen runId={openRunId} />}
          </>
        )}

        {view === 'history' && <History onOpen={openFromHistory} />}
      </main>
    </div>
  )
}

export default App

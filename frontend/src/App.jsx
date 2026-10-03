import { useEffect, useRef, useState } from 'react'
import './App.css'

const API_URL = import.meta.env.VITE_API_URL ?? (
  import.meta.env.DEV ? '' : 'http://127.0.0.1:8000'
)
const EMPTY_DETAILS = 'Not returned by the current API'

const COMMANDS = [
  { id: 'new-query', label: 'New query', shortcut: 'N' },
  { id: 'clear', label: 'Clear conversation', shortcut: 'Backspace' },
  { id: 'execution', label: 'View execution', shortcut: 'G E' },
  { id: 'documents', label: 'View retrieved evidence', shortcut: 'G D' },
  { id: 'database', label: 'View database result', shortcut: 'G B' },
  { id: 'trace', label: 'View trace', shortcut: 'G T' },
  { id: 'copy', label: 'Copy answer', shortcut: 'C' },
]

const formatTime = (date) => date.toLocaleTimeString([], {
  hour: '2-digit',
  minute: '2-digit',
  hour12: false,
})

const formatDuration = (duration) => (
  typeof duration === 'number' && Number.isFinite(duration)
    ? `${duration.toFixed(3)} s`
    : '—'
)

function FlowNode({ id, label, meta, status, selected, onClick, preview }) {
  return (
    <button
      aria-expanded={selected}
      aria-label={`${label}. ${preview}`}
      className="flow-node"
      data-node={id}
      data-status={status}
      data-preview={preview}
      onClick={onClick}
      type="button"
    >
      <span className="node-name">{label}</span>
      <span className="node-type">{meta}</span>
      <span className="node-state">{status}</span>
    </button>
  )
}

function App() {
  const [message, setMessage] = useState('')
  const [answer, setAnswer] = useState('')
  const [route, setRoute] = useState('')
  const [executionSteps, setExecutionSteps] = useState([])
  const [workflow, setWorkflow] = useState({})
  const [sources, setSources] = useState([])
  const [langfuse, setLangfuse] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [requestStatus, setRequestStatus] = useState('')
  const [recentQueries, setRecentQueries] = useState([])
  const [selectedNode, setSelectedNode] = useState('')
  const [commandOpen, setCommandOpen] = useState(false)
  const [commandSearch, setCommandSearch] = useState('')
  const [toast, setToast] = useState('')

  const queryRef = useRef(null)
  const commandDialogRef = useRef(null)
  const commandSearchRef = useRef(null)
  const toastTimerRef = useRef(null)

  useEffect(() => {
    if (!loading) return undefined

    const timeout = window.setTimeout(() => {
      setRequestStatus('Waiting for the agent response')
    }, 500)

    return () => window.clearTimeout(timeout)
  }, [loading])

  useEffect(() => {
    const dialog = commandDialogRef.current
    if (!dialog) return

    if (commandOpen && !dialog.open) {
      dialog.showModal()
      commandSearchRef.current?.focus()
    } else if (!commandOpen && dialog.open) {
      dialog.close()
    }
  }, [commandOpen])

  useEffect(() => () => window.clearTimeout(toastTimerRef.current), [])

  useEffect(() => {
    const handleKeydown = (event) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
        event.preventDefault()
        setCommandSearch('')
        setCommandOpen(true)
      }
      if (event.key === 'Escape' && commandDialogRef.current?.open) {
        event.preventDefault()
        setCommandOpen(false)
      }
    }

    document.addEventListener('keydown', handleKeydown)
    return () => document.removeEventListener('keydown', handleKeydown)
  }, [])

  const showToast = (text) => {
    setToast(text)
    window.clearTimeout(toastTimerRef.current)
    toastTimerRef.current = window.setTimeout(() => setToast(''), 2400)
  }

  const fetchLangfuseData = async (traceId) => {
    if (!traceId) return

    const maxAttempts = 10
    const delay = 3000

    for (let attempt = 1; attempt <= maxAttempts; attempt += 1) {
      try {
        const response = await fetch(`${API_URL}/api/langfuse/trace/${traceId}`)
        if (!response.ok) {
          throw new Error(`Langfuse request failed with status ${response.status}`)
        }

        const data = await response.json()
        if (data.observations?.length > 0) {
          setLangfuse(data)
          return
        }
      } catch (fetchError) {
        console.error('Langfuse fetch error:', fetchError)
      }

      if (attempt < maxAttempts) {
        await new Promise((resolve) => window.setTimeout(resolve, delay))
      }
    }

    setLangfuse({
      status: 'available',
      trace_id: traceId,
      trace_name: 'enterprise_ai_agent',
      llm_calls: 0,
      rag_retrievals: 0,
      mcp_calls: 0,
      validation_calls: 0,
      duration_seconds: null,
      observations: [],
      pending: true,
    })
  }

  const askAgent = async (event) => {
    event.preventDefault()
    if (!message.trim() || loading) return

    const query = message.trim()
    setLoading(true)
    setRequestStatus('Sending question to the agent')
    setError('')
    setAnswer('')
    setRoute('')
    setExecutionSteps([])
    setWorkflow({})
    setSources([])
    setLangfuse(null)
    setSelectedNode('')
    setRecentQueries((current) => [
      { id: `${Date.now()}-${query}`, query, time: formatTime(new Date()) },
      ...current.filter((item) => item.query !== query),
    ].slice(0, 8))

    try {
      const response = await fetch(`${API_URL}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: query }),
      })

      if (!response.ok) {
        throw new Error(`Request failed with status ${response.status}`)
      }

      const data = await response.json()
      setAnswer(data.answer || '')
      setRoute(data.route || '')
      setExecutionSteps(data.execution_steps || [])
      setWorkflow(data.workflow || {})
      setSources(data.sources || [])
      setRequestStatus('Request complete')

      const traceId = data.workflow?.langfuse?.trace_id
      if (traceId) fetchLangfuseData(traceId)
    } catch (requestError) {
      console.error(requestError)
      const statusMatch = requestError.message?.match(/status (\d+)/)
      setError(statusMatch
        ? `The agent returned HTTP ${statusMatch[1]}. Check the service logs, then retry.`
        : 'Could not reach the agent. Check that the FastAPI backend is running, then retry.')
      setRequestStatus('Request failed')
    } finally {
      setLoading(false)
    }
  }

  const clearConversation = () => {
    setAnswer('')
    setRoute('')
    setExecutionSteps([])
    setWorkflow({})
    setSources([])
    setLangfuse(null)
    setError('')
    setRequestStatus('')
    setSelectedNode('')
  }

  const scrollTo = (selector) => {
    document.querySelector(selector)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    setCommandOpen(false)
  }

  const commandActions = {
    'new-query': () => {
      clearConversation()
      setMessage('')
      setCommandOpen(false)
      queryRef.current?.focus()
    },
    clear: () => {
      clearConversation()
      setMessage('')
      setCommandOpen(false)
      showToast('Current result cleared.')
    },
    execution: () => scrollTo('#execution'),
    documents: () => scrollTo('#evidence'),
    database: () => {
      setSelectedNode('database')
      scrollTo('#execution')
    },
    trace: () => scrollTo('#observability'),
    copy: async () => {
      setCommandOpen(false)
      if (!answer) {
        showToast('There is no answer to copy yet.')
        return
      }
      try {
        await navigator.clipboard.writeText(answer)
        showToast('Answer copied.')
      } catch {
        showToast('Clipboard access is unavailable in this browser.')
      }
    },
  }

  const executionSet = new Set(executionSteps)
  const routerData = workflow.router || {}
  const ragData = workflow.rag || {}
  const mcpData = workflow.mcp || {}
  const llmData = workflow.llm || {}
  const validationData = workflow.validation || {}
  const isComplete = executionSteps.length > 0
  const statusText = loading
    ? requestStatus || 'Sending question to the agent'
    : error
      ? 'Request failed · retry when the service is available'
      : isComplete
        ? `Complete · ${route || 'request'} route`
        : 'Ready when you are'

  const nodeStatus = (node) => {
    if (loading) return node === 'query' ? 'complete' : 'waiting'
    if (error) return node === 'router' ? 'error' : 'waiting'
    if (!isComplete) return 'waiting'

    if (node === 'query') return 'complete'
    if (node === 'router') return executionSet.has('router') ? 'complete' : 'waiting'
    if (node === 'rag') {
      if (executionSet.has('retrieve')) return 'complete'
      return routerData.needs_rag === false ? 'skipped' : 'waiting'
    }
    if (node === 'database') {
      if (executionSet.has('database')) return 'complete'
      return routerData.needs_database === false ? 'skipped' : 'waiting'
    }
    if (node === 'mcp') {
      if (mcpData.tool) return 'complete'
      return route === 'database' || route === 'combined' ? 'skipped' : 'waiting'
    }
    if (node === 'model') {
      return executionSet.has('generate') || executionSet.has('direct') ? 'complete' : 'waiting'
    }
    if (node === 'answer') return answer ? 'complete' : 'waiting'
    return 'waiting'
  }

  const detailForNode = (node) => {
    const fields = {
      query: [
        ['Question', message.trim() || '—'],
        ['Request', loading ? 'In progress' : isComplete ? 'Completed' : 'Not sent'],
      ],
      router: [
        ['Route', routerData.route || route || EMPTY_DETAILS],
        ['Needs RAG', typeof routerData.needs_rag === 'boolean' ? (routerData.needs_rag ? 'Yes' : 'No') : EMPTY_DETAILS],
        ['Needs database', typeof routerData.needs_database === 'boolean' ? (routerData.needs_database ? 'Yes' : 'No') : EMPTY_DETAILS],
        ['Employee', routerData.employee_name || EMPTY_DETAILS],
        ['RAG query', routerData.rag_query || EMPTY_DETAILS],
      ],
      rag: [
        ['Embedding model', ragData.embedding_model || EMPTY_DETAILS],
        ['Vector store', ragData.vector_store || EMPTY_DETAILS],
        ['Top K', ragData.top_k ?? EMPTY_DETAILS],
        ['Distance threshold', ragData.distance_threshold ?? EMPTY_DETAILS],
        ['Chunks retrieved', ragData.chunks_retrieved ?? EMPTY_DETAILS],
        ['Chunks after filter', ragData.chunks_after_filter ?? EMPTY_DETAILS],
        ['Query', ragData.query || EMPTY_DETAILS],
      ],
      database: [
        ['Database', 'MySQL'],
        ['Employee', mcpData.employee_name || EMPTY_DETAILS],
        ['Record found', typeof mcpData.found === 'boolean' ? (mcpData.found ? 'Yes' : 'No') : EMPTY_DETAILS],
        ['SQL query', EMPTY_DETAILS],
        ['Execution time', EMPTY_DETAILS],
      ],
      mcp: [
        ['Tool', mcpData.tool || EMPTY_DETAILS],
        ['Employee', mcpData.employee_name || EMPTY_DETAILS],
        ['Record found', typeof mcpData.found === 'boolean' ? (mcpData.found ? 'Yes' : 'No') : EMPTY_DETAILS],
        ['Input / output', EMPTY_DETAILS],
        ['Status', mcpData.status || EMPTY_DETAILS],
      ],
      model: [
        ['Provider', llmData.provider || EMPTY_DETAILS],
        ['Status', llmData.status || EMPTY_DETAILS],
        ['Token usage', EMPTY_DETAILS],
        ['Generation latency', EMPTY_DETAILS],
      ],
      answer: [
        ['Route', route || EMPTY_DETAILS],
        ['Validation', validationData.status || EMPTY_DETAILS],
        ['Valid', typeof validationData.valid === 'boolean' ? (validationData.valid ? 'Yes' : 'No') : EMPTY_DETAILS],
        ['Citations', sources.length ? `${sources.length} source${sources.length === 1 ? '' : 's'}` : EMPTY_DETAILS],
      ],
    }
    return fields[node] || []
  }

  const nodeLabel = (node) => ({
    query: 'User query',
    router: 'Agent router',
    rag: 'RAG retrieval',
    database: 'Database',
    mcp: 'MCP tool',
    model: 'LLM generation',
    answer: 'Final answer',
  }[node] || node)

  const visibleCommands = COMMANDS.filter((command) => (
    command.label.toLowerCase().includes(commandSearch.trim().toLowerCase())
  ))

  const observations = langfuse?.observations || []
  const profileItems = [
    ['Model', llmData.provider || EMPTY_DETAILS],
    ['Routing', route || EMPTY_DETAILS],
    ['Retrieval', ragData.vector_store || 'Not used'],
    ['Top K', ragData.top_k ?? '—'],
    ['Embedding', ragData.embedding_model || '—'],
    ['Vector dimension', EMPTY_DETAILS],
    ['Database', 'MySQL'],
    ['Protocol', 'MCP'],
    ['Orchestration', 'LangGraph'],
    ['Observability', 'Langfuse'],
  ]

  return (
    <div className="app-shell">
      <a className="skip-link" href="#main">Skip to workspace</a>
      <header className="site-header">
        <div className="header-inner">
          <a className="wordmark" href="#main" aria-label="Enterprise AI Knowledge Agent home">
            <span className="wordmark-top">Enterprise /</span>
            <span className="wordmark-bottom">AI Knowledge Agent</span>
          </a>
          <nav className="main-nav" aria-label="Primary navigation">
            <a href="#workspace" aria-current="page">Workspace</a>
            <a href="#execution">Runs</a>
            <a href="#profile">Knowledge</a>
            <a href="#observability">Observability</a>
          </nav>
          <div className="system-state">
            <span className={`system-dot${error ? ' is-error' : ''}`} aria-hidden="true" />
            <span>{error ? 'Agent unavailable' : loading ? 'Request in progress' : 'System operational'}</span>
          </div>
        </div>
      </header>

      <main className="page" id="main">
        <section className="hero" aria-labelledby="hero-title">
          <h1 id="hero-title"><span>KNOWLEDGE</span><span>AT WORK.</span></h1>
          <div className="hero-aside">
            <p>Ask across company documents, employee data and connected tools. Follow the path from question to grounded answer.</p>
            <div className="hero-note">An intelligent engineering workspace</div>
          </div>
        </section>

        <div className="preview-ribbon" role="note">
          <span><strong>ENTERPRISE KNOWLEDGE WORKSPACE</strong> · Live application</span>
          <span className="ribbon-side">Connected to the existing agent API</span>
        </div>

        <section className="workbench" id="workspace" aria-labelledby="ask-title">
          <div className="ask-workspace">
            <div className="ask-heading">
              <div>
                <span className="section-kicker">Ask the agent</span>
                <h2 className="section-title" id="ask-title">What would you like to know?</h2>
              </div>
              <span className="shortcut-hint" aria-label="Keyboard shortcut Control or Command and K">
                <kbd>{/Mac|iPhone|iPad/.test(navigator.platform) ? '⌘' : 'Ctrl'}</kbd><kbd>K</kbd>
              </span>
            </div>
            <form id="query-form" onSubmit={askAgent}>
              <div className={`query-sheet${error ? ' is-error' : ''}`}>
                <div className="input-context"><span className="input-caret" aria-hidden="true" /><span>QUESTION / ENTERPRISE KNOWLEDGE</span></div>
                <label className="visually-hidden" htmlFor="query-input">What would you like to know?</label>
                <textarea
                  aria-describedby="query-feedback query-hint"
                  className="query-input"
                  disabled={loading}
                  id="query-input"
                  onChange={(event) => setMessage(event.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === 'Enter' && !event.shiftKey) {
                      event.preventDefault()
                      queryRef.current?.form?.requestSubmit()
                    }
                  }}
                  placeholder="How many annual leave days are employees entitled to?"
                  ref={queryRef}
                  rows={2}
                  value={message}
                />
                <div className="query-tools">
                  <div className="source-controls" aria-label="Available agent sources">
                    <span className="source-chip">RAG</span>
                    <span className="source-chip">DATABASE</span>
                    <span className="source-chip">MCP</span>
                    <span className="source-chip is-auto">AUTO</span>
                  </div>
                  <div className="query-actions">
                    <button className="text-button" disabled={loading} onClick={() => setMessage('')} type="button">Clear</button>
                    <button className="primary-button" disabled={!message.trim() || loading} type="submit">
                      <span>{loading ? 'RUNNING QUERY' : 'RUN QUERY'}</span><span className="arrow-mark" aria-hidden="true" />
                    </button>
                  </div>
                </div>
              </div>
              <p className="form-feedback" id="query-feedback" role="status" aria-live="polite">{error}</p>
              <p className="sample-note" id="query-hint">Press Enter to run · Shift+Enter for a new line. Routing is selected automatically.</p>
            </form>
          </div>

          <aside className="history" aria-labelledby="history-title">
            <div className="history-head"><h2 id="history-title">Recent</h2><span>{String(recentQueries.length).padStart(2, '0')}</span></div>
            {recentQueries.length ? (
              <ul className="history-list">
                {recentQueries.map((item) => (
                  <li key={item.id}>
                    <button className="history-item" onClick={() => setMessage(item.query)} type="button">
                      <time>{item.time}</time><span>{item.query}</span>
                    </button>
                  </li>
                ))}
              </ul>
            ) : <p className="history-empty">Queries from this session will appear here.</p>}
          </aside>

          <details className="mobile-history">
            <summary><span>Recent queries</span><span className="mono">{String(recentQueries.length).padStart(2, '0')}</span></summary>
            {recentQueries.length ? (
              <ul className="history-list">
                {recentQueries.map((item) => (
                  <li key={item.id}>
                    <button className="history-item" onClick={() => setMessage(item.query)} type="button">
                      <time>{item.time}</time><span>{item.query}</span>
                    </button>
                  </li>
                ))}
              </ul>
            ) : <p className="history-empty">Queries from this session will appear here.</p>}
          </details>
        </section>

        <section className={`agent-state${loading ? ' is-loading' : ''}${error ? ' is-error' : ''}`} aria-live="polite">
          <div className="state-copy">
            <span className="state-indicator" aria-hidden="true" />
            <span className="state-text" key={statusText}>{statusText}</span>
          </div>
          {route && <span className="route-value">ROUTE · {route.toUpperCase()}</span>}
        </section>

        <section className="technical-section" id="execution" aria-labelledby="execution-title">
          <div className="section-topline">
            <div>
              <span className="section-kicker">System / execution</span>
              <h2 className="section-title" id="execution-title">One question. A visible path.</h2>
              <p className="section-intro">Follow the router into retrieval and employee data, through the tool layer and model, to the answer.</p>
            </div>
            <div className="graph-heading-right">
              <span className="section-index">EXECUTION MAP</span>
              <div className="legend" aria-label="Execution state legend">
                <span><i className="legend-active" />Active</span>
                <span><i className="legend-complete" />Complete</span>
                <span><i className="legend-error" />Error</span>
              </div>
            </div>
          </div>
          <div className="execution-shell">
            <div className="graph-caption">
              <span>QUERY → ROUTER → ROUTES → MODEL → ANSWER</span>
              <strong>{route ? `ROUTE · ${route.toUpperCase()}` : 'ROUTE · AUTOMATIC'}</strong>
            </div>
            <div className="execution-map" aria-label="Agent execution graph">
              <FlowNode id="query" label="User query" meta="Input" preview="Submitted question" status={nodeStatus('query')} selected={selectedNode === 'query'} onClick={() => setSelectedNode(selectedNode === 'query' ? '' : 'query')} />
              <span className="connector" data-status={executionSet.has('router') ? 'complete' : loading ? 'active' : 'waiting'} aria-hidden="true" />
              <FlowNode id="router" label="Agent router" meta="LangGraph" preview="Automatic route selection" status={nodeStatus('router')} selected={selectedNode === 'router'} onClick={() => setSelectedNode(selectedNode === 'router' ? '' : 'router')} />
              <span className="connector branch-connector" data-status={executionSet.has('retrieve') || executionSet.has('database') ? 'complete' : 'waiting'} aria-hidden="true" />
              <div className="branch-stack" aria-label="RAG and database routes">
                <FlowNode id="rag" label="RAG" meta={ragData.vector_store || 'Retrieval'} preview="Embedding, vector search, retrieved chunks" status={nodeStatus('rag')} selected={selectedNode === 'rag'} onClick={() => setSelectedNode(selectedNode === 'rag' ? '' : 'rag')} />
                <FlowNode id="database" label="Database" meta="MySQL" preview="Employee data via MCP" status={nodeStatus('database')} selected={selectedNode === 'database'} onClick={() => setSelectedNode(selectedNode === 'database' ? '' : 'database')} />
              </div>
              <span className="connector" data-status={mcpData.tool ? 'complete' : 'waiting'} aria-hidden="true" />
              <FlowNode id="mcp" label="MCP" meta={mcpData.tool || 'Tool layer'} preview="Tool name and returned status" status={nodeStatus('mcp')} selected={selectedNode === 'mcp'} onClick={() => setSelectedNode(selectedNode === 'mcp' ? '' : 'mcp')} />
              <span className="connector" data-status={executionSet.has('generate') || executionSet.has('direct') ? 'complete' : 'waiting'} aria-hidden="true" />
              <FlowNode id="model" label="LLM" meta={llmData.provider || 'Model'} preview="Provider and status from the workflow" status={nodeStatus('model')} selected={selectedNode === 'model'} onClick={() => setSelectedNode(selectedNode === 'model' ? '' : 'model')} />
              <span className="connector" data-status={answer ? 'complete' : 'waiting'} aria-hidden="true" />
              <FlowNode id="answer" label="Answer" meta={validationData.status || 'Output'} preview="Response and validation state" status={nodeStatus('answer')} selected={selectedNode === 'answer'} onClick={() => setSelectedNode(selectedNode === 'answer' ? '' : 'answer')} />
            </div>

            {selectedNode && (
              <div className="detail-drawer" aria-live="polite">
                <div className="detail-header">
                  <h3>{nodeLabel(selectedNode)}</h3>
                  <button className="detail-close" aria-label="Close node details" onClick={() => setSelectedNode('')} type="button">×</button>
                </div>
                <dl className="detail-grid">
                  {detailForNode(selectedNode).map(([label, value]) => (
                    <div className="detail-item" key={label}>
                      <dt>{label}</dt><dd>{value}</dd>
                    </div>
                  ))}
                </dl>
              </div>
            )}
            <div className="graph-foot">
              <span>{isComplete ? `${executionSteps.length} workflow steps returned` : loading ? 'Waiting for the completed workflow response' : 'Select a node to inspect available details'}</span>
              <span>Node states reflect API response data</span>
            </div>
          </div>
        </section>

        <section className="answer-area" id="answer" aria-labelledby="answer-title">
          <article className="answer-main">
            <div className="answer-top"><span className="section-kicker">Answer</span>{answer && <span className="sample-tag">Agent response</span>}</div>
            {error ? (
              <div className="answer-error">
                <h2 id="answer-title">Agent unavailable</h2>
                <p>{error}</p>
                <button className="retry-button" disabled={!message.trim() || loading} onClick={(event) => askAgent(event)} type="button">Retry query</button>
              </div>
            ) : answer ? (
              <div className="answer-copy">
                <h2 id="answer-title">Response</h2>
                {answer.split(/\n+/).filter(Boolean).map((paragraph, index) => <p key={`${index}-${paragraph}`}>{paragraph}</p>)}
                {sources.length > 0 && (
                  <div className="citation-list" aria-label="Response sources">
                    {sources.map((source, index) => {
                      const sourceName = typeof source === 'string'
                        ? source
                        : source.name || source.document || source.filename || source.source || `Source ${index + 1}`
                      return <span className="citation" key={`${index}-${sourceName}`}>{sourceName}</span>
                    })}
                  </div>
                )}
              </div>
            ) : (
              <div className="answer-empty">
                <h2 id="answer-title">Your answer will appear here.</h2>
                <p>When the agent completes a query, its response and available evidence will be shown in this space.</p>
              </div>
            )}
          </article>

          <aside className="evidence" id="evidence" aria-labelledby="evidence-title">
            <h3 id="evidence-title">Evidence &amp; tool activity</h3>
            {sources.length > 0 ? (
              sources.map((source, index) => {
                const sourceName = typeof source === 'string'
                  ? source
                  : source.name || source.document || source.filename || source.source || `Source ${index + 1}`
                return <div className="evidence-row" key={`${index}-${sourceName}`}><span className="evidence-source">{sourceName}</span><span className="evidence-meta">SOURCE<br />{index + 1}</span></div>
              })
            ) : (
              <p className="evidence-empty">The current chat response does not include document-level citations.</p>
            )}
            {workflow.rag && (
              <div className="evidence-detail">
                <span className="evidence-label">Retrieval</span>
                <span>{workflow.rag.vector_store || 'RAG'} · {workflow.rag.chunks_retrieved ?? '—'} chunks</span>
              </div>
            )}
            {workflow.mcp && (
              <div className="evidence-detail">
                <span className="evidence-label">MCP / {workflow.mcp.tool || 'tool'}</span>
                <span>{workflow.mcp.employee_name || EMPTY_DETAILS} · {typeof workflow.mcp.found === 'boolean' ? (workflow.mcp.found ? 'record found' : 'record not found') : EMPTY_DETAILS}</span>
              </div>
            )}
            {workflow.validation && (
              <div className="evidence-detail">
                <span className="evidence-label">Response validation</span>
                <span>{workflow.validation.valid ? 'Valid' : 'Needs review'} · {workflow.validation.warnings?.length || 0} warnings</span>
              </div>
            )}
          </aside>
        </section>

        <section className="profile-section" id="profile" aria-labelledby="profile-title">
          <div className="section-topline">
            <div><span className="section-kicker">Knowledge / runtime</span><h2 className="section-title" id="profile-title">Technical profile</h2></div>
            <span className="section-index">LIVE CONFIGURATION</span>
          </div>
          <dl className="spec-sheet">
            {profileItems.map(([label, value]) => <div className="spec-item" key={label}><dt>{label}</dt><dd>{value}</dd></div>)}
          </dl>
        </section>

        <section className="observability-section" id="observability" aria-labelledby="observability-title">
          <div className="section-topline">
            <div><span className="section-kicker">Observability / Langfuse</span><h2 className="section-title" id="observability-title">A trace you can follow.</h2></div>
            <span className="section-index">{langfuse ? 'TRACE CONNECTED' : 'AWAITING TRACE'}</span>
          </div>
          <div className="trace-shell">
            <div className="trace-main">
              {langfuse ? (
                <>
                  <div className="trace-root">
                    <span className="trace-root-mark" aria-hidden="true" />
                    <span className="trace-name">{langfuse.trace_name || 'enterprise_ai_agent'}</span>
                    <span className="trace-duration">{langfuse.pending ? 'Pending observations' : langfuse.status || 'Available'}</span>
                  </div>
                  {observations.length > 0 ? (
                    <ol className="trace-list" aria-label="Langfuse observations">
                      {observations.map((observation, index) => (
                        <li className="trace-row" key={`${observation.name}-${observation.type}-${index}`}>
                          <details>
                            <summary><span className="trace-tree" aria-hidden="true" /><span className="trace-name">{observation.name || `Observation ${index + 1}`}</span><span className="trace-duration">{observation.type || 'Observation'}</span><span className="trace-chevron" aria-hidden="true" /></summary>
                            <dl className="trace-detail"><dt>Name</dt><dd>{observation.name || '—'}</dd><dt>Type</dt><dd>{observation.type || '—'}</dd></dl>
                          </details>
                        </li>
                      ))}
                    </ol>
                  ) : (
                    <p className="trace-empty">{langfuse.pending ? 'Langfuse is still processing this trace.' : 'No observation details were returned.'}</p>
                  )}
                  <div className="trace-id-row"><span>TRACE ID</span><code>{langfuse.trace_id || '—'}</code></div>
                </>
              ) : (
                <div className="trace-empty-state">
                  <span className="trace-root-mark" aria-hidden="true" />
                  <div><strong>{loading ? 'Trace will appear after the response' : 'No trace for this request yet'}</strong><p>Langfuse details load after the agent returns a trace ID.</p></div>
                </div>
              )}
            </div>
            <aside className="trace-summary">
              <div>
                <span className="summary-label">Total duration</span>
                <p className="trace-total">{formatDuration(langfuse?.duration_seconds)}</p>
                <div className="trace-counts">
                  <div><span>LLM calls</span><strong>{langfuse?.llm_calls ?? '—'}</strong></div>
                  <div><span>RAG retrievals</span><strong>{langfuse?.rag_retrievals ?? '—'}</strong></div>
                  <div><span>MCP calls</span><strong>{langfuse?.mcp_calls ?? (workflow.mcp?.tool ? 1 : '—')}</strong></div>
                  <div><span>Validation</span><strong>{langfuse?.validation_calls ?? '—'}</strong></div>
                </div>
              </div>
              {workflow.langfuse?.trace_url && (
                <a className="langfuse-link" href={workflow.langfuse.trace_url} rel="noreferrer" target="_blank">Open Langfuse trace <span aria-hidden="true">↗</span></a>
              )}
            </aside>
          </div>
        </section>

        <footer className="footer"><span><strong>ENTERPRISE / AI KNOWLEDGE AGENT</strong> · LIVE WORKSPACE</span><span>Runtime values are supplied by the agent API</span></footer>
      </main>

      <dialog aria-label="Command menu" className="command-dialog" onCancel={() => setCommandOpen(false)} onClose={() => setCommandOpen(false)} onClick={(event) => { if (event.target === commandDialogRef.current) setCommandOpen(false) }} ref={commandDialogRef}>
        <div className="command-head">
          <span className="command-search-icon" aria-hidden="true" />
          <input aria-label="Search commands" autoComplete="off" className="command-search" id="command-search" onChange={(event) => setCommandSearch(event.target.value)} onKeyDown={(event) => { if (event.key === 'Escape') { event.preventDefault(); setCommandOpen(false) } }} placeholder="Search commands..." ref={commandSearchRef} type="search" value={commandSearch} />
          <kbd>ESC</kbd>
        </div>
        <div className="command-group-title">Workspace commands</div>
        <ul className="command-list">
          {visibleCommands.map((command) => (
            <li key={command.id}>
              <button className="command-item" onClick={() => commandActions[command.id]()} type="button">
                <span>{command.label}</span><kbd>{command.shortcut}</kbd>
              </button>
            </li>
          ))}
        </ul>
        {visibleCommands.length === 0 && <div className="command-empty">No matching commands.</div>}
      </dialog>
      <div aria-live="polite" className={`toast${toast ? ' is-visible' : ''}`} role="status">{toast}</div>
    </div>
  )
}

export default App

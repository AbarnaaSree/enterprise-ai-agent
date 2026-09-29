import { useState } from 'react'
import './App.css'

const API_URL = 'http://127.0.0.1:8000'

function App() {
  const [message, setMessage] = useState('')
  const [answer, setAnswer] = useState('')
  const [route, setRoute] = useState('')
  const [executionSteps, setExecutionSteps] = useState([])
  const [workflow, setWorkflow] = useState({})
  const [langfuse, setLangfuse] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const fetchLangfuseData = async (traceId) => {
    if (!traceId) {
      return
    }

    const maxAttempts = 10
    const delay = 3000

    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
      try {
        const response = await fetch(
          `${API_URL}/api/langfuse/trace/${traceId}`
        )

        if (!response.ok) {
          throw new Error(
            `Langfuse request failed with status ${response.status}`
          )
        }

        const data = await response.json()

        /*
         * Langfuse ingestion is asynchronous.
         * Retry until observations become available.
         */
        if (
          data.observations &&
          data.observations.length > 0
        ) {
          setLangfuse(data)
          return
        }

      } catch (err) {
        console.error(
          'Langfuse fetch error:',
          err
        )
      }

      if (attempt < maxAttempts) {
        await new Promise(
          (resolve) => setTimeout(resolve, delay)
        )
      }
    }

    /*
     * If observations are still unavailable,
     * keep the trace information that we already have.
     */
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

  const askAgent = async () => {
    if (!message.trim() || loading) {
      return
    }

    setLoading(true)
    setError('')
    setAnswer('')
    setRoute('')
    setExecutionSteps([])
    setWorkflow({})
    setLangfuse(null)

    try {
      const response = await fetch(
        `${API_URL}/api/chat`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            message: message.trim(),
          }),
        }
      )

      if (!response.ok) {
        throw new Error(
          `Request failed with status ${response.status}`
        )
      }

      const data = await response.json()

      setAnswer(data.answer)
      setRoute(data.route)
      setExecutionSteps(
        data.execution_steps || []
      )
      setWorkflow(data.workflow || {})

      /*
       * Get the real Langfuse trace ID
       * returned by the backend.
       */
      const traceId =
        data.workflow?.langfuse?.trace_id

      if (traceId) {
        fetchLangfuseData(traceId)
      }

    } catch (err) {
      console.error(err)

      setError(
        'Could not connect to the agent. Make sure the FastAPI backend is running.'
      )
    } finally {
      setLoading(false)
    }
  }

  const formatStepName = (step) => {
    const names = {
      router: 'LangGraph Router',
      combined: 'Combined Route',
      retrieve: 'RAG Retrieval',
      database: 'MCP / Database',
      generate: 'LLM Generation',
      validate: 'Response Validator',
      direct: 'Direct Response',
    }

    return names[step] || step
  }

  const getStatus = (section) => {
    return workflow[section]?.status || 'waiting'
  }

  return (
    <main className="app">
      <header className="header">
        <div>
          <p className="eyebrow">
            ENTERPRISE AI
          </p>

          <h1>
            Knowledge & Data Agent
          </h1>

          <p className="subtitle">
            Ask questions across company knowledge,
            employee data, and connected tools.
          </p>
        </div>

        <div className="status">
          <span className="status-dot"></span>
          Agent Online
        </div>
      </header>

      <section className="workspace">
        <div className="chat-panel">
          <div className="panel-header">
            <div>
              <p className="panel-label">
                ASK THE AGENT
              </p>

              <h2>
                What would you like to know?
              </h2>
            </div>
          </div>

          <textarea
            value={message}
            onChange={(event) =>
              setMessage(event.target.value)
            }
            placeholder="e.g. Tell me Abarnaa's department and the annual leave policy."
            rows={5}
            disabled={loading}
          />

          <button
            type="button"
            className="ask-button"
            disabled={
              !message.trim() || loading
            }
            onClick={askAgent}
          >
            {loading
              ? 'Asking...'
              : 'Ask Agent'}
          </button>
        </div>

        <div className="answer-panel">
          <p className="panel-label">
            AGENT RESPONSE
          </p>

          {error ? (
            <div className="empty-state">
              <div className="empty-icon">
                !
              </div>

              <h2>
                Agent unavailable
              </h2>

              <p>{error}</p>
            </div>
          ) : answer ? (
            <div className="answer-content">
              <p>{answer}</p>
            </div>
          ) : (
            <div className="empty-state">
              <div className="empty-icon">
                AI
              </div>

              <h2>
                {loading
                  ? 'Processing your question...'
                  : 'Ready for your question'}
              </h2>

              <p>
                The agent will retrieve information
                from the appropriate enterprise
                sources and show how the request
                was processed.
              </p>
            </div>
          )}
        </div>
      </section>

      <section className="execution-panel">
        <div className="panel-header">
          <div>
            <p className="panel-label">
              OBSERVABILITY
            </p>

            <h2>
              Agent Workflow
            </h2>
          </div>

          <span className="route-badge">
            {route || 'Waiting'}
          </span>
        </div>

        {executionSteps.length > 0 ? (
          <>
            <div className="workflow">
              {executionSteps.map(
                (step, index) => (
                  <div
                    className="workflow-step"
                    key={`${step}-${index}`}
                  >
                    <div className="workflow-node">
                      <span className="workflow-index">
                        {index + 1}
                      </span>

                      <div>
                        <strong>
                          {formatStepName(step)}
                        </strong>

                        <span className="workflow-status">
                          completed
                        </span>
                      </div>
                    </div>

                    {index <
                      executionSteps.length - 1 && (
                      <div className="workflow-arrow">
                        ↓
                      </div>
                    )}
                  </div>
                )
              )}
            </div>

            <div className="execution-details">
              <div className="details-header">
                <div>
                  <p className="panel-label">
                    EXECUTION DETAILS
                  </p>

                  <h3>
                    Actual runtime information
                  </h3>
                </div>
              </div>

              {workflow.router && (
                <div className="detail-section">
                  <div className="detail-title">
                    <span>
                      LangGraph Router
                    </span>

                    <span className="detail-status">
                      {getStatus('router')}
                    </span>
                  </div>

                  <div className="detail-grid">
                    <div>
                      <span>Route</span>

                      <strong>
                        {workflow.router.route ||
                          '—'}
                      </strong>
                    </div>

                    <div>
                      <span>
                        Needs RAG
                      </span>

                      <strong>
                        {workflow.router
                          .needs_rag
                          ? 'Yes'
                          : 'No'}
                      </strong>
                    </div>

                    <div>
                      <span>
                        Needs Database
                      </span>

                      <strong>
                        {workflow.router
                          .needs_database
                          ? 'Yes'
                          : 'No'}
                      </strong>
                    </div>

                    <div>
                      <span>
                        Employee
                      </span>

                      <strong>
                        {workflow.router
                          .employee_name ||
                          '—'}
                      </strong>
                    </div>
                  </div>

                  {workflow.router
                    .rag_query && (
                    <div className="detail-query">
                      <span>
                        RAG Query
                      </span>

                      <p>
                        {
                          workflow.router
                            .rag_query
                        }
                      </p>
                    </div>
                  )}
                </div>
              )}

              {workflow.rag && (
                <div className="detail-section">
                  <div className="detail-title">
                    <span>
                      RAG Retrieval
                    </span>

                    <span className="detail-status">
                      {getStatus('rag')}
                    </span>
                  </div>

                  <div className="detail-grid">
                    <div>
                      <span>
                        Embedding Model
                      </span>

                      <strong>
                        {
                          workflow.rag
                            .embedding_model
                        }
                      </strong>
                    </div>

                    <div>
                      <span>
                        Vector Store
                      </span>

                      <strong>
                        {
                          workflow.rag
                            .vector_store
                        }
                      </strong>
                    </div>

                    <div>
                      <span>Top K</span>

                      <strong>
                        {workflow.rag.top_k}
                      </strong>
                    </div>

                    <div>
                      <span>
                        Distance Threshold
                      </span>

                      <strong>
                        {
                          workflow.rag
                            .distance_threshold
                        }
                      </strong>
                    </div>

                    <div>
                      <span>
                        Chunks Retrieved
                      </span>

                      <strong>
                        {
                          workflow.rag
                            .chunks_retrieved
                        }
                      </strong>
                    </div>

                    <div>
                      <span>
                        Chunks After Filter
                      </span>

                      <strong>
                        {
                          workflow.rag
                            .chunks_after_filter
                        }
                      </strong>
                    </div>
                  </div>

                  <div className="detail-query">
                    <span>Query</span>

                    <p>
                      {workflow.rag.query}
                    </p>
                  </div>
                </div>
              )}

              {workflow.mcp && (
                <div className="detail-section">
                  <div className="detail-title">
                    <span>
                      MCP Tool Execution
                    </span>

                    <span className="detail-status">
                      {getStatus('mcp')}
                    </span>
                  </div>

                  <div className="detail-grid">
                    <div>
                      <span>Tool</span>

                      <strong>
                        {workflow.mcp.tool}
                      </strong>
                    </div>

                    <div>
                      <span>
                        Employee
                      </span>

                      <strong>
                        {
                          workflow.mcp
                            .employee_name
                        }
                      </strong>
                    </div>

                    <div>
                      <span>
                        Employee Found
                      </span>

                      <strong>
                        {workflow.mcp.found
                          ? 'Yes'
                          : 'No'}
                      </strong>
                    </div>
                  </div>

                  <div className="detail-query">
                    <span>
                      Actual flow
                    </span>

                    <p>
                      MCP → EmployeeService →
                      SQLAlchemy → MySQL
                    </p>
                  </div>
                </div>
              )}

              {workflow.llm && (
                <div className="detail-section">
                  <div className="detail-title">
                    <span>
                      LLM Generation
                    </span>

                    <span className="detail-status">
                      {getStatus('llm')}
                    </span>
                  </div>

                  <div className="detail-grid">
                    <div>
                      <span>Provider</span>

                      <strong>
                        {
                          workflow.llm
                            .provider
                        }
                      </strong>
                    </div>

                    <div>
                      <span>Status</span>

                      <strong>
                        {
                          workflow.llm.status
                        }
                      </strong>
                    </div>
                  </div>
                </div>
              )}

              {workflow.validation && (
                <div className="detail-section">
                  <div className="detail-title">
                    <span>
                      Response Validation
                    </span>

                    <span className="detail-status">
                      {getStatus(
                        'validation'
                      )}
                    </span>
                  </div>

                  <div className="detail-grid">
                    <div>
                      <span>Valid</span>

                      <strong>
                        {
                          workflow.validation
                            .valid
                            ? 'Yes'
                            : 'No'
                        }
                      </strong>
                    </div>

                    <div>
                      <span>Errors</span>

                      <strong>
                        {
                          workflow.validation
                            .errors?.length ||
                          0
                        }
                      </strong>
                    </div>

                    <div>
                      <span>
                        Warnings
                      </span>

                      <strong>
                        {
                          workflow.validation
                            .warnings
                            ?.length || 0
                        }
                      </strong>
                    </div>
                  </div>
                </div>
              )}

              {langfuse && (
                <div className="detail-section langfuse-section">
                  <div className="detail-title">
                    <span>
                      Langfuse Observability
                    </span>

                    <span className="detail-status">
                      {langfuse.pending
                        ? 'Waiting'
                        : 'Completed'}
                    </span>
                  </div>

                  <div className="detail-grid">
                    <div>
                      <span>Status</span>

                      <strong>
                        {langfuse.pending
                          ? 'Waiting for trace data'
                          : 'Completed'}
                      </strong>
                    </div>

                    <div>
                      <span>
                        Trace Name
                      </span>

                      <strong>
                        {
                          langfuse.trace_name
                        }
                      </strong>
                    </div>

                    <div>
                      <span>
                        LLM Calls
                      </span>

                      <strong>
                        {
                          langfuse.llm_calls
                        }
                      </strong>
                    </div>

                    <div>
                      <span>
                        RAG Retrieval
                      </span>

                      <strong>
                        {
                          langfuse.rag_retrievals
                        }
                      </strong>
                    </div>

                    <div>
                      <span>
                        MCP Calls
                      </span>

                      <strong>
                        {
                          langfuse.mcp_calls
                        }
                      </strong>
                    </div>

                    <div>
                      <span>
                        Validation
                      </span>

                      <strong>
                        {
                          langfuse.validation_calls
                        }
                      </strong>
                    </div>

                    <div>
                      <span>
                        Duration
                      </span>

                      <strong>
                        {langfuse.duration_seconds !==
                        null
                          ? `${langfuse.duration_seconds.toFixed(
                              3
                            )} s`
                          : '—'}
                      </strong>
                    </div>
                  </div>

                  <div className="detail-query">
                    <span>
                      Trace ID
                    </span>

                    <p className="trace-id">
                      {langfuse.trace_id}
                    </p>
                  </div>

                  {workflow.langfuse
                    ?.trace_url && (
                    <div className="langfuse-link-wrapper">
                      <a
                        className="langfuse-link"
                        href={
                          workflow.langfuse
                            .trace_url
                        }
                        target="_blank"
                        rel="noreferrer"
                      >
                        View Langfuse Trace ↗
                      </a>
                    </div>
                  )}
                </div>
              )}
            </div>
          </>
        ) : (
          <div className="flow-placeholder">
            <span>
              Waiting for execution...
            </span>
          </div>
        )}
      </section>
    </main>
  )
}

export default App
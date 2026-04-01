import { useState, useEffect, useCallback } from "react";

const API = "http://127.0.0.1:8000";

const TEAM_STYLES = {
  Backend      : { color: "#00d4ff", bg: "rgba(0,212,255,0.08)", border: "rgba(0,212,255,0.25)" },
  "AOL (Mobile)": { color: "#bf5af2", bg: "rgba(191,90,242,0.08)", border: "rgba(191,90,242,0.25)" },
  DevOps       : { color: "#ffd60a", bg: "rgba(255,214,10,0.08)", border: "rgba(255,214,10,0.25)" },
  Platform     : { color: "#30d158", bg: "rgba(48,209,88,0.08)", border: "rgba(48,209,88,0.25)" },
  Portal       : { color: "#ff9f0a", bg: "rgba(255,159,10,0.08)", border: "rgba(255,159,10,0.25)" },
  Unknown      : { color: "#98989e", bg: "rgba(152,152,158,0.08)", border: "rgba(152,152,158,0.25)" },
};

const SEVERITY_COLORS = {
  Critical: "#ff453a", High: "#ff9f0a", Medium: "#ffd60a", Low: "#30d158", Unknown: "#98989e",
};

const NODES = [
  { id: "router",     label: "Router",     icon: "⬡", desc: "Jira ingestion & categorization" },
  { id: "searcher",   label: "Searcher",   icon: "◈", desc: "GitHub repo mapping" },
  { id: "researcher", label: "Researcher", icon: "◎", desc: "Code analysis" },
  { id: "coder",      label: "Coder",      icon: "◆", desc: "Fix generation" },
];

function PipelineNode({ node, status }) {
  const isDone   = status === "done";
  const isActive = status === "active";
  return (
    <div style={{
      display        : "flex",
      flexDirection  : "column",
      alignItems     : "center",
      gap            : 8,
      flex           : 1,
      position       : "relative",
    }}>
      <div style={{
        width        : 52,
        height       : 52,
        borderRadius : "50%",
        border       : `2px solid ${isDone ? "#30d158" : isActive ? "#00d4ff" : "rgba(255,255,255,0.1)"}`,
        background   : isDone ? "rgba(48,209,88,0.12)" : isActive ? "rgba(0,212,255,0.12)" : "rgba(255,255,255,0.03)",
        display      : "flex",
        alignItems   : "center",
        justifyContent: "center",
        fontSize     : 22,
        transition   : "all 0.4s ease",
        boxShadow    : isActive ? "0 0 20px rgba(0,212,255,0.4)" : isDone ? "0 0 12px rgba(48,209,88,0.3)" : "none",
        animation    : isActive ? "pulse 1.5s ease-in-out infinite" : "none",
      }}>
        {isDone ? "✓" : node.icon}
      </div>
      <div style={{ textAlign: "center" }}>
        <div style={{
          fontSize  : 12,
          fontWeight: 600,
          color     : isDone ? "#30d158" : isActive ? "#00d4ff" : "rgba(255,255,255,0.4)",
          fontFamily: "'JetBrains Mono', monospace",
          transition: "color 0.4s",
        }}>{node.label}</div>
        <div style={{ fontSize: 10, color: "rgba(255,255,255,0.25)", marginTop: 2 }}>{node.desc}</div>
      </div>
    </div>
  );
}

function TicketCard({ ticket, onAnalyze, isRunning, result }) {
  const team    = result?.team || "Unknown";
  const ts      = TEAM_STYLES[team] || TEAM_STYLES.Unknown;
  const hasResult = !!result;

  return (
    <div style={{
      background   : "rgba(255,255,255,0.03)",
      border       : `1px solid ${hasResult ? ts.border : "rgba(255,255,255,0.08)"}`,
      borderRadius : 12,
      padding      : "16px 20px",
      cursor       : "pointer",
      transition   : "all 0.25s ease",
      position     : "relative",
      overflow     : "hidden",
    }}
    onMouseEnter={e => e.currentTarget.style.background = "rgba(255,255,255,0.05)"}
    onMouseLeave={e => e.currentTarget.style.background = "rgba(255,255,255,0.03)"}
    >
      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 12 }}>
        <div style={{ flex: 1 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
            <span style={{
              fontSize    : 11,
              fontFamily  : "'JetBrains Mono', monospace",
              color       : "#00d4ff",
              background  : "rgba(0,212,255,0.1)",
              padding     : "2px 8px",
              borderRadius: 4,
              border      : "1px solid rgba(0,212,255,0.2)",
            }}>{ticket.ticket_id}</span>
            <span style={{
              fontSize    : 10,
              padding     : "2px 8px",
              borderRadius: 4,
              background  : ticket.priority === "High" ? "rgba(255,159,10,0.12)" : "rgba(255,255,255,0.05)",
              color       : ticket.priority === "High" ? "#ff9f0a" : "rgba(255,255,255,0.4)",
              border      : `1px solid ${ticket.priority === "High" ? "rgba(255,159,10,0.3)" : "rgba(255,255,255,0.1)"}`,
            }}>{ticket.priority}</span>
            {hasResult && (
              <span style={{
                fontSize    : 10,
                padding     : "2px 8px",
                borderRadius: 4,
                background  : ts.bg,
                color       : ts.color,
                border      : `1px solid ${ts.border}`,
              }}>{team}</span>
            )}
          </div>
          <div style={{ fontSize: 13, fontWeight: 500, color: "rgba(255,255,255,0.85)", lineHeight: 1.4, marginBottom: 6 }}>
            {ticket.title}
          </div>
          <div style={{ fontSize: 11, color: "rgba(255,255,255,0.3)" }}>
            Reporter: {ticket.reporter} · {ticket.status}
          </div>
          {hasResult && result.root_cause && (
            <div style={{
              marginTop   : 10,
              padding     : "8px 12px",
              background  : "rgba(255,69,58,0.08)",
              border      : "1px solid rgba(255,69,58,0.2)",
              borderRadius: 6,
              fontSize    : 11,
              color       : "rgba(255,255,255,0.6)",
              lineHeight  : 1.6,
            }}>
              <span style={{ color: "#ff453a", fontWeight: 600 }}>Root Cause: </span>
              {result.root_cause.slice(0, 120)}...
            </div>
          )}
        </div>
        <button
          onClick={() => onAnalyze(ticket.ticket_id)}
          disabled={isRunning}
          style={{
            padding      : "8px 16px",
            borderRadius : 8,
            border       : "1px solid rgba(0,212,255,0.3)",
            background   : isRunning ? "rgba(255,255,255,0.03)" : "rgba(0,212,255,0.1)",
            color        : isRunning ? "rgba(255,255,255,0.3)" : "#00d4ff",
            fontSize     : 12,
            fontFamily   : "'JetBrains Mono', monospace",
            cursor       : isRunning ? "not-allowed" : "pointer",
            whiteSpace   : "nowrap",
            transition   : "all 0.2s",
            flexShrink   : 0,
          }}>
          {isRunning ? "Running..." : hasResult ? "Re-analyze" : "Analyze →"}
        </button>
      </div>
    </div>
  );
}

function ResultPanel({ result }) {
  const [tab, setTab] = useState("rootcause");
  if (!result) return null;

  const team = result.team || "Unknown";
  const ts   = TEAM_STYLES[team] || TEAM_STYLES.Unknown;
  const sevColor = SEVERITY_COLORS[result.severity] || "#98989e";

  return (
    <div style={{
      background   : "rgba(255,255,255,0.02)",
      border       : "1px solid rgba(255,255,255,0.08)",
      borderRadius : 16,
      overflow     : "visible",
      animation    : "slideUp 0.4s ease-out",
    }}>
      {/* Header */}
      <div style={{
        padding       : "20px 24px",
        borderBottom  : "1px solid rgba(255,255,255,0.06)",
        background    : "rgba(255,255,255,0.02)",
        display       : "flex",
        alignItems    : "center",
        justifyContent: "space-between",
        flexWrap      : "wrap",
        gap           : 12,
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <div style={{
            width       : 40, height: 40,
            borderRadius: 10,
            background  : ts.bg,
            border      : `1px solid ${ts.border}`,
            display     : "flex", alignItems: "center", justifyContent: "center",
            fontSize    : 18,
          }}>🔍</div>
          <div>
            <div style={{ fontSize: 15, fontWeight: 700, color: "rgba(255,255,255,0.9)" }}>
              {result.ticket_id} — Analysis Complete
            </div>
            <div style={{ fontSize: 11, color: "rgba(255,255,255,0.3)", marginTop: 2 }}>
              {result.microservice} · {result.repo_name}
            </div>
          </div>
        </div>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          {[
            { label: team, color: ts.color, bg: ts.bg, border: ts.border },
            { label: result.severity, color: sevColor, bg: `${sevColor}15`, border: `${sevColor}40` },
            { label: result.bug_type, color: "rgba(255,255,255,0.5)", bg: "rgba(255,255,255,0.05)", border: "rgba(255,255,255,0.1)" },
          ].map((badge, i) => badge.label && (
            <span key={i} style={{
              padding     : "4px 10px",
              borderRadius: 20,
              fontSize    : 11,
              background  : badge.bg,
              color       : badge.color,
              border      : `1px solid ${badge.border}`,
            }}>{badge.label}</span>
          ))}
        </div>
      </div>

      {/* Tabs */}
      <div style={{ display: "flex", borderBottom: "1px solid rgba(255,255,255,0.06)" }}>
        {[["rootcause", "⚠ Root Cause"], ["fix", "⚡ Fix"], ["files", "📁 Files"], ["steps", "🧪 Testing"]].map(([key, label]) => (
          <button key={key} onClick={() => setTab(key)} style={{
            flex        : 1, padding: "12px 0",
            background  : tab === key ? "rgba(0,212,255,0.06)" : "transparent",
            border      : "none",
            borderBottom: tab === key ? "2px solid #00d4ff" : "2px solid transparent",
            color       : tab === key ? "#00d4ff" : "rgba(255,255,255,0.3)",
            fontSize    : 11, fontFamily: "'JetBrains Mono', monospace",
            cursor      : "pointer", transition: "all 0.2s",
          }}>{label}</button>
        ))}
      </div>

      {/* Content */}
      <div style={{ padding: 24, overflowY: "auto", maxHeight: "55vh" }}>
        {tab === "rootcause" && (
          <div>
            <div style={{
              background: "rgba(255,69,58,0.06)", border: "1px solid rgba(255,69,58,0.2)",
              borderRadius: 8, padding: "12px 16px", marginBottom: 16,
              fontSize: 13, color: "rgba(255,255,255,0.7)", lineHeight: 1.8,
            }}>
              <div style={{ color: "#ff453a", fontWeight: 700, marginBottom: 6, fontSize: 11 }}>ROOT CAUSE</div>
              {result.root_cause}
            </div>
            <div style={{
              background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.07)",
              borderRadius: 8, padding: "12px 16px",
              fontSize: 12, color: "rgba(255,255,255,0.5)", lineHeight: 1.8,
            }}>
              <div style={{ color: "rgba(255,255,255,0.4)", fontWeight: 700, marginBottom: 6, fontSize: 11 }}>SUMMARY</div>
              {result.analysis_summary}
            </div>
          </div>
        )}

        {tab === "fix" && (
          <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
            <div style={{
              background: "rgba(48,209,88,0.06)", border: "1px solid rgba(48,209,88,0.2)",
              borderRadius: 8, padding: "10px 14px",
              fontSize: 12, color: "#30d158",
            }}>
              ✓ {result.fix_summary}
            </div>
            {(result.fixes || []).map((fix, i) => (
              <div key={i} style={{
                border: "1px solid rgba(255,255,255,0.08)", borderRadius: 10, overflow: "hidden",
              }}>
                <div style={{
                  padding: "10px 16px", background: "rgba(255,255,255,0.04)",
                  borderBottom: "1px solid rgba(255,255,255,0.06)",
                  display: "flex", alignItems: "center", gap: 10,
                }}>
                  <span style={{ color: "#00d4ff", fontSize: 11, fontFamily: "'JetBrains Mono', monospace" }}>
                    FIX #{i + 1}
                  </span>
                  <span style={{ color: "rgba(255,255,255,0.5)", fontSize: 11, fontFamily: "'JetBrains Mono', monospace" }}>
                    {fix.file_path}
                  </span>
                </div>
                <div style={{ padding: "10px 16px", borderBottom: "1px solid rgba(255,255,255,0.06)" }}>
                  <div style={{ fontSize: 12, color: "rgba(255,255,255,0.5)", lineHeight: 1.6 }}>{fix.explanation}</div>
                </div>
                <pre style={{
                  margin: 0, padding: "16px",
                  background: "#0d1117", overflowX: "auto", overflowY: "auto", maxHeight: "300px", display: "block",
                  fontSize: 12, lineHeight: 1.7,
                  color: "#e6edf3", fontFamily: "'JetBrains Mono', monospace",
                }}>{fix.fixed_code}</pre>
              </div>
            ))}
          </div>
        )}

        {tab === "files" && (
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {(result.files_scanned || result.affected_files || []).map((f, i) => (
              <div key={i} style={{
                display: "flex", alignItems: "center", gap: 10,
                background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.07)",
                borderRadius: 6, padding: "8px 14px",
                fontSize: 12, color: "rgba(255,255,255,0.6)",
                fontFamily: "'JetBrains Mono', monospace",
              }}>
                <span style={{ color: "#00d4ff" }}>📄</span> {f}
              </div>
            ))}
          </div>
        )}

        {tab === "steps" && (
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {(result.testing_steps || []).map((step, i) => (
              <div key={i} style={{
                display: "flex", gap: 12, alignItems: "flex-start",
                background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.07)",
                borderRadius: 8, padding: "10px 14px",
              }}>
                <span style={{
                  width: 22, height: 22, borderRadius: "50%", flexShrink: 0,
                  background: "rgba(0,212,255,0.15)", border: "1px solid rgba(0,212,255,0.3)",
                  color: "#00d4ff", fontSize: 11, display: "flex", alignItems: "center", justifyContent: "center",
                  fontFamily: "'JetBrains Mono', monospace", fontWeight: 700,
                }}>{i + 1}</span>
                <span style={{ fontSize: 12, color: "rgba(255,255,255,0.6)", lineHeight: 1.6 }}>{step}</span>
              </div>
            ))}
            {result.prevention && (
              <div style={{
                marginTop: 8, padding: "12px 14px",
                background: "rgba(255,214,10,0.06)", border: "1px solid rgba(255,214,10,0.2)",
                borderRadius: 8, fontSize: 12, color: "rgba(255,255,255,0.6)", lineHeight: 1.6,
              }}>
                <div style={{ color: "#ffd60a", fontWeight: 700, marginBottom: 4, fontSize: 11 }}>PREVENTION</div>
                {result.prevention}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default function DevBuddy() {
  const [tickets, setTickets]         = useState([]);
  const [results, setResults]         = useState({});
  const [activeTicket, setActiveTicket] = useState(null);
  const [runningTicket, setRunningTicket] = useState(null);
  const [nodeStatus, setNodeStatus]   = useState({});
  const [loading, setLoading]         = useState(false);
  const [manualId, setManualId]       = useState("");
  const [apiOnline, setApiOnline]     = useState(false);

  // Check API health
  useEffect(() => {
    fetch(`${API}/health`)
      .then(r => r.ok ? setApiOnline(true) : setApiOnline(false))
      .catch(() => setApiOnline(false));
  }, []);

  // Fetch tickets
  const fetchTickets = useCallback(async () => {
    setLoading(true);
    try {
      const r = await fetch(`${API}/tickets`);
      const d = await r.json();
      setTickets(d.tickets || []);
    } catch {
      setTickets([]);
    }
    setLoading(false);
  }, []);

  useEffect(() => { fetchTickets(); }, [fetchTickets]);

  // Poll pipeline status
  const pollStatus = useCallback(async (ticketId) => {
    const interval = setInterval(async () => {
      try {
        const r = await fetch(`${API}/status/${ticketId}`);
        const s = await r.json();

        const nodesDone = s.nodes_done || [];
        const current   = s.current_node;

        const ns = {};
        NODES.forEach(n => {
          if (nodesDone.includes(n.id)) ns[n.id] = "done";
          else if (n.id === current)    ns[n.id] = "active";
          else                          ns[n.id] = "idle";
        });
        setNodeStatus(ns);

        if (s.status === "completed" || s.status === "error") {
          clearInterval(interval);
          setRunningTicket(null);

          // Fetch result
          const rr = await fetch(`${API}/result/${ticketId}`);
          const rd = await rr.json();
          if (!rd.error) {
            setResults(prev => ({ ...prev, [ticketId]: rd }));
            setActiveTicket(ticketId);
          }
          setNodeStatus({});
        }
      } catch { clearInterval(interval); setRunningTicket(null); }
    }, 1500);
  }, []);

  const analyzeTicket = useCallback(async (ticketId) => {
    setRunningTicket(ticketId);
    setActiveTicket(ticketId);
    setNodeStatus({ router: "active" });

    try {
      await fetch(`${API}/analyze`, {
        method : "POST",
        headers: { "Content-Type": "application/json" },
        body   : JSON.stringify({ ticket_id: ticketId }),
      });
      pollStatus(ticketId);
    } catch {
      setRunningTicket(null);
      setNodeStatus({});
    }
  }, [pollStatus]);

  const handleManualSubmit = () => {
    if (manualId.trim()) {
      analyzeTicket(manualId.trim().toUpperCase());
      setManualId("");
    }
  };

  const activeResult = activeTicket ? results[activeTicket] : null;

  return (
    <div style={{
      minHeight  : "100vh",
      background : "#0a0a0f",
      backgroundImage: "radial-gradient(ellipse 80% 60% at 50% -20%, rgba(0,212,255,0.07), transparent), radial-gradient(ellipse 50% 40% at 90% 90%, rgba(191,90,242,0.05), transparent)",
      fontFamily : "'SF Pro Display', -apple-system, sans-serif",
      color      : "#fff",
    }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;600;700&display=swap');
        * { box-sizing: border-box; margin: 0; padding: 0; }
        ::-webkit-scrollbar { width: 4px; height: 4px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 4px; }
        @keyframes pulse { 0%,100% { box-shadow: 0 0 20px rgba(0,212,255,0.4); } 50% { box-shadow: 0 0 35px rgba(0,212,255,0.7); } }
        @keyframes slideUp { from { opacity: 0; transform: translateY(12px); } to { opacity: 1; transform: translateY(0); } }
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
        input { outline: none; }
        button { font-family: inherit; }
      `}</style>

      {/* Header */}
      <div style={{
        borderBottom: "1px solid rgba(255,255,255,0.06)",
        padding     : "0 32px",
        display     : "flex",
        alignItems  : "center",
        justifyContent: "space-between",
        height      : 60,
        background  : "rgba(255,255,255,0.02)",
        backdropFilter: "blur(12px)",
        position    : "sticky",
        top         : 0,
        zIndex      : 100,
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <div style={{
            width: 28, height: 28, borderRadius: 8,
            background: "linear-gradient(135deg, #00d4ff, #0099cc)",
            display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: 14,
          }}>⬡</div>
          <span style={{ fontSize: 16, fontWeight: 700, letterSpacing: -0.5 }}>Dev Buddy</span>
          <span style={{
            fontSize: 10, color: "rgba(255,255,255,0.3)",
            fontFamily: "'JetBrains Mono', monospace",
            background: "rgba(255,255,255,0.05)",
            padding: "2px 8px", borderRadius: 4,
          }}>AI Engineering Assistant</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <div style={{
            width: 8, height: 8, borderRadius: "50%",
            background: apiOnline ? "#30d158" : "#ff453a",
            boxShadow : apiOnline ? "0 0 8px #30d158" : "0 0 8px #ff453a",
          }}/>
          <span style={{ fontSize: 11, color: "rgba(255,255,255,0.4)", fontFamily: "'JetBrains Mono', monospace" }}>
            {apiOnline ? "API Online" : "API Offline"}
          </span>
        </div>
      </div>

      <div style={{ display: "flex", height: "calc(100vh - 60px)" }}>

        {/* Sidebar */}
        <div style={{
          width     : 340,
          flexShrink: 0,
          borderRight: "1px solid rgba(255,255,255,0.06)",
          display   : "flex",
          flexDirection: "column",
          background: "rgba(255,255,255,0.01)",
        }}>
          {/* Manual input */}
          <div style={{ padding: "16px 16px 12px", borderBottom: "1px solid rgba(255,255,255,0.06)" }}>
            <div style={{ fontSize: 10, color: "rgba(255,255,255,0.3)", marginBottom: 8, fontFamily: "'JetBrains Mono', monospace", letterSpacing: 1 }}>
              ANALYZE TICKET
            </div>
            <div style={{ display: "flex", gap: 8 }}>
              <input
                value={manualId}
                onChange={e => setManualId(e.target.value)}
                onKeyDown={e => e.key === "Enter" && handleManualSubmit()}
                placeholder="KAN-1, KAN-2..."
                style={{
                  flex        : 1,
                  background  : "rgba(255,255,255,0.05)",
                  border      : "1px solid rgba(255,255,255,0.1)",
                  borderRadius: 8,
                  padding     : "8px 12px",
                  color       : "#fff",
                  fontSize    : 12,
                  fontFamily  : "'JetBrains Mono', monospace",
                }}
              />
              <button
                onClick={handleManualSubmit}
                disabled={!manualId.trim() || !!runningTicket}
                style={{
                  padding     : "8px 14px",
                  borderRadius: 8,
                  border      : "1px solid rgba(0,212,255,0.3)",
                  background  : "rgba(0,212,255,0.1)",
                  color       : "#00d4ff",
                  fontSize    : 12,
                  cursor      : "pointer",
                  fontFamily  : "'JetBrains Mono', monospace",
                }}>→</button>
            </div>
          </div>

          {/* Tickets list */}
          <div style={{ flex: 1, overflowY: "auto", padding: 12 }}>
            <div style={{
              display: "flex", alignItems: "center", justifyContent: "space-between",
              marginBottom: 10, padding: "0 4px",
            }}>
              <span style={{ fontSize: 10, color: "rgba(255,255,255,0.3)", fontFamily: "'JetBrains Mono', monospace", letterSpacing: 1 }}>
                OPEN TICKETS ({tickets.length})
              </span>
              <button onClick={fetchTickets} style={{
                background: "none", border: "none", color: "rgba(255,255,255,0.3)",
                cursor: "pointer", fontSize: 12,
              }}>↻</button>
            </div>

            {loading ? (
              <div style={{ textAlign: "center", padding: 32, color: "rgba(255,255,255,0.2)", fontSize: 12 }}>
                Loading tickets...
              </div>
            ) : tickets.length === 0 ? (
              <div style={{ textAlign: "center", padding: 32, color: "rgba(255,255,255,0.2)", fontSize: 12 }}>
                No open tickets found
              </div>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                {tickets.map(ticket => (
                  <div
                    key={ticket.ticket_id}
                    onClick={() => { setActiveTicket(ticket.ticket_id); }}
                    style={{
                      background  : activeTicket === ticket.ticket_id ? "rgba(0,212,255,0.06)" : "rgba(255,255,255,0.02)",
                      border      : `1px solid ${activeTicket === ticket.ticket_id ? "rgba(0,212,255,0.2)" : "rgba(255,255,255,0.06)"}`,
                      borderRadius: 8,
                      padding     : "10px 12px",
                      cursor      : "pointer",
                      transition  : "all 0.2s",
                    }}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 4 }}>
                      <span style={{
                        fontSize: 10, fontFamily: "'JetBrains Mono', monospace",
                        color: "#00d4ff",
                      }}>{ticket.ticket_id}</span>
                      <span style={{
                        fontSize: 9, padding: "1px 6px", borderRadius: 3,
                        background: ticket.priority === "High" ? "rgba(255,159,10,0.15)" : "rgba(255,255,255,0.05)",
                        color: ticket.priority === "High" ? "#ff9f0a" : "rgba(255,255,255,0.3)",
                      }}>{ticket.priority}</span>
                    </div>
                    <div style={{ fontSize: 11, color: "rgba(255,255,255,0.6)", lineHeight: 1.4 }}>
                      {ticket.title.slice(0, 55)}{ticket.title.length > 55 ? "..." : ""}
                    </div>
                    <div style={{ marginTop: 8, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      {results[ticket.ticket_id] ? (
                        <span style={{ fontSize: 9, color: "#30d158" }}>✓ Analyzed</span>
                      ) : (
                        <span style={{ fontSize: 9, color: "rgba(255,255,255,0.2)" }}>Not analyzed</span>
                      )}
                      <button
                        onClick={e => { e.stopPropagation(); analyzeTicket(ticket.ticket_id); }}
                        disabled={!!runningTicket}
                        style={{
                          fontSize    : 9,
                          padding     : "3px 8px",
                          borderRadius: 4,
                          border      : "1px solid rgba(0,212,255,0.2)",
                          background  : "rgba(0,212,255,0.08)",
                          color       : "#00d4ff",
                          cursor      : "pointer",
                          fontFamily  : "'JetBrains Mono', monospace",
                        }}>
                        {runningTicket === ticket.ticket_id ? "..." : "Run →"}
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Main Content */}
        <div style={{ flex: 1, overflowY: "auto", padding: 24, display: "flex", flexDirection: "column", gap: 20 }}>

          {/* Pipeline Nodes */}
          <div style={{
            background  : "rgba(255,255,255,0.02)",
            border      : "1px solid rgba(255,255,255,0.06)",
            borderRadius: 14,
            padding     : "20px 24px",
          }}>
            <div style={{ fontSize: 10, color: "rgba(255,255,255,0.3)", marginBottom: 16, fontFamily: "'JetBrains Mono', monospace", letterSpacing: 1 }}>
              LANGGRAPH PIPELINE {runningTicket ? `— Processing ${runningTicket}` : ""}
            </div>
            <div style={{ display: "flex", alignItems: "flex-start", gap: 0 }}>
              {NODES.map((node, i) => (
                <div key={node.id} style={{ display: "flex", alignItems: "center", flex: 1 }}>
                  <PipelineNode node={node} status={nodeStatus[node.id] || "idle"} />
                  {i < NODES.length - 1 && (
                    <div style={{
                      width    : 32, flexShrink: 0,
                      height   : 1,
                      background: nodeStatus[NODES[i + 1]?.id] === "done" || nodeStatus[NODES[i + 1]?.id] === "active"
                        ? "rgba(0,212,255,0.4)" : "rgba(255,255,255,0.08)",
                      transition: "background 0.4s",
                      marginBottom: 24,
                    }}/>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Result Panel */}
          {activeResult ? (
            <ResultPanel result={activeResult} />
          ) : (
            <div style={{
              flex        : 1,
              display     : "flex",
              flexDirection: "column",
              alignItems  : "center",
              justifyContent: "center",
              color       : "rgba(255,255,255,0.15)",
              gap         : 12,
              padding     : 40,
            }}>
              <div style={{ fontSize: 48 }}>⬡</div>
              <div style={{ fontSize: 14, fontWeight: 500 }}>Select a ticket and click Analyze</div>
              <div style={{ fontSize: 12, color: "rgba(255,255,255,0.1)" }}>
                Dev Buddy will trace the bug to root cause and suggest a fix
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
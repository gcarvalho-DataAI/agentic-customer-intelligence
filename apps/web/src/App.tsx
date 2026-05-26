import { useEffect, useMemo, useRef, useState } from "react";
import type { FormEvent, KeyboardEvent } from "react";
import {
  FilePenLine,
  LoaderCircle,
  MapPin,
  MessageCircle,
  MessageSquarePlus,
  PanelLeftClose,
  PanelLeftOpen,
  Store,
  RefreshCcw,
  SendHorizontal,
  Square,
  Trash2,
  UsersRound,
  UserRound,
  WalletCards,
  XCircle,
} from "lucide-react";
import "./App.css";
import persona0Photo from "./assets/persona-0-photo.png";
import persona1Photo from "./assets/persona-1-photo.png";
import persona2Photo from "./assets/persona-2-photo.png";

type ConversationSummary = {
  conversation_id: string;
  title: string;
  created_at: string | null;
  updated_at: string | null;
  message_count: number;
};

type ConversationMessage = {
  timestamp: string;
  role: "user" | "assistant";
  content: string;
  metadata?: Record<string, unknown>;
};

type ConversationDetail = {
  conversation_id: string;
  title: string;
  created_at: string | null;
  updated_at: string | null;
  messages: ConversationMessage[];
};

type Persona = {
  cluster_id: number;
  segment_name: string;
};

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8010/api";

const PERSONA_COLORS: Record<number, string> = {
  0: "persona-0",
  1: "persona-1",
  2: "persona-2",
};

const PERSONA_CARD_CONTENT: Record<
  number,
  {
    image: string;
    title: string;
    subtitle: string;
    chips: Array<{ icon: "user" | "store" | "wallet"; label: string }>;
  }
> = {
  0: {
    image: persona0Photo,
    title: "Consumidores Maduros do Norte com Pagamento Digital",
    subtitle: "Compras semanais em loja física • Preferência por bebidas",
    chips: [
      { icon: "user", label: "55+" },
      { icon: "store", label: "Loja física" },
      { icon: "wallet", label: "Carteira digital" },
    ],
  },
  1: {
    image: persona1Photo,
    title: "Jovens Adultos Recorrentes do Sudeste",
    subtitle: "Compras semanais em loja física • Preferência por bebidas",
    chips: [
      { icon: "user", label: "25-34" },
      { icon: "store", label: "Loja física" },
      { icon: "wallet", label: "Crédito" },
    ],
  },
  2: {
    image: persona2Photo,
    title: "Consumidores Mainstream Recorrentes do Sudeste",
    subtitle: "Compras semanais em loja física • Preferência por bebidas",
    chips: [
      { icon: "user", label: "Mainstream" },
      { icon: "store", label: "Loja física" },
      { icon: "wallet", label: "Crédito" },
    ],
  },
};

type StreamingPersonaAnswer = {
  cluster_id: number;
  segment_name: string;
  answer: string;
};

const TITLE_STOP_WORDS = new Set([
  "a",
  "ao",
  "aos",
  "as",
  "com",
  "como",
  "da",
  "das",
  "de",
  "do",
  "dos",
  "e",
  "em",
  "forma",
  "melhor",
  "o",
  "os",
  "ou",
  "para",
  "por",
  "qual",
  "que",
  "sua",
  "um",
  "uma",
  "voce",
  "você",
]);

function PersonaChipIcon({ type }: { type: "user" | "store" | "wallet" }) {
  if (type === "store") return <Store size={14} />;
  if (type === "wallet") return <WalletCards size={14} />;
  return <UserRound size={14} />;
}

function summarizeConversationTitle(prompt: string) {
  const words = prompt
    .normalize("NFKC")
    .toLowerCase()
    .replace(/[^\p{L}\p{N}\s-]/gu, " ")
    .split(/\s+/)
    .map((word) => word.trim())
    .filter((word) => word.length > 2 && !TITLE_STOP_WORDS.has(word))
    .slice(0, 4);
  const selected = words.length > 0 ? words : prompt.trim().split(/\s+/).slice(0, 4);
  const title = selected.join(" ").trim();
  return title ? title.charAt(0).toUpperCase() + title.slice(1) : "Nova conversa";
}

function App() {
  const [personas, setPersonas] = useState<Persona[]>([]);
  const [selectedPersonaIds, setSelectedPersonaIds] = useState<number[]>([0, 1, 2]);
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const [activeConversation, setActiveConversation] = useState<ConversationDetail | null>(null);
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [streamingAnswers, setStreamingAnswers] = useState<StreamingPersonaAnswer[]>([]);
  const [editingResend, setEditingResend] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const streamAbortRef = useRef<AbortController | null>(null);

  const hasMessages = (activeConversation?.messages.length ?? 0) > 0;
  const showHome = !activeConversationId;
  const showEmptyChat = Boolean(activeConversationId) && !hasMessages && !loading;
  const selectedPersonaCards = selectedPersonaIds
    .map((id) => personas.find((persona) => persona.cluster_id === id))
    .filter((persona): persona is Persona => Boolean(persona));

  const lastUserQuestion = useMemo(() => {
    if (!activeConversation) return null;
    for (let i = activeConversation.messages.length - 1; i >= 0; i -= 1) {
      const msg = activeConversation.messages[i];
      if (msg.role === "user") return msg.content;
    }
    return null;
  }, [activeConversation]);

  const groupedAssistantMessages = useMemo(() => {
    if (!activeConversation) return [];
    const rows: Array<{ user?: ConversationMessage; assistants: ConversationMessage[] }> = [];
    let idx = 0;
    while (idx < activeConversation.messages.length) {
      const current = activeConversation.messages[idx];
      if (current.role === "user") {
        const assistants: ConversationMessage[] = [];
        idx += 1;
        while (idx < activeConversation.messages.length && activeConversation.messages[idx].role === "assistant") {
          assistants.push(activeConversation.messages[idx]);
          idx += 1;
        }
        rows.push({ user: current, assistants });
        continue;
      }
      rows.push({ assistants: [current] });
      idx += 1;
    }
    return rows;
  }, [activeConversation]);

  async function request<T>(path: string, options?: RequestInit): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      headers: { "Content-Type": "application/json" },
      ...options,
    });
    if (!response.ok) {
      const text = await response.text();
      throw new Error(text || `Request failed (${response.status})`);
    }
    return (await response.json()) as T;
  }

  async function loadPersonas() {
    const data = await request<Persona[]>("/personas");
    setPersonas(data);
    if (data.length > 0 && selectedPersonaIds.length === 0) {
      setSelectedPersonaIds(data.map((p) => p.cluster_id));
    }
  }

  async function loadConversations() {
    const data = await request<ConversationSummary[]>("/conversations");
    setConversations(data);
    if (!activeConversationId && data.length > 0) {
      setActiveConversationId(data[0].conversation_id);
    }
  }

  async function loadConversation(id: string) {
    const data = await request<ConversationDetail>(`/conversations/${id}`);
    setActiveConversation(data);
  }

  async function createConversation() {
    setError(null);
    const conv = await request<ConversationSummary>("/conversations", {
      method: "POST",
      body: JSON.stringify({ title: "Nova conversa" }),
    });
    setActiveConversationId(conv.conversation_id);
    await loadConversations();
    await loadConversation(conv.conversation_id);
  }

  async function updateConversationTitle(conversationId: string, title: string) {
    await request(`/conversations/${conversationId}`, {
      method: "PATCH",
      body: JSON.stringify({ title }),
    });
  }

  async function startConversationWithPersonas(personaIds: number[], title: string) {
    setError(null);
    setSelectedPersonaIds(personaIds);
    setQuestion("");
    const conv = await request<ConversationSummary>("/conversations", {
      method: "POST",
      body: JSON.stringify({ title }),
    });
    setActiveConversationId(conv.conversation_id);
    await loadConversations();
    await loadConversation(conv.conversation_id);
    window.setTimeout(() => textareaRef.current?.focus(), 0);
  }

  async function sendQuestion(questionOverride?: string) {
    const prompt = (questionOverride ?? question).trim();
    if (!prompt || selectedPersonaIds.length === 0 || loading) return;
    setLoading(true);
    setError(null);
    try {
      let conversationId = activeConversationId;
      const firstPromptInConversation = !activeConversation || activeConversation.messages.length === 0;
      const conversationTitle = summarizeConversationTitle(prompt);
      if (!conversationId) {
        const conv = await request<ConversationSummary>("/conversations", {
          method: "POST",
          body: JSON.stringify({ title: conversationTitle }),
        });
        conversationId = conv.conversation_id;
        setActiveConversationId(conversationId);
      } else if (firstPromptInConversation) {
        await updateConversationTitle(conversationId, conversationTitle);
      }

      setStreamingAnswers([]);

      const controller = new AbortController();
      streamAbortRef.current = controller;
      const response = await fetch(`${API_BASE_URL}/chat/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        signal: controller.signal,
        body: JSON.stringify({
          question: prompt,
          persona_ids: selectedPersonaIds,
          include_context: true,
          conversation_id: conversationId,
        }),
      });

      if (!response.ok || !response.body) {
        throw new Error(`Falha no stream (${response.status})`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let buffer = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const events = buffer.split("\n\n");
        buffer = events.pop() ?? "";

        for (const rawEvent of events) {
          const lines = rawEvent.split("\n");
          const eventNameLine = lines.find((line) => line.startsWith("event: "));
          const dataLine = lines.find((line) => line.startsWith("data: "));
          if (!eventNameLine || !dataLine) continue;
          const eventName = eventNameLine.slice("event: ".length).trim();
          const payload = JSON.parse(dataLine.slice("data: ".length));

          if (eventName === "persona_start") {
            setStreamingAnswers((prev) => [
              ...prev,
              {
                cluster_id: payload.cluster_id,
                segment_name: payload.segment_name,
                answer: "",
              },
            ]);
          }

          if (eventName === "delta") {
            setStreamingAnswers((prev) =>
              prev.map((item) =>
                item.cluster_id === payload.cluster_id
                  ? { ...item, answer: `${item.answer}${payload.text}` }
                  : item,
              ),
            );
          }

          if (eventName === "persona_end") {
            setStreamingAnswers((prev) =>
              prev.map((item) =>
                item.cluster_id === payload.cluster_id
                  ? { ...item, answer: payload.answer || item.answer }
                  : item,
              ),
            );
          }

          if (eventName === "error") {
            throw new Error(payload.message || "Erro durante stream.");
          }
        }
      }

      setQuestion("");
      await loadConversations();
      if (conversationId) await loadConversation(conversationId);
      setStreamingAnswers([]);
    } catch (err) {
      const aborted = err instanceof Error && err.name === "AbortError";
      if (!aborted) {
        setError(err instanceof Error ? err.message : "Falha ao enviar pergunta.");
      }
      if (activeConversationId) {
        await loadConversation(activeConversationId).catch(() => undefined);
      }
      await loadConversations().catch(() => undefined);
      setStreamingAnswers([]);
    } finally {
      streamAbortRef.current = null;
      setLoading(false);
    }
  }

  function stopGeneration() {
    streamAbortRef.current?.abort();
  }

  function editLastQuestion() {
    if (!lastUserQuestion || loading) return;
    setQuestion(lastUserQuestion);
    setEditingResend(true);
    textareaRef.current?.focus();
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    await sendQuestion();
  }

  function handleComposerKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      void sendQuestion();
    }
  }

  function autosizeTextarea() {
    const textarea = textareaRef.current;
    if (!textarea) return;
    textarea.style.height = "0px";
    const nextHeight = Math.min(textarea.scrollHeight, 160);
    textarea.style.height = `${nextHeight}px`;
  }

  async function clearMessages() {
    if (!activeConversationId) return;
    setError(null);
    await request(`/conversations/${activeConversationId}/messages`, { method: "DELETE" });
    await loadConversation(activeConversationId);
    await loadConversations();
  }

  async function deleteConversation() {
    if (!activeConversationId) return;
    setError(null);
    await request(`/conversations/${activeConversationId}`, { method: "DELETE" });
    setActiveConversationId(null);
    setActiveConversation(null);
    await loadConversations();
  }

  async function deleteAllConversations() {
    if (conversations.length === 0 || loading) return;
    const confirmed = window.confirm("Excluir todas as conversas anteriores?");
    if (!confirmed) return;
    setError(null);
    await Promise.all(
      conversations.map((conversation) =>
        request(`/conversations/${conversation.conversation_id}`, { method: "DELETE" }),
      ),
    );
    setActiveConversationId(null);
    setActiveConversation(null);
    await loadConversations();
  }

  function togglePersona(clusterId: number) {
    setSelectedPersonaIds((prev) => {
      if (prev.includes(clusterId)) return prev.filter((id) => id !== clusterId);
      return [...prev, clusterId].sort((a, b) => a - b);
    });
  }

  useEffect(() => {
    loadPersonas().catch((err) => setError(err instanceof Error ? err.message : "Falha ao carregar personas."));
    loadConversations().catch((err) =>
      setError(err instanceof Error ? err.message : "Falha ao carregar conversas."),
    );
  }, []);

  useEffect(() => {
    if (activeConversationId) {
      loadConversation(activeConversationId).catch((err) =>
        setError(err instanceof Error ? err.message : "Falha ao carregar conversa."),
      );
    }
  }, [activeConversationId]);

  useEffect(() => {
    autosizeTextarea();
  }, [question]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [groupedAssistantMessages, loading]);

  useEffect(() => {
    return () => {
      streamAbortRef.current?.abort();
    };
  }, []);

  return (
    <div className="layout">
      <aside className={`sidebar ${sidebarOpen ? "" : "collapsed"}`}>
        <div className="sidebar-top">
          <button className="icon-btn" onClick={() => setSidebarOpen((v) => !v)} aria-label="Alternar painel">
            {sidebarOpen ? <PanelLeftClose size={18} /> : <PanelLeftOpen size={18} />}
          </button>
          {sidebarOpen && <h1>Galaxies Nexus Chat</h1>}
        </div>

        {sidebarOpen && (
          <>
            <button className="new-chat-btn" onClick={createConversation}>
              <MessageSquarePlus size={16} />
              Nova conversa
            </button>

            <section className="persona-panel">
              <p>Personas ativas</p>
              <div className="persona-chips">
                {personas.map((persona) => {
                  const selected = selectedPersonaIds.includes(persona.cluster_id);
                  return (
                    <button
                      key={persona.cluster_id}
                      className={`persona-chip ${selected ? "selected" : ""} ${PERSONA_COLORS[persona.cluster_id] ?? ""}`}
                      onClick={() => togglePersona(persona.cluster_id)}
                    >
                      P{persona.cluster_id} · {persona.segment_name}
                    </button>
                  );
                })}
              </div>
            </section>

            <section className="conversation-list">
              <div className="section-heading-row">
                <p>Conversas</p>
                <button
                  className="clear-history-btn"
                  onClick={() => void deleteAllConversations()}
                  disabled={conversations.length === 0 || loading}
                >
                  <Trash2 size={13} />
                  Limpar tudo
                </button>
              </div>
              {conversations.map((conv) => (
                <button
                  key={conv.conversation_id}
                  className={`conversation-item ${conv.conversation_id === activeConversationId ? "active" : ""}`}
                  onClick={() => setActiveConversationId(conv.conversation_id)}
                >
                  <span>{conv.title}</span>
                  <small>{conv.message_count} msgs</small>
                </button>
              ))}
            </section>
          </>
        )}
      </aside>

      <main className="chat-pane">
        <header className="chat-header">
          <div>
            <h2>{activeConversation?.title ?? "Conversa com personas sintéticas"}</h2>
            <small>{selectedPersonaIds.length} persona(s) em execução</small>
          </div>
          <div className="header-actions">
            <button
              className="icon-btn"
              onClick={() => void sendQuestion(lastUserQuestion ?? undefined)}
              disabled={!lastUserQuestion || loading}
            >
              <RefreshCcw size={16} />
              Regenerate
            </button>
            <button className="icon-btn" onClick={editLastQuestion} disabled={!lastUserQuestion || loading}>
              <FilePenLine size={16} />
              Edit + Resend
            </button>
            <button className="icon-btn danger" onClick={clearMessages} disabled={!hasMessages}>
              <XCircle size={16} />
              Limpar
            </button>
            <button className="icon-btn danger" onClick={deleteConversation} disabled={!activeConversationId}>
              <Trash2 size={16} />
              Excluir
            </button>
          </div>
        </header>

        <section className="messages-area">
          {showHome && (
            <div className="empty-state">
              <div className="empty-copy">
                <h3>Escolha como quer conversar</h3>
                <p>Compare as três personas no chat coletivo ou entre em um segmento para explorar respostas individuais.</p>
                <button
                  className="collective-chat-btn"
                  onClick={() => void startConversationWithPersonas([0, 1, 2], "Chat coletivo com personas")}
                >
                  <UsersRound size={18} />
                  Chat coletivo com as 3 personas
                </button>
              </div>

              <div className="persona-home-grid">
                {personas.map((persona) => (
                  <button
                    key={persona.cluster_id}
                    className={`persona-home-card ${PERSONA_COLORS[persona.cluster_id] ?? ""}`}
                    onClick={() =>
                      void startConversationWithPersonas(
                        [persona.cluster_id],
                        `Chat com ${persona.segment_name}`,
                      )
                    }
                  >
                    <div className="persona-card-shell">
                      <img
                        className="persona-card-photo"
                        src={PERSONA_CARD_CONTENT[persona.cluster_id]?.image}
                        alt={persona.segment_name}
                      />
                      <div className="persona-card-body">
                        <div className="persona-title-row">
                          <span className="persona-map-badge">
                            <MapPin size={22} />
                          </span>
                          <h4>{PERSONA_CARD_CONTENT[persona.cluster_id]?.title ?? persona.segment_name}</h4>
                        </div>
                        <p>{PERSONA_CARD_CONTENT[persona.cluster_id]?.subtitle}</p>
                        <div className="persona-card-tags">
                          {PERSONA_CARD_CONTENT[persona.cluster_id]?.chips.map((chip) => (
                            <span key={chip.label}>
                              <PersonaChipIcon type={chip.icon} />
                              {chip.label}
                            </span>
                          ))}
                        </div>
                      </div>
                      <div className="persona-card-cta">
                        <MessageCircle size={17} />
                        Conversar com esta persona
                        <span aria-hidden="true">›</span>
                      </div>
                    </div>
                    <span className="persona-home-action">
                      <MessageCircle size={17} />
                      Conversar individualmente
                    </span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {showEmptyChat && (
            <div className="empty-chat-state">
              <div className="empty-chat-kicker">
                {selectedPersonaIds.length === 1 ? "Chat individual" : "Chat coletivo"}
              </div>
              <h3>{activeConversation?.title ?? "Nova conversa"}</h3>
              <p>
                {selectedPersonaIds.length === 1
                  ? "Esta conversa vai responder somente com a persona selecionada."
                  : "Esta conversa vai comparar as respostas das personas selecionadas."}
              </p>
              <div className="empty-chat-personas">
                {selectedPersonaCards.map((persona) => (
                  <span key={persona.cluster_id} className={PERSONA_COLORS[persona.cluster_id] ?? ""}>
                    {persona.segment_name}
                  </span>
                ))}
              </div>
            </div>
          )}

          {groupedAssistantMessages.map((group, index) => (
            <div key={`group-${index}`} className="chat-group">
              {group.user && <article className="message message-user">{group.user.content}</article>}
              {group.assistants.filter((msg) => msg.content.trim().length > 0).map((msg, aIdx) => {
                const clusterId = Number(msg.metadata?.cluster_id ?? -1);
                const segmentName = String(msg.metadata?.segment_name ?? "Persona");
                const toneClass = PERSONA_COLORS[clusterId] ?? "";
                return (
                  <article key={`assistant-${index}-${aIdx}`} className={`message message-assistant ${toneClass}`}>
                    <header>
                      {PERSONA_CARD_CONTENT[clusterId]?.image && (
                        <img
                          className="message-persona-avatar"
                          src={PERSONA_CARD_CONTENT[clusterId].image}
                          alt=""
                        />
                      )}
                      <strong>{segmentName}</strong>
                    </header>
                    <p>{msg.content}</p>
                  </article>
                );
              })}
            </div>
          ))}
          {loading && (
            <div className="chat-group">
              {streamingAnswers.length === 0 && (
                <article className="message message-assistant typing-card">
                  <header>
                    <strong>Personas selecionadas</strong>
                  </header>
                  <div className="typing-dots" aria-label="Gerando resposta">
                    <span />
                    <span />
                    <span />
                  </div>
                </article>
              )}
              {streamingAnswers.map((item) => {
                const toneClass = PERSONA_COLORS[item.cluster_id] ?? "";
                return (
                  <article key={`stream-${item.cluster_id}`} className={`message message-assistant ${toneClass}`}>
                    <header>
                      {PERSONA_CARD_CONTENT[item.cluster_id]?.image && (
                        <img
                          className="message-persona-avatar"
                          src={PERSONA_CARD_CONTENT[item.cluster_id].image}
                          alt=""
                        />
                      )}
                      <strong>{item.segment_name}</strong>
                    </header>
                    <p>{item.answer || "..."}</p>
                  </article>
                );
              })}
            </div>
          )}
          <div ref={messagesEndRef} />
        </section>

        <footer className="composer-wrap">
          <form className="composer" onSubmit={onSubmit}>
            <textarea
              ref={textareaRef}
              value={question}
              onChange={(event) => {
                setQuestion(event.target.value);
                if (editingResend) setEditingResend(false);
              }}
              onKeyDown={handleComposerKeyDown}
              rows={1}
              placeholder="Pergunte sobre preço, canal, promoção ou comportamento..."
            />
            <button type="submit" className="send-btn" disabled={loading || selectedPersonaIds.length === 0}>
              {loading ? <LoaderCircle className="spin" size={18} /> : <SendHorizontal size={18} />}
            </button>
            {editingResend && !loading && (
              <button type="button" className="edit-flag-btn" onClick={() => void sendQuestion(question)}>
                Reenviar edição
              </button>
            )}
            {loading && (
              <button type="button" className="stop-btn" onClick={stopGeneration}>
                <Square size={14} />
                Stop
              </button>
            )}
          </form>
          {error && <p className="error-text">{error}</p>}
        </footer>
      </main>
    </div>
  );
}

export default App;

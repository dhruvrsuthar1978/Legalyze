import { useEffect, useMemo, useRef, useState } from 'react';
import {
  MessageCircle,
  Send,
  ShieldAlert,
  Lightbulb,
  Scale,
  Trash2,
  Download,
  Copy,
  Plus,
  RefreshCw,
} from 'lucide-react';
import { useDispatch } from 'react-redux';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import { contractService } from '../services/contractService';
import { ragService } from '../services/ragService';
import { showToast } from '../store/uiSlice';

const SYSTEM_PROMPT = [
  'Act as a contract assistant.',
  'Answer in three sections:',
  '1) Risks',
  '2) Solutions',
  '3) Fair Contract Recommendation (balanced for both parties)',
  'Keep answers practical and concise.',
].join(' ');

const STORAGE_KEY = 'contract_assistant_chat_v1';

const QUICK_PROMPTS = [
  'Find top 5 risks in this contract and explain why.',
  'Suggest balanced replacement clauses for unfair terms.',
  'What termination terms are fair for both parties?',
  'Give a negotiation checklist before signing this contract.',
];

const makeId = () => `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;

const createInitialAssistantMessage = (text) => ({
  id: makeId(),
  role: 'assistant',
  text,
  at: new Date().toISOString(),
  contexts: [],
  scores: [],
});

const createNewChatSession = () => ({
  id: makeId(),
  title: 'New Chat',
  selectedContractId: '',
  createdAt: new Date().toISOString(),
  updatedAt: new Date().toISOString(),
  messages: [
    createInitialAssistantMessage(
      'Ask me about contract risks, solutions, and fair terms. You can optionally choose a contract for context.'
    ),
  ],
});

function ContractAssistantPage() {
  const dispatch = useDispatch();
  const chatEndRef = useRef(null);
  const [contracts, setContracts] = useState([]);
  const [chatSessions, setChatSessions] = useState([createNewChatSession()]);
  const [activeChatId, setActiveChatId] = useState('');
  const [question, setQuestion] = useState('');
  const [loadingContracts, setLoadingContracts] = useState(true);
  const [asking, setAsking] = useState(false);
  const [regeneratingMessageId, setRegeneratingMessageId] = useState('');

  const activeChat = useMemo(
    () => chatSessions.find((chat) => chat.id === activeChatId) || chatSessions[0],
    [activeChatId, chatSessions]
  );
  const messages = useMemo(() => activeChat?.messages || [], [activeChat]);

  useEffect(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return;
      const parsed = JSON.parse(raw);

      // Backward compatibility with older single-chat storage shape.
      if (Array.isArray(parsed.messages) && parsed.messages.length > 0) {
        const migrated = createNewChatSession();
        migrated.messages = parsed.messages.map((m) => ({
          id: m.id || makeId(),
          role: m.role,
          text: m.text,
          at: m.at || new Date().toISOString(),
          contexts: m.contexts || [],
          scores: m.scores || [],
        }));
        migrated.selectedContractId = parsed.selectedContractId || '';
        migrated.title = 'Migrated Chat';
        setChatSessions([migrated]);
        setActiveChatId(migrated.id);
        return;
      }

      if (Array.isArray(parsed.chatSessions) && parsed.chatSessions.length > 0) {
        const hydrated = parsed.chatSessions.map((chat) => ({
          ...chat,
          id: chat.id || makeId(),
          title: chat.title || 'Chat',
          selectedContractId: chat.selectedContractId || '',
          createdAt: chat.createdAt || new Date().toISOString(),
          updatedAt: chat.updatedAt || new Date().toISOString(),
          messages: (chat.messages || []).map((m) => ({
            id: m.id || makeId(),
            role: m.role,
            text: m.text,
            at: m.at || new Date().toISOString(),
            contexts: m.contexts || [],
            scores: m.scores || [],
          })),
        }));
        setChatSessions(hydrated);
        setActiveChatId(parsed.activeChatId || hydrated[0].id);
      }
    } catch {
      // Ignore local storage parse issues.
    }
  }, []);

  useEffect(() => {
    if (!activeChatId && chatSessions.length > 0) {
      setActiveChatId(chatSessions[0].id);
      return;
    }

    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        activeChatId,
        chatSessions,
      })
    );
  }, [activeChatId, chatSessions]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, asking, regeneratingMessageId]);

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const response = await contractService.getContracts(0, 100);
        if (!mounted) return;
        setContracts(response.contracts || []);
      } catch (err) {
        if (!mounted) return;
        dispatch(
          showToast({
            type: 'error',
            title: 'Failed to load contracts',
            message: err.response?.data?.detail || err.message || 'Could not fetch contracts.',
          })
        );
      } finally {
        if (mounted) setLoadingContracts(false);
      }
    })();
    return () => {
      mounted = false;
    };
  }, [dispatch]);

  const contractOptions = useMemo(
    () =>
      contracts.map((contract) => ({
        value: contract.id,
        label: contract.title || contract.filename || contract.id,
      })),
    [contracts]
  );

  const updateActiveChat = (updater) => {
    if (!activeChat) return;
    setChatSessions((prev) =>
      prev.map((chat) =>
        chat.id === activeChat.id
          ? { ...chat, ...updater(chat), updatedAt: new Date().toISOString() }
          : chat
      )
    );
  };

  const executeAssistantQuery = async (userText, chatId, replaceAssistantMessageId = '') => {
    const chat = chatSessions.find((c) => c.id === chatId);
    if (!chat) return;

    const prompt = `${SYSTEM_PROMPT} User question: ${userText}`;
    const response = chat.selectedContractId
      ? await ragService.askContract(chat.selectedContractId, prompt)
      : await ragService.query(prompt);

    const assistantMessage = {
      id: replaceAssistantMessageId || makeId(),
      role: 'assistant',
      text: response.answer || 'No response.',
      at: new Date().toISOString(),
      contexts: response.contexts || [],
      scores: response.scores || [],
    };

    setChatSessions((prev) =>
      prev.map((session) => {
        if (session.id !== chatId) return session;

        const updatedMessages = replaceAssistantMessageId
          ? session.messages.map((m) => (m.id === replaceAssistantMessageId ? assistantMessage : m))
          : [...session.messages, assistantMessage];

        return {
          ...session,
          messages: updatedMessages,
          updatedAt: new Date().toISOString(),
        };
      })
    );
  };

  const askAssistant = async () => {
    const trimmed = question.trim();
    if (!trimmed || !activeChat) return;
    setAsking(true);
    setQuestion('');

    const userMessage = {
      id: makeId(),
      role: 'user',
      text: trimmed,
      at: new Date().toISOString(),
      contexts: [],
      scores: [],
    };

    updateActiveChat((chat) => ({
      title: chat.title === 'New Chat' ? trimmed.slice(0, 40) : chat.title,
      messages: [...chat.messages, userMessage],
    }));

    try {
      await executeAssistantQuery(trimmed, activeChat.id);
    } catch (err) {
      const message = err.response?.data?.detail || err.message || 'Assistant request failed.';
      dispatch(
        showToast({
          type: 'error',
          title: 'Assistant Error',
          message,
        })
      );
      updateActiveChat((chat) => ({
        messages: [
          ...chat.messages,
          createInitialAssistantMessage('I could not process that request. Please try again.'),
        ],
      }));
    } finally {
      setAsking(false);
    }
  };

  const regenerateAssistantMessage = async (assistantMessageId) => {
    if (!activeChat) return;

    const assistantIndex = activeChat.messages.findIndex((m) => m.id === assistantMessageId);
    if (assistantIndex < 0) return;

    let sourceQuestion = '';
    for (let i = assistantIndex - 1; i >= 0; i -= 1) {
      const candidate = activeChat.messages[i];
      if (candidate.role === 'user') {
        sourceQuestion = candidate.text;
        break;
      }
    }

    if (!sourceQuestion) {
      dispatch(showToast({ type: 'error', title: 'Cannot Regenerate', message: 'No previous user question found.' }));
      return;
    }

    setRegeneratingMessageId(assistantMessageId);
    try {
      await executeAssistantQuery(sourceQuestion, activeChat.id, assistantMessageId);
      dispatch(showToast({ type: 'success', title: 'Regenerated', message: 'Assistant response regenerated.' }));
    } catch (err) {
      dispatch(
        showToast({
          type: 'error',
          title: 'Regeneration Failed',
          message: err.response?.data?.detail || err.message || 'Could not regenerate response.',
        })
      );
    } finally {
      setRegeneratingMessageId('');
    }
  };

  const createNewChat = () => {
    const next = createNewChatSession();
    setChatSessions((prev) => [next, ...prev]);
    setActiveChatId(next.id);
    setQuestion('');
  };

  const deleteChat = (chatId) => {
    setChatSessions((prev) => {
      const remaining = prev.filter((chat) => chat.id !== chatId);
      if (remaining.length === 0) {
        const fallback = createNewChatSession();
        setActiveChatId(fallback.id);
        return [fallback];
      }
      if (activeChatId === chatId) {
        setActiveChatId(remaining[0].id);
      }
      return remaining;
    });
  };

  const clearConversation = () => {
    updateActiveChat((chat) => ({
      messages: [
        createInitialAssistantMessage(
          'Chat cleared. Ask a fresh question about risk, solution, and fair terms.'
        ),
      ],
      title: chat.title,
    }));
  };

  const exportConversation = () => {
    const lines = messages.map((msg) => {
      const label = msg.role === 'user' ? 'You' : 'Assistant';
      const ts = msg.at ? new Date(msg.at).toLocaleString() : '';
      return `[${label}] ${ts}\n${msg.text}\n`;
    });
    const content = lines.join('\n');
    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${(activeChat?.title || 'contract-assistant-chat').replace(/[^a-z0-9-_]/gi, '_')}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const copyMessage = async (text) => {
    try {
      await navigator.clipboard.writeText(text);
      dispatch(showToast({ type: 'success', title: 'Copied', message: 'Response copied to clipboard.' }));
    } catch {
      dispatch(showToast({ type: 'error', title: 'Copy failed', message: 'Could not copy text.' }));
    }
  };

  return (
    <div className="w-full space-y-6">
      <div>
        <h1 className="text-3xl font-bold" style={{ color: 'var(--color-text-primary)' }}>
          Contract Assistant
        </h1>
        <p className="mt-1" style={{ color: 'var(--color-text-tertiary)' }}>
          AI guidance for risks, fixes, and fair terms for both parties.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <div className="flex items-center gap-3">
            <ShieldAlert className="w-5 h-5" style={{ color: 'var(--color-error)' }} />
            <p className="font-semibold">Risk Detection</p>
          </div>
        </Card>
        <Card>
          <div className="flex items-center gap-3">
            <Lightbulb className="w-5 h-5" style={{ color: 'var(--color-warning)' }} />
            <p className="font-semibold">Suggested Solutions</p>
          </div>
        </Card>
        <Card>
          <div className="flex items-center gap-3">
            <Scale className="w-5 h-5" style={{ color: 'var(--color-primary-600)' }} />
            <p className="font-semibold">Fairness Recommendation</p>
          </div>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        <Card className="space-y-4 lg:col-span-1">
          <div className="flex items-center justify-between">
            <p className="font-semibold">Chats</p>
            <Button size="sm" variant="ghost" className="gap-1" onClick={createNewChat}>
              <Plus className="w-4 h-4" />
              New
            </Button>
          </div>
          <div className="space-y-2 max-h-[520px] overflow-auto pr-1">
            {chatSessions.map((chat) => (
              <button
                key={chat.id}
                type="button"
                onClick={() => setActiveChatId(chat.id)}
                className="w-full text-left p-3 rounded-lg border smooth-transition hover:bg-neutral-50"
                style={{
                  borderColor: chat.id === activeChat?.id ? 'var(--color-primary-400)' : 'var(--color-neutral-200)',
                  backgroundColor: chat.id === activeChat?.id ? 'var(--color-primary-50)' : 'var(--color-bg-primary)',
                }}
              >
                <div className="flex items-start justify-between gap-2">
                  <p className="text-sm font-semibold truncate">{chat.title}</p>
                  <button
                    type="button"
                    className="opacity-70 hover:opacity-100"
                    onClick={(e) => {
                      e.stopPropagation();
                      deleteChat(chat.id);
                    }}
                    aria-label="Delete chat"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
                <p className="text-xs mt-1" style={{ color: 'var(--color-text-tertiary)' }}>
                  {new Date(chat.updatedAt).toLocaleString()}
                </p>
              </button>
            ))}
          </div>
        </Card>

        <Card className="space-y-4 lg:col-span-4">
          <div>
            <label className="label-text mb-2 block">Optional: Choose Contract Context</label>
            <select
              value={activeChat?.selectedContractId || ''}
              onChange={(e) => {
                const value = e.target.value;
                updateActiveChat(() => ({ selectedContractId: value }));
              }}
              className="w-full px-4 py-3 rounded-xl border border-[var(--color-neutral-300)] bg-white"
              disabled={loadingContracts}
            >
              <option value="">General legal guidance (no specific contract)</option>
              {contractOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          <div className="flex flex-wrap gap-2">
            {QUICK_PROMPTS.map((preset) => (
              <button
                key={preset}
                type="button"
                onClick={() => setQuestion(preset)}
                className="px-3 py-1.5 text-xs rounded-full border smooth-transition hover:bg-neutral-100"
                style={{ borderColor: 'var(--color-neutral-300)', color: 'var(--color-text-secondary)' }}
              >
                {preset}
              </button>
            ))}
          </div>

          <div className="flex gap-2 justify-end">
            <Button variant="ghost" size="sm" onClick={exportConversation} className="gap-2">
              <Download className="w-4 h-4" />
              Export
            </Button>
            <Button variant="ghost" size="sm" onClick={clearConversation} className="gap-2">
              <Trash2 className="w-4 h-4" />
              Clear
            </Button>
          </div>

          <div
            className="rounded-xl p-4 h-96 overflow-y-auto"
            style={{ backgroundColor: 'var(--color-bg-tertiary)', border: 'var(--border-thin) solid var(--color-neutral-200)' }}
          >
            <div className="space-y-3">
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`p-3 rounded-lg max-w-[90%] ${
                    msg.role === 'user' ? 'ml-auto' : ''
                  }`}
                  style={{
                    backgroundColor:
                      msg.role === 'user' ? 'var(--color-primary-600)' : 'var(--color-bg-primary)',
                    color: msg.role === 'user' ? 'white' : 'var(--color-text-primary)',
                  }}
                >
                  <div className="flex items-center gap-2 mb-1">
                    <MessageCircle className="w-4 h-4" />
                    <span className="text-xs font-semibold uppercase">
                      {msg.role === 'user' ? 'You' : 'Assistant'}
                    </span>
                    {msg.at && (
                      <span className="text-[10px] opacity-70">
                        {new Date(msg.at).toLocaleTimeString()}
                      </span>
                    )}
                  </div>
                  <p className="text-sm whitespace-pre-line">{msg.text}</p>
                  {msg.role === 'assistant' && (
                    <div className="mt-2 flex flex-wrap items-center justify-end gap-2">
                      <button
                        type="button"
                        onClick={() => copyMessage(msg.text)}
                        className="text-xs inline-flex items-center gap-1 opacity-80 hover:opacity-100"
                      >
                        <Copy className="w-3 h-3" />
                        Copy
                      </button>
                      <button
                        type="button"
                        onClick={() => regenerateAssistantMessage(msg.id)}
                        className="text-xs inline-flex items-center gap-1 opacity-80 hover:opacity-100 disabled:opacity-50"
                        disabled={regeneratingMessageId === msg.id || asking}
                      >
                        <RefreshCw className="w-3 h-3" />
                        {regeneratingMessageId === msg.id ? 'Regenerating...' : 'Regenerate'}
                      </button>
                    </div>
                  )}
                  {msg.role === 'assistant' && Array.isArray(msg.contexts) && msg.contexts.length > 0 && (
                    <details className="mt-2 text-xs">
                      <summary className="cursor-pointer opacity-80">Sources ({msg.contexts.length})</summary>
                      <div className="mt-2 space-y-2">
                        {msg.contexts.slice(0, 5).map((ctx, i) => (
                          <div
                            key={`${msg.id}-ctx-${i}`}
                            className="p-2 rounded border"
                            style={{ borderColor: 'var(--color-neutral-200)', backgroundColor: 'var(--color-bg-secondary)' }}
                          >
                            <p className="text-[11px] mb-1" style={{ color: 'var(--color-text-tertiary)' }}>
                              Similarity: {typeof msg.scores?.[i] === 'number' ? msg.scores[i].toFixed(3) : 'N/A'}
                            </p>
                            <p className="whitespace-pre-line">{ctx}</p>
                          </div>
                        ))}
                      </div>
                    </details>
                  )}
                </div>
              ))}
              {asking && (
                <div
                  className="p-3 rounded-lg max-w-[90%]"
                  style={{ backgroundColor: 'var(--color-bg-primary)', color: 'var(--color-text-primary)' }}
                >
                  <div className="flex items-center gap-2 mb-1">
                    <MessageCircle className="w-4 h-4" />
                    <span className="text-xs font-semibold uppercase">Assistant</span>
                  </div>
                  <p className="text-sm">Thinking...</p>
                </div>
              )}
              <div ref={chatEndRef} />
            </div>
          </div>

          <div className="flex gap-3">
            <textarea
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Ask about risk, fix, and fair term recommendation..."
              rows={2}
              className="flex-1 px-4 py-3 rounded-xl border border-[var(--color-neutral-300)] bg-white resize-none"
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey && !asking) {
                  e.preventDefault();
                  askAssistant();
                }
              }}
            />
            <Button className="gap-2" onClick={askAssistant} loading={asking} disabled={!activeChat}>
              <Send className="w-4 h-4" style={{ color: 'white' }} />
              Ask
            </Button>
          </div>
        </Card>
      </div>
    </div>
  );
}

export default ContractAssistantPage;

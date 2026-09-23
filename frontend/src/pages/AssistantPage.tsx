import { useEffect, useRef, useState } from 'react';
import { useParams } from 'react-router-dom';
import { DatasetTabs } from '../components/DatasetTabs';
import { PageHeader } from '../components/PageHeader';
import { ErrorBanner, Loading, Notice } from '../components/States';
import { useAsync } from '../hooks/useAsync';
import { api, ApiError } from '../services/api';
import type { ChatMessage, Conversation } from '../types';

const SUGGESTIONS = [
  'What are the most important findings?',
  'Which columns have the most missing data?',
  'What variables appear strongly correlated?',
  'Explain this dataset in simple terms.',
  'What should I investigate next?',
];

export function AssistantPage() {
  const { datasetId } = useParams();
  const id = Number(datasetId);
  const { data, loading, error, reload } = useAsync<Conversation>(
    () => api.getConversation(id),
    [id],
  );

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [question, setQuestion] = useState('');
  const [sending, setSending] = useState(false);
  const [sendError, setSendError] = useState<ApiError | null>(null);
  const logEnd = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (data) setMessages(data.messages);
  }, [data]);

  useEffect(() => {
    logEnd.current?.scrollIntoView({ block: 'nearest' });
  }, [messages.length]);

  async function ask(text: string) {
    const trimmed = text.trim();
    if (trimmed.length < 3 || sending) return;
    setSending(true);
    setSendError(null);
    const optimistic: ChatMessage = {
      id: -Date.now(),
      role: 'user',
      content: trimmed,
      created_at: new Date().toISOString(),
    };
    setMessages((current) => [...current, optimistic]);
    setQuestion('');
    try {
      const response = await api.askQuestion(id, trimmed);
      setMessages((current) => [...current, response.answer]);
    } catch (err) {
      setSendError(
        err instanceof ApiError ? err : new ApiError(0, 'UNKNOWN', 'The request failed.'),
      );
    } finally {
      setSending(false);
    }
  }

  if (loading) return <Loading label="Loading conversation…" />;
  if (error) return <ErrorBanner error={error} onRetry={reload} />;
  if (!data) return null;

  return (
    <div className="stack">
      <PageHeader
        title="AI Assistant"
        subtitle="Answers come from this dataset's computed analysis, not from the raw rows."
      />
      <DatasetTabs datasetId={id} />

      {!data.ai_enabled ? (
        <Notice>
          AI analysis is currently unavailable — no Gemini API key is configured. Your dataset
          analysis and visualizations are still available.
        </Notice>
      ) : null}

      <section className="card chat">
        <div className="chat__log">
          {messages.length === 0 ? (
            <p className="muted">
              Ask about the analysis of this dataset. The assistant can only use the statistics
              InsightAI computed; it will say so when the analysis does not answer your question.
            </p>
          ) : null}
          {messages.map((message) => (
            <article key={message.id} className={`message message--${message.role}`}>
              <p className="message__role">{message.role === 'user' ? 'You' : 'Assistant'}</p>
              <p>{message.content}</p>
            </article>
          ))}
          {sending ? <Loading label="Thinking…" /> : null}
          <div ref={logEnd} />
        </div>

        {sendError ? <ErrorBanner error={sendError} /> : null}

        <div className="suggestions">
          {SUGGESTIONS.map((suggestion) => (
            <button
              key={suggestion}
              type="button"
              className="suggestion"
              disabled={!data.ai_enabled || sending}
              onClick={() => void ask(suggestion)}
            >
              {suggestion}
            </button>
          ))}
        </div>

        <form
          className="chat__form"
          onSubmit={(event) => {
            event.preventDefault();
            void ask(question);
          }}
        >
          <input
            className="input"
            placeholder={
              data.ai_enabled ? 'Ask about this dataset…' : 'The assistant is not configured'
            }
            value={question}
            disabled={!data.ai_enabled || sending}
            onChange={(event) => setQuestion(event.target.value)}
            aria-label="Question"
          />
          <button
            type="submit"
            className="button"
            disabled={!data.ai_enabled || sending || question.trim().length < 3}
          >
            Ask
          </button>
        </form>
      </section>
    </div>
  );
}

import { FormEvent, useMemo, useState } from 'react';
import { invoke } from '@tauri-apps/api/core';

interface QueryMatch {
  id?: string;
  file: string;
  snippet: string;
  score?: number;
  line?: number;
}

interface QueryResponse {
  query?: string;
  matches?: QueryMatch[];
  explanation?: string;
  explanations?: string[];
  confirmations?: string[];
}

const FASTAPI_ENDPOINT = 'http://127.0.0.1:8000/query';

export default function App() {
  const [query, setQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<QueryResponse | null>(null);
  const [openConfirmation, setOpenConfirmation] = useState<string | null>(null);

  const explanations = useMemo(() => {
    if (!result) return [];
    if (Array.isArray(result.explanations) && result.explanations.length > 0) {
      return result.explanations;
    }
    return result.explanation ? [result.explanation] : [];
  }, [result]);

  async function runQuery(event: FormEvent) {
    event.preventDefault();
    if (!query.trim()) return;

    setError(null);
    setOpenConfirmation(null);
    setIsLoading(true);

    try {
      const response = await fetch(FASTAPI_ENDPOINT, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: query.trim() })
      });

      if (!response.ok) {
        throw new Error(`Query failed (${response.status})`);
      }

      const payload = (await response.json()) as QueryResponse;
      setResult(payload);
    } catch (requestError) {
      setError(
        requestError instanceof Error ? requestError.message : 'Unexpected query error'
      );
    } finally {
      setIsLoading(false);
    }
  }

  async function openFile(filePath: string) {
    setOpenConfirmation(null);
    try {
      const message = await invoke<string>('open_file', { path: filePath });
      setOpenConfirmation(message);
    } catch (openError) {
      setError(openError instanceof Error ? openError.message : 'Could not open file');
    }
  }

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-4xl flex-col gap-4 px-6 py-8">
      <header>
        <h1 className="text-2xl font-semibold text-cyan-300">Workspace Assistant</h1>
        <p className="text-sm text-slate-400">
          Press <kbd className="rounded bg-slate-800 px-2 py-1">Ctrl + Space</kbd> to open/focus.
        </p>
      </header>

      <form onSubmit={runQuery} className="flex gap-2 rounded-lg bg-panel p-3 shadow-lg shadow-black/20">
        <input
          className="w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm outline-none ring-cyan-400 transition focus:ring"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Search code, docs, symbols..."
          autoFocus
        />
        <button
          type="submit"
          disabled={isLoading || !query.trim()}
          className="rounded-md bg-cyan-500 px-4 py-2 text-sm font-medium text-slate-950 disabled:cursor-not-allowed disabled:opacity-40"
        >
          {isLoading ? 'Searching…' : 'Search'}
        </button>
      </form>

      {error && (
        <section className="rounded-md border border-rose-500/40 bg-rose-950/40 px-4 py-3 text-sm text-rose-200">
          {error}
        </section>
      )}

      {isLoading && (
        <section className="rounded-md border border-cyan-500/30 bg-cyan-500/10 px-4 py-3 text-sm text-cyan-100">
          Running low-latency query…
        </section>
      )}

      {result && (
        <section className="grid gap-4 md:grid-cols-3">
          <article className="md:col-span-2 rounded-lg bg-panel p-4">
            <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-400">Matches</h2>
            <ul className="mt-3 space-y-2">
              {result.matches?.length ? (
                result.matches.map((match, index) => (
                  <li key={`${match.file}-${index}`} className="rounded-md border border-slate-800 bg-slate-900 p-3">
                    <div className="mb-2 flex items-center justify-between gap-3">
                      <code className="text-xs text-cyan-300">{match.file}</code>
                      <button
                        className="rounded bg-slate-700 px-2 py-1 text-xs text-slate-100 hover:bg-slate-600"
                        onClick={() => openFile(match.file)}
                        type="button"
                      >
                        Open file
                      </button>
                    </div>
                    <p className="text-sm text-slate-200">{match.snippet}</p>
                    <div className="mt-2 text-xs text-slate-500">
                      {match.line ? `Line ${match.line}` : 'Line unknown'}
                      {typeof match.score === 'number' ? ` • Score ${match.score.toFixed(2)}` : ''}
                    </div>
                  </li>
                ))
              ) : (
                <li className="rounded-md border border-slate-800 bg-slate-900 p-3 text-sm text-slate-400">
                  No matches returned.
                </li>
              )}
            </ul>
          </article>

          <aside className="space-y-4">
            <article className="rounded-lg bg-panel p-4">
              <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-400">Explanations</h2>
              <ul className="mt-3 list-disc space-y-2 pl-5 text-sm text-slate-200">
                {explanations.length ? (
                  explanations.map((item, index) => <li key={`${item}-${index}`}>{item}</li>)
                ) : (
                  <li className="list-none text-slate-400">No explanations returned.</li>
                )}
              </ul>
            </article>

            <article className="rounded-lg bg-panel p-4">
              <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-400">Action confirmations</h2>
              <ul className="mt-3 list-disc space-y-2 pl-5 text-sm text-slate-200">
                {openConfirmation && <li>{openConfirmation}</li>}
                {result.confirmations?.map((item, index) => (
                  <li key={`${item}-${index}`}>{item}</li>
                ))}
                {!openConfirmation && !result.confirmations?.length && (
                  <li className="list-none text-slate-400">No actions yet.</li>
                )}
              </ul>
            </article>
          </aside>
        </section>
      )}
    </main>
  );
}

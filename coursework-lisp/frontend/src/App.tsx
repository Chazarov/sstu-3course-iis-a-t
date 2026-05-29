import { FormEvent, useEffect, useState } from 'react'

const API = import.meta.env.VITE_API_URL ?? '/api'

type Question = {
  id: string
  field: string
  text: string
  is_multi: boolean
  available_answers: string[]
}

type Recommendation = {
  title: string
  score: number
  matched: string[]
  author?: string
  genre?: string
  epoch?: string
  image?: string
}

type Answers = Record<string, string | string[]>

export default function App() {
  const [questions, setQuestions] = useState<Question[]>([])
  const [answers, setAnswers] = useState<Answers>({})
  const [items, setItems] = useState<Recommendation[] | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    fetch(`${API}/questions`)
      .then((r) => r.json())
      .then((data) => setQuestions(data.questions ?? []))
      .catch(() => setError('Не удалось загрузить вопросы'))
      .finally(() => setLoading(false))
  }, [])

  const pick = (q: Question, value: string) => {
    setAnswers((prev) => {
      if (q.is_multi) {
        const cur = (prev[q.id] as string[] | undefined) ?? []
        const next = cur.includes(value) ? cur.filter((v) => v !== value) : [...cur, value]
        return { ...prev, [q.id]: next }
      }
      return { ...prev, [q.id]: value }
    })
  }

  const isSelected = (q: Question, value: string) =>
    q.is_multi
      ? ((answers[q.id] as string[] | undefined) ?? []).includes(value)
      : answers[q.id] === value

  const ready = questions.every((q) => {
    const a = answers[q.id]
    return q.is_multi ? Array.isArray(a) && a.length > 0 : typeof a === 'string' && a.length > 0
  })

  const submit = async (e: FormEvent) => {
    e.preventDefault()
    if (!ready) return
    setSubmitting(true)
    setError('')
    try {
      const res = await fetch(`${API}/recommend?top_k=5`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(answers),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail ?? 'Ошибка подбора')
      setItems(data.items ?? [])
    } catch (err) {
      setItems(null)
      setError(err instanceof Error ? err.message : 'Ошибка подбора')
    } finally {
      setSubmitting(false)
    }
  }

  const reset = () => {
    setAnswers({})
    setItems(null)
    setError('')
  }

  if (loading) return <p className="muted">Загрузка…</p>

  return (
    <div className="app">
      <header>
        <h1>Классическая литература</h1>
        <p className="muted">Ответьте на вопросы — система подберёт книги</p>
      </header>

      {!items ? (
        <form onSubmit={submit}>
          {questions.map((q) => (
            <fieldset key={q.id}>
              <legend>{q.text}</legend>
              <div className="chips">
                {q.available_answers.map((opt) => (
                  <button
                    key={opt}
                    type="button"
                    className={isSelected(q, opt) ? 'chip on' : 'chip'}
                    onClick={() => pick(q, opt)}
                  >
                    {opt}
                  </button>
                ))}
              </div>
            </fieldset>
          ))}

          {error && <p className="err">{error}</p>}

          <button type="submit" disabled={!ready || submitting}>
            {submitting ? 'Подбираем…' : 'Подобрать'}
          </button>
        </form>
      ) : (
        <section className="results">
          <div className="results-head">
            <h2>Рекомендации</h2>
            <button type="button" className="link" onClick={reset}>
              Заново
            </button>
          </div>

          {items.length === 0 ? (
            <p className="muted">Совпадений не найдено. Попробуйте другие ответы.</p>
          ) : (
            <ul>
              {items.map((book) => (
                <li key={book.title}>
                  <img
                    src={`/images/${book.image ?? '1.jpg'}`}
                    alt={book.title}
                    loading="lazy"
                  />
                  <div>
                    <h3>{book.title}</h3>
                    <p className="meta">
                      {[book.author, book.genre, book.epoch].filter(Boolean).join(' · ')}
                    </p>
                    <p className="score">Совпадений: {book.score}</p>
                    <p className="matched">{book.matched.join(', ')}</p>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </section>
      )}
    </div>
  )
}

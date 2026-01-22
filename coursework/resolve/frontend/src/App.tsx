import { useEffect, useState, useRef } from 'react'

interface QuestionMessage {
  type: 'question'
  question_id: string
  is_multiple_response_options: boolean
  field: string
  text: string
  avaliable_answers: string[]
}

interface RecommendationItem {
  title: string
  score: number
  matched: string[]
  author?: string
  genre?: string
  epoch?: string
  mood?: string
  difficulty?: string
  volume?: string
  image?: string
}

interface RecommendationsMessage {
  type: 'result'
  text: string
  items: RecommendationItem[]
}

interface ErrorMessage {
  type: 'error'
  text: string
}

interface InfoMessage {
  type: 'info'
  text: string
}

type Message = QuestionMessage | RecommendationsMessage | ErrorMessage | InfoMessage

interface DisplayMessage {
  id: string
  content: Message
}

export default function App() {
  const [messages, setMessages] = useState<DisplayMessage[]>([])
  const [ws, setWs] = useState<WebSocket | null>(null)
  const [connected, setConnected] = useState(false)
  const [selectedOptions, setSelectedOptions] = useState<Set<string>>(new Set())
  const [answeredQuestions, setAnsweredQuestions] = useState<Map<string, string[]>>(new Map())
  const [isFinished, setIsFinished] = useState(false)
  const messageIdCounter = useRef(0)
  const isConnecting = useRef(false)

  const connect = () => {
    if (isConnecting.current) return
    isConnecting.current = true

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = import.meta.env.VITE_WS_HOST || window.location.hostname
    const port = import.meta.env.VITE_WS_PORT || '8000'
    const websocket = new WebSocket(`${protocol}//${host}:${port}/ws`)

    websocket.onopen = () => {
      setConnected(true)
      setIsFinished(false)
    }

    websocket.onmessage = (event) => {
      try {
        const msg: Message = JSON.parse(event.data)
        console.log('Received message:', msg)
        
        if (msg.type === 'result') {
          setIsFinished(true)
        }
        
        if (msg.type === 'question') {
          setSelectedOptions(new Set())
        }
        
        setMessages(prev => [...prev, {
          id: `msg-${messageIdCounter.current++}`,
          content: msg
        }])
      } catch (error) {
        console.error('Error processing message:', error)
      }
    }

    websocket.onclose = () => {
      setConnected(false)
      setWs(null)
      isConnecting.current = false
    }

    setWs(websocket)
  }

  useEffect(() => {
    connect()
    return () => {
      ws?.close()
    }
  }, [])

  const sendAnswer = (textAnswer?: string, itemsAnswer?: string[]) => {
    if (!ws) return
    
    ws.send(JSON.stringify({
      type: 'client-answer',
      text_answer: textAnswer || null,
      items_answer: itemsAnswer || null
    }))
  }

  const handleSingleChoice = (answer: string, questionId: string) => {
    setSelectedOptions(new Set([answer]))
    setAnsweredQuestions(prev => new Map(prev).set(questionId, [answer]))
    sendAnswer(answer)
  }

  const toggleMultiChoice = (option: string) => {
    setSelectedOptions(prev => {
      const newSet = new Set(prev)
      if (newSet.has(option)) {
        newSet.delete(option)
      } else {
        newSet.add(option)
      }
      return newSet
    })
  }

  const submitMultiChoice = (questionId: string) => {
    const answers = Array.from(selectedOptions)
    setAnsweredQuestions(prev => new Map(prev).set(questionId, answers))
    sendAnswer(undefined, answers)
  }

  const handleRestart = () => {
    setMessages([])
    setIsFinished(false)
    setSelectedOptions(new Set())
    setAnsweredQuestions(new Map())
    sendAnswer('restart')
  }

  const handleBack = () => {
    sendAnswer('back')
  }

  const renderMessage = (msg: DisplayMessage) => {
    const { content } = msg

    if (content.type === 'question') {
      const isAnswered = answeredQuestions.has(content.question_id)
      const answeredOptions = answeredQuestions.get(content.question_id) || []
      const displayOptions = isAnswered ? new Set(answeredOptions) : selectedOptions

      return (
        <div key={msg.id} className="message question-block">
          <div className="question-text">{content.text}</div>
          <div className="options">
            {content.avaliable_answers.map((option) => (
              <button
                key={option}
                className={`option-btn ${displayOptions.has(option) ? 'selected' : ''}`}
                onClick={() => content.is_multiple_response_options 
                  ? toggleMultiChoice(option)
                  : handleSingleChoice(option, content.question_id)
                }
                disabled={isAnswered}
              >
                {option}
              </button>
            ))}
          </div>
          {content.is_multiple_response_options && (
            <button
              className="multi-submit"
              onClick={() => submitMultiChoice(content.question_id)}
              disabled={selectedOptions.size === 0 || isAnswered}
            >
              Подтвердить
            </button>
          )}
        </div>
      )
    }

    if (content.type === 'result') {
      return (
        <div key={msg.id} className="message recommendations">
          <div className="rec-header">{content.text}</div>
          <div className="rec-list">
            {content.items.map((item, idx) => (
              <div key={idx} className="rec-item">
                {item.image && (
                  <div className="rec-image-container">
                    <img 
                      src={`/images/${item.image}`} 
                      alt={item.title}
                      className="rec-image"
                    />
                  </div>
                )}
                <div className="rec-title">{item.title}</div>
                <div className="rec-score">Совпадений: {item.score}</div>
                <div className="rec-details">
                  {item.author && (
                    <div className="rec-detail">
                      <span className="rec-detail-label">Автор</span>
                      {item.author}
                    </div>
                  )}
                  {item.genre && (
                    <div className="rec-detail">
                      <span className="rec-detail-label">Жанр</span>
                      {item.genre}
                    </div>
                  )}
                  {item.epoch && (
                    <div className="rec-detail">
                      <span className="rec-detail-label">Эпоха</span>
                      {item.epoch}
                    </div>
                  )}
                  {item.mood && (
                    <div className="rec-detail">
                      <span className="rec-detail-label">Настроение</span>
                      {item.mood}
                    </div>
                  )}
                  {item.difficulty && (
                    <div className="rec-detail">
                      <span className="rec-detail-label">Сложность</span>
                      {item.difficulty}
                    </div>
                  )}
                  {item.volume && (
                    <div className="rec-detail">
                      <span className="rec-detail-label">Объём</span>
                      {item.volume}
                    </div>
                  )}
                </div>
                {item.matched.length > 0 && (
                  <div className="rec-matched">
                    <div className="rec-matched-title">Совпадения</div>
                    <div className="rec-matched-list">
                      {item.matched.map((m, i) => (
                        <span key={i} className="rec-matched-item">{m}</span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )
    }

    if (content.type === 'error') {
      return (
        <div key={msg.id} className="message error-message">
          {content.text}
        </div>
      )
    }

    if (content.type === 'info') {
      return (
        <div key={msg.id} className="message info-message">
          {content.text}
        </div>
      )
    }

    return null
  }

  console.log('Render state:', { connected, messagesCount: messages.length, isFinished })

  return (
    <div className="app">
      <div className="header">
        <p> используется технология Експертных систем </p>
        <h1>Подбор классической русской литературы для чтения</h1>
      </div>

      <div className="messages">
        {!connected && <div className="loading">Соединение...</div>}
        {connected && messages.length === 0 && <div className="loading">Ожидание...</div>}
        {messages.map(renderMessage)}
      </div>

      {connected && messages.length > 0 && (
        
        <div className="controls">
          {!isFinished && (
            <button className="control-btn" onClick={handleBack}>
              Назад
            </button>
          )}
          {isFinished && (
            <button className="control-btn primary" onClick={handleRestart}>
              Начать заново
            </button>
          )}
        </div>
      )}
    </div>
  )
}


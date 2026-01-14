import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../App'
import { api, PsychometricQuestion } from '../services/api'
import './Psychometric.css'

export default function Psychometric() {
  const navigate = useNavigate()
  const { user, token, updateUser } = useAuth()

  const [questions, setQuestions] = useState<PsychometricQuestion[]>([])
  const [currentIndex, setCurrentIndex] = useState(0)
  const [answers, setAnswers] = useState<Record<string, string>>({})
  const [isLoading, setIsLoading] = useState(true)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState('')

  // Redirect if already completed
  useEffect(() => {
    if (user?.psychometric_complete) {
      navigate('/calibration')
    }
  }, [user, navigate])

  // Load questions
  useEffect(() => {
    const loadQuestions = async () => {
      if (!token) return
      try {
        const data = await api.getQuestions(token)
        setQuestions(data.questions)
      } catch (err) {
        setError('Failed to load questions')
        console.error(err)
      } finally {
        setIsLoading(false)
      }
    }
    loadQuestions()
  }, [token])

  const currentQuestion = questions[currentIndex]
  const isLastQuestion = currentIndex === questions.length - 1
  const allAnswered = questions.length > 0 && Object.keys(answers).length === questions.length

  const handleSelect = (optionId: string) => {
    if (!currentQuestion) return
    setAnswers(prev => ({
      ...prev,
      [currentQuestion.id]: optionId
    }))
  }

  const handleNext = () => {
    if (currentIndex < questions.length - 1) {
      setCurrentIndex(prev => prev + 1)
    }
  }

  const handlePrevious = () => {
    if (currentIndex > 0) {
      setCurrentIndex(prev => prev - 1)
    }
  }

  const handleSubmit = async () => {
    if (!token || !allAnswered) return

    setIsSubmitting(true)
    setError('')

    try {
      const formattedAnswers = Object.entries(answers).map(([question_id, selected_option_id]) => ({
        question_id,
        selected_option_id
      }))

      await api.submitPsychometric(token, formattedAnswers)

      // Update user state
      if (user) {
        updateUser({ ...user, psychometric_complete: true })
      }

      navigate('/calibration')
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'response' in err) {
        const axiosError = err as { response?: { data?: { detail?: string } } }
        setError(axiosError.response?.data?.detail || 'Submission failed')
      } else {
        setError('Submission failed')
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  if (isLoading) {
    return (
      <div className="psychometric-page">
        <div className="loading">Loading questions...</div>
      </div>
    )
  }

  if (!currentQuestion) {
    return (
      <div className="psychometric-page">
        <div className="error">No questions available</div>
      </div>
    )
  }

  return (
    <div className="psychometric-page">
      <div className="psychometric-container">
        <header className="psychometric-header">
          <h1>The Fixed Five</h1>
          <p className="subtitle">Answer these scenarios honestly - there are no wrong answers</p>
          <div className="progress-bar">
            <div
              className="progress-fill"
              style={{ width: `${((currentIndex + 1) / questions.length) * 100}%` }}
            />
          </div>
          <span className="progress-text">
            Question {currentIndex + 1} of {questions.length}
          </span>
        </header>

        <div className="question-card">
          <span className="question-label">{currentQuestion.name}</span>
          <p className="scenario">{currentQuestion.scenario}</p>
          <h2 className="question-text">{currentQuestion.question}</h2>

          <div className="options">
            {currentQuestion.options.map((option) => (
              <button
                key={option.id}
                className={`option ${answers[currentQuestion.id] === option.id ? 'option--selected' : ''}`}
                onClick={() => handleSelect(option.id)}
              >
                <span className="option-indicator">
                  {answers[currentQuestion.id] === option.id ? '●' : '○'}
                </span>
                <span className="option-text">{option.text}</span>
              </button>
            ))}
          </div>
        </div>

        {error && <p className="error-text">{error}</p>}

        <div className="navigation">
          <button
            className="btn btn-secondary"
            onClick={handlePrevious}
            disabled={currentIndex === 0}
          >
            Previous
          </button>

          {isLastQuestion ? (
            <button
              className="btn btn-primary"
              onClick={handleSubmit}
              disabled={!allAnswered || isSubmitting}
            >
              {isSubmitting ? 'Submitting...' : 'Complete Assessment'}
            </button>
          ) : (
            <button
              className="btn btn-primary"
              onClick={handleNext}
              disabled={!answers[currentQuestion.id]}
            >
              Next
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

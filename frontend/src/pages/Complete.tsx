import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../App'
import { api, VisualVector } from '../services/api'
import './Complete.css'

export default function Complete() {
  const navigate = useNavigate()
  const { user, token, logout } = useAuth()

  const [vector, setVector] = useState<VisualVector | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  // Redirect if not completed
  useEffect(() => {
    if (user) {
      if (!user.psychometric_complete) {
        navigate('/psychometric')
      } else if (!user.calibration_complete) {
        navigate('/calibration')
      }
    }
  }, [user, navigate])

  // Load visual vector
  useEffect(() => {
    const loadVector = async () => {
      if (!token) return
      try {
        const data = await api.getVisualVector(token)
        setVector(data)
      } catch (err) {
        console.error('Failed to load vector:', err)
      } finally {
        setIsLoading(false)
      }
    }
    loadVector()
  }, [token])

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="complete-page">
      <div className="complete-container">
        <div className="success-animation">
          <div className="checkmark">
            <svg viewBox="0 0 52 52">
              <circle cx="26" cy="26" r="25" fill="none" />
              <path fill="none" d="M14.1 27.2l7.1 7.2 16.7-16.8" />
            </svg>
          </div>
        </div>

        <h1>Phase 1 Complete!</h1>
        <p className="subtitle">
          Your visual calibration has been successfully processed
        </p>

        {isLoading ? (
          <div className="loading">Loading your results...</div>
        ) : vector ? (
          <div className="results-card">
            <h2>Your Visual Profile</h2>

            <div className="stat-grid">
              <div className="stat">
                <span className="stat-value">{vector.meta.images_rated}</span>
                <span className="stat-label">Images Rated</span>
              </div>
              <div className="stat">
                <span className="stat-value">
                  {Math.round(vector.preference_model.calibration_confidence * 100)}%
                </span>
                <span className="stat-label">Confidence</span>
              </div>
              <div className="stat">
                <span className="stat-value">{vector.self_analysis.embedding_vector.length}</span>
                <span className="stat-label">Vector Dimensions</span>
              </div>
            </div>

            <div className="vector-preview">
              <h3>Embedding Vector Preview</h3>
              <code className="vector-code">
                [{vector.self_analysis.embedding_vector.slice(0, 5).map(v => v.toFixed(3)).join(', ')}...]
              </code>
            </div>

            <p className="info-text">
              Your personalized p1_visual_vector.json has been generated and saved.
              This vector represents your unique visual preferences based on your calibration ratings.
            </p>
          </div>
        ) : (
          <div className="results-card">
            <p>Unable to load your visual vector. Please try again later.</p>
          </div>
        )}

        <div className="actions">
          <button className="btn btn-secondary" onClick={handleLogout}>
            Sign Out
          </button>
        </div>

        <p className="next-phase">
          Phase 2 (Psychometric Deep Dive) and Phase 3 (Biological Analysis) coming soon...
        </p>
      </div>
    </div>
  )
}

import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../App'
import './Setup.css'

export default function Setup() {
  const navigate = useNavigate()
  const { user, token } = useAuth()
  const [status, setStatus] = useState('checking')
  const [progress, setProgress] = useState(0)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!user || !token) return

    // If already past setup, redirect
    if (user.psychometric_complete) {
      navigate('/calibration')
      return
    }

    const setupImages = async () => {
      setStatus('downloading')
      setProgress(10)

      try {
        // Check if images already exist
        const checkRes = await fetch('/api/setup/status')
        const checkData = await checkRes.json()

        if (checkData.ready) {
          setProgress(100)
          setStatus('ready')
          setTimeout(() => navigate('/psychometric'), 500)
          return
        }

        setProgress(30)

        // Download images
        const downloadRes = await fetch('/api/setup/download-images', {
          method: 'POST',
          headers: { Authorization: `Bearer ${token}` }
        })
        const downloadData = await downloadRes.json()

        setProgress(90)

        if (downloadData.status === 'ready' || downloadData.downloaded >= 10) {
          setProgress(100)
          setStatus('ready')
          setTimeout(() => navigate('/psychometric'), 500)
        } else {
          setError(`Only downloaded ${downloadData.downloaded}/10 images`)
          setStatus('error')
        }
      } catch (err) {
        console.error('Setup failed:', err)
        setError('Failed to download calibration images')
        setStatus('error')
      }
    }

    setupImages()
  }, [user, token, navigate])

  const handleRetry = () => {
    setError('')
    setStatus('checking')
    setProgress(0)
    window.location.reload()
  }

  return (
    <div className="setup-page">
      <div className="setup-container">
        <h1>Setting Up Your Experience</h1>

        {status === 'checking' && (
          <div className="setup-status">
            <div className="spinner"></div>
            <p>Checking setup status...</p>
          </div>
        )}

        {status === 'downloading' && (
          <div className="setup-status">
            <div className="spinner"></div>
            <p>Downloading calibration images...</p>
            <div className="progress-bar">
              <div className="progress-fill" style={{ width: `${progress}%` }}></div>
            </div>
            <span className="progress-text">{progress}%</span>
          </div>
        )}

        {status === 'ready' && (
          <div className="setup-status success">
            <div className="checkmark">&#10003;</div>
            <p>Setup complete! Redirecting...</p>
          </div>
        )}

        {status === 'error' && (
          <div className="setup-status error">
            <p className="error-text">{error}</p>
            <button className="btn btn-primary" onClick={handleRetry}>
              Retry Setup
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

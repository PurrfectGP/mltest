import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../App'
import { api, CalibrationImage } from '../services/api'
import StarRating from '../components/StarRating'
import './Calibration.css'

export default function Calibration() {
  const navigate = useNavigate()
  const { user, token, updateUser } = useAuth()

  const [images, setImages] = useState<CalibrationImage[]>([])
  const [currentIndex, setCurrentIndex] = useState(0)
  const [ratings, setRatings] = useState<Record<string, number>>({})
  const [isLoading, setIsLoading] = useState(true)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState('')

  // Redirect based on user state
  useEffect(() => {
    if (user) {
      if (!user.psychometric_complete) {
        navigate('/psychometric')
      } else if (user.calibration_complete) {
        navigate('/complete')
      }
    }
  }, [user, navigate])

  // Unsplash portrait photo IDs for fallback (matches backend)
  const unsplashPortraits = [
    "rDEOVtE7vOs", "mEZ3PoFGs_k", "sibVwORYqs0", "d2MSDujJl2g",
    "6W4F62sN_yI", "QXevDflbl8A", "IF9TK5Uy-KI", "WNoLnJo7tS8",
    "MTZTGvDsHFY", "7YVZYZeITc8", "ILip77SbmOE", "C8Ta0gwPbQg",
    "B4TjXnI0Y2c", "pAs4IM6OGWI", "d1UPkiFd04A", "2EGNqazbAMk",
    "y4Y-JK7hwmI", "ZHvM3XIOHoE", "WMD64tMfc4k", "X6Uj51n5CE8"
  ]

  const getUnsplashUrl = (index: number): string => {
    const photoId = unsplashPortraits[index % unsplashPortraits.length]
    return `https://images.unsplash.com/photo-${photoId}?w=400&h=500&fit=crop&crop=faces`
  }

  // Load calibration images
  useEffect(() => {
    const loadImages = async () => {
      if (!token) return
      try {
        const data = await api.getCalibrationImages(token, 20)
        if (data.images.length === 0) {
          // Generate Unsplash portrait images if none exist
          const placeholders: CalibrationImage[] = Array.from({ length: 20 }, (_, i) => ({
            id: `unsplash_${i + 1}`,
            filename: `unsplash_${i + 1}.jpg`,
            url: getUnsplashUrl(i)
          }))
          setImages(placeholders)
        } else {
          setImages(data.images)
        }
      } catch (err) {
        // Use Unsplash portraits on error
        const placeholders: CalibrationImage[] = Array.from({ length: 20 }, (_, i) => ({
          id: `unsplash_${i + 1}`,
          filename: `unsplash_${i + 1}.jpg`,
          url: getUnsplashUrl(i)
        }))
        setImages(placeholders)
        console.error(err)
      } finally {
        setIsLoading(false)
      }
    }
    loadImages()
  }, [token])

  const currentImage = images[currentIndex]
  const isLastImage = currentIndex === images.length - 1
  const allRated = images.length > 0 && Object.keys(ratings).length === images.length

  const handleRating = (rating: number) => {
    if (!currentImage) return
    setRatings(prev => ({
      ...prev,
      [currentImage.id]: rating
    }))
  }

  const handleNext = () => {
    if (currentIndex < images.length - 1) {
      setCurrentIndex(prev => prev + 1)
    }
  }

  const handlePrevious = () => {
    if (currentIndex > 0) {
      setCurrentIndex(prev => prev - 1)
    }
  }

  const handleSubmit = async () => {
    if (!token || !allRated) return

    setIsSubmitting(true)
    setError('')

    try {
      await api.submitCalibration(token, ratings)

      // Update user state
      if (user) {
        updateUser({ ...user, calibration_complete: true })
      }

      navigate('/complete')
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
      <div className="calibration-page">
        <div className="loading">Loading images...</div>
      </div>
    )
  }

  if (!currentImage) {
    return (
      <div className="calibration-page">
        <div className="error">No images available</div>
      </div>
    )
  }

  return (
    <div className="calibration-page">
      <div className="calibration-container">
        <header className="calibration-header">
          <h1>Visual Calibration</h1>
          <p className="subtitle">Rate each image based on your preferences (1-5 stars)</p>
          <div className="progress-bar">
            <div
              className="progress-fill"
              style={{ width: `${((currentIndex + 1) / images.length) * 100}%` }}
            />
          </div>
          <span className="progress-text">
            Image {currentIndex + 1} of {images.length}
          </span>
        </header>

        <div className="image-card">
          <div className="image-wrapper">
            <img
              src={currentImage.url}
              alt={`Calibration image ${currentIndex + 1}`}
              onError={(e) => {
                // Use Unsplash portrait on error
                e.currentTarget.src = getUnsplashUrl(currentIndex)
              }}
            />
          </div>

          <div className="rating-section">
            <p className="rating-prompt">How attractive do you find this image?</p>
            <StarRating
              value={ratings[currentImage.id] || 0}
              onChange={handleRating}
              size="large"
            />
            <div className="rating-labels">
              <span>Not at all</span>
              <span>Very attractive</span>
            </div>
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

          {isLastImage ? (
            <button
              className="btn btn-primary"
              onClick={handleSubmit}
              disabled={!allRated || isSubmitting}
            >
              {isSubmitting ? 'Processing...' : 'Complete Calibration'}
            </button>
          ) : (
            <button
              className="btn btn-primary"
              onClick={handleNext}
              disabled={!ratings[currentImage.id]}
            >
              Next
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

import { useState } from 'react'
import './StarRating.css'

interface StarRatingProps {
  value: number
  onChange: (rating: number) => void
  size?: 'small' | 'medium' | 'large'
  readonly?: boolean
}

export default function StarRating({
  value,
  onChange,
  size = 'medium',
  readonly = false
}: StarRatingProps) {
  const [hoverValue, setHoverValue] = useState(0)

  const handleClick = (rating: number) => {
    if (!readonly) {
      onChange(rating)
    }
  }

  const handleMouseEnter = (rating: number) => {
    if (!readonly) {
      setHoverValue(rating)
    }
  }

  const handleMouseLeave = () => {
    setHoverValue(0)
  }

  const displayValue = hoverValue || value

  return (
    <div className={`star-rating star-rating--${size} ${readonly ? 'star-rating--readonly' : ''}`}>
      {[1, 2, 3, 4, 5].map((star) => (
        <button
          key={star}
          type="button"
          className={`star ${star <= displayValue ? 'star--filled' : 'star--empty'}`}
          onClick={() => handleClick(star)}
          onMouseEnter={() => handleMouseEnter(star)}
          onMouseLeave={handleMouseLeave}
          disabled={readonly}
          aria-label={`Rate ${star} stars`}
        >
          <svg viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
          </svg>
        </button>
      ))}
    </div>
  )
}

import axios from 'axios'

const API_BASE = '/api'

export interface User {
  id: string
  email: string
  username: string
  gender?: string
  preference_target?: string
  created_at: string
  calibration_complete: boolean
  psychometric_complete: boolean
}

export interface AuthResponse {
  access_token: string
  token_type: string
  user: User
}

export interface QuestionOption {
  id: string
  text: string
  traits: Record<string, number>
}

export interface PsychometricQuestion {
  id: string
  name: string
  scenario: string
  question: string
  type: string
  options: QuestionOption[]
}

export interface CalibrationImage {
  id: string
  filename: string
  url: string
}

export interface VisualVector {
  meta: {
    user_id: string
    gender?: string
    preference_target?: string
    calibration_timestamp?: string
    images_rated: number
  }
  self_analysis: {
    embedding_vector: number[]
    detected_traits: {
      facial_landmarks: string[]
      style_presentation: string[]
      vibe_tags: string[]
    }
  }
  preference_model: {
    ideal_vector: number[]
    attraction_triggers: {
      mandatory_traits: string[]
      negative_traits: string[]
    }
    calibration_confidence: number
  }
}

const getAuthHeaders = (token: string) => ({
  headers: { Authorization: `Bearer ${token}` }
})

export const api = {
  // Auth
  async register(data: {
    email: string
    password: string
    username: string
    gender?: string
    preference_target?: string
  }): Promise<AuthResponse> {
    const res = await axios.post(`${API_BASE}/auth/register`, data)
    return res.data
  },

  async login(email: string, password: string): Promise<AuthResponse> {
    const res = await axios.post(`${API_BASE}/auth/login`, { email, password })
    return res.data
  },

  async getMe(token: string): Promise<User> {
    const res = await axios.get(`${API_BASE}/auth/me`, getAuthHeaders(token))
    return res.data
  },

  // Psychometric
  async getQuestions(token: string): Promise<{ questions: PsychometricQuestion[], total: number }> {
    const res = await axios.get(`${API_BASE}/psychometric/questions`, getAuthHeaders(token))
    return res.data
  },

  async submitPsychometric(
    token: string,
    answers: Array<{ question_id: string; selected_option_id: string }>
  ): Promise<{ success: boolean; message: string; traits_detected: Record<string, number> }> {
    const res = await axios.post(
      `${API_BASE}/psychometric/submit`,
      { answers },
      getAuthHeaders(token)
    )
    return res.data
  },

  // Calibration
  async getCalibrationImages(token: string, count = 20): Promise<{ images: CalibrationImage[], total: number }> {
    const res = await axios.get(
      `${API_BASE}/calibration/images?count=${count}`,
      getAuthHeaders(token)
    )
    return res.data
  },

  async submitCalibration(
    token: string,
    ratings: Record<string, number>
  ): Promise<VisualVector> {
    const res = await axios.post(
      `${API_BASE}/calibration/submit`,
      { ratings },
      getAuthHeaders(token)
    )
    return res.data
  },

  async getVisualVector(token: string): Promise<VisualVector> {
    const res = await axios.get(`${API_BASE}/calibration/vector`, getAuthHeaders(token))
    return res.data
  }
}

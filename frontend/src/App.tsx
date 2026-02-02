import { Routes, Route, Navigate } from 'react-router-dom'
import { useState, useEffect, createContext, useContext } from 'react'
import Signup from './pages/Signup'
import Login from './pages/Login'
import Setup from './pages/Setup'
import Psychometric from './pages/Psychometric'
import Calibration from './pages/Calibration'
import Complete from './pages/Complete'
import { api, User } from './services/api'

interface AuthContextType {
  user: User | null
  token: string | null
  login: (token: string, user: User) => void
  logout: () => void
  updateUser: (user: User) => void
  isLoading: boolean
}

const AuthContext = createContext<AuthContextType | null>(null)

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used within AuthProvider')
  return context
}

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, isLoading } = useAuth()

  if (isLoading) {
    return (
      <div className="loading-screen">
        <div className="spinner"></div>
        <p>Loading...</p>
      </div>
    )
  }

  if (!user) {
    return <Navigate to="/login" replace />
  }

  return <>{children}</>
}

function App() {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(localStorage.getItem('token'))
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const initAuth = async () => {
      const storedToken = localStorage.getItem('token')
      if (storedToken) {
        try {
          const userData = await api.getMe(storedToken)
          setUser(userData)
          setToken(storedToken)
        } catch {
          localStorage.removeItem('token')
          setToken(null)
        }
      }
      setIsLoading(false)
    }
    initAuth()
  }, [])

  const login = (newToken: string, newUser: User) => {
    localStorage.setItem('token', newToken)
    setToken(newToken)
    setUser(newUser)
  }

  const logout = () => {
    localStorage.removeItem('token')
    setToken(null)
    setUser(null)
  }

  const updateUser = (updatedUser: User) => {
    setUser(updatedUser)
  }

  return (
    <AuthContext.Provider value={{ user, token, login, logout, updateUser, isLoading }}>
      <div className="app">
        <Routes>
          <Route path="/signup" element={<Signup />} />
          <Route path="/login" element={<Login />} />
          <Route path="/setup" element={
            <ProtectedRoute>
              <Setup />
            </ProtectedRoute>
          } />
          <Route path="/psychometric" element={
            <ProtectedRoute>
              <Psychometric />
            </ProtectedRoute>
          } />
          <Route path="/calibration" element={
            <ProtectedRoute>
              <Calibration />
            </ProtectedRoute>
          } />
          <Route path="/complete" element={
            <ProtectedRoute>
              <Complete />
            </ProtectedRoute>
          } />
          <Route path="/" element={
            <Navigate to={user ? (
              !user.psychometric_complete ? "/setup" :
              !user.calibration_complete ? "/calibration" :
              "/complete"
            ) : "/signup"} replace />
          } />
        </Routes>
      </div>
    </AuthContext.Provider>
  )
}

export default App

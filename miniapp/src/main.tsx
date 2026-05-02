import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import PpgScan from './routes/PpgScan'
import FaceCapture from './routes/FaceCapture'

function App() {
  // Get token from URL
  const urlParams = new URLSearchParams(window.location.search)
  const token = urlParams.get('token')

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/ppg" element={<PpgScan token={token} />} />
        <Route path="/face" element={<FaceCapture token={token} />} />
        <Route path="*" element={<Navigate to="/ppg" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
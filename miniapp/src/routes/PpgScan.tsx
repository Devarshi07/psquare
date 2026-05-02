import { useState, useRef, useEffect, useCallback } from 'react'

interface PpgScanProps {
  token: string | null
}

type ScanState = 'idle' | 'preparing' | 'recording' | 'processing' | 'complete' | 'error'

interface PPGResult {
  hr_bpm: number
  rmssd_ms: number
  sdnn_ms: number
  pnn50_pct: number
  signal_quality: number
}

export default function PpgScan({ token }: PpgScanProps) {
  const [state, setState] = useState<ScanState>('idle')
  const [countdown, setCountdown] = useState(5)
  const [recordingTime, setRecordingTime] = useState(0)
  const [signalQuality, setSignalQuality] = useState(0)
  const [result, setResult] = useState<PPGResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  const videoRef = useRef<HTMLVideoElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const animationRef = useRef<number>(0)
  const signalDataRef = useRef<number[]>([])

  // Camera setup
  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: 'environment',
          width: { ideal: 640 },
          height: { ideal: 480 }
        },
        audio: false
      })
      streamRef.current = stream
      if (videoRef.current) {
        videoRef.current.srcObject = stream
      }
      setState('preparing')
    } catch (err) {
      setError('Camera access denied. Please allow camera permissions.')
      setState('error')
    }
  }

  // Start recording
  const startRecording = useCallback(() => {
    if (!videoRef.current) return

    setState('recording')
    setRecordingTime(0)
    signalDataRef.current = []

    // Capture frames
    const captureFrame = () => {
      if (!videoRef.current || !canvasRef.current) return

      const video = videoRef.current
      const canvas = canvasRef.current
      const ctx = canvas.getContext('2d')
      if (!ctx) return

      canvas.width = video.videoWidth
      canvas.height = video.videoHeight
      ctx.drawImage(video, 0, 0)

      // Extract green channel mean
      const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height)
      const data = imageData.data
      let greenSum = 0
      let count = 0

      for (let i = 1; i < data.length; i += 4) {
        greenSum += data[i]
        count++
      }

      const greenMean = greenSum / count
      signalDataRef.current.push(greenMean)

      // Calculate signal quality (simple variance)
      if (signalDataRef.current.length > 30) {
        const recent = signalDataRef.current.slice(-30)
        const mean = recent.reduce((a, b) => a + b, 0) / recent.length
        const variance = recent.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / recent.length
        const quality = Math.min(variance / 100, 1)
        setSignalQuality(quality)
      }

      // Continue recording
      if (recordingTime < 30) {
        setRecordingTime(t => t + 1)
        animationRef.current = requestAnimationFrame(captureFrame)
      } else {
        processRecording()
      }
    }

    animationRef.current = requestAnimationFrame(captureFrame)
  }, [recordingTime])

  // Process recording and compute metrics
  const processRecording = async () => {
    setState('processing')

    try {
      const signal = signalDataRef.current
      if (signal.length < 100) {
        throw new Error('Not enough signal data')
      }

      // Simple peak detection
      const peaks = detectPeaks(signal)
      const ibi = calculateIBI(peaks)

      // Calculate metrics
      const hr = calculateHR(ibi)
      const rmssd = calculateRMSSD(ibi)
      const sdnn = calculateSDNN(ibi)
      const pnn50 = calculatePNN50(ibi)
      const quality = calculateSignalQuality(signal)

      setResult({
        hr_bpm: hr,
        rmssd_ms: rmssd,
        sdnn_ms: sdnn,
        pnn50_pct: pnn50,
        signal_quality: quality
      })
      setState('complete')
    } catch (err) {
      setError('Could not process the signal. Please try again.')
      setState('error')
    }
  }

  // Peak detection (simplified)
  const detectPeaks = (signal: number[]): number[] => {
    const peaks: number[] = []
    const minDistance = 30 // ~50 BPM minimum

    for (let i = 10; i < signal.length - 10; i++) {
      const prev = signal.slice(i - 10, i)
      const next = signal.slice(i + 1, i + 11)

      if (signal[i] > Math.max(...prev) && signal[i] > Math.max(...next)) {
        if (peaks.length === 0 || i - peaks[peaks.length - 1] > minDistance) {
          peaks.push(i)
        }
      }
    }

    return peaks
  }

  // Calculate IBI from peaks
  const calculateIBI = (peaks: number[]): number[] => {
    return peaks.slice(1).map((peak, i) => {
      const interval = (peak - peaks[i]) * 1000 / 30 // Assuming 30fps
      return interval
    })
  }

  // Calculate HR from IBI
  const calculateHR = (ibi: number[]): number => {
    const meanIBI = ibi.reduce((a, b) => a + b, 0) / ibi.length
    return Math.round(60000 / meanIBI)
  }

  // Calculate RMSSD
  const calculateRMSSD = (ibi: number[]): number => {
    if (ibi.length < 2) return 0
    const successiveDiffs = ibi.slice(1).map((ibi, i) => Math.pow(ibi - ibi[i], 2))
    const sum = successiveDiffs.reduce((a, b) => a + b, 0)
    return Math.sqrt(sum / (ibi.length - 1))
  }

  // Calculate SDNN
  const calculateSDNN = (ibi: number[]): number => {
    const mean = ibi.reduce((a, b) => a + b, 0) / ibi.length
    const variance = ibi.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / ibi.length
    return Math.sqrt(variance)
  }

  // Calculate pNN50
  const calculatePNN50 = (ibi: number[]): number => {
    if (ibi.length < 2) return 0
    let count = 0
    for (let i = 1; i < ibi.length; i++) {
      if (Math.abs(ibi[i] - ibi[i - 1]) > 50) count++
    }
    return (count / (ibi.length - 1)) * 100
  }

  // Calculate signal quality
  const calculateSignalQuality = (signal: number[]): number => {
    if (signal.length < 100) return 0
    const recent = signal.slice(-100)
    const mean = recent.reduce((a, b) => a + b, 0) / recent.length
    const variance = recent.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / recent.length
    return Math.min(Math.sqrt(variance) / 20, 1)
  }

  // Submit results to backend
  const submitResults = async () => {
    if (!result || !token) return

    try {
      const response = await fetch('/miniapp/ppg/result', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          token,
          ...result
        })
      })

      if (response.ok) {
        window.location.href = `whatsapp://send?text=PPG scan complete! HR: ${result.hr_bpm} BPM, HRV: ${result.rmssd_ms.toFixed(0)} ms`
      }
    } catch (err) {
      console.error('Failed to submit results:', err)
    }
  }

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current)
      }
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop())
      }
    }
  }, [])

  // Countdown timer
  useEffect(() => {
    if (state !== 'preparing') return

    if (countdown > 0) {
      const timer = setTimeout(() => setCountdown(c => c - 1), 1000)
      return () => clearTimeout(timer)
    } else {
      startRecording()
    }
  }, [state, countdown, startRecording])

  // Recording timer
  useEffect(() => {
    if (state !== 'recording') return
  }, [state])

  // Render states
  if (!token) {
    return (
      <div style={styles.container}>
        <div style={styles.error}>
          <h2>Invalid Session</h2>
          <p>This link has expired. Please request a new PPG scan from P Square.</p>
        </div>
      </div>
    )
  }

  if (state === 'error') {
    return (
      <div style={styles.container}>
        <div style={styles.error}>
          <h2>⚠️ Error</h2>
          <p>{error}</p>
          <button style={styles.button} onClick={() => window.location.reload()}>
            Try Again
          </button>
        </div>
      </div>
    )
  }

  if (state === 'complete' && result) {
    return (
      <div style={styles.container}>
        <div style={styles.result}>
          <h2>✅ Scan Complete!</h2>
          <div style={styles.metrics}>
            <div style={styles.metric}>
              <span style={styles.metricValue}>{result.hr_bpm}</span>
              <span style={styles.metricLabel}>BPM</span>
            </div>
            <div style={styles.metric}>
              <span style={styles.metricValue}>{result.rmssd_ms.toFixed(0)}</span>
              <span style={styles.metricLabel}>HRV (ms)</span>
            </div>
          </div>
          <p style={styles.disclaimer}>
            This scan is for wellness insight only — not a medical diagnosis.
          </p>
          <button style={styles.button} onClick={submitResults}>
            Send to P Square
          </button>
        </div>
      </div>
    )
  }

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h1>PPG Vitals Scan</h1>
        <p>30-second finger scan</p>
      </div>

      {state === 'idle' && (
        <div style={styles.startScreen}>
          <div style={styles.instruction}>
            <h3>📱 How to scan:</h3>
            <ol>
              <li>Place your finger firmly over the camera lens</li>
              <li>Cover the flash with your finger too</li>
              <li>Hold still for 30 seconds</li>
              <li>Stay calm and don't talk</li>
            </ol>
          </div>
          <p style={styles.warning}>
            This scan estimates heart rate and stress. It's not a medical device.
          </p>
          <button style={styles.startButton} onClick={startCamera}>
            Start Scan
          </button>
        </div>
      )}

      {(state === 'preparing' || state === 'recording') && (
        <div style={styles.scanScreen}>
          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            style={styles.video}
          />
          <canvas ref={canvasRef} style={{ display: 'none' }} />

          {state === 'preparing' && (
            <div style={styles.countdown}>
              <span style={styles.countdownNumber}>{countdown}</span>
              <p>Get ready...</p>
            </div>
          )}

          {state === 'recording' && (
            <div style={styles.recording}>
              <div style={styles.progressBar}>
                <div style={{
                  ...styles.progressFill,
                  width: `${(recordingTime / 30) * 100}%`
                }} />
              </div>
              <p>{30 - recordingTime}s remaining</p>

              <div style={styles.qualityIndicator}>
                <span>Signal Quality:</span>
                <div style={styles.qualityBar}>
                  <div style={{
                    ...styles.qualityFill,
                    width: `${signalQuality * 100}%`,
                    background: signalQuality > 0.7 ? '#10B981' : signalQuality > 0.4 ? '#F59E0B' : '#EF4444'
                  }} />
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {state === 'processing' && (
        <div style={styles.processing}>
          <div style={styles.spinner} />
          <p>Analyzing your vitals...</p>
        </div>
      )}
    </div>
  )
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    minHeight: '100vh',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '20px',
    background: '#FAF7F2',
  },
  header: {
    textAlign: 'center',
    marginBottom: '20px',
  },
  startScreen: {
    maxWidth: '400px',
    textAlign: 'center',
  },
  instruction: {
    background: 'white',
    padding: '20px',
    borderRadius: '12px',
    marginBottom: '20px',
    textAlign: 'left',
  },
  warning: {
    fontSize: '14px',
    color: '#6B7280',
    marginBottom: '20px',
  },
  startButton: {
    background: '#0F766E',
    color: 'white',
    border: 'none',
    padding: '16px 32px',
    fontSize: '18px',
    borderRadius: '12px',
    cursor: 'pointer',
    width: '100%',
  },
  button: {
    background: '#0F766E',
    color: 'white',
    border: 'none',
    padding: '14px 28px',
    fontSize: '16px',
    borderRadius: '12px',
    cursor: 'pointer',
    width: '100%',
    marginTop: '20px',
  },
  video: {
    width: '100%',
    maxWidth: '300px',
    borderRadius: '12px',
    display: 'none',
  },
  scanScreen: {
    position: 'relative',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
  },
  countdown: {
    textAlign: 'center',
  },
  countdownNumber: {
    fontSize: '72px',
    fontWeight: 'bold',
    color: '#0F766E',
  },
  recording: {
    textAlign: 'center',
    width: '100%',
  },
  progressBar: {
    width: '100%',
    height: '8px',
    background: '#E5E7EB',
    borderRadius: '4px',
    marginBottom: '10px',
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    background: '#0F766E',
    transition: 'width 1s linear',
  },
  qualityIndicator: {
    marginTop: '20px',
    width: '100%',
  },
  qualityBar: {
    width: '100%',
    height: '6px',
    background: '#E5E7EB',
    borderRadius: '3px',
    marginTop: '5px',
    overflow: 'hidden',
  },
  qualityFill: {
    height: '100%',
    transition: 'width 0.3s',
  },
  processing: {
    textAlign: 'center',
  },
  spinner: {
    width: '48px',
    height: '48px',
    border: '4px solid #E5E7EB',
    borderTopColor: '#0F766E',
    borderRadius: '50%',
    animation: 'spin 1s linear infinite',
    margin: '0 auto 20px',
  },
  result: {
    textAlign: 'center',
    background: 'white',
    padding: '30px',
    borderRadius: '16px',
    maxWidth: '350px',
    width: '100%',
  },
  metrics: {
    display: 'flex',
    justifyContent: 'space-around',
    margin: '30px 0',
  },
  metric: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
  },
  metricValue: {
    fontSize: '36px',
    fontWeight: 'bold',
    color: '#0F766E',
  },
  metricLabel: {
    fontSize: '14px',
    color: '#6B7280',
  },
  disclaimer: {
    fontSize: '12px',
    color: '#9CA3AF',
    margin: '20px 0',
  },
  error: {
    textAlign: 'center',
    background: 'white',
    padding: '30px',
    borderRadius: '16px',
    maxWidth: '350px',
  },
}
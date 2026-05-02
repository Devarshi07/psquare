import { useState, useRef, useEffect, useCallback } from 'react'

interface FaceCaptureProps {
  token: string | null
}

type CaptureState = 'idle' | 'camera' | 'capturing' | 'processing' | 'complete' | 'error'

export default function FaceCapture({ token }: FaceCaptureProps) {
  const [state, setState] = useState<CaptureState>('idle')
  const [error, setError] = useState<string | null>(null)
  const [countdown, setCountdown] = useState(3)

  const videoRef = useRef<HTMLVideoElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const streamRef = useRef<MediaStream | null>(null)

  // Start camera
  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: 'user',
          width: { ideal: 1024 },
          height: { ideal: 1024 }
        },
        audio: false
      })
      streamRef.current = stream
      if (videoRef.current) {
        videoRef.current.srcObject = stream
      }
      setState('camera')
    } catch (err) {
      setError('Camera access denied. Please allow camera permissions.')
      setState('error')
    }
  }

  // Capture photo
  const capturePhoto = useCallback(async () => {
    if (!videoRef.current || !canvasRef.current) return

    setState('capturing')

    // Countdown
    for (let i = 3; i > 0; i--) {
      setCountdown(i)
      await new Promise(r => setTimeout(r, 1000))
    }

    // Capture
    const video = videoRef.current
    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    canvas.width = 1024
    canvas.height = 1024
    ctx.drawImage(video, 0, 0, 1024, 1024)

    // Stop camera
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop())
    }

    setState('processing')

    // Convert to blob
    canvas.toBlob(async (blob) => {
      if (!blob || !token) {
        setError('Failed to capture image')
        setState('error')
        return
      }

      try {
        // Upload to backend
        const formData = new FormData()
        formData.append('image', blob, 'face.jpg')
        formData.append('token', token)

        const response = await fetch('/miniapp/bioage/upload', {
          method: 'POST',
          body: formData,
        })

        if (response.ok) {
          setState('complete')
        } else {
          throw new Error('Upload failed')
        }
      } catch (err) {
        setError('Failed to upload image. Please try again.')
        setState('error')
      }
    }, 'image/jpeg', 0.9)

  }, [token])

  // Cleanup
  useEffect(() => {
    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop())
      }
    }
  }, [])

  // Render states
  if (!token) {
    return (
      <div style={styles.container}>
        <div style={styles.error}>
          <h2>Invalid Session</h2>
          <p>This link has expired. Please request a new session from P Square.</p>
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

  if (state === 'complete') {
    return (
      <div style={styles.container}>
        <div style={styles.result}>
          <h2>✅ Photo Captured!</h2>
          <p>Your face selfie has been sent for analysis.</p>
          <p style={styles.subtext}>You'll receive your Biological Age result in WhatsApp shortly.</p>
          <button style={styles.button} onClick={() => {
            window.location.href = `whatsapp://send?text=Face selfie complete!`
          }}>
            Back to WhatsApp
          </button>
        </div>
      </div>
    )
  }

  if (state === 'processing') {
    return (
      <div style={styles.container}>
        <div style={styles.processing}>
          <div style={styles.spinner} />
          <p>Analyzing your face...</p>
          <p style={styles.subtext}>This uses AI to estimate visible age markers.</p>
        </div>
      </div>
    )
  }

  if (state === 'capturing') {
    return (
      <div style={styles.container}>
        <div style={styles.countdown}>
          <span style={styles.countdownNumber}>{countdown}</span>
          <p>Keep steady!</p>
        </div>
      </div>
    )
  }

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h1>Face Age Check</h1>
        <p>Take a selfie for biological age estimation</p>
      </div>

      {state === 'idle' && (
        <div style={styles.startScreen}>
          <div style={styles.instruction}>
            <h3>📸 How to take the photo:</h3>
            <ol>
              <li>Face a window with soft daylight</li>
              <li>Remove glasses if possible</li>
              <li>Hold phone at arm's length</li>
              <li>Look at the camera, relax your face</li>
            </ol>
          </div>
          <p style={styles.warning}>
            This estimates visible age markers from your face. It's not a medical test.
          </p>
          <button style={styles.startButton} onClick={startCamera}>
            Start Camera
          </button>
        </div>
      )}

      {state === 'camera' && (
        <div style={styles.cameraScreen}>
          <div style={styles.cameraFrame}>
            <video
              ref={videoRef}
              autoPlay
              playsInline
              muted
              style={styles.video}
            />
            <canvas ref={canvasRef} style={{ display: 'none' }} />

            {/* Oval guide overlay */}
            <div style={styles.ovalGuide}>
              <div style={styles.ovalInner} />
            </div>
          </div>

          <p style={styles.cameraHint}>
            Position your face within the oval
          </p>

          <button style={styles.captureButton} onClick={capturePhoto}>
            Capture
          </button>
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
  cameraScreen: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    width: '100%',
  },
  cameraFrame: {
    position: 'relative',
    width: '280px',
    height: '350px',
    borderRadius: '16px',
    overflow: 'hidden',
    background: '#1F2937',
  },
  video: {
    width: '100%',
    height: '100%',
    objectFit: 'cover',
  },
  ovalGuide: {
    position: 'absolute',
    top: '50%',
    left: '50%',
    transform: 'translate(-50%, -50%)',
    width: '200px',
    height: '260px',
    borderRadius: '50%',
    border: '3px dashed rgba(255,255,255,0.5)',
    pointerEvents: 'none',
  },
  ovalInner: {
    position: 'absolute',
    top: '10%',
    left: '10%',
    width: '80%',
    height: '80%',
    borderRadius: '50%',
    border: '2px solid rgba(15, 118, 110, 0.3)',
  },
  cameraHint: {
    marginTop: '15px',
    color: '#6B7280',
    fontSize: '14px',
  },
  captureButton: {
    marginTop: '20px',
    background: '#0F766E',
    color: 'white',
    border: 'none',
    padding: '16px 48px',
    fontSize: '18px',
    borderRadius: '30px',
    cursor: 'pointer',
  },
  countdown: {
    textAlign: 'center',
  },
  countdownNumber: {
    fontSize: '96px',
    fontWeight: 'bold',
    color: '#0F766E',
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
  subtext: {
    fontSize: '14px',
    color: '#6B7280',
    marginTop: '10px',
  },
  error: {
    textAlign: 'center',
    background: 'white',
    padding: '30px',
    borderRadius: '16px',
    maxWidth: '350px',
  },
}
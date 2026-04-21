/**
 * Real-time audio recording and WebSocket streaming service
 */

class AudioRecorder {
  private mediaStream: MediaStream | null = null;
  private audioContext: AudioContext | null = null;
  private analyser: AnalyserNode | null = null;
  private audioSource: MediaStreamAudioSourceNode | null = null;

  async startRecording(): Promise<void> {
    try {
      console.log('🎤 Starting audio recording...');

      // Request microphone access with verbose error handling
      console.log('  → Requesting microphone access...');
      this.mediaStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      }).catch((err) => {
        console.error('getUserMedia error:', err);
        if (err.name === 'NotAllowedError') {
          throw new Error('Microphone permission denied. Please allow microphone access.');
        } else if (err.name === 'NotFoundError') {
          throw new Error('No microphone device found. Check if microphone is connected.');
        } else if (err.name === 'NotReadableError') {
          throw new Error('Microphone is being used by another application.');
        }
        throw err;
      });
      
      console.log('  ✓ Microphone access granted');
      console.log('    Tracks:', this.mediaStream.getTracks().map(t => `${t.kind}: ${t.label}`));

      // Initialize AudioContext
      console.log('  → Initializing AudioContext...');
      const AudioContextClass =
        window.AudioContext || (window as any).webkitAudioContext;
      if (!AudioContextClass) {
        throw new Error('AudioContext not supported in this browser');
      }

      this.audioContext = new AudioContextClass();
      console.log('  ✓ AudioContext created');

      // Resume AudioContext if suspended
      if (this.audioContext.state === 'suspended') {
        console.log('  → Resuming suspended AudioContext...');
        await this.audioContext.resume();
        console.log('  ✓ AudioContext resumed');
      }

      // Create audio nodes for level detection
      if (!this.audioSource && this.mediaStream) {
        console.log('  → Creating audio nodes...');
        this.audioSource = this.audioContext.createMediaStreamSource(this.mediaStream);
        this.analyser = this.audioContext.createAnalyser();
        this.analyser.fftSize = 256;
        this.audioSource.connect(this.analyser);
        console.log('  ✓ Audio nodes connected');
      }

      console.log('✓ Audio recording initialized successfully');
    } catch (error) {
      console.error('✗ Audio recording error:', error);
      this.cleanup();
      throw error;
    }
  }

  private cleanup(): void {
    if (this.audioSource) {
      try {
        this.audioSource.disconnect();
      } catch (e) {
        // Ignore disconnect errors
      }
    }
    if (this.analyser) {
      try {
        this.analyser.disconnect();
      } catch (e) {
        // Ignore disconnect errors
      }
    }
  }

  stopRecording(): void {
    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach((track) => {
        try {
          console.log(`Stopping track: ${track.kind}`);
          track.stop();
        } catch (e) {
          console.error('Error stopping track:', e);
        }
      });
      this.mediaStream = null;
    }

    this.cleanup();

    if (this.audioContext && this.audioContext.state !== 'closed') {
      try {
        this.audioContext.close();
      } catch (e) {
        console.error('Error closing AudioContext:', e);
      }
    }
    this.audioContext = null;
    this.audioSource = null;
  }

  getAudioLevel(): number {
    if (!this.analyser) return 0;

    try {
      const dataArray = new Uint8Array(this.analyser.frequencyBinCount);
      this.analyser.getByteFrequencyData(dataArray);
      const average = dataArray.reduce((a, b) => a + b) / dataArray.length;
      return Math.min(100, (average / 255) * 100);
    } catch (error) {
      return 0;
    }
  }

  getMediaStream(): MediaStream | null {
    return this.mediaStream;
  }
}

export class WebSocketAudioStreamer {
  private websocket: WebSocket | null = null;
  private sessionId: string;
  private chunkNumber: number = 0;
  private isRecording: boolean = false;
  private recorder: AudioRecorder;
  private mediaRecorder: MediaRecorder | null = null;
  private chunks: BlobPart[] = [];

  constructor(sessionId: string) {
    this.sessionId = sessionId;
    this.recorder = new AudioRecorder();
  }

  async connect(): Promise<void> {
    // Build WebSocket URL
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const url = `${protocol}//${host}/api/ws/stream/${this.sessionId}`;

    console.log('🔌 Connecting WebSocket...');
    console.log(`  URL: ${url}`);

    return new Promise((resolve, reject) => {
      const connectionTimeout = setTimeout(() => {
        if (this.websocket?.readyState === WebSocket.CONNECTING) {
          console.error('WebSocket connection timeout');
          this.websocket.close();
          reject(new Error('WebSocket connection timeout (30s)'));
        }
      }, 30000);

      try {
        this.websocket = new WebSocket(url);
        this.websocket.binaryType = 'arraybuffer';

        this.websocket.onopen = () => {
          clearTimeout(connectionTimeout);
          console.log('✓ WebSocket connected');
          resolve();
        };

        this.websocket.onerror = (event) => {
          clearTimeout(connectionTimeout);
          console.error('✗ WebSocket error:', event);
          reject(new Error(`WebSocket error: ${event.type}`));
        };

        this.websocket.onclose = (event) => {
          clearTimeout(connectionTimeout);
          console.log(`WebSocket closed: ${event.code} ${event.reason}`);
        };
      } catch (error) {
        clearTimeout(connectionTimeout);
        console.error('Failed to create WebSocket:', error);
        reject(error);
      }
    });
  }

  async startRecording(
    onChunk?: (chunk: string) => void,
    onInterrupt?: (payload: any) => void
  ): Promise<void> {
    if (this.isRecording) return;

    await this.recorder.startRecording();
    const stream = this.recorder.getMediaStream();

    if (!stream) throw new Error('No media stream available');

    // Check for supported mimeType
    const supportedTypes = ['audio/webm', 'audio/mp4', 'audio/wav', 'audio/ogg'];
    let mimeType = 'audio/webm';
    for (const type of supportedTypes) {
      if (MediaRecorder.isTypeSupported(type)) {
        mimeType = type;
        break;
      }
    }

    console.log(`Using MIME type: ${mimeType}`);
    this.mediaRecorder = new MediaRecorder(stream, { mimeType });

    this.chunkNumber = 0;
    this.chunks = [];
    this.isRecording = true;

    // Send connection ready message
    this.sendMessage({
      type: 'connection_ready',
      session_id: this.sessionId,
    });

    // Listen for messages from server BEFORE starting recording
    if (this.websocket) {
      this.websocket.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);

          if (message.type === 'transcription' && onChunk) {
            onChunk(message.data);
          }

          if (message.type === 'interrupt' && onInterrupt) {
            onInterrupt(message);
          }

          if (message.type === 'analysis_update') {
            console.log('Analysis update:', message);
            // Dispatch custom event so store can listen
            window.dispatchEvent(new CustomEvent('analysis_update', { detail: message }));
          }

          if (message.type === 'clarification_processed') {
            console.log('Clarification processed:', message);
            // Dispatch custom event so store can listen
            window.dispatchEvent(new CustomEvent('clarification_processed', { detail: message }));
          }

          if (message.type === 'analysis_complete') {
            console.log('Analysis complete:', message);
          }
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };
    }

    // Collect audio data from media recorder
    this.mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        this.chunks.push(event.data);

        // Send chunks every 500ms (approximately 500ms of audio)
        if (this.chunks.length >= 5) {
          this.sendAudioChunk();
          this.chunks = [];
        }
      }
    };

    // Start recording with 100ms timeslice
    this.mediaRecorder.start(100);
    console.log('✓ Recording started');
  }

  private sendAudioChunk(): void {
    if (!this.websocket || this.chunks.length === 0) {
      return;
    }

    if (this.websocket.readyState !== WebSocket.OPEN) {
      console.warn('WebSocket not open, cannot send audio chunk');
      return;
    }

    const blob = new Blob(this.chunks, { type: 'audio/webm' });
    const reader = new FileReader();

    reader.onload = () => {
      if (this.websocket && reader.result) {
        const base64Audio = (reader.result as string).split(',')[1] || (reader.result as string);
        
        this.sendMessage({
          type: 'audio_chunk',
          data: base64Audio,
          chunk_number: this.chunkNumber++,
          size: base64Audio.length,
        });
        
        console.log(`📤 Sent audio chunk #${this.chunkNumber - 1}: ${blob.size} bytes → ${base64Audio.length} base64 chars`);
      }
    };

    reader.onerror = () => {
      console.error('Failed to read audio blob');
    };

    reader.readAsDataURL(blob);
  }

  async stopRecording(): Promise<void> {
    if (!this.isRecording) return;

    this.isRecording = false;
    console.log('⏹️  Stopping recording...');

    if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
      this.mediaRecorder.stop();

      // Wait for remaining chunks to be processed
      await new Promise<void>((resolve) => {
        if (this.mediaRecorder) {
          this.mediaRecorder.onstop = () => {
            console.log(`Flushing ${this.chunks.length} remaining chunks...`);
            if (this.chunks.length > 0) {
              this.sendAudioChunk();
            }
            resolve();
          };
        } else {
          resolve();
        }
      });
    }

    // Send finalize message to trigger analysis
    console.log('📊 Sending finalize message...');
    this.sendMessage({
      type: 'finalize',
    });

    this.recorder.stopRecording();
    console.log('✓ Recording stopped');
  }

  private sendMessage(message: any): void {
    if (!this.websocket) {
      console.warn('WebSocket not initialized');
      return;
    }

    if (this.websocket.readyState !== WebSocket.OPEN) {
      console.warn(`Cannot send message: WebSocket state is ${this.websocket.readyState} (not OPEN)`);
      return;
    }

    try {
      const json = JSON.stringify(message);
      this.websocket.send(json);
      console.log(`📨 Sent message: ${message.type} (${json.length} bytes)`);
    } catch (error) {
      console.error('Failed to send message:', error);
    }
  }

  async sendClarificationResponse(
    clarifications: Record<string, string>
  ): Promise<void> {
    this.sendMessage({
      type: 'clarification_response',
      clarifications: clarifications,
    });
  }

  disconnect(): void {
    if (this.websocket) {
      this.websocket.close();
      this.websocket = null;
    }
    this.recorder.stopRecording();
  }

  getAudioLevel(): number {
    return this.recorder.getAudioLevel();
  }

  isConnected(): boolean {
    return (
      this.websocket !== null && this.websocket.readyState === WebSocket.OPEN
    );
  }

  isStreaming(): boolean {
    return this.isRecording;
  }
}

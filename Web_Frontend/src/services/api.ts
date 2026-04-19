import axios, { AxiosInstance } from 'axios';
import {
  AnalyzeRequirementsRequest,
  AnalysisState,
  FormalizedRequirement,
  ExportRequest,
  ExportResult,
  ClarificationResponseRequest,
} from '@/types/index';

class APIClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: '/api',
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  // Health & Status
  async getHealth(): Promise<{ status: string; version: string }> {
    const { data } = await this.client.get('/health');
    return data;
  }

  async getSystemStatus(): Promise<any> {
    const { data } = await this.client.get('/status');
    return data;
  }

  // Analysis Endpoints
  async analyzeRequirements(
    request: AnalyzeRequirementsRequest
  ): Promise<AnalysisState> {
    const { data } = await this.client.post('/analyze', request);
    return data;
  }

  async clarifyRequirements(
    request: ClarificationResponseRequest
  ): Promise<AnalysisState> {
    const { data } = await this.client.post('/clarify', request);
    return data;
  }

  async getFormalizedRequirements(
    sessionId: string
  ): Promise<FormalizedRequirement> {
    const { data } = await this.client.post('/formalize', { session_id: sessionId });
    return data;
  }

  // Upload Endpoints
  async uploadAudio(file: File): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);
    const { data } = await this.client.post('/upload/audio', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return data;
  }

  async uploadDocument(file: File): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);
    const { data } = await this.client.post('/upload/document', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return data;
  }

  async transcribeAudio(filePath: string, language: string = 'en'): Promise<any> {
    const { data } = await this.client.post('/transcribe', {
      file_path: filePath,
      language,
    });
    return data;
  }
  async exportRequirements(request: ExportRequest): Promise<ExportResult> {
    const { data } = await this.client.post('/export', request);
    return data;
  }

  async exportDryRun(request: ExportRequest): Promise<any> {
    const { data } = await this.client.post('/export/dry-run', request);
    return data;
  }

  // WebSocket for streaming
  connectWebSocket(sessionId: string): WebSocket {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const ws = new WebSocket(
      `${protocol}//${window.location.host}/api/ws/stream/${sessionId}`
    );
    return ws;
  }

  // Error handling
  getErrorMessage(error: any): string {
    if (error.response?.data?.detail) {
      return error.response.data.detail;
    }
    if (error.message) {
      return error.message;
    }
    return 'An error occurred';
  }
}

export const apiClient = new APIClient();

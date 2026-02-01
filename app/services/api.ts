import { 
  VerifyResponse, 
  HistoryItem, 
  Rule, 
  PlaybookStatus, 
  SystemStats,
  BatchTask
} from '../types';

// API Base URL - Configure this for your backend
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Helper for API calls
async function fetchApi<T>(
  endpoint: string, 
  options?: RequestInit
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  
  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }
  
  return response.json();
}

export const api = {
  /**
   * Verify a single claim
   */
  verify: async (claim: string, mode: 'static' | 'evolving'): Promise<VerifyResponse> => {
    return fetchApi<VerifyResponse>('/api/verify', {
      method: 'POST',
      body: JSON.stringify({ claim, mode }),
    });
  },

  /**
   * Upload CSV for batch verification
   */
  uploadBatch: async (file: File, mode: 'static' | 'evolving'): Promise<BatchTask> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('mode', mode);
    
    const url = `${API_BASE_URL}/api/verify/batch`;
    const response = await fetch(url, {
      method: 'POST',
      body: formData,
    });
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Upload failed' }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }
    
    return response.json();
  },

  /**
   * Get batch task status
   */
  getBatchStatus: async (taskId: string): Promise<BatchTask> => {
    return fetchApi<BatchTask>(`/api/verify/batch/${taskId}`);
  },

  /**
   * Download batch results (returns blob URL for download)
   */
  downloadBatchResults: async (taskId: string): Promise<string> => {
    const url = `${API_BASE_URL}/api/verify/batch/${taskId}/download`;
    const response = await fetch(url);
    
    if (!response.ok) {
      throw new Error('Download failed');
    }
    
    const blob = await response.blob();
    return URL.createObjectURL(blob);
  },

  /**
   * Get verification history list
   */
  getHistory: async (params?: {
    page?: number;
    page_size?: number;
    verdict?: 'True' | 'False';
    mode?: 'static' | 'evolving';
    search?: string;
    min_confidence?: number;
    max_confidence?: number;
  }): Promise<{ items: HistoryItem[], total: number, page: number, total_pages: number }> => {
    const searchParams = new URLSearchParams();
    
    if (params?.page) searchParams.append('page', params.page.toString());
    if (params?.page_size) searchParams.append('page_size', params.page_size.toString());
    if (params?.verdict) searchParams.append('verdict', params.verdict);
    if (params?.mode) searchParams.append('mode', params.mode);
    if (params?.search) searchParams.append('search', params.search);
    if (params?.min_confidence) searchParams.append('min_confidence', params.min_confidence.toString());
    if (params?.max_confidence) searchParams.append('max_confidence', params.max_confidence.toString());
    
    const queryString = searchParams.toString();
    const endpoint = queryString ? `/api/history?${queryString}` : '/api/history';
    
    return fetchApi(endpoint);
  },

  /**
   * Get single history detail
   */
  getHistoryDetail: async (caseId: string): Promise<VerifyResponse> => {
    return fetchApi<VerifyResponse>(`/api/history/${caseId}`);
  },

  /**
   * Delete history record
   */
  deleteHistory: async (caseId: string): Promise<{ message: string }> => {
    return fetchApi(`/api/history/${caseId}`, {
      method: 'DELETE',
    });
  },

  /**
   * Get playbook status
   */
  getPlaybookStats: async (): Promise<PlaybookStatus> => {
    return fetchApi<PlaybookStatus>('/api/playbook');
  },

  /**
   * Get all rules
   */
  getRules: async (): Promise<{ detection_rules: Rule[], trust_rules: Rule[], total_count: number }> => {
    return fetchApi('/api/playbook/rules');
  },

  /**
   * Get single rule detail
   */
  getRuleDetail: async (ruleId: string): Promise<Rule> => {
    return fetchApi<Rule>(`/api/playbook/rules/${ruleId}`);
  },

  /**
   * Switch playbook
   */
  switchPlaybook: async (
    playbookName: 'default' | 'warmup' | 'custom',
    customPath?: string
  ): Promise<PlaybookStatus> => {
    return fetchApi<PlaybookStatus>('/api/playbook/switch', {
      method: 'POST',
      body: JSON.stringify({
        playbook_name: playbookName,
        custom_path: customPath,
      }),
    });
  },

  /**
   * Get current playbook info
   */
  getCurrentPlaybook: async (): Promise<{ current_playbook: string, playbook_dir: string }> => {
    return fetchApi('/api/playbook/current');
  },

  /**
   * Get system statistics
   */
  getStats: async (): Promise<SystemStats> => {
    return fetchApi<SystemStats>('/api/stats');
  },

  /**
   * Upload warmup dataset
   */
  uploadWarmupDataset: async (file: File): Promise<{
    filename: string;
    total_rows: number;
    columns: string[];
    sample_claims: string[];
  }> => {
    const formData = new FormData();
    formData.append('file', file);
    
    const url = `${API_BASE_URL}/api/warmup/upload`;
    const response = await fetch(url, {
      method: 'POST',
      body: formData,
    });
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Upload failed' }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }
    
    return response.json();
  },

  /**
   * Start warmup process
   */
  startWarmup: async (params: {
    dataset_path?: string;
    output_playbook_name: string;
  }): Promise<{
    task_id: string;
    status: string;
    total_cases: number;
    output_playbook_path?: string;
  }> => {
    return fetchApi('/api/warmup/start', {
      method: 'POST',
      body: JSON.stringify(params),
    });
  },

  /**
   * Get warmup task status
   */
  getWarmupStatus: async (taskId: string): Promise<{
    task_id: string;
    status: string;
    total_cases: number;
    processed_cases: number;
    correct_verdicts: number;
    incorrect_verdicts: number;
    rules_generated: number;
    detection_rules: number;
    trust_rules: number;
  }> => {
    return fetchApi(`/api/warmup/${taskId}`);
  },

  /**
   * Health check
   */
  healthCheck: async (): Promise<{ status: string }> => {
    return fetchApi('/health');
  },
};
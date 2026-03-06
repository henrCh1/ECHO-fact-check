export type VerificationMode = 'static' | 'evolving';
export type Verdict = 'True' | 'False';
export type Credibility = 'high' | 'medium' | 'low';
export type RuleMatchQuality = 'high' | 'medium' | 'low' | 'none';
export type RuleType = 'strategy' | 'tool_template' | 'pitfall';
export type MemoryType = 'detection' | 'trust';
export type RuleStatus = 'verified' | 'trial';
export type RuleSourceType = 'seed' | 'human_reviewed_generation';
export type TaskStatus = 'pending' | 'running' | 'completed' | 'failed';
export type ReviewBatchStatus = 'pending_review' | 'processing' | 'completed';

export interface Evidence {
  source: string;
  content: string;
  credibility: Credibility;
}

export interface ProcessTrace {
  planner_output: {
    extracted_claims?: string[];
    selected_rules?: string[];
    search_queries?: string[];
  };
  investigator_output: {
    evidence_items?: any[];
  };
  judge_reasoning: string;
}

export interface VerifyResponse {
  case_id: string;
  claim: string;
  verdict: Verdict;
  confidence: number;
  reasoning: string;
  evidence: Evidence[];
  used_rules: string[];
  rule_match_quality: RuleMatchQuality;
  process_trace?: ProcessTrace;
  timestamp: string;
  mode: VerificationMode;
  evolution_meta?: EvolutionMeta;
}

export interface Rule {
  rule_id: string;
  type: RuleType;
  condition: string;
  action: string;
  description: string;
  confidence: number;
  evidence_count: number;
  memory_type?: MemoryType;
  rule_status: RuleStatus;
  source_type: RuleSourceType;
  active: boolean;
  created_from?: string;
  created_at?: string;
  parent_rule?: string;
  support_case_ids?: string[];
}

export interface HistoryItem {
  case_id: string;
  claim_summary: string;
  verdict: Verdict;
  confidence: number;
  rule_match_quality: RuleMatchQuality;
  timestamp: string;
  mode: VerificationMode;
}

export interface PlaybookStatus {
  version: string;
  detection_rules_count: number;
  trust_rules_count: number;
  total_active_rules: number;
  total_cases_processed: number;
  last_updated: string;
}

export interface SystemStats {
  verification: {
    total_verifications: number;
    true_count: number;
    false_count: number;
    avg_confidence: number;
    static_mode_count: number;
    evolving_mode_count: number;
  };
  playbook: PlaybookStatus;
}

export interface BatchTask {
  task_id: string;
  status: TaskStatus;
  total: number;
  completed: number;
  failed: number;
  created_at: string;
  updated_at?: string;
  error_message?: string;
}

export interface EvolutionMeta {
  pending_count: number;
  review_batch_ready: boolean;
  review_batch_id?: string | null;
}

export interface PendingReviewCase extends VerifyResponse {
  mode: 'evolving';
}

export interface ReviewBatch {
  batch_id: string;
  status: ReviewBatchStatus;
  created_at: string;
  updated_at: string;
  deferred_count: number;
  cases: PendingReviewCase[];
}

export interface PendingReviewResponse {
  has_pending_batch: boolean;
  pending_count: number;
  batch?: ReviewBatch | null;
}

export interface ReviewFeedbackItem {
  case_id: string;
  judgment_correct: boolean;
  reasoning_correct: boolean;
  comment?: string;
}

export interface ReviewBatchSubmitResponse {
  batch_id: string;
  status: 'completed';
  processed_cases: number;
  updates_applied: number;
  trial_rules_generated: number;
  detection_rules_generated: number;
  trust_rules_generated: number;
  next_batch_ready: boolean;
  next_batch_id?: string | null;
}

export interface RuntimeSettings {
  google_api_key_configured: boolean;
  gemini_model: string;
  version: string;
}

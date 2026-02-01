export type VerificationMode = 'static' | 'evolving';
export type Verdict = 'True' | 'False';
export type Credibility = 'high' | 'medium' | 'low';
export type RuleMatchQuality = 'high' | 'medium' | 'low' | 'none';
export type RuleType = 'strategy' | 'tool_template' | 'pitfall';
export type MemoryType = 'detection' | 'trust';
export type TaskStatus = 'pending' | 'running' | 'completed' | 'failed';

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
  active: boolean;
  created_from?: string;
  created_at?: string;
  parent_rule?: string;
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
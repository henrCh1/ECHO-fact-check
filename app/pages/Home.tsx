import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Search,
  UploadCloud,
  FileText,
  Zap,
  BrainCircuit,
  Loader2,
  Clock3,
  MessageSquareWarning,
  CheckCircle2,
  XCircle,
} from 'lucide-react';
import { Button, Card, InputLabel, Badge } from '../components/ui';
import { api } from '../services/api';
import {
  PendingReviewResponse,
  ReviewBatch,
  ReviewFeedbackItem,
  VerifyResponse,
} from '../types';

type ReviewDraft = {
  judgment_correct?: boolean;
  reasoning_correct?: boolean;
  comment: string;
};

const buildDrafts = (batch?: ReviewBatch | null): Record<string, ReviewDraft> => {
  if (!batch) {
    return {};
  }

  return Object.fromEntries(
    batch.cases.map((item) => [
      item.case_id,
      {
        judgment_correct: undefined,
        reasoning_correct: undefined,
        comment: '',
      },
    ])
  );
};

const Home: React.FC = () => {
  const navigate = useNavigate();
  const [claim, setClaim] = useState('');
  const [mode, setMode] = useState<'static' | 'evolving'>('static');
  const [isLoading, setIsLoading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<string | null>(null);
  const [pendingReview, setPendingReview] = useState<PendingReviewResponse | null>(null);
  const [showReviewModal, setShowReviewModal] = useState(false);
  const [reviewDrafts, setReviewDrafts] = useState<Record<string, ReviewDraft>>({});
  const [isLoadingPendingReview, setIsLoadingPendingReview] = useState(false);
  const [isSubmittingReview, setIsSubmittingReview] = useState(false);
  const [delayedNavigationResponse, setDelayedNavigationResponse] = useState<VerifyResponse | null>(null);

  const [verificationProgress, setVerificationProgress] = useState({
    step: 0,
    message: '',
    show: false,
  });

  const verificationSteps = [
    { name: '提取关键声明', duration: 2000 },
    { name: '搜索证据', duration: 4000 },
    { name: '分析判断', duration: 3000 },
    { name: '生成报告', duration: 1500 },
    ...(mode === 'evolving' ? [{ name: '写入演化缓冲池', duration: 2000 }] : []),
  ];

  const currentBatch = pendingReview?.batch ?? null;

  useEffect(() => {
    loadPendingReview(true);
  }, []);

  useEffect(() => {
    setReviewDrafts(buildDrafts(currentBatch));
  }, [currentBatch?.batch_id]);

  const loadPendingReview = async (autoOpen: boolean) => {
    setIsLoadingPendingReview(true);
    try {
      const response = await api.getPendingEvolutionBatch();
      setPendingReview(response);
      if (autoOpen && response.has_pending_batch && response.batch) {
        setShowReviewModal(true);
      }
    } catch (error) {
      console.error('Failed to load pending review batch', error);
    } finally {
      setIsLoadingPendingReview(false);
    }
  };

  const navigateToResult = (response: VerifyResponse) => {
    navigate(`/result/${response.case_id}`, { state: { data: response } });
  };

  const handleVerify = async () => {
    if (!claim.trim()) return;
    setIsLoading(true);
    setVerificationProgress({ step: 0, message: verificationSteps[0].name, show: true });

    let currentStep = 0;
    const progressInterval = setInterval(() => {
      currentStep++;
      if (currentStep < verificationSteps.length) {
        setVerificationProgress({
          step: currentStep,
          message: verificationSteps[currentStep].name,
          show: true,
        });
      }
    }, 2500);

    try {
      const response = await api.verify(claim, mode);
      clearInterval(progressInterval);
      setVerificationProgress({ step: verificationSteps.length, message: '完成', show: true });

      if (mode === 'evolving') {
        await loadPendingReview(Boolean(response.evolution_meta?.review_batch_ready));
        if (response.evolution_meta?.review_batch_ready) {
          setDelayedNavigationResponse(response);
          return;
        }
      }

      setTimeout(() => {
        navigateToResult(response);
      }, 500);
    } catch (error) {
      clearInterval(progressInterval);
      setVerificationProgress({ step: 0, message: '', show: false });
      console.error('Verification failed', error);
      alert('核查失败: ' + (error instanceof Error ? error.message : '未知错误'));
    } finally {
      setIsLoading(false);
    }
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleFileUpload = async (file: File) => {
    if (!file.name.endsWith('.csv')) {
      alert('请上传 CSV 文件');
      return;
    }

    setUploadStatus('正在上传...');
    try {
      const task = await api.uploadBatch(file, mode);
      setUploadStatus(`任务已创建: ${task.task_id}`);
      alert(`批量任务已开始。任务 ID: ${task.task_id}\n请在历史记录中查看进度。`);
    } catch (error) {
      setUploadStatus(null);
      alert('上传失败: ' + (error instanceof Error ? error.message : '未知错误'));
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  };

  const updateDraft = (caseId: string, patch: Partial<ReviewDraft>) => {
    setReviewDrafts((current) => ({
      ...current,
      [caseId]: {
        ...current[caseId],
        ...patch,
      },
    }));
  };

  const finishPendingNavigation = () => {
    if (delayedNavigationResponse) {
      const response = delayedNavigationResponse;
      setDelayedNavigationResponse(null);
      navigateToResult(response);
    }
  };

  const handleSubmitReview = async () => {
    if (!currentBatch) return;

    const feedback: ReviewFeedbackItem[] = [];
    for (const item of currentBatch.cases) {
      const draft = reviewDrafts[item.case_id];
      if (draft?.judgment_correct === undefined || draft?.reasoning_correct === undefined) {
        alert('请为每条案例选择“判断是否正确”和“过程是否正确”。');
        return;
      }

      feedback.push({
        case_id: item.case_id,
        judgment_correct: draft.judgment_correct,
        reasoning_correct: draft.reasoning_correct,
        comment: draft.comment.trim() || undefined,
      });
    }

    setIsSubmittingReview(true);
    try {
      const result = await api.submitEvolutionBatch(currentBatch.batch_id, feedback);
      await loadPendingReview(false);
      setShowReviewModal(false);
      alert(
        `反馈已提交。处理 ${result.processed_cases} 条案例，应用 ${result.updates_applied} 次规则更新，新生成 ${result.trial_rules_generated} 条 Trial 规则。`
      );
      finishPendingNavigation();
    } catch (error) {
      alert('提交反馈失败: ' + (error instanceof Error ? error.message : '未知错误'));
    } finally {
      setIsSubmittingReview(false);
    }
  };

  const handleDeferReview = async () => {
    if (!currentBatch) return;

    setIsSubmittingReview(true);
    try {
      const response = await api.skipEvolutionBatch(currentBatch.batch_id);
      setPendingReview(response);
      setShowReviewModal(false);
      finishPendingNavigation();
    } catch (error) {
      alert('稍后处理失败: ' + (error instanceof Error ? error.message : '未知错误'));
    } finally {
      setIsSubmittingReview(false);
    }
  };

  return (
    <div className="space-y-8">
      {pendingReview?.has_pending_batch && pendingReview.batch && (
        <Card className="p-4 border-amber-200 bg-amber-50">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-start gap-3">
              <div className="rounded-full bg-amber-100 p-2 text-amber-700">
                <MessageSquareWarning className="h-5 w-5" />
              </div>
              <div>
                <div className="text-sm font-semibold text-amber-900">有一批待反馈的演化案例</div>
                <div className="text-sm text-amber-800">
                  当前批次包含 {pendingReview.batch.cases.length} 条案例，已延期 {pendingReview.batch.deferred_count} 次。
                </div>
              </div>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" onClick={() => setShowReviewModal(true)}>
                立即处理
              </Button>
              <Badge variant="warning">Pending Buffer</Badge>
            </div>
          </div>
        </Card>
      )}

      <div className="text-center max-w-2xl mx-auto pt-8 pb-4">
        <h2 className="text-3xl font-bold text-gray-900 sm:text-4xl">AI 事实核查系统</h2>
        <p className="mt-4 text-lg text-gray-500">
          输入待核查声明或上传 CSV 文件。演化模式会将案例写入 Pending Buffer，满 3 条后集中请求人工反馈。
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        <div className="md:col-span-2 space-y-6">
          <Card className="p-6">
            <div className="flex items-center justify-between mb-4">
              <InputLabel>待核查声明</InputLabel>
              <div className="flex bg-gray-100 rounded-lg p-1">
                <button
                  onClick={() => setMode('static')}
                  className={`px-3 py-1.5 text-xs font-medium rounded-md transition-all ${
                    mode === 'static' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-900'
                  }`}
                >
                  <div className="flex items-center">
                    <Zap className="w-3 h-3 mr-1.5" />
                    静态模式
                  </div>
                </button>
                <button
                  onClick={() => setMode('evolving')}
                  className={`px-3 py-1.5 text-xs font-medium rounded-md transition-all ${
                    mode === 'evolving' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-900'
                  }`}
                >
                  <div className="flex items-center">
                    <BrainCircuit className="w-3 h-3 mr-1.5" />
                    演化模式
                  </div>
                </button>
              </div>
            </div>

            <textarea
              className="w-full h-40 p-4 text-gray-900 placeholder-gray-400 border border-gray-200 rounded-lg focus:ring-2 focus:ring-gray-900 focus:border-transparent resize-none"
              placeholder="例如：根据最新报道，某公司上个月营收同比增长 50% ..."
              value={claim}
              onChange={(e) => setClaim(e.target.value)}
            />

            <div className="mt-4 flex flex-col">
              <Button onClick={handleVerify} disabled={isLoading || !claim.trim()} className="w-full sm:w-auto self-end">
                {isLoading ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    分析中...
                  </>
                ) : (
                  <>
                    <Search className="w-4 h-4 mr-2" />
                    开始核查
                  </>
                )}
              </Button>

              {verificationProgress.show && (
                <div className="mt-4 p-4 bg-blue-50 rounded-lg border border-blue-100">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-blue-900">{verificationProgress.message}</span>
                    <span className="text-xs text-blue-600">
                      {verificationProgress.step + 1} / {verificationSteps.length}
                    </span>
                  </div>
                  <div className="w-full bg-blue-200 rounded-full h-2 overflow-hidden">
                    <div
                      className="bg-blue-600 h-2 rounded-full transition-all duration-500 ease-out"
                      style={{ width: `${((verificationProgress.step + 1) / verificationSteps.length) * 100}%` }}
                    />
                  </div>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {verificationSteps.map((step, idx) => (
                      <div
                        key={idx}
                        className={`text-xs px-2 py-1 rounded ${
                          idx < verificationProgress.step
                            ? 'bg-blue-600 text-white'
                            : idx === verificationProgress.step
                              ? 'bg-blue-500 text-white animate-pulse'
                              : 'bg-gray-200 text-gray-500'
                        }`}
                      >
                        {step.name}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </Card>
        </div>

        <div className="md:col-span-1">
          <Card className="h-full p-6 flex flex-col">
            <InputLabel>批量核查</InputLabel>
            <div
              className={`relative flex-1 mt-4 border-2 border-dashed rounded-xl flex flex-col items-center justify-center p-6 text-center transition-colors ${
                dragActive ? 'border-gray-900 bg-gray-50' : 'border-gray-200 hover:border-gray-300'
              }`}
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
            >
              <div className="p-3 bg-gray-50 rounded-full mb-3">
                <UploadCloud className="w-6 h-6 text-gray-400" />
              </div>
              <p className="text-sm font-medium text-gray-900">点击上传或拖拽 CSV</p>
              <p className="text-xs text-gray-500 mt-1">支持最大 10MB 的 .csv 文件</p>
              <input
                type="file"
                className="hidden"
                accept=".csv"
                id="file-upload"
                onChange={(e) => {
                  if (e.target.files?.[0]) handleFileUpload(e.target.files[0]);
                }}
              />
              <label htmlFor="file-upload" className="absolute inset-0 cursor-pointer"></label>
            </div>
            <div className="mt-4 space-y-3">
              <div className="flex items-start p-3 text-xs text-blue-700 bg-blue-50 rounded-lg">
                <FileText className="w-4 h-4 mr-2 mt-0.5 flex-shrink-0" />
                <p>请确保 CSV 包含 `Statement` 或 `Claim` 列。</p>
              </div>
              {uploadStatus && <div className="text-xs text-gray-600">{uploadStatus}</div>}
              {isLoadingPendingReview && <div className="text-xs text-gray-500">正在检查待反馈批次...</div>}
            </div>
          </Card>
        </div>
      </div>

      {showReviewModal && currentBatch && (
        <div className="fixed inset-0 z-50 bg-gray-950/50 backdrop-blur-sm px-4 py-8 overflow-y-auto">
          <div className="max-w-5xl mx-auto">
            <Card className="p-6 sm:p-8">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between mb-6">
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-xl font-bold text-gray-900">Pending Buffer 批量反馈</h3>
                    <Badge variant="warning">Batch of {currentBatch.cases.length}</Badge>
                  </div>
                  <p className="text-sm text-gray-500 mt-1">
                    请逐条判断系统结论和核查过程是否正确。提交后将按 warmup 风格生成 Trial 规则。
                  </p>
                </div>
                <div className="flex items-center gap-2 text-sm text-gray-500">
                  <Clock3 className="w-4 h-4" />
                  已延期 {currentBatch.deferred_count} 次
                </div>
              </div>

              <div className="space-y-6 max-h-[70vh] overflow-y-auto pr-1">
                {currentBatch.cases.map((item, index) => {
                  const draft = reviewDrafts[item.case_id] || { comment: '' };
                  return (
                    <div key={item.case_id} className="rounded-2xl border border-gray-200 p-5 space-y-4">
                      <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                        <div>
                          <div className="text-xs font-semibold uppercase tracking-wide text-gray-400">
                            Case {index + 1}
                          </div>
                          <div className="mt-1 text-base font-semibold text-gray-900">{item.claim}</div>
                        </div>
                        <div className="flex flex-wrap gap-2">
                          <Badge variant={item.verdict === 'True' ? 'success' : 'danger'}>
                            结论: {item.verdict}
                          </Badge>
                          <Badge variant="neutral">置信度 {Math.round(item.confidence * 100)}%</Badge>
                        </div>
                      </div>

                      <div className="rounded-xl bg-gray-50 border border-gray-100 p-4 space-y-3">
                        <div>
                          <div className="text-xs font-semibold uppercase tracking-wide text-gray-400">Reasoning</div>
                          <p className="mt-1 text-sm text-gray-700 whitespace-pre-wrap">{item.reasoning}</p>
                        </div>
                        {item.process_trace && (
                          <div className="grid gap-3 md:grid-cols-2">
                            <div>
                              <div className="text-xs font-semibold uppercase tracking-wide text-gray-400">
                                Planner
                              </div>
                              <div className="mt-1 text-sm text-gray-700">
                                Claims: {(item.process_trace.planner_output.extracted_claims || []).join(' | ') || 'None'}
                              </div>
                              <div className="mt-1 text-sm text-gray-700">
                                Queries: {(item.process_trace.planner_output.search_queries || []).join(' | ') || 'None'}
                              </div>
                            </div>
                            <div>
                              <div className="text-xs font-semibold uppercase tracking-wide text-gray-400">
                                Judge
                              </div>
                              <p className="mt-1 text-sm text-gray-700 whitespace-pre-wrap">
                                {item.process_trace.judge_reasoning}
                              </p>
                            </div>
                          </div>
                        )}
                        <div>
                          <div className="text-xs font-semibold uppercase tracking-wide text-gray-400">Rules</div>
                          <div className="mt-1 flex flex-wrap gap-2">
                            {item.used_rules.length > 0 ? (
                              item.used_rules.map((ruleId) => (
                                <Badge key={ruleId} variant="blue">
                                  {ruleId}
                                </Badge>
                              ))
                            ) : (
                              <span className="text-sm text-gray-500">No matched rules</span>
                            )}
                          </div>
                        </div>
                      </div>

                      <div className="grid gap-4 md:grid-cols-2">
                        <div className="space-y-2">
                          <div className="text-sm font-semibold text-gray-900">判断是否正确</div>
                          <div className="flex gap-2">
                            <Button
                              type="button"
                              variant={draft.judgment_correct === true ? 'primary' : 'outline'}
                              className="flex-1"
                              onClick={() => updateDraft(item.case_id, { judgment_correct: true })}
                            >
                              <CheckCircle2 className="w-4 h-4 mr-2" />
                              正确
                            </Button>
                            <Button
                              type="button"
                              variant={draft.judgment_correct === false ? 'primary' : 'outline'}
                              className="flex-1"
                              onClick={() => updateDraft(item.case_id, { judgment_correct: false })}
                            >
                              <XCircle className="w-4 h-4 mr-2" />
                              错误
                            </Button>
                          </div>
                        </div>

                        <div className="space-y-2">
                          <div className="text-sm font-semibold text-gray-900">核查过程是否正确</div>
                          <div className="flex gap-2">
                            <Button
                              type="button"
                              variant={draft.reasoning_correct === true ? 'primary' : 'outline'}
                              className="flex-1"
                              onClick={() => updateDraft(item.case_id, { reasoning_correct: true })}
                            >
                              <CheckCircle2 className="w-4 h-4 mr-2" />
                              正确
                            </Button>
                            <Button
                              type="button"
                              variant={draft.reasoning_correct === false ? 'primary' : 'outline'}
                              className="flex-1"
                              onClick={() => updateDraft(item.case_id, { reasoning_correct: false })}
                            >
                              <XCircle className="w-4 h-4 mr-2" />
                              错误
                            </Button>
                          </div>
                        </div>
                      </div>

                      <div>
                        <div className="text-sm font-semibold text-gray-900 mb-2">补充说明</div>
                        <textarea
                          className="w-full min-h-[88px] rounded-xl border border-gray-200 px-3 py-2 text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-900 focus:border-transparent"
                          placeholder="可选：指出错在何处，或说明为什么过程不合理。"
                          value={draft.comment}
                          onChange={(e) => updateDraft(item.case_id, { comment: e.target.value })}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>

              <div className="mt-6 flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
                <Button variant="outline" onClick={handleDeferReview} disabled={isSubmittingReview}>
                  稍后处理
                </Button>
                <Button onClick={handleSubmitReview} disabled={isSubmittingReview}>
                  {isSubmittingReview ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      提交中...
                    </>
                  ) : (
                    '提交反馈并生成 Trial 规则'
                  )}
                </Button>
              </div>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
};

export default Home;

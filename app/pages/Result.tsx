import React, { useEffect, useState } from 'react';
import { useParams, useLocation, Link } from 'react-router-dom';
import {
  ArrowLeft,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Share2,
  Download,
  ChevronDown,
  ChevronUp,
  Search,
  BookOpen,
  Loader2
} from 'lucide-react';
import { Button, Card, Badge, ProgressBar } from '../components/ui';
import { VerifyResponse, Rule } from '../types';
import { api } from '../services/api';

const Result: React.FC = () => {
  const { caseId } = useParams<{ caseId: string }>();
  const location = useLocation();
  const [data, setData] = useState<VerifyResponse | null>(location.state?.data || null);
  const [expandedTrace, setExpandedTrace] = useState(false);
  const [expandedRules, setExpandedRules] = useState<Set<string>>(new Set());
  const [ruleDetails, setRuleDetails] = useState<Map<string, Rule>>(new Map());
  const [loadingRules, setLoadingRules] = useState<Set<string>>(new Set());

  useEffect(() => {
    if (!data && caseId) {
      api.getHistoryDetail(caseId).then(setData);
    }
  }, [caseId, data]);

  const toggleRuleExpand = async (ruleId: string) => {
    const newExpanded = new Set(expandedRules);

    if (newExpanded.has(ruleId)) {
      newExpanded.delete(ruleId);
      setExpandedRules(newExpanded);
    } else {
      newExpanded.add(ruleId);
      setExpandedRules(newExpanded);

      // Fetch rule details if not already loaded
      if (!ruleDetails.has(ruleId)) {
        setLoadingRules(new Set(loadingRules).add(ruleId));
        try {
          const rule = await api.getRuleDetail(ruleId);
          setRuleDetails(new Map(ruleDetails).set(ruleId, rule));
        } catch (error) {
          console.error('Failed to load rule details:', error);
        } finally {
          const newLoading = new Set(loadingRules);
          newLoading.delete(ruleId);
          setLoadingRules(newLoading);
        }
      }
    }
  };


  if (!data) return <div className="p-8 text-center text-gray-500">正在加载分析结果...</div>;

  const isTrue = data.verdict === 'True';
  const confidenceColor = data.confidence > 0.8 ? 'bg-green-500' : data.confidence > 0.5 ? 'bg-amber-500' : 'bg-red-500';

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <Link to="/" className="flex items-center text-sm text-gray-500 hover:text-gray-900 transition-colors">
          <ArrowLeft className="w-4 h-4 mr-1" />
          返回核查页
        </Link>
        <div className="flex space-x-2">
          <Button variant="outline" className="h-9 px-3">
            <Share2 className="w-4 h-4 mr-2" />
            分享
          </Button>
          <Button variant="outline" className="h-9 px-3">
            <Download className="w-4 h-4 mr-2" />
            导出
          </Button>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Main Verdict Column */}
        <div className="lg:col-span-2 space-y-6">
          {/* Claim & Verdict */}
          <Card className="p-6 overflow-hidden relative">
            <div className={`absolute top-0 left-0 w-1 h-full ${isTrue ? 'bg-green-500' : 'bg-red-500'}`}></div>
            <div className="mb-4">
              <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wider mb-2">已核查声明</h3>
              <p className="text-lg font-medium text-gray-900 leading-relaxed">"{data.claim}"</p>
            </div>

            <div className="flex items-center justify-between pt-6 border-t border-gray-100">
              <div className="flex items-center">
                {isTrue ? (
                  <CheckCircle className="w-10 h-10 text-green-500 mr-4" />
                ) : (
                  <XCircle className="w-10 h-10 text-red-500 mr-4" />
                )}
                <div>
                  <div className="text-sm text-gray-500">结论</div>
                  <div className={`text-2xl font-bold ${isTrue ? 'text-green-600' : 'text-red-600'}`}>
                    {data.verdict}
                  </div>
                </div>
              </div>
              <div className="w-48">
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-500">置信度</span>
                  <span className="font-bold text-gray-900">{Math.round(data.confidence * 100)}%</span>
                </div>
                <ProgressBar value={data.confidence * 100} color={confidenceColor} />
              </div>
            </div>
          </Card>

          {/* Reasoning */}
          <Card className="p-6">
            <h3 className="text-lg font-bold text-gray-900 mb-4">AI 推理分析</h3>
            <p className="text-gray-700 leading-relaxed whitespace-pre-wrap">
              {data.reasoning}
            </p>

            {data.process_trace && (
              <div className="mt-6 border rounded-lg overflow-hidden">
                <button
                  onClick={() => setExpandedTrace(!expandedTrace)}
                  className="w-full flex items-center justify-between px-4 py-3 bg-gray-50 hover:bg-gray-100 transition-colors"
                >
                  <span className="text-sm font-medium text-gray-700 flex items-center">
                    <Search className="w-4 h-4 mr-2" />
                    调查过程追踪
                  </span>
                  {expandedTrace ? <ChevronUp className="w-4 h-4 text-gray-500" /> : <ChevronDown className="w-4 h-4 text-gray-500" />}
                </button>

                {expandedTrace && (
                  <div className="p-4 bg-white space-y-4 text-sm">
                    <div>
                      <span className="font-semibold text-gray-900 block mb-1">规划器 (Planner)</span>
                      <ul className="list-disc list-inside text-gray-600 pl-2">
                        {data.process_trace.planner_output.extracted_claims?.map((c, i) => (
                          <li key={i}>提取关键点: {c}</li>
                        ))}
                      </ul>
                    </div>
                    <div className="pt-2 border-t border-gray-100">
                      <span className="font-semibold text-gray-900 block mb-1">裁判 (Judge)</span>
                      <p className="text-gray-600 pl-2 italic">"{data.process_trace.judge_reasoning}"</p>
                    </div>
                  </div>
                )}
              </div>
            )}
          </Card>

          {/* Evidence */}
          <Card className="p-6">
            <h3 className="text-lg font-bold text-gray-900 mb-4">关键证据</h3>
            <div className="space-y-4">
              {data.evidence.map((item, idx) => (
                <div key={idx} className="flex items-start p-4 bg-gray-50 rounded-lg border border-gray-100">
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-medium text-gray-900">{item.source}</span>
                      <Badge variant={item.credibility === 'high' ? 'success' : item.credibility === 'medium' ? 'warning' : 'danger'}>
                        {item.credibility} 可信度
                      </Badge>
                    </div>
                    <p className="text-sm text-gray-600 mt-1">"{item.content}"</p>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>

        {/* Sidebar Info */}
        <div className="space-y-6">
          <Card className="p-6">
            <h3 className="text-sm font-bold text-gray-900 uppercase tracking-wider mb-4">上下文信息</h3>
            <div className="space-y-4">
              <div>
                <span className="text-xs text-gray-500 block">案件 ID</span>
                <span className="text-sm font-mono text-gray-900">{data.case_id}</span>
              </div>
              <div>
                <span className="text-xs text-gray-500 block">时间戳</span>
                <span className="text-sm text-gray-900">{new Date(data.timestamp).toLocaleString()}</span>
              </div>
              <div>
                <span className="text-xs text-gray-500 block">模式</span>
                <span className="text-sm text-gray-900">{data.mode === 'static' ? '静态' : '演化'}</span>
              </div>
              <div>
                <span className="text-xs text-gray-500 block">匹配质量</span>
                <span className="text-sm capitalize text-gray-900">{data.rule_match_quality}</span>
              </div>
            </div>
          </Card>

          <Card className="p-6">
            <h3 className="text-sm font-bold text-gray-900 uppercase tracking-wider mb-4 flex items-center">
              <BookOpen className="w-4 h-4 mr-2" />
              应用规则
            </h3>
            <div className="space-y-2">
              {data.used_rules.map((ruleId) => {
                const isExpanded = expandedRules.has(ruleId);
                const rule = ruleDetails.get(ruleId);
                const isLoading = loadingRules.has(ruleId);

                return (
                  <div key={ruleId} className="border border-gray-200 rounded-lg overflow-hidden">
                    <div
                      onClick={() => toggleRuleExpand(ruleId)}
                      className="flex items-center justify-between p-3 bg-gray-50 hover:bg-gray-100 transition-colors cursor-pointer"
                    >
                      <span className="font-mono text-sm text-gray-700">{ruleId}</span>
                      <div className="flex items-center gap-2">
                        {isLoading && <Loader2 className="w-3 h-3 text-gray-400 animate-spin" />}
                        {isExpanded ? (
                          <ChevronUp className="w-4 h-4 text-gray-500" />
                        ) : (
                          <ChevronDown className="w-4 h-4 text-gray-500" />
                        )}
                      </div>
                    </div>

                    {isExpanded && rule && (
                      <div className="p-4 bg-white border-t border-gray-200 space-y-3">
                        {/* Rule Type Badge */}
                        <div className="flex items-center gap-2">
                          <Badge variant={
                            rule.type === 'strategy' ? 'blue' :
                              rule.type === 'pitfall' ? 'warning' :
                                'neutral'
                          }>
                            {rule.type}
                          </Badge>
                          {rule.memory_type && (
                            <Badge variant={rule.memory_type === 'detection' ? 'danger' : 'success'}>
                              {rule.memory_type === 'detection' ? '检测记忆' : '信任记忆'}
                            </Badge>
                          )}
                        </div>

                        {/* Description */}
                        <div>
                          <div className="text-xs font-semibold text-gray-500 uppercase mb-1">描述</div>
                          <p className="text-sm text-gray-700">{rule.description}</p>
                        </div>

                        {/* Condition & Action */}
                        <div className="bg-gray-50 rounded-lg p-3 font-mono text-xs space-y-2">
                          <div>
                            <span className="text-purple-600 font-bold">IF</span>
                            <span className="text-gray-700 ml-2">{rule.condition}</span>
                          </div>
                          <div>
                            <span className="text-blue-600 font-bold">THEN</span>
                            <span className="text-gray-700 ml-2">{rule.action}</span>
                          </div>
                        </div>

                        {/* Metrics */}
                        <div className="grid grid-cols-2 gap-3 pt-2 border-t border-gray-100">
                          <div>
                            <div className="text-xs text-gray-500">置信度</div>
                            <div className="text-sm font-bold text-gray-900">
                              {Math.round(rule.confidence * 100)}%
                            </div>
                          </div>
                          <div>
                            <div className="text-xs text-gray-500">证据数</div>
                            <div className="text-sm font-bold text-gray-900">
                              {rule.evidence_count}
                            </div>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
            <Link to="/playbook" className="text-xs text-blue-600 hover:text-blue-800 mt-4 inline-block font-medium">
              在规则库中查看所有规则 &rarr;
            </Link>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default Result;
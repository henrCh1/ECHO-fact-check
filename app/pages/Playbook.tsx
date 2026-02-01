import React, { useEffect, useState } from 'react';
import { Layers, Shield, AlertTriangle, RefreshCw } from 'lucide-react';
import { Button, Card, Badge } from '../components/ui';
import { api } from '../services/api';
import { Rule, PlaybookStatus } from '../types';

const Playbook: React.FC = () => {
  const [stats, setStats] = useState<PlaybookStatus | null>(null);
  const [rules, setRules] = useState<{ detection_rules: Rule[], trust_rules: Rule[] } | null>(null);
  const [activeTab, setActiveTab] = useState<'detection' | 'trust'>('detection');

  useEffect(() => {
    Promise.all([api.getPlaybookStats(), api.getRules()]).then(([s, r]) => {
      setStats(s);
      setRules(r);
    });
  }, []);

  const currentRules = activeTab === 'detection' ? rules?.detection_rules : rules?.trust_rules;

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">规则库</h2>
          <p className="text-sm text-gray-500 mt-1">管理驱动事实核查引擎的逻辑</p>
        </div>
        <div className="flex items-center space-x-3">
           <span className="text-sm text-gray-500 bg-gray-100 px-3 py-1 rounded-full border border-gray-200">
             v{stats?.version.split('|')[0].split(':')[1] || '1.0'}
           </span>
           <Button variant="outline">
             <RefreshCw className="w-4 h-4 mr-2" />
             切换规则库
           </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div 
          onClick={() => setActiveTab('detection')}
          className={`cursor-pointer p-4 rounded-xl border transition-all ${
            activeTab === 'detection' ? 'bg-white border-blue-500 ring-1 ring-blue-500 shadow-sm' : 'bg-gray-50 border-gray-200 hover:bg-white'
          }`}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <div className="p-2 bg-blue-50 rounded-lg text-blue-600 mr-3">
                <AlertTriangle className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-semibold text-gray-900">检测记忆 (Detection)</h3>
                <p className="text-xs text-gray-500">用于识别虚假信息的规则</p>
              </div>
            </div>
            <span className="text-2xl font-bold text-gray-900">{stats?.detection_rules_count || 0}</span>
          </div>
        </div>

        <div 
          onClick={() => setActiveTab('trust')}
          className={`cursor-pointer p-4 rounded-xl border transition-all ${
            activeTab === 'trust' ? 'bg-white border-green-500 ring-1 ring-green-500 shadow-sm' : 'bg-gray-50 border-gray-200 hover:bg-white'
          }`}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <div className="p-2 bg-green-50 rounded-lg text-green-600 mr-3">
                <Shield className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-semibold text-gray-900">信任记忆 (Trust)</h3>
                <p className="text-xs text-gray-500">用于验证真实性的规则</p>
              </div>
            </div>
            <span className="text-2xl font-bold text-gray-900">{stats?.trust_rules_count || 0}</span>
          </div>
        </div>
      </div>

      <div className="space-y-4">
        {currentRules?.map((rule) => (
          <Card key={rule.rule_id} className="p-5 hover:shadow-md transition-shadow">
            <div className="flex items-start justify-between">
              <div className="space-y-2">
                <div className="flex items-center space-x-2">
                   <h4 className="text-lg font-semibold text-gray-900">{rule.rule_id}</h4>
                   <Badge variant={rule.type === 'strategy' ? 'blue' : rule.type === 'pitfall' ? 'warning' : 'neutral'}>
                     {rule.type}
                   </Badge>
                </div>
                <p className="text-sm text-gray-600">{rule.description}</p>
                
                <div className="mt-4 p-3 bg-gray-50 rounded-lg font-mono text-xs text-gray-700 border border-gray-200">
                  <div className="mb-1"><span className="text-purple-600 font-bold">IF</span> {rule.condition}</div>
                  <div><span className="text-blue-600 font-bold">THEN</span> {rule.action}</div>
                </div>
              </div>

              <div className="text-right space-y-1">
                <div className="text-xs text-gray-500">置信度</div>
                <div className="font-bold text-gray-900">{Math.round(rule.confidence * 100)}%</div>
                <div className="text-xs text-gray-500 mt-2">证据数</div>
                <div className="font-bold text-gray-900">{rule.evidence_count}</div>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
};

export default Playbook;
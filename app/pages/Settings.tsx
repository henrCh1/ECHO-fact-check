import React, { useState } from 'react';
import { Upload, Play, Database, Check, Cpu, Save } from 'lucide-react';
import { Button, Card, InputLabel, ProgressBar } from '../components/ui';
import { api } from '../services/api';

const Settings: React.FC = () => {
  const [warmupStatus, setWarmupStatus] = useState<'idle' | 'running' | 'completed' | 'error'>('idle');
  const [progress, setProgress] = useState(0);
  const [modelName, setModelName] = useState('gemini-2.5-flash');
  const [taskId, setTaskId] = useState<string | null>(null);
  const [outputName, setOutputName] = useState('custom_playbook_v1');
  const [rulesGenerated, setRulesGenerated] = useState(0);

  const handleStartWarmup = async () => {
    setWarmupStatus('running');
    setProgress(0);

    try {
      // Start warmup task
      const task = await api.startWarmup({
        output_playbook_name: outputName,
      });
      setTaskId(task.task_id);

      // Poll for progress
      const pollInterval = setInterval(async () => {
        try {
          const status = await api.getWarmupStatus(task.task_id);
          const progressPercent = status.total_cases > 0
            ? Math.round((status.processed_cases / status.total_cases) * 100)
            : 0;
          setProgress(progressPercent);
          setRulesGenerated(status.rules_generated);

          if (status.status === 'completed') {
            clearInterval(pollInterval);
            setWarmupStatus('completed');
          } else if (status.status === 'failed') {
            clearInterval(pollInterval);
            setWarmupStatus('error');
          }
        } catch (err) {
          clearInterval(pollInterval);
          setWarmupStatus('error');
        }
      }, 2000);
    } catch (err) {
      setWarmupStatus('error');
      alert('启动预热失败: ' + (err instanceof Error ? err.message : '未知错误'));
    }
  };

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-900">系统设置</h2>

      {/* Model Configuration */}
      <Card className="p-6">
        <div className="flex items-center space-x-3 mb-6 pb-4 border-b border-gray-100">
          <div className="p-2 bg-blue-50 rounded-lg text-blue-600">
            <Cpu className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-gray-900">模型配置</h3>
            <p className="text-sm text-gray-500">配置底层大语言模型参数。</p>
          </div>
        </div>

        <div className="space-y-6">
          <div>
            <InputLabel>模型名称 (Gemini Version)</InputLabel>
            <input
              type="text"
              className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-gray-900 focus:border-gray-900 sm:text-sm"
              value={modelName}
              onChange={(e) => setModelName(e.target.value)}
              placeholder="e.g. gemini-2.5-flash"
            />
            <p className="mt-1 text-xs text-gray-500">推荐使用: gemini-2.5-flash, gemini-3-pro-preview</p>
          </div>

          <div className="pt-2 flex justify-end">
            <Button className="w-full sm:w-auto">
              <Save className="w-4 h-4 mr-2" />
              保存配置
            </Button>
          </div>
        </div>
      </Card>

      {/* Warmup Configuration */}
      <Card className="p-6">
        <div className="flex items-center space-x-3 mb-6 pb-4 border-b border-gray-100">
          <div className="p-2 bg-amber-50 rounded-lg text-amber-600">
            <Database className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-gray-900">知识库预热 (Warmup)</h3>
            <p className="text-sm text-gray-500">使用标注数据集训练系统以生成初始规则。</p>
          </div>
        </div>

        <div className="space-y-6">
          <div>
            <InputLabel>数据集来源</InputLabel>
            <div className="mt-2 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-md hover:border-gray-400 transition-colors cursor-pointer bg-gray-50">
              <div className="space-y-1 text-center">
                <Upload className="mx-auto h-12 w-12 text-gray-400" />
                <div className="flex text-sm text-gray-600">
                  <span className="relative cursor-pointer bg-white rounded-md font-medium text-blue-600 hover:text-blue-500 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-blue-500 px-1">
                    上传文件
                  </span>
                  <p className="pl-1">或拖拽至此</p>
                </div>
                <p className="text-xs text-gray-500">支持最大 10MB 的 CSV (必需列: Statement, Rating, Full_Analysis)</p>
              </div>
            </div>
          </div>

          <div>
            <InputLabel>输出规则库名称</InputLabel>
            <input
              type="text"
              className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-gray-900 focus:border-gray-900 sm:text-sm"
              value={outputName}
              onChange={(e) => setOutputName(e.target.value)}
              placeholder="custom_playbook_v1"
            />
          </div>

          {warmupStatus === 'running' && (
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">正在生成规则...</span>
                <span className="font-bold">{progress}%</span>
              </div>
              <ProgressBar value={progress} color="bg-amber-500" />
            </div>
          )}

          {warmupStatus === 'completed' && (
            <div className="p-4 bg-green-50 rounded-lg flex items-center text-green-700">
              <Check className="w-5 h-5 mr-2" />
              预热成功。已生成 15 条新规则。
            </div>
          )}

          <div className="pt-4 flex justify-end">
            <Button
              onClick={handleStartWarmup}
              disabled={warmupStatus === 'running'}
              className="w-full sm:w-auto"
            >
              <Play className="w-4 h-4 mr-2" />
              开始预热流程
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default Settings;
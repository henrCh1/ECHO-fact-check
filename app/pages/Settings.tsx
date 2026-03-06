import React, { useEffect, useState } from 'react';
import { Upload, Play, Database, Check, Cpu, Save, KeyRound } from 'lucide-react';
import { Button, Card, InputLabel, ProgressBar, Badge } from '../components/ui';
import { api } from '../services/api';

const Settings: React.FC = () => {
  const [warmupStatus, setWarmupStatus] = useState<'idle' | 'running' | 'completed' | 'error'>('idle');
  const [progress, setProgress] = useState(0);
  const [modelName, setModelName] = useState('gemini-3-flash-preview');
  const [apiKey, setApiKey] = useState('');
  const [apiKeyConfigured, setApiKeyConfigured] = useState(false);
  const [isSavingSettings, setIsSavingSettings] = useState(false);
  const [taskId, setTaskId] = useState<string | null>(null);
  const [outputName, setOutputName] = useState('custom_playbook_v1');
  const [rulesGenerated, setRulesGenerated] = useState(0);

  useEffect(() => {
    loadRuntimeSettings();
  }, []);

  const loadRuntimeSettings = async () => {
    try {
      const settings = await api.getRuntimeSettings();
      setModelName(settings.gemini_model || 'gemini-3-flash-preview');
      setApiKeyConfigured(settings.google_api_key_configured);
    } catch (error) {
      console.error('Failed to load runtime settings', error);
    }
  };

  const handleSaveSettings = async () => {
    setIsSavingSettings(true);
    try {
      const settings = await api.updateRuntimeSettings({
        google_api_key: apiKey.trim() || undefined,
        gemini_model: modelName.trim() || 'gemini-3-flash-preview',
      });
      setApiKey('');
      setModelName(settings.gemini_model);
      setApiKeyConfigured(settings.google_api_key_configured);
      alert('运行时配置已保存并生效。');
    } catch (error) {
      alert('保存配置失败: ' + (error instanceof Error ? error.message : '未知错误'));
    } finally {
      setIsSavingSettings(false);
    }
  };

  const handleStartWarmup = async () => {
    setWarmupStatus('running');
    setProgress(0);

    try {
      const task = await api.startWarmup({
        output_playbook_name: outputName,
      });
      setTaskId(task.task_id);

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
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">系统设置</h2>
        <Badge variant="blue">v2.0.0</Badge>
      </div>

      <Card className="p-6">
        <div className="flex items-center space-x-3 mb-6 pb-4 border-b border-gray-100">
          <div className="p-2 bg-blue-50 rounded-lg text-blue-600">
            <Cpu className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-gray-900">Gemini 运行时配置</h3>
            <p className="text-sm text-gray-500">从前端填写 API Key 和默认模型，保存后立即作用于后端。</p>
          </div>
        </div>

        <div className="space-y-6">
          <div>
            <InputLabel>Gemini API Key</InputLabel>
            <div className="relative mt-1">
              <KeyRound className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
              <input
                type="password"
                className="block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 pl-10 focus:outline-none focus:ring-gray-900 focus:border-gray-900 sm:text-sm"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder={apiKeyConfigured ? '已配置 API Key，如需更换请重新输入' : '输入 Gemini API Key'}
              />
            </div>
            <div className="mt-2 flex items-center gap-2">
              <Badge variant={apiKeyConfigured ? 'success' : 'warning'}>
                {apiKeyConfigured ? '已配置' : '未配置'}
              </Badge>
              <span className="text-xs text-gray-500">出于安全考虑，已保存的密钥不会回显。</span>
            </div>
          </div>

          <div>
            <InputLabel>模型名称 (Gemini Model)</InputLabel>
            <input
              type="text"
              className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-gray-900 focus:border-gray-900 sm:text-sm"
              value={modelName}
              onChange={(e) => setModelName(e.target.value)}
              placeholder="gemini-3-flash-preview"
            />
            <p className="mt-1 text-xs text-gray-500">默认模型已调整为 `gemini-3-flash-preview`。</p>
          </div>

          <div className="pt-2 flex justify-end">
            <Button className="w-full sm:w-auto" onClick={handleSaveSettings} disabled={isSavingSettings}>
              <Save className="w-4 h-4 mr-2" />
              {isSavingSettings ? '保存中...' : '保存配置'}
            </Button>
          </div>
        </div>
      </Card>

      <Card className="p-6">
        <div className="flex items-center space-x-3 mb-6 pb-4 border-b border-gray-100">
          <div className="p-2 bg-amber-50 rounded-lg text-amber-600">
            <Database className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-gray-900">知识库预热 (Warmup)</h3>
            <p className="text-sm text-gray-500">使用标注数据集训练系统并生成初始规则。</p>
          </div>
        </div>

        <div className="space-y-6">
          <div>
            <InputLabel>数据集来源</InputLabel>
            <div className="mt-2 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-md hover:border-gray-400 transition-colors cursor-pointer bg-gray-50">
              <div className="space-y-1 text-center">
                <Upload className="mx-auto h-12 w-12 text-gray-400" />
                <div className="flex text-sm text-gray-600">
                  <span className="relative cursor-pointer bg-white rounded-md font-medium text-blue-600 hover:text-blue-500 focus-within:outline-none px-1">
                    上传文件
                  </span>
                  <p className="pl-1">或拖拽至此</p>
                </div>
                <p className="text-xs text-gray-500">支持最大 10MB 的 CSV，需要列: Statement, Rating, Full_Analysis</p>
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
            <div className="p-4 bg-green-50 rounded-lg flex items-center justify-between text-green-700">
              <div className="flex items-center">
                <Check className="w-5 h-5 mr-2" />
                预热成功，已生成 {rulesGenerated} 条规则。
              </div>
              {taskId && <span className="text-xs font-mono">{taskId}</span>}
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

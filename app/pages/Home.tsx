import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, UploadCloud, FileText, Zap, BrainCircuit, Loader2 } from 'lucide-react';
import { Button, Card, InputLabel } from '../components/ui';
import { api } from '../services/api';

const Home: React.FC = () => {
  const navigate = useNavigate();
  const [claim, setClaim] = useState('');
  const [mode, setMode] = useState<'static' | 'evolving'>('static');
  const [isLoading, setIsLoading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<string | null>(null);

  const [verificationProgress, setVerificationProgress] = useState({
    step: 0,
    message: '',
    show: false
  });

  const verificationSteps = [
    { name: '提取关键声明', duration: 2000 },
    { name: '搜集证据', duration: 4000 },
    { name: '分析判断', duration: 3000 },
    { name: '生成报告', duration: 1500 },
    ...(mode === 'evolving' ? [{ name: '规则演化', duration: 2000 }] : [])
  ];

  const handleVerify = async () => {
    if (!claim.trim()) return;
    setIsLoading(true);
    setVerificationProgress({ step: 0, message: verificationSteps[0].name, show: true });

    // Simulate progress through steps
    let currentStep = 0;
    const progressInterval = setInterval(() => {
      currentStep++;
      if (currentStep < verificationSteps.length) {
        setVerificationProgress({
          step: currentStep,
          message: verificationSteps[currentStep].name,
          show: true
        });
      }
    }, 2500);

    try {
      const response = await api.verify(claim, mode);
      clearInterval(progressInterval);
      setVerificationProgress({ step: verificationSteps.length, message: '完成', show: true });

      // Brief delay before navigation to show completion
      setTimeout(() => {
        navigate(`/result/${response.case_id}`, { state: { data: response } });
      }, 500);
    } catch (error) {
      clearInterval(progressInterval);
      setVerificationProgress({ step: 0, message: '', show: false });
      console.error("Verification failed", error);
      alert("核查失败: " + (error instanceof Error ? error.message : "未知错误"));
    } finally {
      setIsLoading(false);
    }
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleFileUpload = async (file: File) => {
    if (!file.name.endsWith('.csv')) {
      alert("请上传 CSV 文件");
      return;
    }

    setUploadStatus("正在上传...");
    try {
      const task = await api.uploadBatch(file, mode);
      setUploadStatus(`任务已创建: ${task.task_id}`);
      // Navigate to history or show task status
      alert(`批量任务已开始! 任务ID: ${task.task_id}\n请在历史记录中查看进度`);
    } catch (error) {
      setUploadStatus(null);
      alert("上传失败: " + (error instanceof Error ? error.message : "未知错误"));
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


  return (
    <div className="space-y-8">
      <div className="text-center max-w-2xl mx-auto pt-8 pb-4">
        <h2 className="text-3xl font-bold text-gray-900 sm:text-4xl">AI 事实核查系统</h2>
        <p className="mt-4 text-lg text-gray-500">
          在下方输入声明或上传 CSV 进行批量处理，选择演化模式系统可从新模式中学习。
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        {/* Main Input Area */}
        <div className="md:col-span-2 space-y-6">
          <Card className="p-6">
            <div className="flex items-center justify-between mb-4">
              <InputLabel>待核查声明</InputLabel>
              <div className="flex bg-gray-100 rounded-lg p-1">
                <button
                  onClick={() => setMode('static')}
                  className={`px-3 py-1.5 text-xs font-medium rounded-md transition-all ${mode === 'static' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-900'
                    }`}
                >
                  <div className="flex items-center">
                    <Zap className="w-3 h-3 mr-1.5" />
                    静态模式
                  </div>
                </button>
                <button
                  onClick={() => setMode('evolving')}
                  className={`px-3 py-1.5 text-xs font-medium rounded-md transition-all ${mode === 'evolving' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-900'
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
              placeholder="例如：根据最新报道，X 国上个月的通货膨胀率下降了 50%..."
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

              {/* Progress Indicator */}
              {verificationProgress.show && (
                <div className="mt-4 p-4 bg-blue-50 rounded-lg border border-blue-100">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-blue-900">
                      {verificationProgress.message}
                    </span>
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
                        className={`text-xs px-2 py-1 rounded ${idx < verificationProgress.step
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

        {/* Batch Upload Area */}
        <div className="md:col-span-1">
          <Card className="h-full p-6 flex flex-col">
            <InputLabel>批量核查</InputLabel>
            <div
              className={`relative flex-1 mt-4 border-2 border-dashed rounded-xl flex flex-col items-center justify-center p-6 text-center transition-colors ${dragActive ? 'border-gray-900 bg-gray-50' : 'border-gray-200 hover:border-gray-300'
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
            <div className="mt-4">
              <div className="flex items-start p-3 text-xs text-blue-700 bg-blue-50 rounded-lg">
                <FileText className="w-4 h-4 mr-2 mt-0.5 flex-shrink-0" />
                <p>请确保 CSV 包含 "Statement" 或 "Claim" 列。</p>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default Home;
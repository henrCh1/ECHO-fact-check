import React, { useEffect, useState } from 'react';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from 'recharts';
import { Card } from '../components/ui';
import { api } from '../services/api';
import { SystemStats } from '../types';

const Stats: React.FC = () => {
  const [stats, setStats] = useState<SystemStats | null>(null);

  useEffect(() => {
    api.getStats().then(setStats);
  }, []);

  if (!stats) return <div className="p-8 text-center">正在加载统计数据...</div>;

  const pieData = [
    { name: 'True (真)', value: stats.verification.true_count },
    { name: 'False (假)', value: stats.verification.false_count },
  ];

  const COLORS = ['#22c55e', '#ef4444'];

  const barData = [
    { name: '静态模式', count: stats.verification.static_mode_count },
    { name: '演化模式', count: stats.verification.evolving_mode_count },
  ];

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-900">系统分析</h2>
      
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="p-4 border-l-4 border-l-blue-500">
          <div className="text-xs text-gray-500 uppercase font-medium">总核查次数</div>
          <div className="text-2xl font-bold text-gray-900 mt-1">{stats.verification.total_verifications}</div>
        </Card>
        <Card className="p-4 border-l-4 border-l-purple-500">
          <div className="text-xs text-gray-500 uppercase font-medium">平均置信度</div>
          <div className="text-2xl font-bold text-gray-900 mt-1">{(stats.verification.avg_confidence * 100).toFixed(1)}%</div>
        </Card>
        <Card className="p-4 border-l-4 border-l-green-500">
          <div className="text-xs text-gray-500 uppercase font-medium">结果为真 (True)</div>
          <div className="text-2xl font-bold text-gray-900 mt-1">{stats.verification.true_count}</div>
        </Card>
        <Card className="p-4 border-l-4 border-l-red-500">
          <div className="text-xs text-gray-500 uppercase font-medium">结果为假 (False)</div>
          <div className="text-2xl font-bold text-gray-900 mt-1">{stats.verification.false_count}</div>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="p-6 h-80">
          <h3 className="text-sm font-bold text-gray-900 mb-4">结论分布</h3>
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={80}
                paddingAngle={5}
                dataKey="value"
              >
                {pieData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </Card>

        <Card className="p-6 h-80">
          <h3 className="text-sm font-bold text-gray-900 mb-4">模式使用情况</h3>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={barData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" horizontal={false} />
              <XAxis type="number" />
              <YAxis dataKey="name" type="category" width={100} tick={{fontSize: 12}} />
              <Tooltip cursor={{fill: '#f9fafb'}} />
              <Bar dataKey="count" fill="#3b82f6" radius={[0, 4, 4, 0]} barSize={20} />
            </BarChart>
          </ResponsiveContainer>
        </Card>
      </div>
    </div>
  );
};

export default Stats;
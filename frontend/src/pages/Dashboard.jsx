import { useSelector, useDispatch } from 'react-redux';
import { useEffect } from 'react';
import { Link } from 'react-router-dom';
import { FileText, Upload, ShieldCheck, TrendingUp } from 'lucide-react';
import { contractService } from '../services/contractService';
import { analysisService } from '../services/analysisService';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import Badge from '../components/ui/Badge';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';

function Dashboard() {
  const { user } = useSelector(state => state.auth);

  // Mock data
  const stats = [
    { label: 'Total Contracts', value: '24', icon: FileText, color: 'blue' },
    { label: 'High Risk', value: '3', icon: ShieldCheck, color: 'red' },
    { label: 'Pending Review', value: '7', icon: Upload, color: 'yellow' },
    { label: 'AI Accuracy', value: '94%', icon: TrendingUp, color: 'green' },
  ];

  const riskData = [
    { name: 'Low Risk', value: 15, color: '#10b981' },
    { name: 'Medium Risk', value: 6, color: '#f59e0b' },
    { name: 'High Risk', value: 3, color: '#ef4444' },
  ];

  const recentActivity = [
    { id: 1, action: 'Contract uploaded', contract: 'Employment Agreement', time: '2 hours ago', risk: 'low' },
    { id: 2, action: 'Analysis completed', contract: 'NDA Document', time: '5 hours ago', risk: 'medium' },
    { id: 3, action: 'Signature pending', contract: 'Service Contract', time: '1 day ago', risk: 'high' },
  ];

  return (
    <div className="space-y-10">
      {/* Header */}
      <div>
        <h1 className="text-4xl md:text-5xl font-bold mb-3" style={{ color: 'var(--color-text-primary)' }}>Welcome back, {user?.name || 'User'}! 👋</h1>
        <p className="text-xl" style={{ color: 'var(--color-text-tertiary)' }}>
          Here&apos;s what&apos;s happening with your contracts today.
        </p>
      </div>

      {/* Stats Grid - Enhanced Bento */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, index) => {
          const Icon = stat.icon;
          const gradients = {
            blue: 'from-[var(--color-primary-500)] to-[var(--color-accent-blue)]',
            red: 'from-red-500 to-red-600',
            yellow: 'from-amber-500 to-orange-600',
            green: 'from-emerald-500 to-green-600',
          };
          
          return (
            <Card key={index} hover className="group">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <p className="label-text mb-3 uppercase tracking-wider">{stat.label}</p>
                  <p className="text-4xl font-bold mb-1">{stat.value}</p>
                  <div className="flex items-center gap-1 text-xs font-semibold" style={{ color: 'var(--color-success)' }}>
                    <TrendingUp className="w-3 h-3" />
                    <span>+12% this month</span>
                  </div>
                </div>
                <div className={`w-16 h-16 rounded-2xl flex items-center justify-center bg-linear-to-br ${gradients[stat.color]} shadow-lg group-hover:scale-110 transition-transform`}>
                  <Icon className="w-8 h-8" style={{ color: 'white' }} />
                </div>
              </div>
            </Card>
          );
        })}
      </div>

      {/* Charts and Activity - Bento Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Risk Summary Chart */}
        <Card>
          <h2 className="text-2xl font-bold mb-6">Risk Summary</h2>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={riskData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {riskData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </Card>

        {/* Recent Activity */}
        <Card>
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold">Recent Activity</h2>
            <Link to="/profile">
              <Button variant="outline" size="sm">View All</Button>
            </Link>
          </div>
          <div className="space-y-3">
            {recentActivity.map((activity) => (
              <div 
                key={activity.id} 
                className="flex items-start justify-between p-4 rounded-xl smooth-transition hover:bg-(--color-neutral-50)"
                style={{ border: 'var(--border-thin) solid var(--color-neutral-200)' }}
              >
                <div className="flex-1">
                  <p className="font-semibold mb-1">{activity.contract}</p>
                  <p className="text-sm mb-1" style={{ color: 'var(--color-neutral-600)' }}>
                    {activity.action}
                  </p>
                  <p className="text-xs" style={{ color: 'var(--color-neutral-500)' }}>
                    {activity.time}
                  </p>
                </div>
                <Badge variant={activity.risk}>
                  {activity.risk}
                </Badge>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* Quick Actions - Bento Grid */}
      <Card>
        <h2 className="text-2xl font-bold mb-6">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Link to="/upload" className="block group">
            <div className="p-6 rounded-xl smooth-transition text-center hover:bg-linear-to-br hover:from-(--color-primary-50) hover:to-(--color-primary-100)" style={{ border: '2px dashed var(--color-neutral-300)' }}>
              <div className="w-14 h-14 mx-auto mb-4 rounded-2xl bg-linear-to-br from-(--color-primary-100) to-(--color-primary-200) flex items-center justify-center group-hover:scale-110 smooth-transition">
                <Upload className="w-7 h-7" style={{ color: 'var(--color-primary-600)' }} />
              </div>
              <p className="font-semibold">Upload New Contract</p>
            </div>
          </Link>
          <Link to="/generate" className="block group">
            <div className="p-6 rounded-xl smooth-transition text-center hover:bg-linear-to-br hover:from-(--color-primary-50) hover:to-(--color-primary-100)" style={{ border: '2px dashed var(--color-neutral-300)' }}>
              <div className="w-14 h-14 mx-auto mb-4 rounded-2xl bg-linear-to-br from-(--color-primary-100) to-(--color-primary-200) flex items-center justify-center group-hover:scale-110 smooth-transition">
                <FileText className="w-7 h-7" style={{ color: 'var(--color-primary-600)' }} />
              </div>
              <p className="font-semibold">Generate Contract</p>
            </div>
          </Link>
          <Link to="/compare" className="block group">
            <div className="p-6 rounded-xl smooth-transition text-center hover:bg-linear-to-br hover:from-(--color-primary-50) hover:to-(--color-primary-100)" style={{ border: '2px dashed var(--color-neutral-300)' }}>
              <div className="w-14 h-14 mx-auto mb-4 rounded-2xl bg-linear-to-br from-(--color-primary-100) to-(--color-primary-200) flex items-center justify-center group-hover:scale-110 smooth-transition">
                <ShieldCheck className="w-7 h-7" style={{ color: 'var(--color-primary-600)' }} />
              </div>
              <p className="font-semibold">Compare Contracts</p>
            </div>
          </Link>
        </div>
      </Card>
    </div>
  );
}

export default Dashboard;
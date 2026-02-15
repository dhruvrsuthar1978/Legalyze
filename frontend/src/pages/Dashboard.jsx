import { useEffect, useMemo, useState } from 'react';
import { useSelector } from 'react-redux';
import { Link } from 'react-router-dom';
import { FileText, Upload, ShieldCheck, TrendingUp } from 'lucide-react';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';
import { contractService } from '../services/contractService';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import Badge from '../components/ui/Badge';

function Dashboard() {
  const { user } = useSelector((state) => state.auth);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState(null);
  const [contracts, setContracts] = useState([]);

  useEffect(() => {
    let mounted = true;

    (async () => {
      try {
        const [statsRes, contractsRes] = await Promise.all([
          contractService.getContractStats(),
          contractService.getContracts(0, 6),
        ]);
        if (!mounted) return;
        setStats(statsRes);
        setContracts(contractsRes.contracts || []);
      } catch {
        if (!mounted) return;
        setStats(null);
        setContracts([]);
      } finally {
        if (mounted) setLoading(false);
      }
    })();

    return () => {
      mounted = false;
    };
  }, []);

  const statCards = useMemo(() => {
    const total = stats?.total_contracts ?? contracts.length;
    const high = stats?.total_high_risk_clauses ?? 0;
    const pending = stats?.by_status?.pending ?? contracts.filter((c) => c.analysis_status === 'pending').length;
    const avg = stats?.avg_risk_score ?? 0;
    return [
      { label: 'Total Contracts', value: String(total), icon: FileText, color: 'blue' },
      { label: 'High Risk Clauses', value: String(high), icon: ShieldCheck, color: 'red' },
      { label: 'Pending Analysis', value: String(pending), icon: Upload, color: 'yellow' },
      { label: 'Avg Risk Score', value: `${Math.round(avg)}%`, icon: TrendingUp, color: 'green' },
    ];
  }, [stats, contracts]);

  const riskData = useMemo(
    () => [
      { name: 'Low Risk', value: stats?.total_low_risk_clauses ?? 0, color: '#10b981' },
      { name: 'Medium Risk', value: stats?.total_medium_risk_clauses ?? 0, color: '#f59e0b' },
      { name: 'High Risk', value: stats?.total_high_risk_clauses ?? 0, color: '#ef4444' },
    ],
    [stats]
  );

  return (
    <div className="space-y-10">
      <div>
        <h1 className="text-4xl md:text-5xl font-bold mb-3" style={{ color: 'var(--color-text-primary)' }}>
          Welcome back, {user?.name || 'User'}!
        </h1>
        <p className="text-xl" style={{ color: 'var(--color-text-tertiary)' }}>
          Here&apos;s your latest contract activity.
        </p>
      </div>

      {loading ? (
        <Card>
          <p style={{ color: 'var(--color-text-tertiary)' }}>Loading dashboard...</p>
        </Card>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {statCards.map((stat) => {
              const Icon = stat.icon;
              const gradients = {
                blue: 'from-[var(--color-primary-500)] to-[var(--color-accent-blue)]',
                red: 'from-red-500 to-red-600',
                yellow: 'from-amber-500 to-orange-600',
                green: 'from-emerald-500 to-green-600',
              };

              return (
                <Card key={stat.label}>
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="label-text mb-3 uppercase tracking-wider">{stat.label}</p>
                      <p className="text-4xl font-bold">{stat.value}</p>
                    </div>
                    <div className={`w-16 h-16 rounded-2xl flex items-center justify-center bg-linear-to-br ${gradients[stat.color]}`}>
                      <Icon className="w-8 h-8" style={{ color: 'white' }} />
                    </div>
                  </div>
                </Card>
              );
            })}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
            <Card>
              <h2 className="text-2xl font-bold mb-6">Risk Summary</h2>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie data={riskData} cx="50%" cy="50%" outerRadius={80} dataKey="value" labelLine={false}>
                    {riskData.map((entry) => (
                      <Cell key={entry.name} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </Card>

            <Card>
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-2xl font-bold">Recent Contracts</h2>
                <Link to="/profile">
                  <Button variant="outline" size="sm">View All</Button>
                </Link>
              </div>
              <div className="space-y-3">
                {contracts.length === 0 && (
                  <p style={{ color: 'var(--color-text-tertiary)' }}>No contracts yet.</p>
                )}
                {contracts.map((contract) => (
                  <Link
                    key={contract.id}
                    to={`/contract/${contract.id}`}
                    className="block p-4 rounded-xl hover:bg-[var(--color-neutral-50)]"
                    style={{ border: 'var(--border-thin) solid var(--color-neutral-200)' }}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="font-semibold">{contract.title || contract.filename}</p>
                        <p className="text-xs" style={{ color: 'var(--color-text-tertiary)' }}>
                          {new Date(contract.uploaded_at).toLocaleString()}
                        </p>
                      </div>
                      <Badge variant={contract.analysis_status === 'completed' ? 'success' : 'warning'}>
                        {contract.analysis_status}
                      </Badge>
                    </div>
                  </Link>
                ))}
              </div>
            </Card>
          </div>

          <Card>
            <h2 className="text-2xl font-bold mb-6">Quick Actions</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Link to="/upload" className="block">
                <div className="p-6 rounded-xl text-center" style={{ border: '2px dashed var(--color-neutral-300)' }}>
                  <Upload className="w-7 h-7 mx-auto mb-3" style={{ color: 'var(--color-primary-600)' }} />
                  <p className="font-semibold">Upload Contract</p>
                </div>
              </Link>
              <Link to="/generate" className="block">
                <div className="p-6 rounded-xl text-center" style={{ border: '2px dashed var(--color-neutral-300)' }}>
                  <FileText className="w-7 h-7 mx-auto mb-3" style={{ color: 'var(--color-primary-600)' }} />
                  <p className="font-semibold">Generate Draft</p>
                </div>
              </Link>
              <Link to="/compare" className="block">
                <div className="p-6 rounded-xl text-center" style={{ border: '2px dashed var(--color-neutral-300)' }}>
                  <ShieldCheck className="w-7 h-7 mx-auto mb-3" style={{ color: 'var(--color-primary-600)' }} />
                  <p className="font-semibold">Compare Contracts</p>
                </div>
              </Link>
            </div>
          </Card>
        </>
      )}
    </div>
  );
}

export default Dashboard;

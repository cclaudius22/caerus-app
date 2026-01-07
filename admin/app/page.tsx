'use client';

export const dynamic = 'force-dynamic';

import { useEffect, useState } from 'react';
import AdminLayout from '@/components/AdminLayout';
import { getDashboardStats, getTalentStats } from '@/lib/api';
import { Users, Briefcase, TrendingUp, UserCheck, AlertCircle } from 'lucide-react';

interface DashboardStats {
  users: {
    founders: number;
    investors: number;
    talent: number;
    total: number;
  };
  pending_talent: number;
  startups: number;
}

interface TalentStats {
  pending: number;
  approved: number;
  rejected: number;
  total: number;
}

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [talentStats, setTalentStats] = useState<TalentStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      const [dashboardData, talentData] = await Promise.all([
        getDashboardStats(),
        getTalentStats(),
      ]);
      setStats(dashboardData);
      setTalentStats(talentData);
    } catch (err: any) {
      setError(err.message || 'Failed to load stats');
    } finally {
      setLoading(false);
    }
  };

  return (
    <AdminLayout>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-600">Overview of Caerus platform</p>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-3 text-red-700">
          <AlertCircle className="w-5 h-5" />
          {error}
        </div>
      )}

      {loading ? (
        <div className="text-gray-500">Loading stats...</div>
      ) : stats && (
        <>
          {/* Main Stats */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <StatCard
              title="Total Users"
              value={stats.users.total}
              icon={Users}
              color="bg-blue-500"
            />
            <StatCard
              title="Founders"
              value={stats.users.founders}
              icon={Briefcase}
              color="bg-green-500"
            />
            <StatCard
              title="Investors"
              value={stats.users.investors}
              icon={TrendingUp}
              color="bg-purple-500"
            />
            <StatCard
              title="Talent"
              value={stats.users.talent}
              icon={UserCheck}
              color="bg-orange-500"
            />
          </div>

          {/* Pending Actions */}
          {stats.pending_talent > 0 && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 mb-8">
              <h2 className="text-lg font-semibold text-yellow-800 mb-2">
                Action Required
              </h2>
              <p className="text-yellow-700">
                {stats.pending_talent} talent application{stats.pending_talent !== 1 ? 's' : ''} pending review
              </p>
              <a
                href="/users/talent?status=pending"
                className="inline-block mt-3 text-yellow-800 font-medium hover:underline"
              >
                Review Applications →
              </a>
            </div>
          )}

          {/* Talent Breakdown */}
          {talentStats && (
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">
                Talent Applications
              </h2>
              <div className="grid grid-cols-3 gap-4">
                <div className="text-center p-4 bg-yellow-50 rounded-lg">
                  <div className="text-2xl font-bold text-yellow-600">
                    {talentStats.pending}
                  </div>
                  <div className="text-sm text-gray-600">Pending</div>
                </div>
                <div className="text-center p-4 bg-green-50 rounded-lg">
                  <div className="text-2xl font-bold text-green-600">
                    {talentStats.approved}
                  </div>
                  <div className="text-sm text-gray-600">Approved</div>
                </div>
                <div className="text-center p-4 bg-red-50 rounded-lg">
                  <div className="text-2xl font-bold text-red-600">
                    {talentStats.rejected}
                  </div>
                  <div className="text-sm text-gray-600">Rejected</div>
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </AdminLayout>
  );
}

function StatCard({
  title,
  value,
  icon: Icon,
  color,
}: {
  title: string;
  value: number;
  icon: any;
  color: string;
}) {
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center">
        <div className={`p-3 rounded-lg ${color}`}>
          <Icon className="w-6 h-6 text-white" />
        </div>
        <div className="ml-4">
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
        </div>
      </div>
    </div>
  );
}

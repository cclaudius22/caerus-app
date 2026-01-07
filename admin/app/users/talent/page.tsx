'use client';

import { useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import AdminLayout from '@/components/AdminLayout';
import { getTalent, approveTalent, rejectTalent } from '@/lib/api';
import { Search, ExternalLink, Check, X, MapPin } from 'lucide-react';

interface TalentProfile {
  id: string;
  user_id: string;
  email: string;
  avatar_url: string | null;
  full_name: string | null;
  status: 'pending' | 'approved' | 'rejected';
  applied_at: string;
  approved_at: string | null;
  job_title_seeking: string | null;
  skills: string[] | null;
  experience_level: string | null;
  compensation_type: string | null;
  linkedin_url: string | null;
  location: string | null;
  remote_preference: string | null;
  availability: string | null;
  profile_completed: boolean;
  onboarding_completed: boolean;
}

const STATUS_COLORS = {
  pending: 'bg-yellow-100 text-yellow-800',
  approved: 'bg-green-100 text-green-800',
  rejected: 'bg-red-100 text-red-800',
};

const EXPERIENCE_LABELS: Record<string, string> = {
  junior: 'Junior (0-2 yrs)',
  mid: 'Mid (3-5 yrs)',
  senior: 'Senior (6-9 yrs)',
  lead: 'Lead (10+ yrs)',
  executive: 'Executive',
};

export default function TalentPage() {
  const searchParams = useSearchParams();
  const initialStatus = searchParams.get('status') || '';

  const [talent, setTalent] = useState<TalentProfile[]>([]);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState(initialStatus);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  useEffect(() => {
    loadTalent();
  }, [search, statusFilter]);

  const loadTalent = async () => {
    setLoading(true);
    try {
      const data = await getTalent({
        search: search || undefined,
        status: statusFilter || undefined,
      });
      setTalent(data.talent);
      setTotal(data.total);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (profileId: string) => {
    setActionLoading(profileId);
    try {
      await approveTalent(profileId);
      loadTalent();
    } catch (err) {
      console.error(err);
      alert('Failed to approve talent');
    } finally {
      setActionLoading(null);
    }
  };

  const handleReject = async (profileId: string) => {
    const reason = prompt('Rejection reason (optional):');
    setActionLoading(profileId);
    try {
      await rejectTalent(profileId, reason || undefined);
      loadTalent();
    } catch (err) {
      console.error(err);
      alert('Failed to reject talent');
    } finally {
      setActionLoading(null);
    }
  };

  return (
    <AdminLayout>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Talent</h1>
        <p className="text-gray-600">{total} total talent profiles</p>
      </div>

      {/* Filters */}
      <div className="flex gap-4 mb-6">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by email or name..."
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
          />
        </div>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
        >
          <option value="">All Status</option>
          <option value="pending">Pending</option>
          <option value="approved">Approved</option>
          <option value="rejected">Rejected</option>
        </select>
      </div>

      {/* Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Talent
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Role Seeking
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Experience
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Applied
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {loading ? (
              <tr>
                <td colSpan={6} className="px-6 py-4 text-center text-gray-500">
                  Loading...
                </td>
              </tr>
            ) : talent.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-6 py-4 text-center text-gray-500">
                  No talent found
                </td>
              </tr>
            ) : (
              talent.map((profile) => (
                <tr key={profile.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4">
                    <div className="flex items-center">
                      {profile.avatar_url ? (
                        <img
                          src={profile.avatar_url}
                          alt=""
                          className="w-10 h-10 rounded-full object-cover"
                        />
                      ) : (
                        <div className="w-10 h-10 rounded-full bg-gray-200 flex items-center justify-center">
                          <span className="text-gray-500 text-sm">
                            {profile.full_name?.[0] || profile.email?.[0]?.toUpperCase() || '?'}
                          </span>
                        </div>
                      )}
                      <div className="ml-4">
                        <div className="text-sm font-medium text-gray-900">
                          {profile.full_name || 'No name'}
                        </div>
                        <div className="text-sm text-gray-500">{profile.email}</div>
                        {profile.location && (
                          <div className="text-xs text-gray-400 flex items-center mt-1">
                            <MapPin className="w-3 h-3 mr-1" />
                            {profile.location}
                          </div>
                        )}
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="text-sm text-gray-900">
                      {profile.job_title_seeking || '-'}
                    </div>
                    {profile.skills && profile.skills.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-1">
                        {profile.skills.slice(0, 3).map((skill) => (
                          <span
                            key={skill}
                            className="inline-flex px-2 py-0.5 text-xs bg-gray-100 text-gray-600 rounded"
                          >
                            {skill}
                          </span>
                        ))}
                        {profile.skills.length > 3 && (
                          <span className="text-xs text-gray-400">
                            +{profile.skills.length - 3}
                          </span>
                        )}
                      </div>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {profile.experience_level
                      ? EXPERIENCE_LABELS[profile.experience_level] || profile.experience_level
                      : '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${STATUS_COLORS[profile.status]}`}>
                      {profile.status.charAt(0).toUpperCase() + profile.status.slice(1)}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {new Date(profile.applied_at).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <div className="flex items-center gap-2">
                      {profile.linkedin_url && (
                        <a
                          href={profile.linkedin_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-blue-600 hover:text-blue-800 p-1"
                          title="LinkedIn"
                        >
                          <ExternalLink className="w-4 h-4" />
                        </a>
                      )}
                      {profile.status === 'pending' && (
                        <>
                          <button
                            onClick={() => handleApprove(profile.id)}
                            disabled={actionLoading === profile.id}
                            className="p-1 text-green-600 hover:text-green-800 hover:bg-green-50 rounded disabled:opacity-50"
                            title="Approve"
                          >
                            <Check className="w-5 h-5" />
                          </button>
                          <button
                            onClick={() => handleReject(profile.id)}
                            disabled={actionLoading === profile.id}
                            className="p-1 text-red-600 hover:text-red-800 hover:bg-red-50 rounded disabled:opacity-50"
                            title="Reject"
                          >
                            <X className="w-5 h-5" />
                          </button>
                        </>
                      )}
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </AdminLayout>
  );
}

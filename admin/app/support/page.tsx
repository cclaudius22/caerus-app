'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import AdminLayout from '@/components/AdminLayout';
import { getSupportTickets } from '@/lib/api';
import { MessageSquare, Clock, CheckCircle, AlertCircle } from 'lucide-react';

interface SupportTicket {
  id: string;
  user_id: string;
  user_email: string | null;
  subject: string;
  status: 'open' | 'resolved';
  created_at: string;
  updated_at: string;
  message_count: number;
  last_message: string | null;
  last_sender: string | null;
  has_unread: boolean;
}

const STATUS_COLORS = {
  open: 'bg-yellow-100 text-yellow-800',
  resolved: 'bg-green-100 text-green-800',
};

export default function SupportPage() {
  const [tickets, setTickets] = useState<SupportTicket[]>([]);
  const [total, setTotal] = useState(0);
  const [openCount, setOpenCount] = useState(0);
  const [statusFilter, setStatusFilter] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadTickets();
  }, [statusFilter]);

  const loadTickets = async () => {
    setLoading(true);
    try {
      const data = await getSupportTickets({
        status: statusFilter || undefined,
      });
      setTickets(data.tickets);
      setTotal(data.total);
      setOpenCount(data.open_count);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <AdminLayout>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Support Inbox</h1>
        <p className="text-gray-600">
          {openCount > 0 ? (
            <span className="text-yellow-600 font-medium">{openCount} open ticket{openCount !== 1 ? 's' : ''}</span>
          ) : (
            'No open tickets'
          )}
          {' '}&middot; {total} total
        </p>
      </div>

      {/* Filters */}
      <div className="mb-6">
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
        >
          <option value="">All Tickets</option>
          <option value="open">Open</option>
          <option value="resolved">Resolved</option>
        </select>
      </div>

      {/* Tickets List */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-gray-500">Loading...</div>
        ) : tickets.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            <MessageSquare className="w-12 h-12 mx-auto mb-4 text-gray-300" />
            <p>No support tickets yet</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {tickets.map((ticket) => (
              <Link
                key={ticket.id}
                href={`/support/${ticket.id}`}
                className="block p-4 hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      {ticket.has_unread && (
                        <span className="w-2 h-2 rounded-full bg-blue-500" />
                      )}
                      <h3 className="text-sm font-medium text-gray-900 truncate">
                        {ticket.subject}
                      </h3>
                    </div>
                    <p className="text-sm text-gray-500 truncate">
                      {ticket.user_email || 'Unknown user'}
                    </p>
                    {ticket.last_message && (
                      <p className="mt-1 text-sm text-gray-400 truncate">
                        {ticket.last_sender === 'admin' ? 'You: ' : ''}
                        {ticket.last_message}
                      </p>
                    )}
                  </div>
                  <div className="ml-4 flex flex-col items-end gap-2">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${STATUS_COLORS[ticket.status]}`}>
                      {ticket.status === 'open' ? (
                        <><Clock className="w-3 h-3 mr-1" /> Open</>
                      ) : (
                        <><CheckCircle className="w-3 h-3 mr-1" /> Resolved</>
                      )}
                    </span>
                    <span className="text-xs text-gray-400">
                      {new Date(ticket.updated_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </AdminLayout>
  );
}

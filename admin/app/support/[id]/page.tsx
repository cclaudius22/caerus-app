'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import AdminLayout from '@/components/AdminLayout';
import { getSupportTicket, replyToTicket, resolveTicket, reopenTicket } from '@/lib/api';
import { ArrowLeft, Send, CheckCircle, RotateCcw, User, Bot, Headphones } from 'lucide-react';

interface Message {
  id: string;
  sender_type: 'user' | 'admin' | 'ai';
  content: string;
  created_at: string;
}

interface Ticket {
  id: string;
  user_id: string;
  user_email: string | null;
  user_role: string | null;
  subject: string;
  status: 'open' | 'resolved';
  created_at: string;
  updated_at: string;
  messages: Message[];
}

export default function SupportTicketPage() {
  const params = useParams();
  const router = useRouter();
  const ticketId = params.id as string;

  const [ticket, setTicket] = useState<Ticket | null>(null);
  const [loading, setLoading] = useState(true);
  const [replyText, setReplyText] = useState('');
  const [sending, setSending] = useState(false);

  useEffect(() => {
    loadTicket();
  }, [ticketId]);

  const loadTicket = async () => {
    try {
      const data = await getSupportTicket(ticketId);
      setTicket(data.ticket);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSendReply = async () => {
    if (!replyText.trim() || sending) return;

    setSending(true);
    try {
      await replyToTicket(ticketId, replyText.trim());
      setReplyText('');
      loadTicket();
    } catch (err) {
      console.error(err);
      alert('Failed to send reply');
    } finally {
      setSending(false);
    }
  };

  const handleResolve = async () => {
    try {
      await resolveTicket(ticketId);
      loadTicket();
    } catch (err) {
      console.error(err);
      alert('Failed to resolve ticket');
    }
  };

  const handleReopen = async () => {
    try {
      await reopenTicket(ticketId);
      loadTicket();
    } catch (err) {
      console.error(err);
      alert('Failed to reopen ticket');
    }
  };

  const getSenderIcon = (senderType: string) => {
    switch (senderType) {
      case 'user':
        return <User className="w-5 h-5" />;
      case 'ai':
        return <Bot className="w-5 h-5" />;
      case 'admin':
        return <Headphones className="w-5 h-5" />;
      default:
        return <User className="w-5 h-5" />;
    }
  };

  const getSenderLabel = (senderType: string) => {
    switch (senderType) {
      case 'user':
        return 'User';
      case 'ai':
        return 'AI Assistant';
      case 'admin':
        return 'Support Team';
      default:
        return 'Unknown';
    }
  };

  return (
    <AdminLayout>
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={() => router.push('/support')}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h1 className="text-xl font-bold text-gray-900">
              {ticket?.subject || 'Loading...'}
            </h1>
            <p className="text-sm text-gray-500">
              {ticket?.user_email} &middot; {ticket?.user_role}
            </p>
          </div>
        </div>
        {ticket && (
          <div className="flex items-center gap-2">
            {ticket.status === 'open' ? (
              <button
                onClick={handleResolve}
                className="flex items-center gap-2 px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors"
              >
                <CheckCircle className="w-4 h-4" />
                Mark Resolved
              </button>
            ) : (
              <button
                onClick={handleReopen}
                className="flex items-center gap-2 px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors"
              >
                <RotateCcw className="w-4 h-4" />
                Reopen
              </button>
            )}
          </div>
        )}
      </div>

      {loading ? (
        <div className="text-center text-gray-500 py-12">Loading...</div>
      ) : ticket ? (
        <div className="bg-white rounded-lg shadow flex flex-col" style={{ height: 'calc(100vh - 220px)' }}>
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-6 space-y-4">
            {ticket.messages.map((message) => (
              <div
                key={message.id}
                className={`flex gap-3 ${message.sender_type === 'admin' ? 'flex-row-reverse' : ''}`}
              >
                <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                  message.sender_type === 'user' ? 'bg-gray-100 text-gray-600' :
                  message.sender_type === 'ai' ? 'bg-purple-100 text-purple-600' :
                  'bg-primary text-gray-900'
                }`}>
                  {getSenderIcon(message.sender_type)}
                </div>
                <div className={`max-w-[70%] ${message.sender_type === 'admin' ? 'text-right' : ''}`}>
                  <div className="text-xs text-gray-500 mb-1">
                    {getSenderLabel(message.sender_type)} &middot; {new Date(message.created_at).toLocaleString()}
                  </div>
                  <div className={`inline-block p-3 rounded-lg ${
                    message.sender_type === 'admin'
                      ? 'bg-primary text-gray-900'
                      : message.sender_type === 'ai'
                      ? 'bg-purple-50 text-gray-900'
                      : 'bg-gray-100 text-gray-900'
                  }`}>
                    <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Reply Input */}
          {ticket.status === 'open' && (
            <div className="border-t border-gray-200 p-4">
              <div className="flex gap-3">
                <textarea
                  value={replyText}
                  onChange={(e) => setReplyText(e.target.value)}
                  placeholder="Type your reply..."
                  className="flex-1 px-4 py-3 border border-gray-300 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                  rows={2}
                />
                <button
                  onClick={handleSendReply}
                  disabled={!replyText.trim() || sending}
                  className="px-4 py-2 bg-primary text-gray-900 rounded-lg hover:bg-opacity-90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Send className="w-5 h-5" />
                </button>
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="text-center text-gray-500 py-12">Ticket not found</div>
      )}
    </AdminLayout>
  );
}

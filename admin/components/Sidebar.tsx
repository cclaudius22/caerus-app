'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { LayoutDashboard, Users, Briefcase, TrendingUp, UserCheck, LogOut, MessageSquare } from 'lucide-react';
import { useAuth } from '@/lib/auth-context';

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Founders', href: '/users/founders', icon: Briefcase },
  { name: 'Investors', href: '/users/investors', icon: TrendingUp },
  { name: 'Talent', href: '/users/talent', icon: UserCheck },
  { name: 'Support', href: '/support', icon: MessageSquare },
];

export default function Sidebar() {
  const pathname = usePathname();
  const { user, signOut } = useAuth();

  return (
    <div className="flex flex-col w-64 bg-gray-900 min-h-screen">
      <div className="flex items-center h-16 px-4 bg-gray-800">
        <span className="text-xl font-bold text-primary">Caerus Admin</span>
      </div>

      <nav className="flex-1 px-2 py-4 space-y-1">
        {navigation.map((item) => {
          const isActive = pathname === item.href ||
            (item.href !== '/' && pathname.startsWith(item.href));

          return (
            <Link
              key={item.name}
              href={item.href}
              className={`flex items-center px-4 py-3 text-sm font-medium rounded-lg transition-colors ${
                isActive
                  ? 'bg-primary text-gray-900'
                  : 'text-gray-300 hover:bg-gray-800 hover:text-white'
              }`}
            >
              <item.icon className="w-5 h-5 mr-3" />
              {item.name}
            </Link>
          );
        })}
      </nav>

      <div className="px-2 py-4 border-t border-gray-800">
        <div className="px-4 py-2 text-sm text-gray-400 truncate">
          {user?.email}
        </div>
        <button
          onClick={signOut}
          className="flex items-center w-full px-4 py-3 text-sm font-medium text-gray-300 rounded-lg hover:bg-gray-800 hover:text-white transition-colors"
        >
          <LogOut className="w-5 h-5 mr-3" />
          Sign Out
        </button>
      </div>
    </div>
  );
}

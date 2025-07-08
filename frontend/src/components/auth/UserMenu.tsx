import React from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { LogOut, User } from 'lucide-react';

export const UserMenu: React.FC = () => {
  const { user, logout, isAuthenticated } = useAuth();

  if (!isAuthenticated || !user) {
    return null;
  }

  return (
    <div className="flex items-center gap-3 px-4 py-2 bg-neutral-700/50 rounded-lg border border-neutral-600">
      <div className="flex items-center gap-2">
        <div className="flex items-center justify-center w-8 h-8 bg-blue-600 rounded-full">
          <User className="h-4 w-4 text-white" />
        </div>
        <div className="flex flex-col">
          <span className="text-sm font-medium text-neutral-100">
            {user.username}
          </span>
          <span className="text-xs text-neutral-400">
            {user.email}
          </span>
        </div>
      </div>
      
      <Button
        onClick={logout}
        variant="ghost"
        size="sm"
        className="ml-auto text-neutral-400 hover:text-neutral-100 hover:bg-neutral-600"
      >
        <LogOut className="h-4 w-4" />
      </Button>
    </div>
  );
}; 
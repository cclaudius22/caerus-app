'use client';

import { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { User } from 'firebase/auth';
import { onAuthChange, signIn as firebaseSignIn, signOut as firebaseSignOut, getIdToken } from './firebase';
import { login, getMe, setAuthToken } from './api';

interface AuthContextType {
  user: User | null;
  backendUser: any | null;
  isLoading: boolean;
  isAdmin: boolean;
  signIn: (email: string, password: string) => Promise<void>;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [backendUser, setBackendUser] = useState<any | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAdmin, setIsAdmin] = useState(false);

  useEffect(() => {
    const unsubscribe = onAuthChange(async (firebaseUser) => {
      setUser(firebaseUser);

      if (firebaseUser) {
        try {
          const token = await firebaseUser.getIdToken();
          // Login to backend
          const response = await login(token);
          setAuthToken(response.token);

          // Get user profile
          const me = await getMe();
          setBackendUser(me);

          // Check if admin (email ends with @caerus.app)
          setIsAdmin(firebaseUser.email?.endsWith('@caerus.app') || false);
        } catch (error) {
          console.error('Auth error:', error);
          setBackendUser(null);
          setIsAdmin(false);
        }
      } else {
        setAuthToken(null);
        setBackendUser(null);
        setIsAdmin(false);
      }

      setIsLoading(false);
    });

    return () => unsubscribe();
  }, []);

  const signIn = async (email: string, password: string) => {
    await firebaseSignIn(email, password);
  };

  const signOut = async () => {
    await firebaseSignOut();
    setAuthToken(null);
    setBackendUser(null);
    setIsAdmin(false);
  };

  return (
    <AuthContext.Provider value={{ user, backendUser, isLoading, isAdmin, signIn, signOut }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}

import { initializeApp, getApps, FirebaseApp } from 'firebase/app';
import { getAuth, signInWithEmailAndPassword, signOut as firebaseSignOut, onAuthStateChanged, User, Auth } from 'firebase/auth';

// Firebase config - same as mobile app
// Add your Firebase config here or use environment variables
const firebaseConfig = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY || '',
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN || '',
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID || '',
  storageBucket: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET || '',
  messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID || '',
  appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID || '',
};

// Only initialize Firebase if we have the required config
const hasFirebaseConfig = firebaseConfig.apiKey && firebaseConfig.projectId;

let app: FirebaseApp | null = null;
let auth: Auth | null = null;

if (hasFirebaseConfig && typeof window !== 'undefined') {
  app = getApps().length === 0 ? initializeApp(firebaseConfig) : getApps()[0];
  auth = getAuth(app);
}

export { auth };

export async function signIn(email: string, password: string) {
  if (!auth) throw new Error('Firebase not initialized');
  const userCredential = await signInWithEmailAndPassword(auth, email, password);
  return userCredential.user;
}

export async function signOut() {
  if (!auth) return;
  await firebaseSignOut(auth);
}

export async function getIdToken(): Promise<string | null> {
  if (!auth) return null;
  const user = auth.currentUser;
  if (!user) return null;
  return user.getIdToken();
}

export function onAuthChange(callback: (user: User | null) => void) {
  if (!auth) {
    // If Firebase is not initialized, call callback with null once
    callback(null);
    return () => {};
  }
  return onAuthStateChanged(auth, callback);
}

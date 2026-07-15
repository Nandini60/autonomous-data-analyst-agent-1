import { useState } from 'react';
import { useStore } from './store';
import LandingPage from './pages/LandingPage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import ChatPage from './pages/ChatPage';

type Page = 'landing' | 'login' | 'register' | 'chat';

export default function App() {
  const user = useStore((s) => s.user);
  const [page, setPage] = useState<Page>(user ? 'chat' : 'landing');

  const navigate = (p: string) => {
    if (p === 'chat' && !user) { setPage('login'); return; }
    setPage(p as Page);
  };

  switch (page) {
    case 'login': return <LoginPage onNavigate={navigate} />;
    case 'register': return <RegisterPage onNavigate={navigate} />;
    case 'chat': return user ? <ChatPage onNavigate={navigate} /> : <LoginPage onNavigate={navigate} />;
    default: return <LandingPage onNavigate={navigate} />;
  }
}

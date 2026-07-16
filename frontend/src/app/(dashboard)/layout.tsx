"use client";

import React, { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { 
  LayoutDashboard, 
  GitPullRequest, 
  Settings, 
  LogOut,
  AlertCircle
} from "lucide-react";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [isClient, setIsClient] = useState(false);

  useEffect(() => {
    setIsClient(true);
    const token = localStorage.getItem("prism_token");
    if (!token && !pathname.includes("login")) {
      router.push("/login");
    }
  }, [router, pathname]);

  const handleLogout = () => {
    localStorage.removeItem("prism_token");
    router.push("/login");
  };

  if (!isClient) return null;

  return (
    <div id="app-container">
      <aside className="sidebar">
        <div className="sidebar-header">
          <GitPullRequest className="logo-icon glow" />
          <h2>PRism</h2>
        </div>
        <nav className="sidebar-nav">
          <a href="/dashboard" className={`nav-item ${pathname === '/dashboard' ? 'active' : ''}`}>
            <LayoutDashboard size={20} />
            <span>Dashboard</span>
          </a>
          <a href="/explorer" className={`nav-item ${pathname === '/explorer' ? 'active' : ''}`}>
            <GitPullRequest size={20} />
            <span>Review Explorer</span>
          </a>
          <a href="/issues" className={`nav-item ${pathname === '/issues' ? 'active' : ''}`}>
            <AlertCircle size={20} />
            <span>Global Issues</span>
          </a>
        </nav>
        <div className="sidebar-footer">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>Settings</span>
            <button className="btn-icon">
              <Settings size={20} />
            </button>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '0.5rem' }}>
            <span style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>Logout</span>
            <button onClick={handleLogout} className="btn-icon">
              <LogOut size={20} />
            </button>
          </div>
        </div>
      </aside>
      <main className="main-content">
        {children}
      </main>
    </div>
  );
}

"use client";

import React, { useEffect, useState } from "react";
import { Activity, ShieldAlert, GitPullRequest, Code, Clock } from "lucide-react";

export default function Dashboard() {
  const [stats, setStats] = useState<any>(null);

  useEffect(() => {
    const fetchStats = async () => {
      const token = localStorage.getItem("prism_token");
      try {
        const res = await fetch("/api/v1/dashboard/stats", {
          headers: {
            "Authorization": `Bearer ${token}`
          }
        });
        if (res.ok) {
          const data = await res.json();
          setStats(data);
        }
      } catch (err) {
        console.error("Error fetching stats:", err);
      }
    };
    fetchStats();
  }, []);

  return (
    <div className="view">
      <div className="topbar">
        <h1 id="page-title">Command Center</h1>
        <div className="status-indicator">
          <div className="status-dot healthy"></div>
          <span>System Healthy</span>
        </div>
      </div>

      <div style={{ textAlign: "center", marginBottom: "3rem", marginTop: "2rem" }}>
        <h2 style={{ fontSize: "2rem", marginBottom: "0.5rem" }}>PRism Intelligent Pull Request Agent</h2>
        <p className="subtitle">Review and analyze pull requests autonomously.</p>
      </div>

      {stats && (
        <div className="kpi-grid">
          <div className="glass-card kpi-card">
            <div className="kpi-icon blue"><GitPullRequest size={24} /></div>
            <div className="kpi-data">
              <span className="kpi-label">Total Reviews</span>
              <span className="kpi-value">{stats.total_reviews}</span>
            </div>
          </div>
          <div className="glass-card kpi-card">
            <div className="kpi-icon purple"><Code size={24} /></div>
            <div className="kpi-data">
              <span className="kpi-label">Repositories</span>
              <span className="kpi-value">{stats.total_repositories}</span>
            </div>
          </div>
          <div className="glass-card kpi-card">
            <div className="kpi-icon green"><Activity size={24} /></div>
            <div className="kpi-data">
              <span className="kpi-label">Health Score</span>
              <span className="kpi-value" style={{ color: stats.avg_health_score > 80 ? 'var(--color-success)' : stats.avg_health_score < 50 ? 'var(--color-danger)' : 'var(--text-main)' }}>
                {stats.avg_health_score}
              </span>
            </div>
          </div>
          <div className="glass-card kpi-card">
            <div className="kpi-icon orange"><Clock size={24} /></div>
            <div className="kpi-data">
              <span className="kpi-label">Avg Processing Time</span>
              <span className="kpi-value">{stats.avg_review_time}s</span>
            </div>
          </div>
          <div className="glass-card kpi-card">
            <div className="kpi-icon red"><ShieldAlert size={24} /></div>
            <div className="kpi-data">
              <span className="kpi-label">Total Findings</span>
              <span className="kpi-value">{stats.security_issues + stats.quality_issues + stats.logic_issues}</span>
              <span className="kpi-subtext">S:{stats.security_issues} | Q:{stats.quality_issues} | L:{stats.logic_issues}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

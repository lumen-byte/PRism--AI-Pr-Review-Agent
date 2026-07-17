"use client";

import React from "react";
import { useRouter } from "next/navigation";
import { 
  Sparkles, 
  GitPullRequest, 
  ArrowRight, 
  Cpu, 
  ShieldCheck, 
  MessageSquareCode, 
  Webhook, 
  Layers, 
  GitMerge 
} from "lucide-react";

export default function Dashboard() {
  const router = useRouter();

  const handleCtaClick = () => {
    router.push("/explorer");
  };

  return (
    <div className="view">
      <div className="topbar">
        <div>
          <h1 id="page-title">Demo Overview</h1>
          <p className="subtitle" id="page-subtitle">AI-Powered Pull Request Review Agent</p>
        </div>
        <div className="status-indicator">
          <div className="status-dot healthy"></div>
          <span>System Optimal</span>
        </div>
      </div>

      <div className="demo-landing-container">
        {/* Hero Section */}
        <section className="demo-hero-section">
          <div className="demo-badge">
            <Sparkles size={16} />
            <span>AI-Powered Pull Request Review Agent</span>
          </div>
          
          <h1 className="demo-hero-title">PRism</h1>
          
          <p className="demo-hero-subtitle">
            Multi-agent system that reviews pull requests like a senior engineer.
          </p>
          
          <div className="demo-cta-wrapper">
            <button onClick={handleCtaClick} className="btn-hero-cta">
              <GitPullRequest size={20} />
              <span>Review Sample Pull Request</span>
              <ArrowRight size={20} />
            </button>
          </div>
        </section>

        {/* Feature Cards Section (3 Cards) */}
        <section className="demo-features-section">
          <div className="demo-features-grid">
            {/* Feature Card 1 */}
            <div className="glass-card demo-feature-card">
              <div className="feature-card-icon blue">
                <Cpu size={24} />
              </div>
              <h3>5 Specialized AI Agents</h3>
              <p>Diff Analyzer, Tree-sitter AST, Security, Quality, and Logic agents evaluate pull requests in parallel to detect issues across languages.</p>
            </div>
            
            {/* Feature Card 2 */}
            <div className="glass-card demo-feature-card">
              <div className="feature-card-icon red">
                <ShieldCheck size={24} />
              </div>
              <h3>Security • Quality • Logic Analysis</h3>
              <p>Comprehensive tri-agent inspection targeting SQL vulnerabilities, secret leaks, cyclomatic complexity, code smells, and logical edge cases.</p>
            </div>

            {/* Feature Card 3 */}
            <div className="glass-card demo-feature-card">
              <div className="feature-card-icon green">
                <MessageSquareCode size={24} />
              </div>
              <h3>GitHub Inline Review Comments</h3>
              <p>Publishes line-level contextual review comments with actionable replacement code suggestions directly onto GitHub pull request diffs.</p>
            </div>
          </div>
        </section>

        {/* How PRism Works Section (3 Steps Only) */}
        <section className="demo-how-it-works-section">
          <div className="section-header text-center">
            <h2 className="section-title">How PRism Works</h2>
            <p className="section-subtitle">Autonomous 3-step pipeline from GitHub event to code review comment</p>
          </div>
          
          <div className="demo-steps-grid">
            {/* Step 1 */}
            <div className="glass-card demo-step-card">
              <div className="step-number-badge">1</div>
              <div className="step-content">
                <div className="step-header">
                  <Webhook size={18} />
                  <h4>Webhook & Diff Trigger</h4>
                </div>
                <p>GitHub emits a webhook on PR creation. PRism intercepts diffs and extracts syntax trees via native Tree-sitter grammars.</p>
              </div>
            </div>

            {/* Step 2 */}
            <div className="glass-card demo-step-card">
              <div className="step-number-badge">2</div>
              <div className="step-content">
                <div className="step-header">
                  <Layers size={18} />
                  <h4>Multi-Agent Analysis</h4>
                </div>
                <p>LangGraph orchestrates parallel execution of Security, Quality, and Logic agents, resolving issue conflicts transactionally.</p>
              </div>
            </div>

            {/* Step 3 */}
            <div className="glass-card demo-step-card">
              <div className="step-number-badge">3</div>
              <div className="step-content">
                <div className="step-header">
                  <GitMerge size={18} />
                  <h4>Inline GitHub Publishing</h4>
                </div>
                <p>Review Orchestrator synthesizes findings and automatically posts structured inline code review comments back to GitHub.</p>
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}


"use client";

import React, { useEffect, useState } from "react";

export default function Issues() {
  const [issues, setIssues] = useState<any[]>([]);

  useEffect(() => {
    const fetchIssues = async () => {
      const token = localStorage.getItem("prism_token");
      try {
        const res = await fetch("/api/v1/dashboard/issues", {
          headers: { "Authorization": `Bearer ${token}` }
        });
        if (res.ok) {
          const data = await res.json();
          setIssues(data);
        }
      } catch (err) {
        console.error(err);
      }
    };
    fetchIssues();
  }, []);

  return (
    <div className="full-height">
      <div className="topbar">
        <h1 id="page-title">Global Findings</h1>
      </div>

      <div className="table-container glass-card" style={{ padding: "1rem" }}>
        <table className="glass-table">
          <thead>
            <tr>
              <th>PR</th>
              <th>Location</th>
              <th>Severity</th>
              <th>Category</th>
              <th>Description</th>
            </tr>
          </thead>
          <tbody>
            {issues.map((i, idx) => (
              <tr key={idx}>
                <td><span style={{ color: "var(--brand-primary)" }}>#{i.pr_number}</span></td>
                <td>
                  <span title={i.file_path} style={{ maxWidth: "200px", display: "inline-block", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                    {i.file_path}:{i.line_number}
                  </span>
                </td>
                <td>
                  <span className={`decision-badge ${i.severity}`}>
                    {i.severity}
                  </span>
                </td>
                <td>{i.category}</td>
                <td>{i.text.substring(0, 50)}{i.text.length > 50 ? '...' : ''}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

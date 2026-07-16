"use client";

import React, { useEffect, useState } from "react";

export default function Explorer() {
  const [reviews, setReviews] = useState<any[]>([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [repo, setRepo] = useState("");
  const [status, setStatus] = useState("");

  useEffect(() => {
    const fetchReviews = async () => {
      const token = localStorage.getItem("prism_token");
      let url = `/api/v1/dashboard/reviews?page=${page}&limit=10`;
      if (repo) url += `&repo=${repo}`;
      if (status) url += `&status=${status}`;

      try {
        const res = await fetch(url, {
          headers: { "Authorization": `Bearer ${token}` }
        });
        if (res.ok) {
          const data = await res.json();
          setReviews(data.items);
          setTotalPages(data.pages);
        }
      } catch (err) {
        console.error(err);
      }
    };
    fetchReviews();
  }, [page, repo, status]);

  return (
    <div className="full-height">
      <div className="topbar">
        <h1 id="page-title">Review Explorer</h1>
      </div>

      <div className="toolbar">
        <div className="search-box">
          <input 
            type="text" 
            placeholder="Search by repository..." 
            value={repo}
            onChange={(e) => { setRepo(e.target.value); setPage(1); }}
          />
        </div>
        <select 
          className="glass-select"
          value={status}
          onChange={(e) => { setStatus(e.target.value); setPage(1); }}
        >
          <option value="">All Statuses</option>
          <option value="APPROVED">Approved</option>
          <option value="CHANGES_REQUESTED">Changes Requested</option>
          <option value="COMMENTED">Commented</option>
        </select>
      </div>

      <div className="table-container glass-card" style={{ padding: "1rem" }}>
        <table className="glass-table">
          <thead>
            <tr>
              <th>Repository</th>
              <th>PR</th>
              <th>Author</th>
              <th>Health</th>
              <th>Decision</th>
              <th>Date</th>
            </tr>
          </thead>
          <tbody>
            {reviews.map(r => (
              <tr key={r.id}>
                <td>{r.repo_name}</td>
                <td><span style={{ color: "var(--brand-primary)" }}>#{r.pr_number}</span></td>
                <td>{r.author}</td>
                <td style={{ color: r.health_score > 80 ? 'var(--color-success)' : r.health_score < 50 ? 'var(--color-danger)' : 'inherit' }}>
                  {r.health_score}
                </td>
                <td>
                  <span className={`decision-badge ${r.decision}`}>
                    {r.decision}
                  </span>
                </td>
                <td>{new Date(r.reviewed_at).toLocaleDateString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="pagination">
        <button className="btn-secondary" disabled={page <= 1} onClick={() => setPage(page - 1)}>Prev</button>
        <span style={{ color: "var(--text-muted)", fontSize: "0.875rem" }}>Page {page} of {totalPages}</span>
        <button className="btn-secondary" disabled={page >= totalPages} onClick={() => setPage(page + 1)}>Next</button>
      </div>
    </div>
  );
}

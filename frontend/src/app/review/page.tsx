"use client";

import React, { useEffect, useState } from "react";
import { Question } from "../../lib/types";
import { fetchQuestions, approveQuestion, rejectQuestion, regenerateQuestion } from "../../lib/api";
import QuestionCard from "../../components/QuestionCard";
import QuestionEditor from "../../components/QuestionEditor";
import { CheckCircle2, XCircle, Filter, RefreshCw, Layers } from "lucide-react";

export default function ReviewQueue() {
  const [questions, setQuestions] = useState<Question[]>([]);
  const [filterDifficulty, setFilterDifficulty] = useState<string>("All");
  const [filterTopic, setFilterTopic] = useState<string>("All");
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [selectedQuestion, setSelectedQuestion] = useState<Question | null>(null);
  const [loading, setLoading] = useState(true);

  const loadReviewQuestions = async () => {
    setLoading(true);
    try {
      const data = await fetchQuestions({ status: "review_ready" });
      setQuestions(data);
    } catch (e) {
      console.error("Failed to load review queue:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadReviewQuestions();
  }, []);

  const handleApprove = async (id: string) => {
    await approveQuestion(id);
    loadReviewQuestions();
  };

  const handleReject = async (id: string) => {
    await rejectQuestion(id, "Rejected via Review Queue");
    loadReviewQuestions();
  };

  const handleRegenerate = async (id: string) => {
    await regenerateQuestion(id);
    loadReviewQuestions();
  };

  const handleBatchApprove = async () => {
    for (const id of selectedIds) {
      await approveQuestion(id);
    }
    setSelectedIds([]);
    loadReviewQuestions();
  };

  const toggleSelect = (id: string) => {
    if (selectedIds.includes(id)) {
      setSelectedIds(selectedIds.filter((item) => item !== id));
    } else {
      setSelectedIds([...selectedIds, id]);
    }
  };

  const filtered = questions.filter((q) => {
    if (filterDifficulty !== "All" && q.difficulty !== filterDifficulty) return false;
    if (filterTopic !== "All" && !q.tags.includes(filterTopic.toLowerCase())) return false;
    return true;
  });

  return (
    <div className="space-y-6">
      {/* Header & Batch Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-xl font-extrabold text-slate-900">Human Review Queue</h1>
            <span className="px-2 py-0.5 rounded-full text-xs font-bold bg-amber-100 text-amber-800">
              {questions.length} Pending
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Review AI-generated problems, inspect automated sandbox verification logs, critic scores, and approve for publishing.
          </p>
        </div>

        <div className="flex items-center space-x-2">
          {selectedIds.length > 0 && (
            <button
              onClick={handleBatchApprove}
              className="inline-flex items-center space-x-1.5 px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-bold transition shadow-sm"
            >
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>Approve Selected ({selectedIds.length})</span>
            </button>
          )}

          <button
            onClick={loadReviewQuestions}
            className="p-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl transition"
            title="Refresh queue"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Filters bar */}
      <div className="flex flex-wrap items-center gap-3 bg-white p-4 rounded-xl border border-slate-200 text-xs">
        <div className="flex items-center space-x-2 text-slate-500 font-semibold mr-2">
          <Filter className="w-3.5 h-3.5" />
          <span>Filters:</span>
        </div>

        <div>
          <select
            value={filterDifficulty}
            onChange={(e) => setFilterDifficulty(e.target.value)}
            className="px-3 py-1.5 rounded-lg border border-slate-300 bg-slate-50 font-medium text-slate-800 focus:outline-none"
          >
            <option value="All">All Difficulties</option>
            <option value="Easy">Easy</option>
            <option value="Medium">Medium</option>
            <option value="Hard">Hard</option>
          </select>
        </div>

        <div>
          <select
            value={filterTopic}
            onChange={(e) => setFilterTopic(e.target.value)}
            className="px-3 py-1.5 rounded-lg border border-slate-300 bg-slate-50 font-medium text-slate-800 focus:outline-none"
          >
            <option value="All">All Topics</option>
            <option value="arrays">Arrays</option>
            <option value="dp">Dynamic Programming</option>
            <option value="graphs">Graphs</option>
            <option value="greedy">Greedy</option>
            <option value="sql">SQL</option>
          </select>
        </div>
      </div>

      {/* Questions list */}
      {loading ? (
        <div className="p-12 text-center text-xs text-slate-500">Loading review queue...</div>
      ) : filtered.length === 0 ? (
        <div className="p-16 bg-white rounded-2xl border border-slate-200 text-center space-y-2">
          <CheckCircle2 className="w-10 h-10 text-emerald-500 mx-auto" />
          <h3 className="text-sm font-bold text-slate-900">Review Queue is Clear!</h3>
          <p className="text-xs text-slate-500 max-w-sm mx-auto">
            All generated questions have been reviewed or auto-published. Launch a new generation job from the dashboard.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {filtered.map((q) => {
            const isSelected = selectedIds.includes(q.id);
            return (
              <div key={q.id} className="relative group">
                <div className="absolute top-3 left-3 z-10">
                  <input
                    type="checkbox"
                    checked={isSelected}
                    onChange={() => toggleSelect(q.id)}
                    className="w-4 h-4 accent-indigo-600 rounded cursor-pointer"
                  />
                </div>
                <div className="pl-6">
                  <QuestionCard
                    question={q}
                    onSelect={(selected) => setSelectedQuestion(selected)}
                    onApprove={handleApprove}
                    onReject={handleReject}
                    onRegenerate={handleRegenerate}
                  />
                </div>
              </div>
            );
          })}
        </div>
      )}

      {selectedQuestion && (
        <QuestionEditor
          question={selectedQuestion}
          onClose={() => setSelectedQuestion(null)}
          onUpdated={(updated) => {
            setSelectedQuestion(updated);
            loadReviewQuestions();
          }}
        />
      )}
    </div>
  );
}

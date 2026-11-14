"use client";

import React, { useEffect, useState } from "react";
import { Question } from "../../lib/types";
import { fetchQuestions } from "../../lib/api";
import QuestionCard from "../../components/QuestionCard";
import QuestionEditor from "../../components/QuestionEditor";
import { Search, Filter, History, RefreshCw } from "lucide-react";

export default function HistoryPage() {
  const [questions, setQuestions] = useState<Question[]>([]);
  const [search, setSearch] = useState("");
  const [filterDifficulty, setFilterDifficulty] = useState("All");
  const [filterStatus, setFilterStatus] = useState("All");
  const [selectedQuestion, setSelectedQuestion] = useState<Question | null>(null);
  const [loading, setLoading] = useState(true);

  const loadAll = async () => {
    setLoading(true);
    try {
      const data = await fetchQuestions({
        search: search.trim() || undefined,
        difficulty: filterDifficulty !== "All" ? filterDifficulty : undefined,
        status: filterStatus !== "All" ? filterStatus : undefined,
        limit: 50,
      });
      setQuestions(data);
    } catch (e) {
      console.error("Failed to load questions:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAll();
  }, [filterDifficulty, filterStatus]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    loadAll();
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <History className="w-5 h-5 text-indigo-600" />
            <h1 className="text-xl font-bold text-slate-900">Question History & Audit Archive</h1>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Browse all generated questions, audit trails, LLM prompts, and sandbox verification histories.
          </p>
        </div>

        <button
          onClick={loadAll}
          className="p-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl transition self-start sm:self-auto"
          title="Refresh"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 flex flex-wrap items-center gap-3 text-xs">
        <form onSubmit={handleSearchSubmit} className="flex-1 min-w-[240px] relative">
          <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
          <input
            type="text"
            placeholder="Search questions by title, story keyword, or tag..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-slate-800 placeholder-slate-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </form>

        <div className="flex items-center space-x-2">
          <Filter className="w-3.5 h-3.5 text-slate-400" />
          <select
            value={filterDifficulty}
            onChange={(e) => setFilterDifficulty(e.target.value)}
            className="px-3 py-2 rounded-lg border border-slate-300 bg-slate-50 font-medium text-slate-800 focus:outline-none"
          >
            <option value="All">All Difficulties</option>
            <option value="Easy">Easy</option>
            <option value="Medium">Medium</option>
            <option value="Hard">Hard</option>
          </select>
        </div>

        <div>
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="px-3 py-2 rounded-lg border border-slate-300 bg-slate-50 font-medium text-slate-800 focus:outline-none"
          >
            <option value="All">All Statuses</option>
            <option value="review_ready">Review Ready</option>
            <option value="approved">Approved</option>
            <option value="published">Published</option>
            <option value="rejected">Rejected</option>
          </select>
        </div>
      </div>

      {/* Question Cards Grid */}
      {loading ? (
        <div className="p-12 text-center text-xs text-slate-500">Loading archived questions...</div>
      ) : questions.length === 0 ? (
        <div className="p-16 bg-white rounded-2xl border border-slate-200 text-center text-xs text-slate-500">
          No questions matched your search criteria.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {questions.map((q) => (
            <QuestionCard
              key={q.id}
              question={q}
              onSelect={(selected) => setSelectedQuestion(selected)}
              showActions={true}
            />
          ))}
        </div>
      )}

      {selectedQuestion && (
        <QuestionEditor
          question={selectedQuestion}
          onClose={() => setSelectedQuestion(null)}
          onUpdated={(updated) => {
            setSelectedQuestion(updated);
            loadAll();
          }}
        />
      )}
    </div>
  );
}

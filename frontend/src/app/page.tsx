"use client";

import React, { useEffect, useState } from "react";
import JobCreator from "../components/JobCreator";
import JobProgressTracker from "../components/JobProgressTracker";
import QuestionCard from "../components/QuestionCard";
import QuestionEditor from "../components/QuestionEditor";
import { Question, GenerationJob } from "../lib/types";
import { fetchQuestions, fetchJobs, approveQuestion, rejectQuestion, regenerateQuestion } from "../lib/api";
import { Layers, CheckCircle2, Send, Cpu, ArrowUpRight, Sparkles } from "lucide-react";
import Link from "next/link";

export default function Dashboard() {
  const [activeJobIds, setActiveJobIds] = useState<string[]>([]);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [selectedQuestion, setSelectedQuestion] = useState<Question | null>(null);
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    try {
      const [qs, jobs] = await Promise.all([
        fetchQuestions({ limit: 100 }),
        fetchJobs(),
      ]);
      setQuestions(qs);
      const runningJobs = jobs.filter(
        (j) => j.status === "running" || j.status === "pending" || j.status === "processing"
      );
      setActiveJobIds(runningJobs.map((j) => j.id));
    } catch (e) {
      console.error("Dashboard data load error:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 10000);
    return () => clearInterval(interval);
  }, []);

  const handleJobCreated = (newJobId: string) => {
    setActiveJobIds((prev) => Array.from(new Set([newJobId, ...prev])));
    loadData();
  };

  const handleApprove = async (id: string) => {
    await approveQuestion(id);
    loadData();
  };

  const handleReject = async (id: string) => {
    await rejectQuestion(id, "Rejected via dashboard quick action");
    loadData();
  };

  const handleRegenerate = async (id: string) => {
    await regenerateQuestion(id);
    loadData();
  };

  const reviewReadyCount = questions.filter((q) => q.status === "review_ready").length;
  const publishedCount = questions.filter((q) => q.status === "published").length;
  const approvedCount = questions.filter((q) => q.status === "approved").length;

  return (
    <div className="space-y-8">
      {/* Top Banner & Quick Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex items-center space-x-4">
          <div className="w-12 h-12 rounded-xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600">
            <Layers className="w-6 h-6" />
          </div>
          <div>
            <div className="text-2xl font-black text-slate-900">{questions.length}</div>
            <div className="text-xs text-slate-500 font-medium">Total Questions in DB</div>
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex items-center space-x-4">
          <div className="w-12 h-12 rounded-xl bg-amber-50 border border-amber-100 flex items-center justify-center text-amber-600">
            <CheckCircle2 className="w-6 h-6" />
          </div>
          <div>
            <div className="text-2xl font-black text-slate-900">{reviewReadyCount}</div>
            <div className="text-xs text-slate-500 font-medium">Pending Review</div>
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex items-center space-x-4">
          <div className="w-12 h-12 rounded-xl bg-blue-50 border border-blue-100 flex items-center justify-center text-blue-600">
            <Send className="w-6 h-6" />
          </div>
          <div>
            <div className="text-2xl font-black text-slate-900">{approvedCount}</div>
            <div className="text-xs text-slate-500 font-medium">Ready to Publish</div>
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex items-center space-x-4">
          <div className="w-12 h-12 rounded-xl bg-emerald-50 border border-emerald-100 flex items-center justify-center text-emerald-600">
            <Cpu className="w-6 h-6" />
          </div>
          <div>
            <div className="text-2xl font-black text-slate-900">{publishedCount}</div>
            <div className="text-xs text-slate-500 font-medium">Live on HackerRank</div>
          </div>
        </div>
      </div>

      {/* Main Grid: Job Creator + Active Jobs */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2">
          <JobCreator onJobCreated={handleJobCreated} />
        </div>

        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider">
              Active Pipeline Jobs ({activeJobIds.length})
            </h3>
          </div>

          {activeJobIds.length === 0 ? (
            <div className="p-8 bg-white border border-dashed border-slate-300 rounded-2xl text-center space-y-2">
              <Sparkles className="w-8 h-8 text-slate-300 mx-auto" />
              <p className="text-xs font-semibold text-slate-600">No generation jobs running</p>
              <p className="text-[11px] text-slate-400">
                Configure your topic and difficulty to kick off isolated generation and sandbox testing.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {activeJobIds.map((id) => (
                <JobProgressTracker
                  key={id}
                  jobId={id}
                  onCompleted={() => {
                    loadData();
                  }}
                />
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Recent Questions */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold text-slate-900">Recently Generated Questions</h2>
            <p className="text-xs text-slate-500">
              Generated by Claude 3.5 Sonnet, verified via isolated Docker test runs
            </p>
          </div>
          <Link
            href="/history"
            className="inline-flex items-center space-x-1 text-xs font-bold text-indigo-600 hover:text-indigo-800"
          >
            <span>View All Questions</span>
            <ArrowUpRight className="w-4 h-4" />
          </Link>
        </div>

        {loading ? (
          <div className="p-12 text-center text-xs text-slate-500">Loading questions...</div>
        ) : questions.length === 0 ? (
          <div className="p-12 bg-white rounded-2xl border border-slate-200 text-center text-slate-500 text-xs">
            No questions generated yet. Launch your first job above!
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {questions.slice(0, 6).map((q) => (
              <QuestionCard
                key={q.id}
                question={q}
                onSelect={(selected) => setSelectedQuestion(selected)}
                onApprove={handleApprove}
                onReject={handleReject}
                onRegenerate={handleRegenerate}
              />
            ))}
          </div>
        )}
      </div>

      {/* Deep Question Inspector / Editor Modal */}
      {selectedQuestion && (
        <QuestionEditor
          question={selectedQuestion}
          onClose={() => setSelectedQuestion(null)}
          onUpdated={(updated) => {
            setSelectedQuestion(updated);
            loadData();
          }}
        />
      )}
    </div>
  );
}

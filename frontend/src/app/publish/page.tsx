"use client";

import React, { useEffect, useState } from "react";
import { Question, PublishResult } from "../../lib/types";
import { fetchQuestions, publishBulk, publishQuestion, getExportZipUrl } from "../../lib/api";
import QuestionEditor from "../../components/QuestionEditor";
import { Send, Download, ExternalLink, CheckCircle2, AlertTriangle, ShieldCheck, RefreshCw, Key, Check, X } from "lucide-react";

export default function PublishPage() {
  const [approvedQuestions, setApprovedQuestions] = useState<Question[]>([]);
  const [publishedQuestions, setPublishedQuestions] = useState<Question[]>([]);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [dryRun, setDryRun] = useState<boolean>(false);
  const [publishing, setPublishing] = useState<boolean>(false);
  const [results, setResults] = useState<PublishResult[] | null>(null);
  const [selectedQuestion, setSelectedQuestion] = useState<Question | null>(null);
  const [loading, setLoading] = useState(true);
  const [hrToken, setHrToken] = useState<string>("");
  const [showTokenInput, setShowTokenInput] = useState<boolean>(false);
  const [tokenInputVal, setTokenInputVal] = useState<string>("");

  useEffect(() => {
    if (typeof window !== "undefined") {
      const stored = localStorage.getItem("questforge_hr_token") || "";
      setHrToken(stored);
      setTokenInputVal(stored);
    }
  }, []);

  const saveToken = () => {
    const trimmed = tokenInputVal.trim();
    setHrToken(trimmed);
    if (typeof window !== "undefined") {
      if (trimmed) {
        localStorage.setItem("questforge_hr_token", trimmed);
      } else {
        localStorage.removeItem("questforge_hr_token");
      }
    }
    setShowTokenInput(false);
  };

  const loadQuestions = async () => {
    setLoading(true);
    try {
      const [approved, published] = await Promise.all([
        fetchQuestions({ status: "approved" }),
        fetchQuestions({ status: "published" }),
      ]);
      setApprovedQuestions(approved);
      setPublishedQuestions(published);
    } catch (e) {
      console.error("Failed to load questions for publishing:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadQuestions();
  }, []);

  const toggleSelect = (id: string) => {
    if (selectedIds.includes(id)) {
      setSelectedIds(selectedIds.filter((item) => item !== id));
    } else {
      setSelectedIds([...selectedIds, id]);
    }
  };

  const selectAll = () => {
    if (selectedIds.length === approvedQuestions.length) {
      setSelectedIds([]);
    } else {
      setSelectedIds(approvedQuestions.map((q) => q.id));
    }
  };

  const handleBulkPublish = async () => {
    if (selectedIds.length === 0) return;
    setPublishing(true);
    setResults(null);
    try {
      const res = await publishBulk(selectedIds, dryRun, hrToken || undefined);
      setResults(res.results);
      setSelectedIds([]);
      loadQuestions();
    } catch (e: any) {
      alert(`Bulk publish error: ${e.message}`);
    } finally {
      setPublishing(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* Top Banner & HackerRank Config Status */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 text-white p-6 rounded-2xl shadow-lg border border-slate-800">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center space-x-2">
              <Send className="w-5 h-5 text-indigo-400" />
              <h1 className="text-xl font-black tracking-tight">HackerRank Publishing Center</h1>
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-500/30 text-indigo-300 border border-indigo-400/30 uppercase">
                REST v3 API
              </span>
            </div>
            <p className="text-xs text-slate-300">
              Deploy approved coding challenges directly to HackerRank for Work or export as 1-click importable packages.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <button
              onClick={() => setShowTokenInput(!showTokenInput)}
              className={`flex items-center space-x-2 px-3 py-1.5 rounded-xl border text-xs font-semibold transition ${
                hrToken
                  ? "bg-emerald-950/70 border-emerald-700/80 text-emerald-300 hover:bg-emerald-900/60"
                  : "bg-slate-800/80 border-slate-700 text-slate-300 hover:bg-slate-700"
              }`}
            >
              <Key className="w-3.5 h-3.5" />
              <span>{hrToken ? "Bearer Token: Active" : "Set API Token"}</span>
            </button>

            <div className="bg-slate-800/80 px-3.5 py-1.5 rounded-xl border border-slate-700/80">
              <label className="flex items-center space-x-2 text-xs font-medium cursor-pointer">
                <input
                  type="checkbox"
                  checked={dryRun}
                  onChange={(e) => setDryRun(e.target.checked)}
                  className="accent-indigo-500 rounded"
                />
                <span className={dryRun ? "text-amber-300 font-bold" : "text-slate-400"}>
                  Dry-Run Mode
                </span>
              </label>
            </div>
          </div>
        </div>

        {/* Token Configuration Drawer */}
        {showTokenInput && (
          <div className="mt-4 pt-4 border-t border-slate-800/80 flex flex-col sm:flex-row sm:items-center gap-2">
            <div className="flex-1">
              <input
                type="password"
                placeholder="Enter HackerRank for Work Bearer Access Token (or leave blank for Dry-Run mode)..."
                value={tokenInputVal}
                onChange={(e) => setTokenInputVal(e.target.value)}
                className="w-full px-3.5 py-2 text-xs bg-slate-800 text-white border border-slate-700 rounded-xl focus:outline-none focus:border-indigo-500"
              />
            </div>
            <div className="flex items-center space-x-2">
              <button
                onClick={saveToken}
                className="px-3.5 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-bold transition flex items-center space-x-1"
              >
                <Check className="w-3.5 h-3.5" />
                <span>Save Token</span>
              </button>
              {hrToken && (
                <button
                  onClick={() => {
                    setTokenInputVal("");
                    setHrToken("");
                    if (typeof window !== "undefined") localStorage.removeItem("questforge_hr_token");
                    setShowTokenInput(false);
                  }}
                  className="px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white rounded-xl text-xs font-bold transition"
                >
                  Clear
                </button>
              )}
              <button
                onClick={() => setShowTokenInput(false)}
                className="p-2 text-slate-400 hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Results Banner if published */}
      {results && (
        <div className="p-4 bg-white border border-slate-200 rounded-2xl text-xs space-y-2 shadow-sm">
          <div className="flex items-center justify-between font-bold text-slate-900 border-b border-slate-100 pb-2">
            <span className="flex items-center space-x-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              <span>Publish Batch Results</span>
            </span>
            <button onClick={() => setResults(null)} className="text-slate-400 hover:text-slate-600 font-normal">
              Dismiss
            </button>
          </div>
          <div className="divide-y divide-slate-100">
            {results.map((r: any) => (
              <div key={r.question_id} className="py-2 flex flex-col sm:flex-row sm:items-center justify-between gap-1 text-slate-800">
                <span className="font-mono text-xs text-slate-600">{r.question_id}</span>
                {r.success ? (
                  <div className="flex items-center space-x-3">
                    {r.url ? (
                      <a
                        href={r.url}
                        target="_blank"
                        rel="noreferrer"
                        className="flex items-center space-x-1 font-bold text-indigo-600 hover:text-indigo-800 underline"
                      >
                        <span>View on HackerRank</span>
                        <ExternalLink className="w-3 h-3" />
                      </a>
                    ) : (
                      <span className="font-semibold text-emerald-600">Validated (Dry-Run Mode)</span>
                    )}
                  </div>
                ) : (
                  <span className="text-rose-600 font-semibold">{r.error || "Publish failed"}</span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Approved Questions Ready for Publishing */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-5 border-b border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-slate-50">
          <div>
            <h2 className="text-base font-bold text-slate-900">Approved Questions Ready to Publish</h2>
            <p className="text-xs text-slate-500">
              Select questions to deploy via HackerRank REST v3 or export as ZIP packages
            </p>
          </div>

          <div className="flex items-center space-x-2">
            {approvedQuestions.length > 0 && (
              <button
                onClick={selectAll}
                className="px-3 py-1.5 rounded-lg border border-slate-300 bg-white hover:bg-slate-50 text-xs font-semibold text-slate-700 transition"
              >
                {selectedIds.length === approvedQuestions.length ? "Deselect All" : "Select All"}
              </button>
            )}

            <button
              onClick={handleBulkPublish}
              disabled={publishing || selectedIds.length === 0}
              className="inline-flex items-center space-x-2 px-4 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-bold transition disabled:opacity-50 shadow-sm"
            >
              <Send className="w-3.5 h-3.5" />
              <span>
                {publishing
                  ? "Publishing..."
                  : `Publish Selected (${selectedIds.length})`}
              </span>
            </button>
          </div>
        </div>

        {loading ? (
          <div className="p-8 text-center text-xs text-slate-500">Loading approved questions...</div>
        ) : approvedQuestions.length === 0 ? (
          <div className="p-12 text-center text-slate-500 text-xs space-y-1">
            <CheckCircle2 className="w-8 h-8 text-slate-300 mx-auto mb-2" />
            <p className="font-semibold text-slate-700">No approved questions waiting in queue.</p>
            <p className="text-slate-400">Head over to the Review Queue to approve questions first.</p>
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {approvedQuestions.map((q) => {
              const checked = selectedIds.includes(q.id);
              return (
                <div
                  key={q.id}
                  className={`p-4 flex items-center justify-between transition ${
                    checked ? "bg-indigo-50/50" : "hover:bg-slate-50"
                  }`}
                >
                  <div className="flex items-center space-x-4">
                    <input
                      type="checkbox"
                      checked={checked}
                      onChange={() => toggleSelect(q.id)}
                      className="w-4 h-4 accent-indigo-600 rounded cursor-pointer"
                    />
                    <div>
                      <div className="flex items-center space-x-2 mb-0.5">
                        <span className="font-bold text-sm text-slate-900">{q.title}</span>
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-700 uppercase">
                          {q.difficulty}
                        </span>
                        <span className="text-xs text-slate-400">• {q.test_cases?.length || 0} Test Cases</span>
                      </div>
                      <p className="text-xs text-slate-500 line-clamp-1">{q.story}</p>
                    </div>
                  </div>

                  <div className="flex items-center space-x-2 flex-shrink-0">
                    <a
                      href={getExportZipUrl(q.id)}
                      download
                      className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-lg border border-slate-200 text-xs font-semibold text-slate-700 hover:bg-slate-100 transition"
                      title="Download challenge ZIP for offline/manual upload"
                    >
                      <Download className="w-3.5 h-3.5" />
                      <span>ZIP</span>
                    </a>
                    <button
                      onClick={() => setSelectedQuestion(q)}
                      className="px-3 py-1 rounded-lg bg-slate-900 text-white text-xs font-semibold hover:bg-slate-800 transition"
                    >
                      Inspect
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Published Questions List */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-5 border-b border-slate-200 bg-slate-50">
          <h2 className="text-base font-bold text-slate-900">Live Published Questions ({publishedQuestions.length})</h2>
          <p className="text-xs text-slate-500">Coding challenges successfully synced to HackerRank</p>
        </div>

        {publishedQuestions.length === 0 ? (
          <div className="p-10 text-center text-slate-400 text-xs">
            No questions published yet. Select and publish from the approved section above.
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {publishedQuestions.map((q) => (
              <div key={q.id} className="p-4 flex items-center justify-between hover:bg-slate-50 transition">
                <div>
                  <div className="flex items-center space-x-2 mb-1">
                    <span className="font-bold text-sm text-slate-900">{q.title}</span>
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800">
                      LIVE
                    </span>
                    <span className="text-xs text-slate-500 font-mono">
                      HackerRank ID: {q.hackerrank_question_id || "sim-hr-id"}
                    </span>
                  </div>
                  <div className="flex items-center space-x-3 text-xs text-slate-500">
                    <span>{q.difficulty}</span>
                    <span>• {q.tags.join(", ")}</span>
                    <span>• {q.test_cases?.length || 0} Test Cases</span>
                  </div>
                </div>

                <div className="flex items-center space-x-2">
                  <a
                    href={getExportZipUrl(q.id)}
                    download
                    className="p-1.5 rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-100 transition"
                    title="Export challenge ZIP"
                  >
                    <Download className="w-4 h-4" />
                  </a>

                  {q.hackerrank_url && (
                    <a
                      href={q.hackerrank_url}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold transition shadow-sm"
                    >
                      <span>Open on HackerRank</span>
                      <ExternalLink className="w-3.5 h-3.5" />
                    </a>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {selectedQuestion && (
        <QuestionEditor
          question={selectedQuestion}
          onClose={() => setSelectedQuestion(null)}
          onUpdated={(updated) => {
            setSelectedQuestion(updated);
            loadQuestions();
          }}
        />
      )}
    </div>
  );
}

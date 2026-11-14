"use client";

import React, { useState } from "react";
import { Question, TestCase, VerificationLog } from "../lib/types";
import { updateQuestion, approveQuestion, rejectQuestion, regenerateQuestion, publishQuestion, getExportZipUrl } from "../lib/api";
import {
  X,
  Save,
  CheckCircle2,
  XCircle,
  RefreshCw,
  Send,
  Download,
  Terminal,
  FileCode,
  ShieldCheck,
  Star,
  Layers,
  ChevronRight,
  ExternalLink,
} from "lucide-react";

interface QuestionEditorProps {
  question: Question;
  onClose: () => void;
  onUpdated: (q: Question) => void;
}

export default function QuestionEditor({ question, onClose, onUpdated }: QuestionEditorProps) {
  const [activeTab, setActiveTab] = useState<"statement" | "testcases" | "code" | "logs" | "critic">("statement");
  const [title, setTitle] = useState(question.title);
  const [story, setStory] = useState(question.story);
  const [inputFormat, setInputFormat] = useState(question.input_format);
  const [outputFormat, setOutputFormat] = useState(question.output_format);
  const [constraints, setConstraints] = useState(question.constraints);
  const [explanation, setExplanation] = useState(question.explanation || "");

  const [saving, setSaving] = useState(false);
  const [publishing, setPublishing] = useState(false);
  const [feedbackMsg, setFeedbackMsg] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const handleSave = async () => {
    setSaving(true);
    setFeedbackMsg(null);
    try {
      const updated = await updateQuestion(question.id, {
        title,
        story,
        input_format: inputFormat,
        output_format: outputFormat,
        constraints,
        explanation,
      });
      onUpdated(updated);
      setFeedbackMsg({ type: "success", text: "Question updated successfully." });
    } catch (e: any) {
      setFeedbackMsg({ type: "error", text: e.message || "Failed to update." });
    } finally {
      setSaving(false);
    }
  };

  const handleApprove = async () => {
    try {
      const res = await approveQuestion(question.id);
      onUpdated(res);
      setFeedbackMsg({ type: "success", text: "Question approved! Ready for publishing." });
    } catch (e: any) {
      setFeedbackMsg({ type: "error", text: e.message || "Failed to approve." });
    }
  };

  const handleReject = async () => {
    try {
      const res = await rejectQuestion(question.id, "Rejected during manual reviewer pass");
      onUpdated(res);
      setFeedbackMsg({ type: "success", text: "Question marked as rejected." });
    } catch (e: any) {
      setFeedbackMsg({ type: "error", text: e.message || "Failed to reject." });
    }
  };

  const handleRegenerate = async () => {
    try {
      const res = await regenerateQuestion(question.id);
      onUpdated(res);
      setFeedbackMsg({ type: "success", text: "Regeneration job triggered." });
    } catch (e: any) {
      setFeedbackMsg({ type: "error", text: e.message || "Failed to regenerate." });
    }
  };

  const handlePublish = async (dryRun = false) => {
    setPublishing(true);
    setFeedbackMsg(null);
    try {
      const pubRes = await publishQuestion(question.id, dryRun);
      if (pubRes.url) {
        setFeedbackMsg({
          type: "success",
          text: `Published successfully to HackerRank! ID: ${pubRes.hackerrank_question_id}`,
        });
      } else {
        setFeedbackMsg({
          type: "success",
          text: dryRun
            ? "Dry-run validation succeeded!"
            : "Publishing initiated.",
        });
      }
    } catch (e: any) {
      setFeedbackMsg({ type: "error", text: e.message || "Publishing failed." });
    } finally {
      setPublishing(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/70 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 w-full max-w-5xl max-h-[92vh] flex flex-col overflow-hidden">
        {/* Top Header */}
        <div className="p-4 sm:p-5 border-b border-slate-200 flex items-center justify-between bg-slate-50">
          <div className="flex items-center space-x-3">
            <span className="px-2.5 py-1 rounded-md text-xs font-bold uppercase tracking-wider bg-indigo-100 text-indigo-800 border border-indigo-200">
              {question.difficulty}
            </span>
            <span className="text-xs text-slate-500 font-mono">ID: {question.id}</span>
            <span className="text-xs font-semibold px-2 py-0.5 rounded bg-slate-200 text-slate-700">
              {question.status.toUpperCase()}
            </span>
          </div>

          <div className="flex items-center space-x-2">
            <a
              href={getExportZipUrl(question.id)}
              download
              className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-white border border-slate-300 text-slate-700 hover:bg-slate-100 transition"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Export ZIP</span>
            </a>
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-slate-500 hover:text-slate-800 hover:bg-slate-200 transition"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Action alerts */}
        {feedbackMsg && (
          <div
            className={`px-5 py-2.5 text-xs font-medium flex items-center justify-between ${
              feedbackMsg.type === "success"
                ? "bg-emerald-50 text-emerald-800 border-b border-emerald-200"
                : "bg-rose-50 text-rose-800 border-b border-rose-200"
            }`}
          >
            <span>{feedbackMsg.text}</span>
            <button onClick={() => setFeedbackMsg(null)} className="underline ml-4">
              Dismiss
            </button>
          </div>
        )}

        {/* Tab Navigation */}
        <div className="flex border-b border-slate-200 bg-white px-5 space-x-6 text-sm font-medium">
          {[
            { id: "statement", label: "Problem Statement", icon: FileCode },
            { id: "testcases", label: `Test Cases (${question.test_cases?.length || 0})`, icon: Layers },
            { id: "code", label: "Reference Solutions", icon: Terminal },
            { id: "logs", label: `Sandbox Logs (${question.verification_logs?.length || 0})`, icon: ShieldCheck },
            { id: "critic", label: "Critic Quality Score", icon: Star },
          ].map((t) => {
            const Icon = t.icon;
            const active = activeTab === t.id;
            return (
              <button
                key={t.id}
                onClick={() => setActiveTab(t.id as any)}
                className={`flex items-center space-x-2 py-3.5 border-b-2 transition ${
                  active
                    ? "border-indigo-600 text-indigo-600 font-bold"
                    : "border-transparent text-slate-500 hover:text-slate-800"
                }`}
              >
                <Icon className="w-4 h-4" />
                <span>{t.label}</span>
              </button>
            );
          })}
        </div>

        {/* Tab Content */}
        <div className="p-6 overflow-y-auto flex-1 space-y-5">
          {activeTab === "statement" && (
            <div className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Title</label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="w-full px-3.5 py-2 bg-slate-50 border border-slate-300 rounded-lg text-sm font-semibold text-slate-900 focus:bg-white focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase mb-1">
                  Problem Story / Description (Markdown)
                </label>
                <textarea
                  rows={6}
                  value={story}
                  onChange={(e) => setStory(e.target.value)}
                  className="w-full px-3.5 py-2 bg-slate-50 border border-slate-300 rounded-lg text-sm text-slate-800 font-mono focus:bg-white focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Input Format</label>
                  <textarea
                    rows={3}
                    value={inputFormat}
                    onChange={(e) => setInputFormat(e.target.value)}
                    className="w-full px-3.5 py-2 bg-slate-50 border border-slate-300 rounded-lg text-xs font-mono text-slate-800 focus:bg-white focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Output Format</label>
                  <textarea
                    rows={3}
                    value={outputFormat}
                    onChange={(e) => setOutputFormat(e.target.value)}
                    className="w-full px-3.5 py-2 bg-slate-50 border border-slate-300 rounded-lg text-xs font-mono text-slate-800 focus:bg-white focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Constraints</label>
                <textarea
                  rows={2}
                  value={constraints}
                  onChange={(e) => setConstraints(e.target.value)}
                  className="w-full px-3.5 py-2 bg-slate-50 border border-slate-300 rounded-lg text-xs font-mono text-slate-800 focus:bg-white focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase mb-1">Explanation & Editorial</label>
                <textarea
                  rows={3}
                  value={explanation}
                  onChange={(e) => setExplanation(e.target.value)}
                  className="w-full px-3.5 py-2 bg-slate-50 border border-slate-300 rounded-lg text-xs text-slate-800 focus:bg-white focus:ring-2 focus:ring-indigo-500"
                />
              </div>
            </div>
          )}

          {activeTab === "testcases" && (
            <div className="space-y-4">
              <div className="flex items-center justify-between text-xs text-slate-500">
                <span>Total Generated Test Cases: {question.test_cases?.length || 0}</span>
                <span className="flex items-center space-x-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-500"></span>
                  <span>Sample</span>
                  <span className="w-2.5 h-2.5 rounded-full bg-blue-500"></span>
                  <span>Visible Edge</span>
                  <span className="w-2.5 h-2.5 rounded-full bg-purple-500"></span>
                  <span>Hidden Stress</span>
                </span>
              </div>

              <div className="divide-y divide-slate-200 border border-slate-200 rounded-xl overflow-hidden max-h-[480px] overflow-y-auto">
                {question.test_cases?.map((tc, idx) => (
                  <div key={tc.id || idx} className="p-3.5 bg-white hover:bg-slate-50 transition text-xs">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center space-x-2">
                        <span className="font-bold text-slate-800">Case #{idx}</span>
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                            tc.is_sample
                              ? "bg-emerald-100 text-emerald-800"
                              : tc.is_hidden
                              ? "bg-purple-100 text-purple-800"
                              : "bg-blue-100 text-blue-800"
                          }`}
                        >
                          {tc.is_sample ? "Sample" : tc.is_hidden ? "Hidden Stress" : "Visible Edge"}
                        </span>
                        {tc.description && <span className="text-slate-500 italic">({tc.description})</span>}
                      </div>
                      <span className="font-semibold text-slate-600">{tc.score_weight} pts</span>
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <span className="text-[10px] uppercase font-bold text-slate-400">Standard Input</span>
                        <pre className="p-2 bg-slate-100 rounded text-[11px] font-mono text-slate-800 overflow-x-auto max-h-24">
                          {tc.stdin}
                        </pre>
                      </div>
                      <div>
                        <span className="text-[10px] uppercase font-bold text-slate-400">Expected Output</span>
                        <pre className="p-2 bg-slate-100 rounded text-[11px] font-mono text-slate-800 overflow-x-auto max-h-24">
                          {tc.expected_output}
                        </pre>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === "code" && (
            <div className="space-y-4">
              <div>
                <span className="text-xs font-bold text-slate-700 uppercase mb-1 block">
                  Reference Solution (Python 3)
                </span>
                <pre className="p-4 bg-slate-900 text-slate-100 rounded-xl font-mono text-xs overflow-x-auto max-h-64">
                  {question.reference_solution?.python || "# No Python reference solution"}
                </pre>
              </div>

              {question.reference_solution?.java && (
                <div>
                  <span className="text-xs font-bold text-slate-700 uppercase mb-1 block">
                    Reference Solution (Java)
                  </span>
                  <pre className="p-4 bg-slate-900 text-slate-100 rounded-xl font-mono text-xs overflow-x-auto max-h-64">
                    {question.reference_solution.java}
                  </pre>
                </div>
              )}

              {question.reference_solution?.c && (
                <div>
                  <span className="text-xs font-bold text-slate-700 uppercase mb-1 block">
                    Reference Solution (C)
                  </span>
                  <pre className="p-4 bg-slate-900 text-slate-100 rounded-xl font-mono text-xs overflow-x-auto max-h-64">
                    {question.reference_solution.c}
                  </pre>
                </div>
              )}

              {question.reference_solution?.cpp && (
                <div>
                  <span className="text-xs font-bold text-slate-700 uppercase mb-1 block">
                    Reference Solution (C++)
                  </span>
                  <pre className="p-4 bg-slate-900 text-slate-100 rounded-xl font-mono text-xs overflow-x-auto max-h-64">
                    {question.reference_solution.cpp}
                  </pre>
                </div>
              )}

              {question.brute_force_solution && (
                <div>
                  <span className="text-xs font-bold text-slate-700 uppercase mb-1 block">
                    Differential Brute-Force Solution
                  </span>
                  <pre className="p-4 bg-slate-800 text-slate-200 rounded-xl font-mono text-xs overflow-x-auto max-h-48">
                    {question.brute_force_solution}
                  </pre>
                </div>
              )}
            </div>
          )}

          {activeTab === "logs" && (
            <div className="space-y-3">
              <div className="text-xs text-slate-600 mb-2">
                Execution records captured during isolated sandbox verification runs:
              </div>
              <div className="space-y-2">
                {question.verification_logs?.map((vl, i) => (
                  <div key={vl.id || i} className="p-3 bg-slate-50 border border-slate-200 rounded-xl text-xs">
                    <div className="flex items-center justify-between mb-1.5">
                      <div className="flex items-center space-x-2">
                        <span
                          className={`w-2 h-2 rounded-full ${
                            vl.passed ? "bg-emerald-500" : "bg-rose-500"
                          }`}
                        ></span>
                        <span className="font-bold uppercase text-slate-800">{vl.language}</span>
                        <span className="text-slate-500">• {vl.run_type}</span>
                      </div>
                      <div className="flex items-center space-x-3 text-slate-600">
                        <span>Runtime: {vl.runtime_ms} ms</span>
                        <span>Mem: {vl.memory_kb} KB</span>
                        <span
                          className={`font-bold ${
                            vl.passed ? "text-emerald-700" : "text-rose-700"
                          }`}
                        >
                          {vl.status.toUpperCase()}
                        </span>
                      </div>
                    </div>
                    {vl.stderr && (
                      <pre className="p-2 bg-rose-950 text-rose-200 rounded font-mono text-[11px] overflow-x-auto mt-2">
                        {vl.stderr}
                      </pre>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === "critic" && (
            <div className="space-y-5">
              <div className="p-5 bg-indigo-50 border border-indigo-200 rounded-2xl flex items-center justify-between">
                <div>
                  <h4 className="text-sm font-bold text-indigo-950">LLM Critic Evaluation</h4>
                  <p className="text-xs text-indigo-700 mt-0.5">
                    Multi-dimensional quality assessment scoring clarity, originality, difficulty match, and unambiguity.
                  </p>
                </div>
                <div className="text-right">
                  <div className="text-3xl font-extrabold text-indigo-600">
                    {question.critic_score?.toFixed(1) || "N/A"}
                  </div>
                  <span className="text-[10px] uppercase font-bold text-indigo-400">Overall Score / 10</span>
                </div>
              </div>

              {question.critic_feedback?.scores && (
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  {[
                    { label: "Clarity", val: question.critic_feedback.scores.clarity },
                    { label: "Originality", val: question.critic_feedback.scores.originality },
                    { label: "Difficulty Match", val: question.critic_feedback.scores.difficulty_match },
                    { label: "Unambiguity", val: question.critic_feedback.scores.unambiguity },
                  ].map((s) => (
                    <div key={s.label} className="p-3 bg-white border border-slate-200 rounded-xl text-center">
                      <div className="text-lg font-bold text-slate-900">{s.val?.toFixed(1) || "-"}</div>
                      <div className="text-[11px] text-slate-500 uppercase font-semibold">{s.label}</div>
                    </div>
                  ))}
                </div>
              )}

              {question.critic_feedback?.critique && (
                <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl text-xs space-y-2">
                  <span className="font-bold text-slate-800 uppercase block">Critique Summary:</span>
                  <p className="text-slate-700 leading-relaxed">{question.critic_feedback.critique}</p>
                </div>
              )}

              {question.critic_feedback?.suggested_improvements && question.critic_feedback.suggested_improvements.length > 0 && (
                <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl text-xs space-y-2">
                  <span className="font-bold text-slate-800 uppercase block">Suggested Enhancements:</span>
                  <ul className="list-disc list-inside space-y-1 text-slate-600">
                    {question.critic_feedback.suggested_improvements.map((imp, idx) => (
                      <li key={idx}>{imp}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Bottom Actions Footer */}
        <div className="p-4 bg-slate-50 border-t border-slate-200 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center space-x-2">
            <button
              onClick={handleSave}
              disabled={saving}
              className="inline-flex items-center space-x-1.5 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-bold transition disabled:opacity-50"
            >
              <Save className="w-3.5 h-3.5" />
              <span>{saving ? "Saving..." : "Save Edits"}</span>
            </button>
            <button
              onClick={handleRegenerate}
              className="inline-flex items-center space-x-1.5 px-3 py-2 bg-white border border-slate-300 text-slate-700 hover:bg-slate-100 rounded-xl text-xs font-semibold transition"
            >
              <RefreshCw className="w-3.5 h-3.5 text-amber-600" />
              <span>Regenerate</span>
            </button>
          </div>

          <div className="flex items-center space-x-2">
            {question.status !== "rejected" && (
              <button
                onClick={handleReject}
                className="inline-flex items-center space-x-1.5 px-3 py-2 bg-rose-50 text-rose-700 border border-rose-200 hover:bg-rose-100 rounded-xl text-xs font-bold transition"
              >
                <XCircle className="w-3.5 h-3.5" />
                <span>Reject</span>
              </button>
            )}

            {question.status !== "approved" && question.status !== "published" && (
              <button
                onClick={handleApprove}
                className="inline-flex items-center space-x-1.5 px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-bold transition"
              >
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>Approve</span>
              </button>
            )}

            <button
              onClick={() => handlePublish(false)}
              disabled={publishing}
              className="inline-flex items-center space-x-1.5 px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-xl text-xs font-bold transition disabled:opacity-50"
            >
              <Send className="w-3.5 h-3.5 text-indigo-400" />
              <span>{publishing ? "Publishing..." : "Publish to HackerRank"}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

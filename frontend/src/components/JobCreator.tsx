"use client";

import React, { useState } from "react";
import { CreateJobPayload, Difficulty, QuestionType } from "../lib/types";
import { createGenerationJob } from "../lib/api";
import { Sparkles, Sliders, CheckSquare, Zap, AlertCircle, CheckCircle2 } from "lucide-react";

interface JobCreatorProps {
  onJobCreated?: (jobId: string) => void;
}

const PRESET_TOPICS = [
  "Arrays",
  "Dynamic Programming",
  "Graphs",
  "Binary Trees",
  "Strings",
  "Greedy Algorithms",
  "SQL & Relational",
  "Bit Manipulation",
];

const DIFFICULTY_RUBRICS = {
  Easy: "Single concept, O(N) or O(N log N), <20 lines, small constraints (N <= 10^4)",
  Medium: "Combines 2 concepts, optimal DS/algo, edge cases matter, constraints (N <= 2*10^5)",
  Hard: "Non-obvious insight, advanced algorithms, tight time/memory bounds (N <= 5*10^5)",
  Custom: "Tailored constraints and problem depth based on subtopic specifications",
};

export default function JobCreator({ onJobCreated }: JobCreatorProps) {
  const [topic, setTopic] = useState("Arrays");
  const [customTopic, setCustomTopic] = useState("");
  const [subtopic, setSubtopic] = useState("Sliding Window");
  const [difficulty, setDifficulty] = useState<Difficulty>("Medium");
  const [questionType, setQuestionType] = useState<QuestionType>("coding");
  const [languages, setLanguages] = useState<string[]>(["python", "java", "cpp"]);
  const [count, setCount] = useState<number>(1);
  const [autoPublish, setAutoPublish] = useState<boolean>(false);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const toggleLanguage = (lang: string) => {
    if (languages.includes(lang)) {
      if (languages.length > 1) {
        setLanguages(languages.filter((l) => l !== lang));
      }
    } else {
      setLanguages([...languages, lang]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);
    setSuccessMessage(null);

    const effectiveTopic = topic === "Custom" ? customTopic.trim() : topic;
    if (!effectiveTopic) {
      setError("Please specify a topic.");
      setIsSubmitting(false);
      return;
    }

    try {
      const payload: CreateJobPayload = {
        topic: effectiveTopic,
        subtopic: subtopic.trim() || undefined,
        difficulty,
        question_type: questionType,
        languages,
        count,
        auto_publish: autoPublish,
      };

      const job = await createGenerationJob(payload);
      setSuccessMessage(`Coding challenge for "${effectiveTopic}" was generated successfully and added to the review queue!`);
      if (onJobCreated) {
        onJobCreated(job.id);
      }
    } catch (err: any) {
      setError(err.message || "Failed to launch generation job.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
      <div className="flex items-center justify-between pb-5 border-b border-slate-100 mb-6">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600">
            <Sliders className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-slate-900">New Question Generation Job</h2>
            <p className="text-xs text-slate-500">Configure parameters for AI generation and multi-stage verification</p>
          </div>
        </div>
        <span className="hidden sm:inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
          Docker Sandbox Protected
        </span>
      </div>

      {isSubmitting && (
        <div className="mb-6 p-4 rounded-xl bg-indigo-50 border border-indigo-200 flex items-start space-x-3 text-indigo-900 text-sm animate-pulse">
          <div className="w-5 h-5 flex-shrink-0 mt-0.5 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin" />
          <div>
            <p className="font-semibold text-indigo-950">Generating Challenge with AI Pipeline...</p>
            <p className="text-indigo-700 text-xs mt-0.5">
              Generating problem story, reference solutions, and test cases via Gemini. This typically takes 10–20 seconds. Please hold on!
            </p>
          </div>
        </div>
      )}

      {successMessage && (
        <div className="mb-6 p-4 rounded-xl bg-emerald-50 border border-emerald-200 flex items-start space-x-3 text-emerald-900 text-sm">
          <CheckCircle2 className="w-5 h-5 flex-shrink-0 mt-0.5 text-emerald-600" />
          <div className="flex-1">
            <p className="font-semibold text-emerald-950">Generation Complete!</p>
            <p className="text-emerald-700 text-xs mt-0.5">{successMessage}</p>
          </div>
          <button
            type="button"
            onClick={() => setSuccessMessage(null)}
            className="text-emerald-700 hover:text-emerald-900 text-xs font-bold"
          >
            Dismiss
          </button>
        </div>
      )}

      {error && (
        <div className="mb-6 p-4 rounded-xl bg-rose-50 border border-rose-200 flex items-start space-x-3 text-rose-800 text-sm">
          <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5 text-rose-600" />
          <div>
            <p className="font-semibold">Generation Launch Error</p>
            <p className="text-rose-700 mt-0.5">{error}</p>
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Topic & Subtopic */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
              Core Topic
            </label>
            <select
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-sm font-medium text-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:bg-white transition"
            >
              {PRESET_TOPICS.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
              <option value="Custom">Custom Topic...</option>
            </select>
            {topic === "Custom" && (
              <input
                type="text"
                placeholder="Enter custom topic (e.g. Trie, Segment Trees)..."
                value={customTopic}
                onChange={(e) => setCustomTopic(e.target.value)}
                className="mt-2 w-full px-3.5 py-2 bg-white border border-slate-300 rounded-xl text-sm text-slate-800 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                required
              />
            )}
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
              Sub-Topic / Focus Pattern
            </label>
            <input
              type="text"
              placeholder="e.g. Monotonic Stack, Shortest Path, Two Pointers"
              value={subtopic}
              onChange={(e) => setSubtopic(e.target.value)}
              className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-sm font-medium text-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:bg-white transition"
            />
          </div>
        </div>

        {/* Difficulty Selector with Rubric Card */}
        <div>
          <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
            Target Difficulty Level
          </label>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
            {(["Easy", "Medium", "Hard", "Custom"] as Difficulty[]).map((level) => {
              const selected = difficulty === level;
              return (
                <button
                  type="button"
                  key={level}
                  onClick={() => setDifficulty(level)}
                  className={`py-2.5 px-3 rounded-xl border text-sm font-semibold transition-all ${
                    selected
                      ? "bg-indigo-600 text-white border-indigo-600 shadow-md shadow-indigo-100"
                      : "bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100"
                  }`}
                >
                  {level}
                </button>
              );
            })}
          </div>
          <div className="mt-2 p-3 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-600 flex items-start space-x-2">
            <span className="font-bold text-slate-800 flex-shrink-0">Rubric Spec:</span>
            <span>{DIFFICULTY_RUBRICS[difficulty]}</span>
          </div>
        </div>

        {/* Question Type & Target Languages */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
              Question Type
            </label>
            <select
              value={questionType}
              onChange={(e) => setQuestionType(e.target.value as QuestionType)}
              className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-sm font-medium text-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:bg-white transition"
            >
              <option value="coding">Standard Algorithmic Coding</option>
              <option value="debugging">Code Debugging Challenge</option>
              <option value="sql">SQL Query & Schema Task</option>
              <option value="mcq">Multiple Choice Question</option>
              <option value="output-prediction">Output Prediction</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
              Reference Languages
            </label>
            <div className="flex items-center space-x-2 pt-1">
              {[
                { id: "c", label: "C" },
                { id: "cpp", label: "C++ 20" },
                { id: "python", label: "Python 3" },
                { id: "java", label: "Java 17" },
                { id: "sql", label: "PostgreSQL" },
              ].map((lang) => {
                const active = languages.includes(lang.id);
                return (
                  <button
                    type="button"
                    key={lang.id}
                    onClick={() => toggleLanguage(lang.id)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition ${
                      active
                        ? "bg-slate-900 text-white border-slate-900"
                        : "bg-white text-slate-600 border-slate-200 hover:bg-slate-50"
                    }`}
                  >
                    {lang.label}
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        {/* Count Slider & Auto-Publish Toggle */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2 border-t border-slate-100">
          <div>
            <div className="flex justify-between items-center mb-2">
              <label className="text-xs font-semibold text-slate-700 uppercase tracking-wider">
                Number of Questions
              </label>
              <span className="text-sm font-bold text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded-md">
                {count} {count === 1 ? "Question" : "Questions"}
              </span>
            </div>
            <input
              type="range"
              min={1}
              max={10}
              value={count}
              onChange={(e) => setCount(parseInt(e.target.value, 10))}
              className="w-full accent-indigo-600 cursor-pointer"
            />
            <div className="flex justify-between text-[11px] text-slate-400 mt-1">
              <span>1</span>
              <span>5</span>
              <span>10</span>
            </div>
          </div>

          <div className="flex items-center justify-between p-3.5 bg-slate-50 rounded-xl border border-slate-200">
            <div>
              <div className="flex items-center space-x-2">
                <Zap className="w-4 h-4 text-amber-500" />
                <span className="text-xs font-bold text-slate-900">Auto-Publish to HackerRank</span>
              </div>
              <p className="text-[11px] text-slate-500 mt-0.5">
                Automatically publish upon sandbox verification & critic score approval (bypasses manual queue)
              </p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer ml-3 flex-shrink-0">
              <input
                type="checkbox"
                checked={autoPublish}
                onChange={(e) => setAutoPublish(e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-slate-300 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-indigo-600"></div>
            </label>
          </div>
        </div>

        {/* Submit Button */}
        <div className="pt-2">
          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full py-3.5 px-4 bg-gradient-to-r from-indigo-600 to-indigo-700 hover:from-indigo-700 hover:to-indigo-800 text-white font-bold rounded-xl shadow-lg shadow-indigo-200 flex items-center justify-center space-x-2 transition disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSubmitting ? (
              <div className="flex items-center space-x-2">
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                <span>Initializing Pipeline...</span>
              </div>
            ) : (
              <>
                <Sparkles className="w-5 h-5 text-indigo-200" />
                <span>Launch Question Generation Job</span>
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}

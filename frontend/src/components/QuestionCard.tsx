"use client";

import React from "react";
import { Question } from "../lib/types";
import { CheckCircle2, XCircle, RefreshCw, Download, Star, Code2, ExternalLink } from "lucide-react";
import { getExportZipUrl } from "../lib/api";

interface QuestionCardProps {
  question: Question;
  onSelect?: (question: Question) => void;
  onApprove?: (id: string) => void;
  onReject?: (id: string) => void;
  onRegenerate?: (id: string) => void;
  showActions?: boolean;
}

export default function QuestionCard({
  question,
  onSelect,
  onApprove,
  onReject,
  onRegenerate,
  showActions = true,
}: QuestionCardProps) {
  const getDifficultyColor = (diff: string) => {
    switch (diff.toLowerCase()) {
      case "easy":
        return "bg-emerald-50 text-emerald-700 border-emerald-200";
      case "medium":
        return "bg-amber-50 text-amber-700 border-amber-200";
      case "hard":
        return "bg-rose-50 text-rose-700 border-rose-200";
      default:
        return "bg-indigo-50 text-indigo-700 border-indigo-200";
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "published":
        return "bg-emerald-100 text-emerald-800 border-emerald-300";
      case "approved":
        return "bg-blue-100 text-blue-800 border-blue-300";
      case "review_ready":
        return "bg-amber-100 text-amber-800 border-amber-300";
      case "rejected":
        return "bg-rose-100 text-rose-800 border-rose-300";
      default:
        return "bg-slate-100 text-slate-800 border-slate-300";
    }
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm hover:shadow-md transition p-5 flex flex-col justify-between">
      <div>
        <div className="flex items-start justify-between gap-3 mb-2">
          <div className="flex flex-wrap items-center gap-1.5">
            <span
              className={`px-2 py-0.5 rounded text-[11px] font-bold uppercase tracking-wider border ${getDifficultyColor(
                question.difficulty
              )}`}
            >
              {question.difficulty}
            </span>
            <span
              className={`px-2 py-0.5 rounded text-[11px] font-semibold border ${getStatusColor(
                question.status
              )}`}
            >
              {question.status.replace("_", " ").toUpperCase()}
            </span>
            {question.subtopic && (
              <span className="px-2 py-0.5 rounded text-[11px] font-medium bg-slate-100 text-slate-600 border border-slate-200">
                {question.subtopic}
              </span>
            )}
          </div>

          {question.critic_score !== undefined && question.critic_score !== null && (
            <div className="flex items-center space-x-1 px-2 py-0.5 rounded-full bg-indigo-50 border border-indigo-100 text-indigo-700 text-xs font-bold">
              <Star className="w-3 h-3 fill-indigo-600 text-indigo-600" />
              <span>{question.critic_score.toFixed(1)}/10</span>
            </div>
          )}
        </div>

        <h3
          onClick={() => onSelect && onSelect(question)}
          className="text-base font-bold text-slate-900 hover:text-indigo-600 cursor-pointer transition line-clamp-1 mb-1"
        >
          {question.title}
        </h3>

        <p className="text-xs text-slate-500 line-clamp-2 mb-3">{question.story}</p>

        {/* Tags */}
        <div className="flex flex-wrap gap-1 mb-4">
          {question.tags.map((t) => (
            <span
              key={t}
              className="text-[10px] font-medium px-2 py-0.5 rounded-md bg-slate-100 text-slate-600"
            >
              #{t}
            </span>
          ))}
        </div>
      </div>

      <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
        <div className="flex items-center space-x-3 text-slate-500">
          <span className="flex items-center space-x-1">
            <Code2 className="w-3.5 h-3.5" />
            <span>{question.test_cases?.length || 0} Cases</span>
          </span>
          {question.hackerrank_url && (
            <a
              href={question.hackerrank_url}
              target="_blank"
              rel="noreferrer"
              className="flex items-center space-x-1 text-indigo-600 font-semibold hover:underline"
            >
              <ExternalLink className="w-3 h-3" />
              <span>HackerRank</span>
            </a>
          )}
        </div>

        {showActions && (
          <div className="flex items-center space-x-1.5">
            <a
              href={getExportZipUrl(question.id)}
              download
              title="Download HackerRank ZIP challenge package"
              className="p-1.5 rounded-lg text-slate-600 hover:text-indigo-600 hover:bg-slate-100 transition"
            >
              <Download className="w-4 h-4" />
            </a>

            {question.status === "review_ready" && (
              <>
                {onReject && (
                  <button
                    onClick={() => onReject(question.id)}
                    title="Reject question"
                    className="p-1.5 rounded-lg text-rose-600 hover:bg-rose-50 transition"
                  >
                    <XCircle className="w-4 h-4" />
                  </button>
                )}
                {onRegenerate && (
                  <button
                    onClick={() => onRegenerate(question.id)}
                    title="Regenerate question"
                    className="p-1.5 rounded-lg text-amber-600 hover:bg-amber-50 transition"
                  >
                    <RefreshCw className="w-4 h-4" />
                  </button>
                )}
                {onApprove && (
                  <button
                    onClick={() => onApprove(question.id)}
                    title="Approve for Publishing"
                    className="p-1.5 rounded-lg bg-emerald-600 text-white hover:bg-emerald-700 transition"
                  >
                    <CheckCircle2 className="w-4 h-4" />
                  </button>
                )}
              </>
            )}

            <button
              onClick={() => onSelect && onSelect(question)}
              className="px-2.5 py-1 rounded-lg bg-slate-900 text-white font-medium hover:bg-slate-800 transition text-[11px]"
            >
              Inspect
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

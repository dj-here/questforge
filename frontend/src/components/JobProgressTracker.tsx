"use client";

import React, { useEffect, useState } from "react";
import { GenerationJob } from "../lib/types";
import { fetchJob } from "../lib/api";
import { CheckCircle2, Clock, AlertTriangle, Loader2 } from "lucide-react";

interface JobProgressTrackerProps {
  jobId: string;
  onCompleted?: () => void;
}

const STAGES = [
  { id: "pending", label: "Queued" },
  { id: "spec_stage", label: "1. Spec" },
  { id: "generate_stage", label: "2. Generate" },
  { id: "test_case_stage", label: "3. Test Cases" },
  { id: "verification_stage", label: "4. Verify" },
  { id: "quality_stage", label: "5. Critic" },
  { id: "dedup_stage", label: "6. Dedup" },
  { id: "completed", label: "Persisted" },
];

export default function JobProgressTracker({ jobId, onCompleted }: JobProgressTrackerProps) {
  const [job, setJob] = useState<GenerationJob | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let interval: any;

    const poll = async () => {
      try {
        const data = await fetchJob(jobId);
        setJob(data);
        if (data.status === "completed") {
          clearInterval(interval);
          if (onCompleted) onCompleted();
        } else if (data.status === "failed") {
          clearInterval(interval);
        }
      } catch (err: any) {
        setError(err.message);
        clearInterval(interval);
      }
    };

    poll();
    interval = setInterval(poll, 2000);
    return () => clearInterval(interval);
  }, [jobId, onCompleted]);

  if (error) {
    return (
      <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-rose-700 text-xs flex items-center space-x-2">
        <AlertTriangle className="w-4 h-4 flex-shrink-0" />
        <span>Failed to monitor job: {error}</span>
      </div>
    );
  }

  if (!job) {
    return (
      <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl flex items-center justify-center space-x-2 text-slate-500 text-xs">
        <Loader2 className="w-4 h-4 animate-spin text-indigo-600" />
        <span>Loading pipeline job {jobId}...</span>
      </div>
    );
  }

  const currentStageIdx = STAGES.findIndex((s) => s.id === job.current_stage);

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-2">
          <span className="text-xs font-bold text-slate-900">Job {job.id.slice(0, 12)}</span>
          <span className="text-xs text-slate-500">
            • {job.topic} ({job.difficulty})
          </span>
        </div>
        <div className="flex items-center space-x-2">
          {job.status === "running" && (
            <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold bg-amber-50 text-amber-700 border border-amber-200">
              <Loader2 className="w-3 h-3 mr-1 animate-spin" /> In Progress ({Math.round(job.progress)}%)
            </span>
          )}
          {job.status === "completed" && (
            <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
              <CheckCircle2 className="w-3 h-3 mr-1" /> Complete
            </span>
          )}
          {job.status === "failed" && (
            <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold bg-rose-50 text-rose-700 border border-rose-200">
              <AlertTriangle className="w-3 h-3 mr-1" /> Failed
            </span>
          )}
        </div>
      </div>

      {/* Progress Bar */}
      <div className="w-full bg-slate-100 rounded-full h-2 mb-4 overflow-hidden">
        <div
          className={`h-full transition-all duration-500 ${
            job.status === "failed" ? "bg-rose-500" : "bg-indigo-600"
          }`}
          style={{ width: `${Math.max(5, job.progress)}%` }}
        ></div>
      </div>

      {/* Stage indicators */}
      <div className="grid grid-cols-4 sm:grid-cols-8 gap-1.5">
        {STAGES.map((st, i) => {
          let stageState = "pending";
          if (job.status === "completed") {
            stageState = "done";
          } else if (job.status === "failed" && st.id === job.current_stage) {
            stageState = "failed";
          } else if (i < currentStageIdx) {
            stageState = "done";
          } else if (i === currentStageIdx) {
            stageState = "active";
          }

          return (
            <div
              key={st.id}
              className={`p-1.5 rounded-lg text-center text-[10px] font-medium border ${
                stageState === "done"
                  ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                  : stageState === "active"
                  ? "bg-indigo-50 text-indigo-700 border-indigo-300 font-bold"
                  : stageState === "failed"
                  ? "bg-rose-50 text-rose-700 border-rose-200"
                  : "bg-slate-50 text-slate-400 border-slate-100"
              }`}
            >
              {st.label}
            </div>
          );
        })}
      </div>

      {job.error_message && (
        <div className="mt-3 p-2.5 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 text-[11px]">
          <span className="font-bold">Error:</span> {job.error_message}
        </div>
      )}
    </div>
  );
}

"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";
import { api, Stats } from "@/lib/api";

export default function AnalyticsPage() {
  const { user } = useAuth();
  const router = useRouter();
  const [stats, setStats] = useState<Stats | null>(null);

  useEffect(() => {
    if (!user) { router.push("/login"); return; }
    api.user.stats().then(setStats).catch(() => {});
  }, [user, router]);

  if (!user) return <div className="p-8 text-center">Redirecting...</div>;

  if (!stats) return <div className="p-8 text-center">Loading analytics...</div>;

  const maxVal = Math.max(stats.exams_predicted, stats.files_uploaded, stats.summaries_generated, stats.teacher_mode_sessions, 1);

  const bars = [
    { label: "Exams Predicted", value: stats.exams_predicted, color: "bg-indigo-500" },
    { label: "Files Uploaded", value: stats.files_uploaded, color: "bg-green-500" },
    { label: "Summaries", value: stats.summaries_generated, color: "bg-purple-500" },
    { label: "Teacher Sessions", value: stats.teacher_mode_sessions, color: "bg-orange-500" },
  ];

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-2">Analytics</h1>
      <p className="text-gray-600 mb-8">Track your AI learning activity.</p>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        {bars.map((b) => (
          <div key={b.label} className="text-center">
            <div className="text-3xl font-bold text-gray-800">{b.value}</div>
            <div className="text-sm text-gray-600">{b.label}</div>
          </div>
        ))}
      </div>

      <div className="space-y-4">
        {bars.map((b) => (
          <div key={b.label}>
            <div className="flex justify-between text-sm mb-1">
              <span>{b.label}</span>
              <span className="text-gray-500">{b.value}</span>
            </div>
            <div className="bg-gray-200 rounded-full h-4 overflow-hidden">
              <div className={`${b.color} h-full rounded-full transition-all duration-1000`} style={{ width: `${(b.value / maxVal) * 100}%` }} />
            </div>
          </div>
        ))}
      </div>

      <div className="mt-8 bg-gray-50 rounded-2xl p-6">
        <h3 className="font-semibold mb-2">Account Status</h3>
        <p>{stats.is_premium ? "Premium - All features unlocked" : "Free - Limited access"}</p>
      </div>
    </div>
  );
}

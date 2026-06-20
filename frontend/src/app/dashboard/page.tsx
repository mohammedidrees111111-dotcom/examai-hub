"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";
import { api, Stats, ReferralInfo, UserScore } from "@/lib/api";
import Link from "next/link";
import { Suspense } from "react";
import AdBanner from "@/components/AdBanner";

function DashboardContent() {
  const { user } = useAuth();
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(false);
  const [payResult, setPayResult] = useState<"success" | "cancelled" | "">("");
  const [referral, setReferral] = useState<ReferralInfo | null>(null);
  const [score, setScore] = useState<UserScore | null>(null);
  const [shareMsg, setShareMsg] = useState("");
  const [error, setError] = useState("");
  const router = useRouter();
  const searchParams = useSearchParams();

  const handleCapture = useCallback(async (orderId: string) => {
    setLoading(true);
    try {
      const res = await api.payments.captureOrder(orderId);
      if (res.premium_activated) {
        setPayResult("success");
        sessionStorage.removeItem("pending_order_id");
        window.location.reload();
      } else {
        setPayResult("");
        setError("Payment not completed. Please try again.");
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Payment failed";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!user) { router.push("/login"); return; }

    const paymentParam = searchParams.get("payment");
    const orderIdParam = searchParams.get("order_id");
    const savedOrderId = sessionStorage.getItem("pending_order_id");

    if ((paymentParam === "success" || paymentParam === "demo") && orderIdParam) {
      handleCapture(orderIdParam);
    } else if (paymentParam === "success" && savedOrderId) {
      handleCapture(savedOrderId);
    } else if (paymentParam === "cancelled") {
      setPayResult("cancelled");
      sessionStorage.removeItem("pending_order_id");
    }

    api.user.stats().then(setStats).catch(() => {});
    api.growth.referral().then(setReferral).catch(() => {});
    api.growth.score().then(setScore).catch(() => {});
    api.growth.checkAchievements().catch(() => {});
  }, [user, router, searchParams, handleCapture]);

  if (!user) return <div className="p-8 text-center">Redirecting...</div>;

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold">Welcome, {user.full_name || user.username}</h1>
          <p className="text-gray-600 mt-1">
            {user.is_premium ? (
              <span className="text-yellow-600 font-semibold">Premium Account</span>
            ) : (
              <span>Free Account · <Link href="#upgrade" className="text-indigo-600 underline">Upgrade</Link></span>
            )}
          </p>
        </div>
      </div>

      {payResult === "success" && (
        <div className="bg-green-50 border border-green-200 text-green-700 p-4 rounded-xl mb-6">
          Payment successful! Your premium features are now active.
        </div>
      )}
      {payResult === "cancelled" && (
        <div className="bg-yellow-50 border border-yellow-200 text-yellow-700 p-4 rounded-xl mb-6">
          Payment was cancelled. You can try again anytime.
        </div>
      )}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded-xl mb-6">
          {error} <button onClick={() => setError("")} className="ml-2 underline">Dismiss</button>
        </div>
      )}

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        {[
          { label: "Exams Predicted", value: stats?.exams_predicted ?? "-", color: "bg-indigo-100 text-indigo-700" },
          { label: "Files Uploaded", value: stats?.files_uploaded ?? "-", color: "bg-green-100 text-green-700" },
          { label: "Summaries", value: stats?.summaries_generated ?? "-", color: "bg-purple-100 text-purple-700" },
          { label: "Teacher Sessions", value: stats?.teacher_mode_sessions ?? "-", color: "bg-orange-100 text-orange-700" },
        ].map((s) => (
          <div key={s.label} className={`rounded-xl p-6 ${s.color}`}>
            <div className="text-3xl font-bold">{s.value}</div>
            <div className="text-sm mt-1 opacity-80">{s.label}</div>
          </div>
        ))}
      </div>

      <AdBanner slot="dashboard-mid" format="auto" className="mb-8" />

      <h2 className="text-xl font-semibold mb-4">Quick Actions</h2>
      <div className="grid md:grid-cols-2 gap-6 mb-12">
        {[
          { title: "AI Lab", desc: "Exam prediction, teacher mode, and PDF summarization", href: "/ai-lab", color: "border-indigo-200 hover:border-indigo-400" },
          { title: "Analytics", desc: "View your learning stats", href: "/analytics", color: "border-purple-200 hover:border-purple-400" },
        ].map((a) => (
          <Link key={a.title} href={a.href} className={`border-2 rounded-2xl p-6 card-hover ${a.color}`}>
            <h3 className="text-lg font-semibold mb-2">{a.title}</h3>
            <p className="text-gray-600 text-sm">{a.desc}</p>
          </Link>
        ))}
      </div>

      {/* Growth Section */}
      <div className="grid md:grid-cols-3 gap-6 mb-12">
        {score && (
          <div className="bg-gradient-to-br from-emerald-500 to-teal-600 text-white rounded-2xl p-6 text-center">
            <div className="text-sm text-emerald-100 mb-1">Study Readiness</div>
            <div className="text-5xl font-extrabold mb-2">{score.study_readiness}</div>
            <div className="text-emerald-100 text-sm">out of 100</div>
            <div className="mt-3 bg-white/20 rounded-full px-3 py-1 text-sm inline-block">
              {score.exam_confidence} Confidence
            </div>
          </div>
        )}

        {referral && (
          <div className="border border-amber-200 bg-amber-50 rounded-2xl p-6">
            <h3 className="font-semibold mb-2">Invite Friends</h3>
            <p className="text-sm text-gray-600 mb-3">Both get {referral.credits_earned > 0 ? "500" : "500"} free credits</p>
            <div className="flex gap-2 mb-3">
              <input readOnly value={referral.referral_code} className="flex-1 border border-amber-300 rounded-lg px-3 py-2 text-sm bg-white font-mono" />
              <button onClick={() => { navigator.clipboard.writeText(referral.referral_link); setShareMsg("Copied!"); setTimeout(() => setShareMsg(""), 2000); }} className="bg-amber-600 text-white px-3 py-2 rounded-lg text-sm hover:bg-amber-700">
                {shareMsg || "Copy"}
              </button>
            </div>
            <p className="text-xs text-gray-500">{referral.total_referrals} friends joined</p>
          </div>
        )}

        <button
          onClick={async () => {
            try {
              const res = await api.growth.share({
                title: "My Study Analysis",
                subject: "ExamAI Hub",
                course: "",
                data: { summary: "Check out my AI-generated study pack on ExamAI Hub!", stats },
              });
              await navigator.clipboard.writeText(res.share_url);
              setShareMsg("Share link copied!");
              setTimeout(() => setShareMsg(""), 2000);
              api.growth.checkAchievements().catch(() => {});
            } catch { setShareMsg("Failed to share"); }
          }}
          className="border-2 border-indigo-200 hover:border-indigo-400 rounded-2xl p-6 text-center bg-white transition"
        >
          <div className="text-4xl mb-2">🔗</div>
          <div className="font-semibold text-indigo-700">Share Study Pack</div>
          <div className="text-sm text-gray-500 mt-1">Generate & share your results</div>
          {shareMsg && <div className="mt-2 text-xs text-green-600 font-medium">{shareMsg}</div>}
        </button>
      </div>

      {!user.is_premium && (
        <div id="upgrade" className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-2xl p-8 text-center">
          <h2 className="text-2xl font-bold mb-4">Upgrade to Premium</h2>
          <p className="mb-6 text-indigo-100">Unlock unlimited predictions, teacher mode, and more.</p>
          <button
            onClick={async () => {
              setLoading(true);
              try {
                const order = await api.payments.createOrder("monthly");
                if (order.status === "demo") {
                  const res = await api.payments.activateDemo("monthly");
                  if (res.premium_activated) {
                    setPayResult("success");
                    window.location.reload();
                  }
                } else if (order.approval_url) {
                  sessionStorage.setItem("pending_order_id", order.order_id);
                  window.location.href = order.approval_url;
                } else {
                  alert("Payment system unavailable. Please try again later.");
                }
              } catch (err: unknown) {
                const msg = err instanceof Error ? err.message : "Payment failed";
                if (msg.includes("Real payment required")) {
                  alert("Demo payments are disabled. Real PayPal is configured — you will be redirected to complete your payment.");
                } else {
                  alert(msg);
                }
              } finally {
                setLoading(false);
              }
            }}
            disabled={loading}
            className="bg-white text-indigo-700 px-8 py-3 rounded-xl font-semibold hover:bg-indigo-50 transition disabled:opacity-50"
          >
            {loading ? "Activating..." : "Upgrade to Premium"}
          </button>
        </div>
      )}
    </div>
  );
}

export default function DashboardPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center">Loading dashboard...</div>}>
      <DashboardContent />
    </Suspense>
  );
}

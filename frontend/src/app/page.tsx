"use client";

import Link from "next/link";
import { useAuth } from "@/contexts/AuthContext";

export default function HomePage() {
  const { user } = useAuth();

  return (
    <div>
      {/* Hero */}
      <section className="gradient-hero text-white py-24">
        <div className="max-w-5xl mx-auto px-4 text-center">
          <h1 className="text-5xl font-extrabold mb-6">ExamAI Hub</h1>
          <p className="text-xl mb-8 text-indigo-100 max-w-2xl mx-auto">
            Predict exam questions, get AI-powered explanations, and summarize your study materials in seconds.
          </p>
          <div className="flex gap-4 justify-center">
            {user ? (
              <Link href="/dashboard" className="bg-white text-indigo-700 px-8 py-3 rounded-xl font-semibold hover:bg-indigo-50 transition">
                Go to Dashboard
              </Link>
            ) : (
              <>
                <Link href="/register" className="bg-white text-indigo-700 px-8 py-3 rounded-xl font-semibold hover:bg-indigo-50 transition">
                  Get Started Free
                </Link>
                <Link href="/login" className="border-2 border-white text-white px-8 py-3 rounded-xl font-semibold hover:bg-white/10 transition">
                  Login
                </Link>
              </>
            )}
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-20 bg-gray-50">
        <div className="max-w-6xl mx-auto px-4">
          <h2 className="text-3xl font-bold text-center mb-12">Powerful AI Tools</h2>
          <div className="grid md:grid-cols-3 gap-8">
            {[
              { title: "Exam Predictor", desc: "Upload your notes and our AI predicts likely exam questions with answers.", icon: "🎯" },
              { title: "Teacher Mode", desc: "Get detailed explanations, key concepts, and study recommendations.", icon: "👨‍🏫" },
              { title: "AI Summarizer", desc: "Condense long materials into concise summaries with keyword extraction.", icon: "📄" },
            ].map((f) => (
              <div key={f.title} className="bg-white p-8 rounded-2xl shadow-sm card-hover">
                <div className="text-4xl mb-4">{f.icon}</div>
                <h3 className="text-xl font-semibold mb-2">{f.title}</h3>
                <p className="text-gray-600">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section className="py-20">
        <div className="max-w-5xl mx-auto px-4 text-center">
          <h2 className="text-3xl font-bold mb-4">Simple Pricing</h2>
          <p className="text-gray-600 mb-12">Choose the plan that fits your needs</p>
          <div className="grid md:grid-cols-3 gap-8">
            {[
              { plan: "Free", price: "$0", features: ["5 exam predictions/mo", "Basic summarizer", "5 uploads/mo"] },
              { plan: "Monthly", price: "$9.99", features: ["Unlimited predictions", "Full teacher mode", "Unlimited uploads", "Priority support"] },
              { plan: "Lifetime", price: "$149.99", features: ["Everything in Monthly", "Lifetime access", "VIP support", "Early features"] },
            ].map((p) => (
              <div key={p.plan} className={`border rounded-2xl p-8 card-hover ${p.plan === "Monthly" ? "border-indigo-500 ring-2 ring-indigo-200" : ""}`}>
                <h3 className="text-xl font-semibold mb-2">{p.plan}</h3>
                <p className="text-4xl font-bold text-indigo-600 mb-4">{p.price}</p>
                <ul className="text-gray-600 space-y-2 mb-6">
                  {p.features.map((f) => <li key={f}>{f}</li>)}
                </ul>
                <Link href="/register" className="block bg-indigo-600 text-white py-3 rounded-xl font-semibold hover:bg-indigo-700">
                  Get Started
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-gray-400 py-8 text-center text-sm">
        ExamAI Hub. Built for students who want to ace their exams.
      </footer>
    </div>
  );
}

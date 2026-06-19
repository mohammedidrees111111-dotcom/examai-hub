import Link from "next/link";
import Footer from "@/components/Footer";

export default function AboutPage() {
  return (
    <div className="max-w-4xl mx-auto px-4 py-12">
      <h1 className="text-3xl font-bold mb-8">About ExamAI Hub</h1>

      <div className="space-y-8 text-gray-700">
        <section>
          <h2 className="text-xl font-semibold mb-3 text-gray-900">Our Mission</h2>
          <p className="text-lg">ExamAI Hub transforms academic materials into exam-ready intelligence. We use advanced AI to analyze textbooks, lectures, and past exams — generating high-probability exam questions, comprehensive summaries, and personalized study plans.</p>
        </section>

        <section>
          <h2 className="text-xl font-semibold mb-3 text-gray-900">What We Offer</h2>
          <div className="grid md:grid-cols-3 gap-4 mt-4">
            {[
              { title: "AI Summarizer", desc: "Transform 200-page books into comprehensive study guides. Hierarchical chapter-by-chapter analysis preserves 40-70% of key information." },
              { title: "Exam Predictor", desc: "AI analyzes your material and predicts likely exam questions. MCQ, essay, short answer, and problem-solving types included." },
              { title: "Teacher Mode", desc: "Understand how your professor thinks. Detect teaching patterns, emphasis signals, and exam question preferences." },
              { title: "Flashcards", desc: "Auto-generated flashcards from your study material with difficulty ratings." },
              { title: "Multi-Language", desc: "Supports 20+ languages including Arabic, English, Spanish, French, German, and more." },
              { title: "Study Plans", desc: "Custom study schedules based on your material and available study time." },
            ].map((f) => (
              <div key={f.title} className="bg-gray-50 rounded-xl p-5">
                <h3 className="font-semibold text-gray-900 mb-1">{f.title}</h3>
                <p className="text-sm text-gray-600">{f.desc}</p>
              </div>
            ))}
          </div>
        </section>

        <section>
          <h2 className="text-xl font-semibold mb-3 text-gray-900">Why Choose Us</h2>
          <ul className="space-y-2 list-disc pl-5">
            <li>20+ languages supported with automatic detection</li>
            <li>Hierarchical summarization preserves knowledge, not just compresses text</li>
            <li>PayPal-integrated payments with subscription and pay-per-use options</li>
            <li>Teacher fingerprint analysis for personalized exam predictions</li>
            <li>Self-improving AI that learns from your feedback</li>
            <li>300MB+ PDF support — process entire textbooks</li>
          </ul>
        </section>

        <div className="bg-indigo-50 border border-indigo-200 rounded-2xl p-8 text-center">
          <h2 className="text-2xl font-bold text-indigo-700 mb-3">Ready to ace your exams?</h2>
          <p className="text-indigo-600 mb-4">Join thousands of students using AI to study smarter.</p>
          <Link href="/register" className="bg-indigo-600 text-white px-8 py-3 rounded-xl font-semibold hover:bg-indigo-700 transition inline-block">
            Get Started Free
          </Link>
        </div>
      </div>
      <Footer />
    </div>
  );
}

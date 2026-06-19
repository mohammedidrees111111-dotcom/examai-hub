import Footer from "@/components/Footer";

export default function TermsPage() {
  return (
    <div className="max-w-4xl mx-auto px-4 py-12">
      <h1 className="text-3xl font-bold mb-8">Terms of Service / شروط الاستخدام</h1>
      
      <div className="prose max-w-none space-y-8 text-gray-700">
        <section>
          <h2 className="text-xl font-semibold mb-3 text-gray-900">1. Acceptance of Terms</h2>
          <p>By accessing or using ExamAI Hub, you agree to be bound by these Terms of Service. If you do not agree, please do not use our services.</p>
        </section>

        <section>
          <h2 className="text-xl font-semibold mb-3 text-gray-900">2. Service Description</h2>
          <p>ExamAI Hub provides AI-powered academic tools including document summarization, exam question prediction, teacher behavior analysis, and study material generation. These tools are intended for educational purposes only.</p>
        </section>

        <section>
          <h2 className="text-xl font-semibold mb-3 text-gray-900">3. User Responsibilities</h2>
          <p>You are responsible for maintaining the confidentiality of your account credentials. You agree not to upload content that violates copyright laws, contains malware, or is otherwise illegal. You retain ownership of content you upload; we only process it for AI analysis.</p>
        </section>

        <section>
          <h2 className="text-xl font-semibold mb-3 text-gray-900">4. Payments & Subscriptions</h2>
          <p>Premium subscriptions and usage-based credits are processed through PayPal. All payments are non-refundable unless required by law. Subscription plans auto-renew unless cancelled. Free tier includes limited usage; premium and pay-per-use options are available.</p>
        </section>

        <section>
          <h2 className="text-xl font-semibold mb-3 text-gray-900">5. AI Output Disclaimer</h2>
          <p>AI-generated content (summaries, exam predictions, teacher analysis) is produced by automated systems and may contain inaccuracies. This content should be used as a study supplement only and does not guarantee exam performance. Always verify important information against official course materials.</p>
        </section>

        <section>
          <h2 className="text-xl font-semibold mb-3 text-gray-900">6. Limitation of Liability</h2>
          <p>ExamAI Hub is provided "as is" without warranties of any kind. We are not liable for any damages arising from the use of our services, including but not limited to academic performance, exam results, or data loss.</p>
        </section>

        <section>
          <h2 className="text-xl font-semibold mb-3 text-gray-900">7. Termination</h2>
          <p>We reserve the right to suspend or terminate accounts that violate these terms. You may delete your account at any time through your account settings or by contacting us.</p>
        </section>

        <p className="text-sm text-gray-400 pt-4">Last updated: June 2026</p>
      </div>
      <Footer />
    </div>
  );
}

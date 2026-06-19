import Footer from "@/components/Footer";

export default function PrivacyPage() {
  return (
    <div className="max-w-4xl mx-auto px-4 py-12">
      <h1 className="text-3xl font-bold mb-8">Privacy Policy / سياسة الخصوصية</h1>
      
      <div className="prose max-w-none space-y-8 text-gray-700">
        <section>
          <h2 className="text-xl font-semibold mb-3 text-gray-900">1. Information We Collect</h2>
          <p>We collect information you provide directly, including your email address, username, and account credentials when you register. We also collect usage data including uploaded documents, AI analysis history, and payment information processed through PayPal.</p>
          <p className="mt-2 text-right" dir="rtl">نجمع المعلومات التي تقدمها مباشرة، بما في ذلك عنوان بريدك الإلكتروني واسم المستخدم وبيانات الاعتماد عند التسجيل. كما نجمع بيانات الاستخدام بما في ذلك المستندات المرفوعة وتحليلات الذكاء الاصطناعي ومعلومات الدفع عبر PayPal.</p>
        </section>

        <section>
          <h2 className="text-xl font-semibold mb-3 text-gray-900">2. How We Use Information</h2>
          <p>Your information is used to provide and improve our AI-powered academic services, process payments, communicate with you about your account, and comply with legal obligations. Uploaded documents are processed for AI analysis only and are not shared with third parties.</p>
        </section>

        <section>
          <h2 className="text-xl font-semibold mb-3 text-gray-900">3. Cookies & Google AdSense</h2>
          <p>We use cookies for authentication and to improve your experience. Third-party vendors, including Google, use cookies to serve ads based on your prior visits. Google's use of advertising cookies enables it and its partners to serve ads based on your visit to our site and/or other sites on the Internet. You may opt out of personalized advertising by visiting <a href="https://www.google.com/settings/ads" className="text-indigo-600 underline">Google Ads Settings</a>.</p>
        </section>

        <section>
          <h2 className="text-xl font-semibold mb-3 text-gray-900">4. Data Security</h2>
          <p>We implement security measures including encryption, secure servers, and access controls. Passwords are hashed using bcrypt. Payment processing is handled securely through PayPal. However, no method of transmission over the Internet is 100% secure.</p>
        </section>

        <section>
          <h2 className="text-xl font-semibold mb-3 text-gray-900">5. Your Rights</h2>
          <p>You have the right to access, correct, or delete your personal data. You can delete your account at any time by contacting us. We retain your data only as long as necessary to provide our services.</p>
        </section>

        <section>
          <h2 className="text-xl font-semibold mb-3 text-gray-900">6. Contact</h2>
          <p>For privacy-related inquiries, contact us at: <a href="/contact" className="text-indigo-600 underline">Contact Page</a></p>
        </section>

        <p className="text-sm text-gray-400 pt-4">Last updated: June 2026</p>
      </div>
      <Footer />
    </div>
  );
}

import Link from "next/link";

export default function Footer() {
  return (
    <footer className="mt-16 border-t border-gray-200 pt-8 pb-12">
      <div className="grid md:grid-cols-3 gap-8 text-sm text-gray-500">
        <div>
          <h4 className="font-semibold text-gray-700 mb-3">ExamAI Hub</h4>
          <p className="leading-relaxed">AI-powered academic tools for exam prediction, summarization, and study optimization. Supporting students worldwide.</p>
        </div>
        <div>
          <h4 className="font-semibold text-gray-700 mb-3">Legal</h4>
          <ul className="space-y-1.5">
            <li><Link href="/privacy" className="hover:text-indigo-600">Privacy Policy</Link></li>
            <li><Link href="/terms" className="hover:text-indigo-600">Terms of Service</Link></li>
            <li><Link href="/contact" className="hover:text-indigo-600">Contact Us</Link></li>
            <li><Link href="/about" className="hover:text-indigo-600">About</Link></li>
          </ul>
        </div>
        <div>
          <h4 className="font-semibold text-gray-700 mb-3">Features</h4>
          <ul className="space-y-1.5">
            <li><Link href="/ai-lab" className="hover:text-indigo-600">AI Lab</Link></li>
            <li><Link href="/dashboard" className="hover:text-indigo-600">Dashboard</Link></li>
            <li><Link href="/analytics" className="hover:text-indigo-600">Analytics</Link></li>
          </ul>
        </div>
      </div>
      <div className="mt-8 pt-6 border-t border-gray-100 text-center text-xs text-gray-400">
        {new Date().getFullYear()} ExamAI Hub. All rights reserved.
      </div>
    </footer>
  );
}

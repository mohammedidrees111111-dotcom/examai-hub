"use client";

import { useState } from "react";
import Footer from "@/components/Footer";

export default function ContactPage() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");
  const [sent, setSent] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
      const res = await fetch(`${API_BASE}/contact`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, email, message }),
      });
      if (res.ok) {
        setSent(true);
        setName(""); setEmail(""); setMessage("");
      } else {
        setError("Failed to send. Please try again.");
      }
    } catch {
      setError("Network error. Please try again later.");
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-12">
      <h1 className="text-3xl font-bold mb-2">Contact Us / اتصل بنا</h1>
      <p className="text-gray-600 mb-8">Have questions or feedback? We would love to hear from you.</p>

      <div className="grid md:grid-cols-2 gap-8">
        <div>
          {sent ? (
            <div className="bg-green-50 border border-green-200 text-green-700 p-6 rounded-xl">
              <h3 className="font-semibold text-lg mb-2">Message Sent!</h3>
              <p>Thank you for reaching out. We will get back to you within 24 hours.</p>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
                <input type="text" value={name} onChange={(e) => setName(e.target.value)} required className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-indigo-500" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-indigo-500" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Message</label>
                <textarea value={message} onChange={(e) => setMessage(e.target.value)} required rows={5} className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-indigo-500" />
              </div>
              {error && <p className="text-red-500 text-sm">{error}</p>}
              <button type="submit" className="bg-indigo-600 text-white px-6 py-3 rounded-xl font-semibold hover:bg-indigo-700 transition">Send Message</button>
            </form>
          )}
        </div>

        <div className="text-gray-600 space-y-4">
          <div>
            <h3 className="font-semibold text-gray-800 mb-1">Email</h3>
            <p>support@examaihub.com</p>
          </div>
          <div>
            <h3 className="font-semibold text-gray-800 mb-1">Response Time</h3>
            <p>We typically respond within 24 hours.</p>
          </div>
          <div>
            <h3 className="font-semibold text-gray-800 mb-1">Follow Us</h3>
            <p>Stay updated with new features and improvements.</p>
          </div>
        </div>
      </div>
      <Footer />
    </div>
  );
}

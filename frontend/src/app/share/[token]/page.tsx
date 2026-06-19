import { Metadata } from "next";
import Footer from "@/components/Footer";
import Link from "next/link";

async function getSharedData(token: string) {
  const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
  try {
    const res = await fetch(`${API_BASE}/growth/share/${token}`, { cache: "no-store" });
    if (!res.ok) return null;
    return res.json();
  } catch { return null; }
}

export async function generateMetadata({ params }: { params: Promise<{ token: string }> }): Promise<Metadata> {
  const { token } = await params;
  const data = await getSharedData(token);
  if (!data) return { title: "Not Found" };
  return {
    title: `${data.title} — Study Pack | ExamAI Hub`,
    description: `AI-generated study pack: ${data.subject || "Study Material"}. Summary, exam predictions, flashcards included.`,
    openGraph: {
      title: data.title,
      description: `AI-powered study analysis for ${data.subject || data.course || "your course"}`,
      type: "article",
    },
  };
}

export default async function SharePage({ params }: { params: Promise<{ token: string }> }) {
  const { token } = await params;
  const data = await getSharedData(token);

  if (!data) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-20 text-center">
        <h1 className="text-2xl font-bold mb-4">Study Pack Not Found</h1>
        <p className="text-gray-600 mb-6">This link may have expired or been removed.</p>
        <Link href="/" className="bg-indigo-600 text-white px-6 py-3 rounded-xl font-semibold hover:bg-indigo-700">Go to ExamAI Hub</Link>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <div className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-2xl p-8 mb-8">
        <h1 className="text-3xl font-bold mb-2">{data.title}</h1>
        <div className="flex gap-4 text-indigo-100 text-sm">
          {data.subject && <span>{data.subject}</span>}
          {data.course && <span>· {data.course}</span>}
          <span>· {data.views} views</span>
        </div>
      </div>

      <div className="bg-white rounded-2xl p-6 mb-8 border shadow-sm">
        <div className="flex items-center gap-4 mb-6">
          <div className="bg-indigo-100 text-indigo-700 px-4 py-2 rounded-xl text-sm font-medium">
            AI-Generated Study Pack
          </div>
          <div className="text-gray-500 text-sm">Created by ExamAI Hub</div>
        </div>
        <div className="prose max-w-none text-gray-700 whitespace-pre-line">
          {data.data?.summary || "No summary available"}
        </div>
      </div>

      <div className="bg-indigo-50 border-2 border-indigo-200 rounded-2xl p-8 text-center">
        <h2 className="text-2xl font-bold text-indigo-700 mb-3">Want your own?</h2>
        <p className="text-indigo-600 mb-6">Generate a personalized study pack from your own materials — free.</p>
        <Link href="/register" className="bg-indigo-600 text-white px-8 py-3 rounded-xl font-semibold hover:bg-indigo-700 transition inline-block">
          Create Your Free Study Pack
        </Link>
      </div>

      <Footer />
    </div>
  );
}

"use client";

import Link from "next/link";
import { useAuth } from "@/contexts/AuthContext";

export default function Navbar() {
  const { user, logout } = useAuth();

  return (
    <nav className="bg-white border-b border-gray-200 shadow-sm sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16 items-center">
          <Link href="/" className="flex items-center gap-2 font-bold text-xl text-indigo-600">
            ExamAI Hub
          </Link>

          <div className="flex items-center gap-4">
            {user ? (
              <>
                <Link href="/dashboard" className="text-gray-700 hover:text-indigo-600">Dashboard</Link>
                <Link href="/ai-lab" className="text-gray-700 hover:text-indigo-600 font-medium">AI Lab</Link>
                <Link href="/analytics" className="text-gray-700 hover:text-indigo-600">Analytics</Link>
                <span className="text-sm text-gray-500">
                  {user.is_premium ? <span className="text-yellow-600 font-semibold">Premium</span> : "Free"}
                </span>
                <span className="text-sm text-gray-700">{user.username}</span>
                <button onClick={logout} className="text-red-500 hover:text-red-700 text-sm">Logout</button>
              </>
            ) : (
              <>
                <Link href="/login" className="text-gray-700 hover:text-indigo-600">Login</Link>
                <Link href="/register" className="bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700">Sign Up</Link>
              </>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}

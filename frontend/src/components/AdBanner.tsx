"use client";

import { useEffect, useRef } from "react";
import { useAuth } from "@/contexts/AuthContext";

const PUB_ID = process.env.NEXT_PUBLIC_ADSENSE_PUB_ID || "";

interface AdBannerProps {
  slot?: string;
  format?: "auto" | "horizontal" | "vertical" | "rectangle";
  className?: string;
  showForPremium?: boolean;
}

export default function AdBanner({
  slot = "1234567890",
  format = "auto",
  className = "",
  showForPremium = false,
}: AdBannerProps) {
  const { user } = useAuth();
  const containerRef = useRef<HTMLModElement>(null);
  const pushedRef = useRef(false);

  const hide = !PUB_ID || (user?.is_premium && !showForPremium);

  useEffect(() => {
    if (hide || pushedRef.current) return;
    pushedRef.current = true;

    try {
      const w = window as unknown as Record<string, unknown>;
      const adsbygoogle = (w.adsbygoogle as unknown[]) || [];
      adsbygoogle.push({});
    } catch {
      // adsbygoogle not ready — will retry on script load
    }
  }, [hide]);

  if (hide) return null;

  return (
    <div className={`my-4 overflow-hidden ${className}`}>
      <ins
        ref={containerRef}
        className="adsbygoogle"
        style={{ display: "block", minHeight: "90px" }}
        data-ad-client={`ca-pub-${PUB_ID}`}
        data-ad-slot={slot}
        data-ad-format={format}
        data-full-width-responsive="true"
      />
    </div>
  );
}

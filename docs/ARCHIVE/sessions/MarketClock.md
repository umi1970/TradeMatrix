import React, { useEffect, useState } from "react";

type Market = {
  name: string;
  timezone: string;
  open: string;   // Local market time
  close: string;  // Local market time
  flag: string;
};

const markets: Market[] = [
  { name: "DAX (XETRA)", timezone: "Europe/Berlin", open: "08:00", close: "22:00", flag: "🇩🇪" },
  { name: "NASDAQ / NYSE", timezone: "America/New_York", open: "09:30", close: "16:00", flag: "🇺🇸" },
  { name: "CME Futures", timezone: "America/Chicago", open: "08:30", close: "15:15", flag: "🇺🇸" },
];

const isMarketOpen = (now: Date, market: Market) => {
  const options: Intl.DateTimeFormatOptions = {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
    timeZone: market.timezone,
  };
  const localTime = new Intl.DateTimeFormat("en-GB", options).formatToParts(now);
  const hour = parseInt(localTime.find(p => p.type === "hour")?.value || "0", 10);
  const minute = parseInt(localTime.find(p => p.type === "minute")?.value || "0", 10);
  const currentMinutes = hour * 60 + minute;

  const [openHour, openMinute] = market.open.split(":").map(Number);
  const [closeHour, closeMinute] = market.close.split(":").map(Number);
  const openMins = openHour * 60 + openMinute;
  const closeMins = closeHour * 60 + closeMinute;

  return currentMinutes >= openMins && currentMinutes <= closeMins;
};

export default function MarketClock() {
  const [time, setTime] = useState(new Date());

  useEffect(() => {
    const interval = setInterval(() => setTime(new Date()), 1000 * 15); // Update every 15s
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="bg-[#0C0C0C] text-[#E0E0E0] p-6 rounded-2xl shadow-lg grid gap-4 w-full max-w-2xl">
      <h2 className="text-xl font-semibold text-[#0070F3] text-center">🌐 Global Market Clocks</h2>
      {markets.map((mkt) => {
        const tzTime = new Intl.DateTimeFormat("en-GB", {
          hour: "2-digit",
          minute: "2-digit",
          hour12: false,
          timeZone: mkt.timezone,
        }).format(time);

        const open = isMarketOpen(time, mkt);
        const color = open ? "#00D084" : "#FF3B30";
        const status = open ? "OPEN" : "CLOSED";

        return (
          <div key={mkt.name} className="flex justify-between items-center bg-[#1A1A1A] p-4 rounded-xl">
            <div className="flex flex-col">
              <span className="text-lg font-medium">{mkt.flag} {mkt.name}</span>
              <span className="text-sm text-[#E0E0E0]/70">Local: {mkt.open} – {mkt.close}</span>
            </div>
            <div className="text-right">
              <span className="text-xl font-semibold">{tzTime}</span>
              <span
                className="block text-sm font-medium mt-1"
                style={{ color }}
              >
                {status}
              </span>
            </div>
          </div>
        );
      })}
      <p className="text-center text-xs text-[#E0E0E0]/50 mt-2">
        Auto-adjusts for Daylight Saving Time (EU & US)
      </p>
    </div>
  );
}




💅 Styling

Nutzt TailwindCSS (wie dein restliches Dashboard)

Farben aus deinem TradeMatrix-Design

Update alle 15 Sekunden automatisch



---

🚀 Einsatz

Datei: components/MarketClock.tsx
Import im Dashboard:

import MarketClock from "@/components/MarketClock";

export default function Dashboard() {
  return (
    <div className="p-8">
      <MarketClock />
    </div>
  );
}

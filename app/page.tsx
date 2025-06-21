
'use client';

import * as React from "react";
import { cn } from "../src/lib/utils";
import { ScrollArea, ScrollBar } from "../components/ui/scroll-area";
import { Textarea } from "../components/ui/textarea";
import { Avatar, AvatarFallback } from "../components/ui/avatar";
import html2canvas from 'html2canvas';
import { balloons } from 'balloons-js';
import { Share2 } from 'lucide-react';

type Clone = {
  name: string;
  emoji: string;
  personality: string;
  score: number;
  remix?: string;
};

const clones: Clone[] = [
  {
    name: "Elon",
    emoji: "🚀",
    personality: "Wants to colonize Mars. Rates ideas by how big and insane they are.",
    score: 93,
    remix: "Make this 100x bigger and use AI to automate everything.",
  },
  {
    name: "Naval",
    emoji: "🧘",
    personality: "Wants leverage and passive income. Rates ideas based on productizing oneself.",
    score: 87,
    remix: "Turn this into a productized service with media distribution built-in.",
  },
  {
    name: "Ali Abdaal",
    emoji: "📚",
    personality: "Thinks everything is a video idea or a Notion template.",
    score: 75,
    remix: "Could be a great YouTube series + productivity dashboard combo.",
  },
];

export default function Page() {
  const [idea, setIdea] = React.useState("An app where AI clones rate your startup idea.");
  const [selectedClone, setSelectedClone] = React.useState<Clone | null>(null);
  const [showVerdict, setShowVerdict] = React.useState(false);
  const [remixMode, setRemixMode] = React.useState(false);
  const cardRef = React.useRef<HTMLDivElement>(null);

  const handleRate = () => {
    if (selectedClone) {
      setShowVerdict(true);
      balloons();
    }
  };

  const handleDownload = async () => {
    if (cardRef.current) {
      const canvas = await html2canvas(cardRef.current);
      const link = document.createElement("a");
      link.download = "clone-verdict.png";
      link.href = canvas.toDataURL("image/png");
      link.click();
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-600 via-pink-500 to-orange-400 text-white flex flex-col items-center px-4 py-10">
      <h1 className="text-5xl font-extrabold mb-4 text-center">🧠 Clone Council</h1>
      <p className="text-center max-w-xl mb-6 text-lg">
        Pitch your startup idea. Let iconic AI clones rate it, remix it, and cheer (or roast) you.
      </p>

      <Textarea
        value={idea}
        onChange={(e) => setIdea(e.target.value)}
        placeholder="Type your wild startup idea here..."
        className="bg-white text-black max-w-xl"
      />

      <h2 className="mt-8 text-2xl font-semibold">Pick Your Clone:</h2>
      <div className="flex gap-4 flex-wrap justify-center mt-4">
        {clones.map((clone) => (
          <button
            key={clone.name}
            onClick={() => {
              setSelectedClone(clone);
              setShowVerdict(false);
            }}
            className={cn(
              "px-4 py-2 rounded-lg border transition",
              selectedClone?.name === clone.name ? "bg-white text-black" : "bg-black bg-opacity-40"
            )}
          >
            {clone.emoji} {clone.name}
          </button>
        ))}
      </div>

      <div className="mt-4 flex items-center gap-2">
        <input type="checkbox" id="remix" checked={remixMode} onChange={() => setRemixMode(!remixMode)} />
        <label htmlFor="remix" className="cursor-pointer text-sm">Enable Remix Mode</label>
      </div>

      <button
        onClick={handleRate}
        disabled={!selectedClone}
        className="mt-6 bg-black bg-opacity-70 hover:bg-opacity-90 px-6 py-3 rounded-full text-white font-bold"
      >
        Get Clone Verdict
      </button>

      {showVerdict && selectedClone && (
        <div
          ref={cardRef}
          className="mt-8 p-6 bg-white text-black rounded-2xl shadow-xl max-w-lg w-full border-4 border-black space-y-4 text-left"
        >
          <h3 className="text-2xl font-bold">{selectedClone.emoji} {selectedClone.name} says:</h3>
          <p className="text-lg italic">"{selectedClone.personality}"</p>
          <p className="text-md font-semibold">Your idea: <span className="font-normal">"{idea}"</span></p>
          <div className="font-bold text-xl">Score: {selectedClone.score}/100</div>

          <div className="w-full h-3 bg-gray-200 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-red-400 via-yellow-300 to-green-500"
              style={{ width: `${selectedClone.score}%` }}
            />
          </div>

          {remixMode && selectedClone.remix && (
            <div className="bg-purple-100 text-purple-900 p-3 rounded-md mt-4">
              <p className="font-semibold">Remix:</p>
              <p>{selectedClone.remix}</p>
            </div>
          )}

          <button
            onClick={handleDownload}
            className="mt-4 flex items-center gap-2 text-sm bg-black text-white px-4 py-2 rounded-full"
          >
            <Share2 size={16} /> Download Verdict
          </button>
        </div>
      )}
    </div>
  );
}

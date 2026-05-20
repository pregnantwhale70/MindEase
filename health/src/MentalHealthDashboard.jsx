import { useState, useRef, useEffect } from "react";
import { useChat } from "./hooks/useChat";


// Main frontend component for the mental wellness dashboard
export default function MentalHealthDashboard() {
  // Sample conversation messages between user and AI
  const { stress, anxiety, messages, sendMessage, loading } = useChat();

  const messagesContainerRef = useRef(null);
  useEffect(() => {
    if (messagesContainerRef.current) {
      messagesContainerRef.current.scrollTop = messagesContainerRef.current.scrollHeight;
    }
  }, [messages]);
  
  const [input, setInput] = useState("");
  // AI-generated emotional reflection insights
  const reflections = [
    "You tend to feel calmer after short breaks.",
    "Late-night study sessions are increasing anxiety patterns.",
    "Your emotional state improved after grounding exercises.",
  ];

  // Main UI layout
  return (
    <>
      {/* Full page background with soft wellness gradients */}
    <div className="h-screen overflow-hidden w-full bg-[linear-gradient(135deg,#f7f4ff_0%,#eef6f3_35%,#fff7ed_100%)] overflow-hidden relative text-slate-700">
      <div className="absolute top-[-10rem] left-[-5rem] w-[30rem] h-[30rem] rounded-full bg-violet-200/40 blur-3xl" />
      <div className="absolute bottom-[-10rem] right-[-5rem] w-[35rem] h-[35rem] rounded-full bg-orange-100/70 blur-3xl" />

      {/* Main content wrapper */}
      <div className="relative z-10 flex h-screen w-full flex-col overflow-hidden px-5 py-5 sm:px-7 lg:px-9">
        {/* Header section */}
        <div className="flex shrink-0 items-center justify-between mb-5">
          <div>
            <h1 className="text-4xl font-semibold tracking-tight text-slate-800">
              CalmSpace
            </h1>
            <p className="text-slate-500/90 mt-2 text-sm">
              Gentle AI-assisted emotional wellness companion
            </p>
          </div>

          <div className="hidden md:flex items-center gap-3 bg-white/70 backdrop-blur-xl border border-white rounded-full px-5 py-3 shadow-sm">
            <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <p className="text-sm text-slate-600">Support mode active</p>
          </div>
        </div>

        {/* Three-column dashboard layout */}
        <div className="grid flex-1 min-h-0 grid-cols-1 gap-5 lg:grid-cols-[1.15fr_2.15fr_1.15fr] overflow-hidden">
          {/* Left analytics + reflections panel */}
          {/* Right wellness tools panel */}
          <div className="grid min-h-0 gap-5 lg:grid-rows-[1fr_1fr]">
            {/* Emotional state card */}
            <div className="flex flex-col justify-center bg-white/70 backdrop-blur-2xl rounded-[2rem] p-6 border border-white shadow-[0_10px_40px_rgba(180,180,255,0.15)]">
              <p className="text-sm uppercase tracking-[0.2em] text-slate-400 mb-4">
                Emotional State
              </p>

              <div className="flex items-center justify-center py-4">
                <div className="w-40 h-40 rounded-full bg-gradient-to-br from-violet-100 via-sky-100 to-teal-100 flex items-center justify-center shadow-inner">
                  <div className="w-28 h-28 rounded-full bg-white flex flex-col items-center justify-center shadow-lg">
                    <p className="text-4xl font-semibold text-slate-700">72%</p>
                    <p className="text-xs text-slate-400 mt-1">stress load</p>
                  </div>
                </div>
              </div>

              <div className="mt-6 space-y-4">
                <div>
                  <div className="flex justify-between text-sm mb-2">
                    <span>Stress</span>
                    <span>{stress}/10</span>
                  </div>
                  <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-teal-300 to-emerald-300 transition-all duration-500"
                    style={{ width: `${stress * 10}%` }}
                  />
                </div>
                </div>

                <div>
                  <div className="flex justify-between text-sm mb-2">
                    <span>Anxiety</span>
                    <span>{anxiety}/10</span>
                  </div>
                  <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                    <div
                    className="h-full rounded-full bg-gradient-to-r from-teal-300 to-emerald-300 transition-all duration-500"
                    style={{ width: `${stress * 10}%` }}
                  />
                    </div>
                </div>
              </div>
            </div>

            <div className="flex flex-col bg-white/70 backdrop-blur-2xl rounded-[2rem] p-6 border border-white shadow-[0_10px_40px_rgba(180,180,255,0.15)]">
              <p className="text-sm uppercase tracking-[0.2em] text-slate-400 mb-4">
                Reflection Insights
              </p>

              <div className="grid flex-1 content-center gap-3">
                {reflections.map((item, idx) => (
                  <div
                    key={idx}
                    className="bg-white rounded-2xl p-4 text-sm leading-relaxed text-slate-600 shadow-sm"
                  >
                    {item}
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Central AI chat interface */}
          <div className="bg-white/70 backdrop-blur-2xl rounded-[2.5rem] border border-white shadow-[0_10px_40px_rgba(180,180,255,0.15)] flex min-h-[36rem] flex-col overflow-hidden lg:min-h-0">
            <div className="px-8 pt-8 pb-5 border-b border-slate-100">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-2xl font-semibold text-slate-800">
                    How are you feeling today?
                  </h2>
                  <p className="text-slate-500/90 mt-2 text-sm">
                    Your space to pause, reflect, and breathe.
                  </p>
                </div>

                <div className="hidden md:flex items-center gap-2 px-4 py-2 rounded-full bg-gradient-to-r from-violet-50 to-sky-50 text-violet-700 text-sm">
                  Calm conversation active
                </div>
              </div>
            </div>

            {/* Chat messages area */}
            <div ref={messagesContainerRef} className="flex-1 overflow-y-auto px-8 py-8 space-y-5">
              {/* Rendering conversation messages dynamically */}
              {messages.map((msg, idx) => (
                <div
                  key={idx}
                  className={`flex ${
                    msg.role === "user" ? "justify-end" : "justify-start"
                  }`}
                >
                  <div
                    className={`max-w-lg px-6 py-4 rounded-[1.8rem] text-sm leading-relaxed shadow-sm ${
                      msg.role === "user"
                        ? "bg-gradient-to-br from-slate-700 to-slate-800 text-white"
                        : "bg-white text-slate-600"
                    }`}
                  >
                    {msg.text}
                  </div>
                </div>
              ))} 
            </div>

            {/* User message input section */}
            <div className="p-6 shrink-0">
              <div className="bg-white rounded-[2rem] border border-slate-100 p-3 flex items-center gap-3 shadow-sm">
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Tell me what's weighing on your mind..."
                  className="flex-1 bg-transparent px-3 py-3 outline-none text-slate-700 placeholder:text-slate-400"
                />
                <button
                  onClick={() => {
                    sendMessage(input);
                    setInput("");
                  }}
                  className="px-6 py-3 rounded-full bg-gradient-to-r from-violet-500 to-indigo-500 text-white text-sm font-medium hover:opacity-90 transition"
                >
                  Send
                </button>
              </div>
            </div>
          </div>

          <div className="grid min-h-0 gap-5 lg:grid-rows-[1fr_1fr]">
            <div className="flex flex-col justify-center bg-white/70 backdrop-blur-2xl rounded-[2rem] p-6 border border-white shadow-[0_10px_40px_rgba(180,180,255,0.15)]">
              {/* Guided breathing exercise section */}
              <p className="text-sm uppercase tracking-[0.2em] text-slate-400 mb-5">
                Breathing Companion
              </p>

              <div className="flex flex-col items-center justify-center py-4">
                <div className="w-40 h-40 rounded-full bg-gradient-to-br from-violet-100 via-sky-100 to-teal-100 animate-pulse flex items-center justify-center">
                  <div className="w-24 h-24 rounded-full bg-white flex items-center justify-center shadow-inner">
                    <p className="text-slate-500/90 text-sm">inhale</p>
                  </div>
                </div>

                <p className="text-slate-500/90 text-sm mt-6 text-center leading-relaxed max-w-xs">
                  Follow the rhythm slowly and allow your breathing to settle.
                </p>
              </div>
            </div>

            {/* Personalized wellness suggestions */}
            <div className="flex flex-col bg-gradient-to-br from-violet-50 via-pink-50 to-orange-50 rounded-[2rem] p-6 border border-white shadow-[0_10px_40px_rgba(180,180,255,0.15)]">
              <p className="text-sm uppercase tracking-[0.2em] text-slate-400 mb-4">
                Gentle Suggestions
              </p>

              <div className="grid flex-1 content-center gap-4 text-sm text-slate-600 leading-relaxed">
                <div className="bg-white/90 rounded-2xl p-4 border border-white shadow-sm">
                  Take a 10-minute break away from screens.
                </div>

                <div className="bg-white/90 rounded-2xl p-4 border border-white shadow-sm">
                  Drink water and relax your shoulders for a moment.
                </div>

                <div className="bg-white/90 rounded-2xl p-4 border border-white shadow-sm">
                  Your recent stress patterns suggest mental fatigue.
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    </>
  );
}

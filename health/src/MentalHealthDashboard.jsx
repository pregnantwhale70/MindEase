import { useState, useRef, useEffect } from "react";
import { useChat } from "./hooks/useChat";

export default function MentalHealthDashboard() {

  const { stress, anxiety, messages, sendMessage, loading } = useChat();

  const messagesContainerRef = useRef(null);

  const [input, setInput] = useState("");

  const [showTelegramModal, setShowTelegramModal] =
    useState(false);

  const [userName, setUserName] = useState(
    localStorage.getItem("userName") || ""
  ); const [emergencyContactName, setEmergencyContactName] = useState(
    localStorage.getItem("emergencyContactName") || ""
  );
  const [chatId, setChatId] = useState(
    localStorage.getItem("telegramChatId") || ""
  );

  useEffect(() => {
    if (messagesContainerRef.current) {
      messagesContainerRef.current.scrollTop =
        messagesContainerRef.current.scrollHeight;
    }
  }, [messages]);

  const reflections = [
    "You tend to feel calmer after short breaks.",
    "Late-night study sessions are increasing anxiety patterns.",
    "Your emotional state improved after grounding exercises.",
  ];

  return (
    <>
      {/* Telegram Modal */}
      {showTelegramModal && (

        <div className="fixed inset-0 bg-black/60 backdrop-blur-md flex items-center justify-center z-50 p-4">

          <div className="bg-slate-900 border border-white/10 w-full max-w-[420px] rounded-[2rem] p-5 sm:p-7 shadow-2xl">

            {/* Heading */}
            <h2 className="text-2xl font-semibold text-white mb-2">
              MindEase Setup
            </h2>

            <p className="text-slate-400 text-sm mb-6 leading-relaxed">
              Add your details and Telegram contact for
              emergency wellness alerts.
            </p>

            {/* Inputs */}
            <div className="space-y-4 mb-6">

              {/* User Name */}
              <input
                type="text"
                placeholder="Your Name"
                value={userName}
                onChange={(e) =>
                  setUserName(e.target.value)
                }
                className="w-full rounded-2xl border border-white/10 bg-slate-800 px-4 py-3 outline-none text-white placeholder:text-slate-500"
              />

              {/* Trusted Contact */}
              <input
                type="text"
                placeholder="Trusted Contact Name"
                value={emergencyContactName}
                onChange={(e) =>
                  setEmergencyContactName(e.target.value)
                }
                className="w-full rounded-2xl border border-white/10 bg-slate-800 px-4 py-3 outline-none text-white placeholder:text-slate-500"
              />

              {/* Telegram Chat ID */}
              <input
                type="text"
                placeholder="Telegram Chat ID (Optional)"
                value={chatId}
                onChange={(e) =>
                  setChatId(e.target.value)
                }
                className="w-full rounded-2xl border border-white/10 bg-slate-800 px-4 py-3 outline-none text-white placeholder:text-slate-500"
              />

            </div>

            {/* Buttons */}
            <div className="flex flex-col sm:flex-row gap-3">

              {/* Save */}
              <button
                onClick={() => {

                  // validate telegram only if entered
                  if (chatId.trim()) {

                    if (!/^\d+$/.test(chatId)) {

                      alert(
                        "Chat ID must contain only numbers"
                      );

                      return;
                    }

                    localStorage.setItem(
                      "telegramChatId",
                      chatId
                    );
                  }

                  // save user name
                  localStorage.setItem(
                    "userName",
                    userName || "MindEase User"
                  );

                  // save trusted contact
                  localStorage.setItem(
                    "emergencyContactName",
                    emergencyContactName ||
                    "Trusted Contact"
                  );

                  // save setup state
                  localStorage.setItem(
                    "setupComplete",
                    "true"
                  );

                  // create persistent session
                  let sessionId =
                    localStorage.getItem(
                      "sessionId"
                    );

                  if (!sessionId) {

                    sessionId =
                      crypto.randomUUID();

                    localStorage.setItem(
                      "sessionId",
                      sessionId
                    );
                  }

                  alert(
                    "MindEase setup complete"
                  );

                  setShowTelegramModal(false);

                  window.location.reload();
                }}

                className="flex-1 rounded-full bg-gradient-to-r from-violet-500 via-indigo-500 to-cyan-500 text-white py-3 text-sm font-medium hover:opacity-90 transition"
              >
                Save Setup
              </button>

              {/* Close */}
              <button
                onClick={() =>
                  setShowTelegramModal(false)
                }
                className="px-5 py-3 rounded-full bg-slate-700 text-slate-200 text-sm hover:bg-slate-600 transition"
              >
                Close
              </button>

            </div>

            {/* Footer */}
            <p className="text-xs text-slate-500 text-center mt-5 leading-relaxed">
              Telegram can be added later from the
              dashboard settings.
            </p>

          </div>

        </div>
      )}

      {/* Main Background */}
      <div className="h-screen overflow-hidden w-full bg-[linear-gradient(135deg,#09090f_0%,#111827_35%,#0f172a_100%)] relative text-slate-200">

        {/* Background Glow */}
        <div className="absolute top-[-10rem] left-[-5rem] w-[30rem] h-[30rem] rounded-full bg-violet-500/20 blur-3xl" />

        <div className="absolute bottom-[-10rem] right-[-5rem] w-[35rem] h-[35rem] rounded-full bg-cyan-500/10 blur-3xl" />

        {/* Main Wrapper */}
        <div className="relative z-10 flex h-screen w-full flex-col overflow-hidden px-5 py-5 sm:px-7 lg:px-9">

          {/* Header */}
          <div className="flex shrink-0 items-center justify-between mb-5">

            <div>
              <h1 className="text-4xl font-semibold tracking-tight text-white">
                CalmSpace
              </h1>

              <p className="text-slate-400 mt-2 text-sm">
                Gentle AI-assisted emotional wellness companion
              </p>
            </div>

            <div className="flex items-center gap-3">

              {/* Telegram Button */}
              <button
                onClick={() =>
                  setShowTelegramModal(true)
                }
                className="flex items-center gap-2 bg-white/5 backdrop-blur-xl border border-white/10 rounded-full px-5 py-3 shadow-sm hover:scale-[1.02] transition"
              >
                <div className="w-2 h-2 rounded-full bg-blue-500" />

                <p className="text-sm text-slate-200">
                  {chatId
                    ? "Telegram Connected"
                    : "Connect Telegram"}
                </p>
              </button>

              <div className="hidden md:flex items-center gap-3 bg-white/5 backdrop-blur-xl border border-white/10 rounded-full px-5 py-3 shadow-sm">

                <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />

                <p className="text-sm text-slate-300">
                  Support mode active
                </p>

              </div>

            </div>

          </div>

          {/* Dashboard Grid */}
          <div className="grid flex-1 min-h-0 grid-cols-1 gap-5 lg:grid-cols-[1.15fr_2.15fr_1.15fr] overflow-hidden">

            {/* Left Panel */}
            <div className="grid min-h-0 gap-5 lg:grid-rows-[1fr_1fr]">

              {/* Emotional State */}
              <div className="flex flex-col justify-center bg-white/5 backdrop-blur-2xl rounded-[2rem] p-6 border border-white/10 shadow-[0_10px_40px_rgba(0,0,0,0.4)]">

                <p className="text-sm uppercase tracking-[0.2em] text-slate-500 mb-4">
                  Emotional State
                </p>

                <div className="flex items-center justify-center py-4">

                  <div className="w-40 h-40 rounded-full bg-gradient-to-br from-violet-500/20 via-cyan-500/20 to-teal-500/20 flex items-center justify-center shadow-inner">

                    <div className="w-28 h-28 rounded-full bg-slate-900 flex flex-col items-center justify-center shadow-lg border border-white/10">

                      <p className="text-4xl font-semibold text-white">
                        72%
                      </p>

                      <p className="text-xs text-slate-500 mt-1">
                        stress load
                      </p>

                    </div>

                  </div>

                </div>

                <div className="mt-6 space-y-4">

                  <div>
                    <div className="flex justify-between text-sm mb-2">
                      <span>Stress</span>
                      <span>{stress}/10</span>
                    </div>

                    <div className="h-2 w-full bg-slate-800 rounded-full overflow-hidden">

                      <div
                        className="h-full rounded-full bg-gradient-to-r from-cyan-400 to-violet-500 transition-all duration-500"
                        style={{
                          width: `${stress * 10}%`,
                        }}
                      />

                    </div>
                  </div>

                  <div>
                    <div className="flex justify-between text-sm mb-2">
                      <span>Anxiety</span>
                      <span>{anxiety}/10</span>
                    </div>

                    <div className="h-2 bg-slate-800 rounded-full overflow-hidden">

                      <div
                        className="h-full rounded-full bg-gradient-to-r from-pink-500 to-violet-500 transition-all duration-500"
                        style={{
                          width: `${anxiety * 10}%`,
                        }}
                      />

                    </div>
                  </div>

                </div>

              </div>

              {/* Reflection */}
              <div className="flex flex-col bg-white/5 backdrop-blur-2xl rounded-[2rem] p-6 border border-white/10 shadow-[0_10px_40px_rgba(0,0,0,0.4)]">

                <p className="text-sm uppercase tracking-[0.2em] text-slate-500 mb-4">
                  Reflection Insights
                </p>

                <div className="grid flex-1 content-center gap-3">

                  {reflections.map((item, idx) => (
                    <div
                      key={idx}
                      className="bg-slate-900/80 border border-white/10 rounded-2xl p-4 text-sm leading-relaxed text-slate-300 shadow-sm"
                    >
                      {item}
                    </div>
                  ))}

                </div>

              </div>

            </div>

            {/* Chat */}
            <div className="bg-white/5 backdrop-blur-2xl rounded-[2.5rem] border border-white/10 shadow-[0_10px_40px_rgba(0,0,0,0.4)] flex min-h-[36rem] flex-col overflow-hidden lg:min-h-0">

              <div className="px-8 pt-8 pb-5 border-b border-white/10">

                <div className="flex items-center justify-between">

                  <div>
                    <h2 className="text-2xl font-semibold text-white">
                      How are you feeling today?
                    </h2>

                    <p className="text-slate-400 mt-2 text-sm">
                      Your space to pause, reflect, and breathe.
                    </p>
                  </div>

                  <div className="hidden md:flex items-center gap-2 px-4 py-2 rounded-full bg-violet-500/10 text-violet-300 text-sm border border-violet-500/20">
                    Calm conversation active
                  </div>

                </div>

              </div>

              {/* Messages */}
              <div
                ref={messagesContainerRef}
                className="flex-1 overflow-y-auto px-8 py-8 space-y-5"
              >

                {messages.map((msg, idx) => (
                  <div
                    key={idx}
                    className={`flex ${msg.role === "user"
                      ? "justify-end"
                      : "justify-start"
                      }`}
                  >

                    <div
                      className={`max-w-lg px-6 py-4 rounded-[1.8rem] text-sm leading-relaxed shadow-sm ${msg.role === "user"
                        ? "bg-gradient-to-br from-violet-600 to-indigo-700 text-white"
                        : "bg-slate-800/80 text-slate-200 border border-white/10"
                        }`}
                    >
                      {msg.text}
                    </div>

                  </div>
                ))}

              </div>

              {/* Input */}
              <div className="p-6 shrink-0">

                <div className="bg-slate-900/80 rounded-[2rem] border border-white/10 p-3 flex items-center gap-3 shadow-sm">

                  <input
                    type="text"
                    value={input}
                    onChange={(e) =>
                      setInput(e.target.value)
                    }
                    placeholder="Tell me what's weighing on your mind..."
                    className="flex-1 bg-transparent px-3 py-3 outline-none text-white placeholder:text-slate-500"
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

            {/* Right Panel */}
            <div className="grid min-h-0 gap-5 lg:grid-rows-[1fr_1fr]">

              {/* Breathing */}
              <div className="flex flex-col justify-center bg-white/5 backdrop-blur-2xl rounded-[2rem] p-6 border border-white/10 shadow-[0_10px_40px_rgba(0,0,0,0.4)]">

                <p className="text-sm uppercase tracking-[0.2em] text-slate-500 mb-5">
                  Breathing Companion
                </p>

                <div className="flex flex-col items-center justify-center py-4">

                  <div className="w-40 h-40 rounded-full bg-gradient-to-br from-violet-500/20 via-cyan-500/20 to-teal-500/20 animate-pulse flex items-center justify-center">

                    <div className="w-24 h-24 rounded-full bg-slate-900 flex items-center justify-center shadow-inner border border-white/10">

                      <p className="text-slate-300 text-sm">
                        inhale
                      </p>

                    </div>

                  </div>

                  <p className="text-slate-400 text-sm mt-6 text-center leading-relaxed max-w-xs">
                    Follow the rhythm slowly and allow
                    your breathing to settle.
                  </p>

                </div>

              </div>

              {/* Suggestions */}
              <div className="flex flex-col bg-gradient-to-br from-violet-900/30 via-slate-900/50 to-cyan-900/20 rounded-[2rem] p-6 border border-white/10 shadow-[0_10px_40px_rgba(0,0,0,0.4)]">

                <p className="text-sm uppercase tracking-[0.2em] text-slate-500 mb-4">
                  Gentle Suggestions
                </p>

                <div className="grid flex-1 content-center gap-4 text-sm text-slate-300 leading-relaxed">

                  <div className="bg-slate-900/70 rounded-2xl p-4 border border-white/10 shadow-sm">
                    Take a 10-minute break away from
                    screens.
                  </div>

                  <div className="bg-slate-900/70 rounded-2xl p-4 border border-white/10 shadow-sm">
                    Drink water and relax your shoulders
                    for a moment.
                  </div>

                  <div className="bg-slate-900/70 rounded-2xl p-4 border border-white/10 shadow-sm">
                    Your recent stress patterns suggest
                    mental fatigue.
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
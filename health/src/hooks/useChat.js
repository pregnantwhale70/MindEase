import { useState } from "react";
import { sendChatMessage } from "../services/chatService";

export const useChat = () => {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      text: "How are you feeling today?",
    },
  ]);

  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [stress, setStress] = useState(0);
  const [anxiety, setAnxiety] = useState(0);
  const [stressLoadPercent, setStressLoadPercent] = useState(0);
  const [breathingPattern, setBreathingPattern] = useState({
    pattern: "rhythmic",
    label: "Follow the rhythm slowly and allow your breathing to settle.",
    inhale: 4,
    hold1: 4,
    exhale: 4,
    hold2: 0,
  });
  const [emotionalState, setEmotionalState] = useState({
    stress_score: 0,
    anxiety_score: 0,
    stress_load_percent: 0,
    stress_color: "yellow",
    anxiety_color: "yellow",
    trend: "stable",
    emotions: [],
  });
  const [insights, setInsights] = useState([
    "You tend to feel calmer after short breaks.",
    "Late-night study sessions are increasing anxiety patterns.",
    "Your emotional state improved after grounding exercises.",
  ]);
  const [suggestions, setSuggestions] = useState([
    "Take a 10-minute break away from screens.",
    "Drink water and relax your shoulders for a moment.",
    "Your recent stress patterns suggest mental fatigue."
  ]);

  const sendMessage = async (input) => {
    if (!input.trim() || loading) return;

    const userMessage = {
      role: "user",
      text: input,
    };

    setMessages((prev) => [...prev, userMessage]);

    setLoading(true);
 
    try {
const updatedHistory = [
  ...history,
  {
    role: "user",
    content: input,
  },
];

console.log("Sending history:", updatedHistory);

const data = await sendChatMessage(
  input,
  updatedHistory
);
      const aiMessage = {
        role: "assistant",
        text:
          data.reply ||
          data.response ||
          data.message ||
          "I am here with you.",
      };

      setMessages((prev) => [...prev, aiMessage]);
      setHistory([
  ...updatedHistory,
  {
    role: "assistant",
    content: aiMessage.text,
  },
]);
      const nextStress =
        data.emotional_state?.stress_score ??
        data.emotion_scores?.stress_score ??
        0;
      const nextAnxiety =
        data.emotional_state?.anxiety_score ??
        data.emotion_scores?.anxiety_score ??
        0;
      const nextStressLoad =
        data.emotional_state?.stress_load_percent ??
        data.stress_load_percent ??
        Math.round(((nextStress + nextAnxiety) / 2) * 10);

      
      setStress(nextStress);
      setAnxiety(nextAnxiety);
      setStressLoadPercent(nextStressLoad);
      if (data.breathing_pattern) {
        setBreathingPattern(data.breathing_pattern);
      }
      if (data.emotional_state) {
        setEmotionalState(data.emotional_state);
      }
      setInsights(
        Array.isArray(data.insights) && data.insights.length
          ? data.insights
          : insights
      );
      setSuggestions(
        Array.isArray(data.suggestions) && data.suggestions.length
          ? data.suggestions
          : suggestions
      );

    } catch (error) {
      console.error(error);

      setMessages((prev) => [
        ...prev,
        {

          role: "assistant",
          text: "Backend connection failed.",
        },
      ]);
    }

    setLoading(false);
  };

  return {
    stress,
    anxiety,
    stressLoadPercent,
    breathingPattern,
    emotionalState,
    messages,
    sendMessage,
    loading,
    insights,
    suggestions
  };
};

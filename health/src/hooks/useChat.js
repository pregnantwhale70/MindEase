import { useState } from "react";
import { sendChatMessage } from "../services/chatService";

export const useChat = () => {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      text: "How are you feeling today?",
    },
  ]);

  const [loading, setLoading] = useState(false);
  const [stress, setStress] = useState(0);
  const [anxiety, setAnxiety] = useState(0);
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
      const history = messages
        .filter((message) => message.role === "user" || message.role === "assistant")
        .map((message) => ({
          role: message.role,
          content: message.text,
        }));

      const data = await sendChatMessage(input, history);

      const aiMessage = {
        role: "assistant",
        text:
          data.reply ||
          data.response ||
          data.message ||
          "I am here with you.",
      };

      console.log(data);
      setMessages((prev) => [...prev, aiMessage]);
      setStress(data.emotion_scores.stress_score);
      setAnxiety(data.emotion_scores.anxiety_score);
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
    messages,
    sendMessage,
    loading,
    insights,
    suggestions
  };
};

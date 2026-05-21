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

  const sendMessage = async (input) => {
    if (!input.trim()) return;

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

      setMessages((prev) => [...prev, aiMessage]);
      setStress(data.emotion_scores.stress_score);
      setAnxiety(data.emotion_scores.anxiety_score);

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
  };
};

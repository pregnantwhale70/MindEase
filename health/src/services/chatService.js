const API_URL = "http://127.0.0.1:8000/api/v1/chat";

export const sendChatMessage = async (message) => {
  const response = await fetch(API_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      message: message,
      session_id: "demo-session",

      history: [],

      emergency_contact: {
        name: "Demo Contact",
        telegram_chat_id: "123456",
      },
    }),
  });

  if (!response.ok) {
    throw new Error("Backend request failed");
  }

  return response.json();
};
import { useState } from "react";

export default function TelegramSetup() {
    const [chatId, setChatId] = useState("");

    const handleContinue = () => {
        // save only if entered
        if (chatId.trim()) {

            // validate numbers only
            if (!/^\d+$/.test(chatId)) {
                alert("Chat ID must contain only numbers");
                return;
            }

            localStorage.setItem("telegramChatId", chatId);
        }

        // mark setup complete
        localStorage.setItem("setupComplete", "true");

        window.location.reload();
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-gray-100">
            <div className="bg-white p-8 rounded-2xl shadow-xl w-[350px]">

                <h1 className="text-3xl font-bold text-center mb-2">
                    MindEase
                </h1>

                <p className="text-gray-600 text-center mb-6">
                    Add Telegram Chat ID (Optional)
                </p>

                <input
                    type="text"
                    placeholder="Telegram Chat ID"
                    value={chatId}
                    onChange={(e) => setChatId(e.target.value)}
                    className="w-full border border-gray-300 rounded-lg px-4 py-3 mb-4 outline-none focus:ring-2 focus:ring-blue-500"
                />

                <div className="flex flex-col gap-3">

                    <button
                        onClick={handleContinue}
                        className="w-full bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 transition"
                    >
                        Submit
                    </button>

                    <button
                        onClick={() => {
                            localStorage.setItem("setupComplete", "true");
                            window.location.reload();
                        }}
                        className="w-full bg-gray-300 text-black py-3 rounded-lg hover:bg-gray-400 transition"
                    >
                        Continue Without Telegram
                    </button>

                </div>

                <p className="text-xs text-gray-500 mt-4 text-center">
                    You can skip this and add it later.
                </p>

            </div>
        </div>
    );
}
// src/App.tsx
import { useState } from "react";
import { Mic, Send } from "lucide-react";
import { motion } from "framer-motion";
import VoiceRecorder from "./components/voiceRecorder";

function App() {
  const [messages, setMessages] = useState<string[]>([]);
  const [input, setInput] = useState("");

  const handleSend = () => {
    if (!input.trim()) return;
    setMessages([...messages, input]);
    setInput("");
  };

  return (
    <div className="scrollbar-hidden">
    <div className="flex h-screen bg-gradient-to-br from-gray-100 to-gray-200">
      {/* Левая колонка */}
      <aside className="w-64 bg-gradient-to-b from-blue-600 to-indigo-700 text-white shadow-xl flex flex-col items-center items-center">
        <div className="p-4 border-b border-indigo-500 flex items-center gap-3">
          <img src="/LogoWebV2.svg" alt="Elli" className="w-10 h-10 rounded-full" />
          <h1 className="text-2xl font-bold italic font-sf">Elli</h1>
        </div>
        <div className="flex-1 p-8 space-y-3 flex flex-col items-center">
          <h2 className="text-sm uppercase tracking-wide text-indigo-200">
            История
          </h2>
          {messages.length === 0 ? (
            <p className="text-indigo-100 text-sm">Пока пусто...</p>
          ) : (
            messages.map((msg, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
                className="p-3 bg-white/10 rounded-xl shadow-md text-sm"
              >
                {msg}
              </motion.div>
            ))
          )}
        </div>

      </aside>

      {/* Основная рабочая зона */}
      <main className="flex-1 flex flex-col">
        <div className="flex-1 flex items-center justify-center">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.8 }}
            className="text-gray-500 text-lg"
          >
            Тут будет ассистент Elli 👋
          </motion.div>
        </div>

        {/* Поле ввода + кнопки */}
        <div className="border-t bg-white p-4 flex items-center gap-3 shadow-md">
          <input
            type="text"
            placeholder="Введите запрос..."
            className="flex-1 border rounded-xl px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400 transition"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
          />
          <button
            onClick={handleSend}
            className="p-3 rounded-full bg-blue-500 text-white hover:bg-blue-600 transition shadow-md"
          >
            <Send size={20} />
          </button>
          <button
            onClick={() => alert("🎤 скоро будет работать")}
            className="relative flex items-center justify-center w-12 h-12 rounded-full bg-red-500 text-white hover:bg-red-600 transition shadow-md overflow-hidden"
          >
            {/* Пульсация внутри */}
            <span className="absolute inset-0 rounded-full bg-red-400 opacity-40 animate-ping"></span>

            {/* Иконка */}
            {/*<Mic size={22} className="relative z-10" />*/}
            
          </button>
          <VoiceRecorder/>

        </div>
      </main>
    </div>
  </div>
  );
}

export default App;

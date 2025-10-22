import React, { useState, useRef } from "react";

const VoiceRecorder: React.FC = () => {
  const [isRecording, setIsRecording] = useState(false);
  const [recognizedText, setRecognizedText] = useState("");
  const [assistantReply, setAssistantReply] = useState("");
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunks = useRef<Blob[]>([]);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunks.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunks.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunks.current, { type: "audio/wav" });
        await sendAudio(audioBlob);
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (err) {
      console.error("Ошибка доступа к микрофону:", err);
    }
  };

  const stopRecording = () => {
    mediaRecorderRef.current?.stop();
    setIsRecording(false);
  };

  const sendAudio = async (audioBlob: Blob) => {
    const formData = new FormData();
    formData.append("file", audioBlob, "voice.wav");
console.log("12313123131313213")
    try {
      const res = await fetch("http://127.0.0.1:8000/api/audio", {
        method: "POST",
        body: formData,
      });

      const data = await res.json();
      setRecognizedText(data.text || "Не удалось распознать речь");
      setAssistantReply(data.reply || "Элли не ответила");
    } catch (err) {
      console.error("Ошибка при отправке аудио:", err);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center space-y-4">
      <button
        onClick={isRecording ? stopRecording : startRecording}
        className={`p-4 rounded-full text-white transition-all duration-300 ${
          isRecording
            ? "bg-red-500 animate-pulse"
            : "bg-indigo-600 hover:bg-indigo-700"
        }`}
      >
        {isRecording ? "⏹ Остановить" : "🎤 Записать"}
      </button>

      {recognizedText && (
        <div className="text-center text-indigo-200">
          <p className="text-sm">Вы сказали:</p>
          <p className="font-semibold">{recognizedText}</p>
        </div>
      )}

      {assistantReply && (
        <div className="text-center text-white bg-indigo-900/30 p-3 rounded-xl shadow-md w-80">
          <p className="text-sm opacity-70">Ответ Элли:</p>
          <p className="font-medium">{assistantReply}</p>
        </div>
      )}
    </div>
  );
};

export default VoiceRecorder;

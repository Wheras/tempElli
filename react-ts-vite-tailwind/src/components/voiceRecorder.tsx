// src/components/VoiceRecorder.tsx
import { useState, useRef } from 'react';
import { Mic, Square } from 'lucide-react';

interface VoiceRecorderProps {
  onMessage: (message: any) => void;
}

const VoiceRecorder: React.FC<VoiceRecorderProps> = ({ onMessage }) => {
  const [isRecording, setIsRecording] = useState(false);
  const mediaRecorder = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          sampleRate: 16000,
          channelCount: 1,
        } 
      });
      
      streamRef.current = stream;
      
      const recorder = new MediaRecorder(stream);
      mediaRecorder.current = recorder;

      // Начало записи
      onMessage({ type: 'voice_start' });

      recorder.ondataavailable = async (event) => {
        if (event.data.size > 0) {
          // Конвертируем в base64
          const reader = new FileReader();
          reader.onload = () => {
            onMessage({
              type: 'voice_chunk',
              audio: reader.result
            });
          };
          reader.readAsDataURL(event.data);
        }
      };

      recorder.start(500); // Чанки каждые 500мс
      setIsRecording(true);
      
    } catch (error) {
      console.error('Error starting recording:', error);
      alert('Не удалось получить доступ к микрофону');
    }
  };

  const stopRecording = () => {
    if (mediaRecorder.current && isRecording) {
      mediaRecorder.current.stop();
      
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
      
      setIsRecording(false);
      onMessage({ type: 'voice_stop' });
    }
  };

  return (
    <button
      onClick={isRecording ? stopRecording : startRecording}
      className={`relative flex items-center justify-center w-12 h-12 rounded-full text-white transition shadow-md ${
        isRecording 
          ? 'bg-red-600 hover:bg-red-700' 
          : 'bg-green-500 hover:bg-green-600'
      }`}
    >
      {isRecording ? (
        <>
          <span className="absolute inset-0 rounded-full bg-red-400 opacity-40 animate-ping"></span>
          <Square size={20} className="relative z-10" />
        </>
      ) : (
        <Mic size={20} className="relative z-10" />
      )}
    </button>
  );
};

export default VoiceRecorder;
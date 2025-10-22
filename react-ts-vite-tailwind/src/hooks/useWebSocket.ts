// src/hooks/useWebSocket.ts
import { useState, useEffect, useRef } from 'react';

interface WebSocketMessage {
  type: string;
  text?: string;
  transcribed_text?: string;
  audio?: string;
}

interface UseWebSocketProps {
  onAssistantResponse?: (text: string, transcribedText?: string) => void;
  onListeningStarted?: () => void;
  onProcessingAudio?: () => void;
  onError?: (error: string) => void;
}

export const useWebSocket = (url: string, props?: UseWebSocketProps) => {
  const [isConnected, setIsConnected] = useState(false);
  const socketRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    console.log('🔄 Подключаю WebSocket к:', url);
    const ws = new WebSocket(url);
    socketRef.current = ws;
    
    ws.onopen = () => {
      console.log('✅ WebSocket connected');
      setIsConnected(true);
    };

    ws.onclose = () => {
      console.log('❌ WebSocket disconnected');
      setIsConnected(false);
      if (props?.onError) {
        props.onError('Соединение с сервером потеряно');
      }
    };

    ws.onerror = (error) => {
      console.error('❌ WebSocket error:', error);
      setIsConnected(false);
      if (props?.onError) {
        props.onError('Ошибка подключения к серверу');
      }
    };

    ws.onmessage = (event) => {
      console.log('📨 Получено сообщение от сервера:', event.data);
      try {
        const data = JSON.parse(event.data);
        
        if (data.type === 'assistant_response' && data.text) {
          console.log('🤖 Ответ ассистента:', data.text);
          if (props?.onAssistantResponse) {
            props.onAssistantResponse(data.text, data.transcribed_text);
          }
        } else if (data.type === 'listening_started') {
          console.log('🎤 Ассистент начал слушать');
          if (props?.onListeningStarted) {
            props.onListeningStarted();
          }
        } else if (data.type === 'processing_audio') {
          console.log('🔊 Обрабатывается аудио');
          if (props?.onProcessingAudio) {
            props.onProcessingAudio();
          }
        } else if (data.type === 'error') {
          console.error('❌ Ошибка от сервера:', data.message);
          if (props?.onError) {
            props.onError(data.message || 'Произошла ошибка');
          }
        }
      } catch (e) {
        console.error('❌ Ошибка парсинга сообщения:', e);
        if (props?.onError) {
          props.onError('Ошибка обработки ответа от сервера');
        }
      }
    };

    return () => {
      console.log('🧹 Очистка WebSocket');
      if (socketRef.current) {
        socketRef.current.close();
      }
    };
  }, [url, props]);

  const sendMessage = (message: WebSocketMessage) => {
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      console.log('📤 Отправляю сообщение:', message.type);
      socketRef.current.send(JSON.stringify(message));
      return true;
    } else {
      console.warn('⚠️ WebSocket не подключен. Сообщение не отправлено:', message);
      return false;
    }
  };

  return { 
    sendMessage, 
    isConnected 
  };
};
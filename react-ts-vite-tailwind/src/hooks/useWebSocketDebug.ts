// src/hooks/useWebSocketDebug.ts
import { useState, useEffect, useRef } from 'react';

interface UseWebSocketProps {
  onAssistantResponse?: (text: string, transcribedText?: string) => void;
  onError?: (error: string) => void;
}

export const useWebSocketDebug = (url: string, props?: UseWebSocketProps) => {
  const [isConnected, setIsConnected] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState('disconnected');

  useEffect(() => {
    console.log('🔄 Пытаюсь подключиться к:', url);
    setConnectionStatus('connecting');
    
    try {
      const ws = new WebSocket(url);
      
      ws.onopen = () => {
        console.log('✅ WebSocket подключен!');
        setIsConnected(true);
        setConnectionStatus('connected');
      };

      ws.onclose = (event) => {
        console.log('❌ WebSocket отключен:', event.code, event.reason);
        setIsConnected(false);
        setConnectionStatus(`disconnected: ${event.code} - ${event.reason}`);
        
        if (props?.onError) {
          props.onError(`WebSocket закрыт: ${event.code} - ${event.reason}`);
        }
      };

      ws.onerror = (error) => {
        console.error('❌ WebSocket ошибка:', error);
        setIsConnected(false);
        setConnectionStatus('error');
        
        if (props?.onError) {
          props.onError('Ошибка подключения WebSocket');
        }
      };

      ws.onmessage = (event) => {
        console.log('📨 Получено сообщение:', event.data);
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'assistant_response' && data.text && props?.onAssistantResponse) {
            props.onAssistantResponse(data.text, data.transcribed_text);
          }
        } catch (e) {
          console.error('Ошибка парсинга:', e);
        }
      };

      return () => {
        console.log('🧹 Очистка WebSocket');
        ws.close();
      };
    } catch (error) {
      console.error('❌ Ошибка создания WebSocket:', error);
      setConnectionStatus('creation_error');
      if (props?.onError) {
        props.onError('Не удалось создать WebSocket соединение');
      }
    }
  }, [url, props]);

  const sendMessage = (message: any) => {
    console.log('📤 Попытка отправить:', message);
    return false; // временно не отправляем
  };

  return { 
    sendMessage, 
    isConnected,
    connectionStatus
  };
};
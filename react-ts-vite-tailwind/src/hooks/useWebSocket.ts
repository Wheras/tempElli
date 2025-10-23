// src/hooks/useWebSocket.ts
import { useEffect, useRef, useState, useCallback } from "react";

type IncomingHandler = (text: string, transcribedText?: string) => void;
type ErrorHandler = (msg: string) => void;

interface UseWebSocketOptions {
  onAssistantResponse?: IncomingHandler;
  onError?: ErrorHandler;
  reconnectAttempts?: number;
  reconnectInterval?: number;
}

function getAutoWebSocketUrl(customUrl?: string): string {
  if (customUrl) return customUrl;

  const loc = window.location;
  const protocol = loc.protocol === "https:" ? "wss:" : "ws:";
  const host =
    loc.hostname === "localhost" || loc.hostname === "127.0.0.1"
      ? "localhost:8003" // порт твоего Python-сервера
      : loc.host;

  return `${protocol}//${host}/ws`;
}

export function useWebSocket(customUrl?: string, opts: UseWebSocketOptions = {}) {
  const url = getAutoWebSocketUrl(customUrl);
  const { onAssistantResponse, onError, reconnectAttempts = Infinity, reconnectInterval = 1000 } = opts;

  const wsRef = useRef<WebSocket | null>(null); // <--- добавь это
  const shouldReconnect = useRef(true);
  const attemptsRef = useRef(0);
  const reconnectTimer = useRef<number | null>(null);

  const [isConnected, setIsConnected] = useState(false);

  const connect = useCallback(() => {
    if (wsRef.current) {
      try { wsRef.current.close(); } catch {}
      wsRef.current = null;
    }

    try {
      console.log("🔌 Подключение к:", url);
      wsRef.current = new WebSocket(url);
    } catch (err) {
      setIsConnected(false);
      onError?.("Не удалось создать WebSocket: " + String(err));
      return;
    }

    wsRef.current.onopen = () => {
      attemptsRef.current = 0;
      setIsConnected(true);
      console.log("✅ WebSocket открыт");
    };

    wsRef.current.onmessage = (ev) => {
      try {
        const data = typeof ev.data === "string" ? JSON.parse(ev.data) : ev.data;
        if (data?.type === "assistant" || data?.role === "assistant" || data?.text) {
          const text = data.text ?? JSON.stringify(data);
          const transcribed = data.transcribed ?? undefined;
          onAssistantResponse?.(text, transcribed);
        } else {
          onAssistantResponse?.(JSON.stringify(data));
        }
      } catch {
        onAssistantResponse?.(String(ev.data));
      }
    };

    wsRef.current.onclose = (ev) => {
      setIsConnected(false);
      console.warn("⚠️ WebSocket закрыт:", ev.code, ev.reason || "");
      if (shouldReconnect.current && attemptsRef.current < reconnectAttempts) {
        attemptsRef.current += 1;
        const backoff = reconnectInterval * Math.pow(1.5, attemptsRef.current - 1);
        reconnectTimer.current = window.setTimeout(connect, Math.min(backoff, 30000));
      } else {
        onError?.("WebSocket закрыт и повторные попытки отключены.");
      }
    };

    wsRef.current.onerror = (ev) => {
      console.error("❌ WebSocket ошибка:", ev);
      setIsConnected(false);
      onError?.("Ошибка WebSocket (см. консоль).");
      try { wsRef.current?.close(); } catch {}
    };
  }, [url, onAssistantResponse, onError, reconnectAttempts, reconnectInterval]);

  useEffect(() => {
    shouldReconnect.current = true;
    connect();

    return () => {
      shouldReconnect.current = false;
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
      try { wsRef.current?.close(); } catch {}
    };
  }, [connect]);

  const sendMessage = useCallback((payload: any): boolean => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return false;
    try {
      const dataToSend = typeof payload === "string" ? payload : JSON.stringify(payload);
      wsRef.current.send(dataToSend);
      return true;
    } catch (e) {
      onError?.("Не удалось отправить сообщение: " + String(e));
      return false;
    }
  }, [onError]);

  const close = useCallback(() => {
    shouldReconnect.current = false;
    try { wsRef.current?.close(); } catch {}
  }, []);

  return { sendMessage, isConnected, close };
}

export default useWebSocket;
import { useEffect, useRef, useState } from "react";
import { WS_BASE } from "./api";

export interface WSEvent {
  type: "reading" | "alert" | "sos";
  data: any;
}

/**
 * Connects to the backend's /ws stream and calls onEvent for every message.
 * Auto-reconnects with backoff if the connection drops — a hackathon demo
 * shouldn't die because a laptop dozed off between the WiFi handoff.
 */
export function useLiveFeed(onEvent: (evt: WSEvent) => void) {
  const [connected, setConnected] = useState(false);
  const handlerRef = useRef(onEvent);
  handlerRef.current = onEvent;

  useEffect(() => {
    let ws: WebSocket | null = null;
    let retryTimer: ReturnType<typeof setTimeout>;
    let closedByUs = false;

    function connect() {
      ws = new WebSocket(`${WS_BASE}/ws`);
      ws.onopen = () => setConnected(true);
      ws.onclose = () => {
        setConnected(false);
        if (!closedByUs) retryTimer = setTimeout(connect, 3000);
      };
      ws.onerror = () => ws?.close();
      ws.onmessage = (msg) => {
        try {
          const evt: WSEvent = JSON.parse(msg.data);
          handlerRef.current(evt);
        } catch {
          /* ignore malformed frames */
        }
      };
    }

    connect();
    return () => {
      closedByUs = true;
      clearTimeout(retryTimer);
      ws?.close();
    };
  }, []);

  return { connected };
}

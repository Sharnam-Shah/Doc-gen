import { useState, useEffect, useCallback, useRef } from 'react';

const useWebSocket = (documentId) => {
    const [messages, setMessages] = useState([]);
    const [isConnected, setIsConnected] = useState(false);
    const wsRef = useRef(null);

    // Simple pub/sub for incoming messages so components can register
    // listeners and react immediately (avoids relying on array diffs).
    const listenersRef = useRef(new Set());

    useEffect(() => {
        // Do not connect if documentId is not provided or explicitly 'undefined'
        if (!documentId || documentId === 'undefined') {
            console.warn('useWebSocket: no valid documentId provided, skipping WebSocket connection');
            return;
        }

        // Prefer an explicit backend host (API base) for WebSocket connections so
        // we don't accidentally try to open ws:// on the frontend dev server.
        // Use VITE_API_BASE_URL when available, otherwise default to localhost:8000
        const apiBaseRaw = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
        const apiBase = apiBaseRaw.replace(/\/$/, '');

        // Build a WebSocket URL from the API base, but strip any '/api' suffix
        // because the HTTP API uses '/api/' while websocket routes live at the
        // root path (e.g. '/ws/document/:id/'). If the env contains a path like
        // 'http://localhost:8000/api', we want ws://localhost:8000/ws/...
        try {
            const parsed = new URL(apiBase);
            const protocol = parsed.protocol === 'https:' ? 'wss' : 'ws';
            // Remove trailing '/api' segment from pathname if present
            let basePath = parsed.pathname.replace(/\/api\/?$/i, '');
            // Ensure basePath does not end with slash
            basePath = basePath.replace(/\/$/, '');
            const host = parsed.host; // hostname:port
            const wsUrl = `${protocol}://${host}${basePath}/ws/document/${documentId}/`;
            console.debug('useWebSocket: connecting to', wsUrl);

            // Create WebSocket connection
            const ws = new WebSocket(wsUrl);
            wsRef.current = ws;
            
            ws.onopen = () => {
                setIsConnected(true);
                console.log('useWebSocket: connected to', wsUrl);
            };

            ws.onclose = (ev) => {
                setIsConnected(false);
                console.log('useWebSocket: disconnected', ev);
            };

            ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    // update message list
                    setMessages(prev => {
                        const next = [...prev, data];
                        return next;
                    });

                    // notify listeners immediately
                    listenersRef.current.forEach((cb) => {
                        try { cb(data); } catch (e) { console.error('useWebSocket listener error', e); }
                    });
                } catch (err) {
                    console.error('useWebSocket: failed to parse message', err, event.data);
                }
            };

            ws.onerror = (err) => {
                console.error('useWebSocket: WebSocket error', err);
            };

            return () => {
                try {
                    if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) {
                        ws.close();
                    }
                } catch (e) {
                    // ignore close errors
                }
                wsRef.current = null;
            };
        } catch (e) {
            console.error('useWebSocket: invalid VITE_API_BASE_URL', apiBaseRaw, e);
            return;
        }
    }, [documentId]);

    const sendMessage = useCallback((type, content) => {
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
            const message = {
                type,
                ...content
            };
            console.log('useWebSocket: sending message', message);
            wsRef.current.send(JSON.stringify(message));
        } else {
            console.error('useWebSocket: cannot send message, WebSocket not open. ReadyState:', wsRef.current?.readyState);
        }
    }, []);

    const addListener = useCallback((cb) => {
        listenersRef.current.add(cb);
        return () => listenersRef.current.delete(cb);
    }, []);

    const removeListener = useCallback((cb) => {
        listenersRef.current.delete(cb);
    }, []);

    return {
        isConnected,
        messages,
        sendMessage
        , addListener, removeListener
    };
};

export default useWebSocket;
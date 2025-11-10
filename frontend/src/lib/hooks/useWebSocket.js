import { useEffect, useRef, useCallback } from 'react';

export const useWebSocket = (documentId) => {
    const ws = useRef(null);

    const sendMessage = useCallback((data) => {
        if (ws.current?.readyState === WebSocket.OPEN) {
            ws.current.send(JSON.stringify(data));
        } else {
            console.error('WebSocket is not connected');
        }
    }, []);

    useEffect(() => {
        // Clean up previous connection
        if (ws.current) {
            ws.current.close();
        }

        // Only connect if we have a valid document ID
        if (documentId && documentId !== 'undefined') {
            const wsUrl = `ws://${window.location.hostname}:8000/ws/document/${documentId}/`;
            ws.current = new WebSocket(wsUrl);

            ws.current.onopen = () => {
                console.log('WebSocket connected');
            };

            ws.current.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    if (data.type === 'error') {
                        console.error('WebSocket error:', data.message);
                    }
                } catch (error) {
                    console.error('Error parsing WebSocket message:', error);
                }
            };

            ws.current.onerror = (error) => {
                console.error('WebSocket error:', error);
            };

            ws.current.onclose = () => {
                console.log('WebSocket disconnected');
            };
        }

        // Cleanup on unmount or document ID change
        return () => {
            if (ws.current) {
                ws.current.close();
            }
        };
    }, [documentId]);

    // Return functions and state needed by components
    return {
        sendMessage,
        isConnected: ws.current?.readyState === WebSocket.OPEN,
        // Additional WebSocket state or methods can be added here
    };
};
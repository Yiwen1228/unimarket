/**
 * chat.js — WebSocket real-time chat client (S2).
 * Expects CHAT_SENDER, CHAT_ROLE, CHAT_ROOM to be set in the template.
 * Supports message history on connect, timestamps, and typing indicator.
 */
(function () {
    'use strict';

    const messagesDiv = document.getElementById('chat-messages');
    const chatForm = document.getElementById('chat-form');
    const chatInput = document.getElementById('chat-input');

    // Extract productId from URL params (if chatting about a specific product)
    const urlParams = new URLSearchParams(window.location.search);
    const CHAT_PRODUCT_ID = urlParams.get('productId') || '';

    const wsProtocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
    const wsUrl = wsProtocol + window.location.host + '/ws/chat/' + CHAT_ROOM + '/';

    let socket;
    let reconnectAttempts = 0;
    let historyDone = false;

    /* ── Typing indicator state ───────────────────────── */
    let typingTimer = null;
    let typingClearTimer = null;
    var typingIndicator = document.createElement('p');
    typingIndicator.className = 'text-muted small mb-0 fst-italic';
    typingIndicator.id = 'typing-indicator';
    typingIndicator.style.display = 'none';
    messagesDiv.parentNode.insertBefore(typingIndicator, messagesDiv.nextSibling);

    function fmtTime(iso) {
        if (!iso) return '';
        var d = new Date(iso);
        return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }

    function connect() {
        historyDone = false;
        socket = new WebSocket(wsUrl);

        socket.onopen = function () {
            reconnectAttempts = 0;
            messagesDiv.innerHTML = '';
        };

        socket.onmessage = function (e) {
            var data = JSON.parse(e.data);

            // Handle typing indicator
            if (data.type === 'typing') {
                if (data.sender !== CHAT_SENDER) {
                    typingIndicator.textContent = data.sender + ' is typing...';
                    typingIndicator.style.display = 'block';
                    clearTimeout(typingClearTimer);
                    typingClearTimer = setTimeout(function () {
                        typingIndicator.style.display = 'none';
                    }, 3000);
                }
                return;
            }

            if (data.history && !historyDone) {
                appendMessage(data.sender, data.message, data.role, data.sender === CHAT_SENDER, data.timestamp, true);
            } else {
                historyDone = true;
                appendMessage(data.sender, data.message, data.role, data.sender === CHAT_SENDER, data.timestamp, false);
            }
        };

        socket.onclose = function () {
            if (reconnectAttempts < 5) {
                reconnectAttempts++;
                setTimeout(connect, 2000 * reconnectAttempts);
                appendSystemMsg('Disconnected. Reconnecting...');
            } else {
                appendSystemMsg('Connection lost. Please refresh the page.');
            }
        };

        socket.onerror = function () {
            appendSystemMsg('Connection error.');
        };
    }

    function appendMessage(sender, message, role, isSelf, timestamp, isHistory) {
        var wrapper = document.createElement('div');
        wrapper.className = 'd-flex ' + (isSelf ? 'justify-content-end' : 'justify-content-start');
        if (isHistory) wrapper.classList.add('chat-history');

        var bubble = document.createElement('div');
        bubble.className = 'chat-bubble ' + (isSelf ? 'sent' : 'received');

        var senderEl = document.createElement('div');
        senderEl.className = 'chat-sender';
        senderEl.textContent = sender + (role === 'staff' ? ' (Staff)' : '');

        var msgEl = document.createElement('div');
        msgEl.textContent = message;

        bubble.appendChild(senderEl);
        bubble.appendChild(msgEl);

        if (timestamp) {
            var timeEl = document.createElement('div');
            timeEl.className = 'chat-time';
            timeEl.textContent = fmtTime(timestamp);
            bubble.appendChild(timeEl);
        }

        wrapper.appendChild(bubble);
        messagesDiv.appendChild(wrapper);
        messagesDiv.scrollTop = messagesDiv.scrollHeight;

        // Hide typing indicator when a message arrives
        typingIndicator.style.display = 'none';
    }

    function appendSystemMsg(text) {
        var p = document.createElement('p');
        p.className = 'text-muted text-center small';
        p.textContent = text;
        messagesDiv.appendChild(p);
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
    }

    /* ── Send typing event (debounced, max once per 2s) ─ */
    function sendTypingEvent() {
        if (socket && socket.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify({ type: 'typing', sender: CHAT_SENDER }));
        }
    }

    chatInput.addEventListener('input', function () {
        if (!typingTimer) {
            sendTypingEvent();
            typingTimer = setTimeout(function () {
                typingTimer = null;
            }, 2000);
        }
    });

    chatForm.addEventListener('submit', function (e) {
        e.preventDefault();
        var msg = chatInput.value.trim();
        if (!msg) return;
        if (!socket || socket.readyState !== WebSocket.OPEN) {
            appendSystemMsg('Not connected. Please wait...');
            return;
        }
        var payload = {
            message: msg,
            sender: CHAT_SENDER,
            role: CHAT_ROLE,
        };
        if (CHAT_PRODUCT_ID) payload.productId = CHAT_PRODUCT_ID;
        socket.send(JSON.stringify(payload));
        chatInput.value = '';
        chatInput.focus();
    });

    connect();
})();

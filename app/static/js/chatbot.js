// ============================================================
// Galbay Predictor - Chatbot Widget (Phase 1: FAQ rule-based)
// ============================================================

(function() {
  'use strict';

  const QUICK_REPLIES = [
    'Apa itu galbay?',
    'Cek pinjol',
    'Snowball vs Avalanche',
    'DC agresif',
    'Cara recovery',
  ];

  const ICON_OPEN = '💬';
  const ICON_CLOSE = '✕';

  function el(tag, attrs, children) {
    const e = document.createElement(tag);
    if (attrs) {
      for (const k in attrs) {
        if (k === 'class') e.className = attrs[k];
        else if (k === 'html') e.innerHTML = attrs[k];
        else if (k.startsWith('on') && typeof attrs[k] === 'function') {
          e.addEventListener(k.slice(2), attrs[k]);
        } else e.setAttribute(k, attrs[k]);
      }
    }
    if (children) {
      (Array.isArray(children) ? children : [children]).forEach(c => {
        if (c == null) return;
        e.appendChild(typeof c === 'string' ? document.createTextNode(c) : c);
      });
    }
    return e;
  }

  function formatAnswer(text) {
    // Convert **bold** to <strong> and keep line breaks
    if (!text) return '';
    let html = text
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.+?)\*/g, '<em>$1</em>');
    return html;
  }

  function timeNow() {
    const d = new Date();
    return d.getHours().toString().padStart(2, '0') + ':' + d.getMinutes().toString().padStart(2, '0');
  }

  function addMessage(role, text, meta) {
    const messages = document.getElementById('chatMessages');
    if (!messages) return;

    const wrapper = el('div');
    const msg = el('div', { class: 'chat-msg ' + role, html: formatAnswer(text) });
    wrapper.appendChild(msg);
    if (meta) {
      const m = el('div', { class: 'chat-msg-meta ' + role, html: meta });
      wrapper.appendChild(m);
    }
    messages.appendChild(wrapper);
    messages.scrollTop = messages.scrollHeight;
  }

  function addTypingIndicator() {
    const messages = document.getElementById('chatMessages');
    if (!messages) return null;
    const t = el('div', { class: 'chat-typing' });
    t.appendChild(el('span'));
    t.appendChild(el('span'));
    t.appendChild(el('span'));
    t.id = 'chatTyping';
    messages.appendChild(t);
    messages.scrollTop = messages.scrollHeight;
    return t;
  }

  function removeTypingIndicator() {
    const t = document.getElementById('chatTyping');
    if (t) t.remove();
  }

  function showRelatedActions(actions) {
    const relatedEl = document.getElementById('chatRelated');
    if (!relatedEl) return;
    if (!actions || !actions.length) {
      relatedEl.style.display = 'none';
      relatedEl.innerHTML = '';
      return;
    }
    relatedEl.innerHTML = '';
    actions.forEach(a => {
      const link = el('a', { href: a.href || '#' });
      link.appendChild(el('span', null, '→'));
      link.appendChild(document.createTextNode(a.label));
      relatedEl.appendChild(link);
    });
    relatedEl.style.display = 'flex';
  }

  function showSuggestions(suggestions) {
    const actionsEl = document.getElementById('chatActions');
    if (!actionsEl) return;
    actionsEl.innerHTML = '';
    if (!suggestions || !suggestions.length) return;
    suggestions.slice(0, 6).forEach(s => {
      const chip = el('button', { type: 'button', class: 'chat-action-chip' }, s);
      chip.addEventListener('click', () => {
        document.getElementById('chatInput').value = s;
        sendMessage();
      });
      actionsEl.appendChild(chip);
    });
  }

  async function sendMessage() {
    const input = document.getElementById('chatInput');
    if (!input) return;
    const text = input.value.trim();
    if (!text) return;
    input.value = '';
    addMessage('user', text, timeNow());
    showRelatedActions([]);
    const typingEl = addTypingIndicator();
    const sendBtn = document.querySelector('.chat-send');
    if (sendBtn) sendBtn.disabled = true;

    try {
      const resp = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text }),
      });
      const result = await resp.json();
      if (typingEl) removeTypingIndicator();
      if (result.valid) {
        const meta = `${result.intent || 'unknown'} · ${(result.confidence || 0).toFixed(0)}%`;
        addMessage('bot', result.answer, meta);
        showSuggestions(result.suggestions || []);
        showRelatedActions(result.related_actions || []);
      } else {
        addMessage('bot', result.error || 'Maaf, ada error. Coba lagi ya.', 'error');
      }
    } catch (err) {
      if (typingEl) removeTypingIndicator();
      addMessage('bot', 'Koneksi gagal. Cek internet kamu lalu coba lagi.', 'network-error');
    } finally {
      if (sendBtn) sendBtn.disabled = false;
    }
  }

  function openChat() {
    const panel = document.getElementById('chatPanel');
    const bubble = document.getElementById('chatBubble');
    if (!panel) return;
    panel.classList.add('open');
    panel.setAttribute('aria-hidden', 'false');
    if (bubble) {
      bubble.classList.remove('has-unread');
      const icon = document.getElementById('chatBubbleIcon');
      if (icon) icon.textContent = ICON_CLOSE;
    }
    setTimeout(() => {
      const inp = document.getElementById('chatInput');
      if (inp) inp.focus();
    }, 200);
  }

  function closeChat() {
    const panel = document.getElementById('chatPanel');
    const bubble = document.getElementById('chatBubble');
    if (!panel) return;
    panel.classList.remove('open');
    panel.setAttribute('aria-hidden', 'true');
    if (bubble) {
      const icon = document.getElementById('chatBubbleIcon');
      if (icon) icon.textContent = ICON_OPEN;
    }
  }

  function init() {
    const bubble = document.getElementById('chatBubble');
    const closeBtn = document.getElementById('chatCloseBtn');
    const form = document.getElementById('chatForm');
    if (!bubble) return;

    bubble.addEventListener('click', () => {
      const panel = document.getElementById('chatPanel');
      if (panel && panel.classList.contains('open')) closeChat();
      else openChat();
    });
    if (closeBtn) closeBtn.addEventListener('click', closeChat);
    if (form) form.addEventListener('submit', (e) => { e.preventDefault(); sendMessage(); });

    // ESC close
    document.addEventListener('keydown', (e) => {
      const panel = document.getElementById('chatPanel');
      if (e.key === 'Escape' && panel && panel.classList.contains('open')) closeChat();
    });

    // Initial welcome message
    setTimeout(() => {
      if (document.getElementById('chatMessages').children.length === 0) {
        addMessage('bot',
          'Halo! 👋 Saya **Galbay AI Coach**. Saya bisa bantu jelasin soal galbay, pinjol, recovery, dll.\n\nMau tanya apa?',
          'welcome');
        showSuggestions(QUICK_REPLIES);
      }
    }, 500);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();

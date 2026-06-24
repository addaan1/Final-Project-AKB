// ============================================================
// Galbay Predictor - Chatbot Widget v2 (NLP-like, 38 intents)
// ============================================================

(function() {
  'use strict';

  const QUICK_REPLIES = [
    'Apa itu galbay?',
    'Cek pinjol legal?',
    'Snowball vs Avalanche',
    'DC agresif, gimana?',
    'Cara recovery',
  ];

  const CATEGORY_CHIPS = [
    { label: 'Galbay basics', query: 'apa itu galbay?' },
    { label: 'Pinjol legal?', query: 'cara cek pinjol legal' },
    { label: 'Strategi bayar', query: 'snowball vs avalanche' },
    { label: 'DC agresif', query: 'DC agresif' },
    { label: 'Recovery', query: 'cara recovery' },
    { label: 'Hak hukum', query: 'hak borrower' },
    { label: 'Mental health', query: 'stress finansial' },
  ];

  const SENTIMENT_EMOJI = {
    curious: '🤔',
    stressed: '😟',
    anxious: '😰',
    crisis: '🆘',
    frustrated: '😤',
    positive: '🙂',
    grateful: '🙏',
    neutral: '',
  };

  const ICON_OPEN = '💬';
  const ICON_CLOSE = '✕';

  let sessionLog = [];
  let voiceRecorder = null;

  // ============================================================
  // DOM helpers
  // ============================================================
  function el(tag, attrs, children) {
    const e = document.createElement(tag);
    if (attrs) {
      for (const k in attrs) {
        if (k === 'class') e.className = attrs[k];
        else if (k === 'html') e.innerHTML = attrs[k];
        else if (k.startsWith('on') && typeof attrs[k] === 'function') {
          e.addEventListener(k.slice(2).toLowerCase(), attrs[k]);
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

  function timeNow() {
    const d = new Date();
    return d.getHours().toString().padStart(2, '0') + ':' + d.getMinutes().toString().padStart(2, '0');
  }

  function pageContext() {
    const path = window.location.pathname || '';
    if (path.includes('ringkasan')) return 'ringkasan';
    if (path.includes('analisis')) return 'analisis';
    if (path.includes('solusi')) return 'solusi';
    if (path.includes('produk')) return 'produk';
    if (path.includes('kesimpulan')) return 'kesimpulan';
    return null;
  }

  // ============================================================
  // Message rendering
  // ============================================================
  function addMessage(role, text, meta, html) {
    const messages = document.getElementById('chatMessages');
    if (!messages) return;

    const wrapper = el('div', { class: 'chat-msg-wrap ' + role });
    const rendered = html || (role === 'bot' ? renderMarkdown(text) : escapeHtml(text).replace(/\n/g, '<br>'));
    const msg = el('div', {
      class: 'chat-msg ' + role,
      html: rendered,
    });
    wrapper.appendChild(msg);

    if (meta) {
      const m = el('div', { class: 'chat-msg-meta ' + role, html: meta });
      wrapper.appendChild(m);
    }

    messages.appendChild(wrapper);
    messages.scrollTop = messages.scrollHeight;
  }

  function escapeHtml(s) {
    const d = document.createElement('div');
    d.textContent = s;
    return d.innerHTML;
  }

  // ============================================================
  // Mini markdown renderer (XSS-safe)
  // Handles: **bold**, *italic*, `code`, - list, 1. ordered, [text](url)
  // Plus: collapse excessive whitespace, normalize line breaks
  // ============================================================
  function renderMarkdown(text) {
    if (!text) return '';
    // Step 1: escape HTML first (XSS-safe foundation)
    let s = escapeHtml(text);
    // Step 2: collapse 3+ newlines into 2 (max one blank line)
    s = s.replace(/\n{3,}/g, '\n\n');
    // Step 3: extract code spans `xxx` (placeholder to avoid inner ** processing)
    const codeStore = [];
    s = s.replace(/`([^`\n]+)`/g, function(m, c) {
      codeStore.push(c);
      return '\x00CODE' + (codeStore.length - 1) + '\x00';
    });
    // Step 4: extract markdown links [text](url) before doing other formatting
    s = s.replace(/\[([^\]]+)\]\(([^)\s]+)\)/g, function(m, label, url) {
      const isExternal = /^https?:\/\//.test(url);
      const safeUrl = url.replace(/"/g, '&quot;');
      const target = isExternal ? ' target="_blank" rel="noopener noreferrer"' : '';
      const ext = isExternal ? ' <span class="ext-link-icon" aria-hidden="true">↗</span>' : '';
      return '<a href="' + safeUrl + '"' + target + ' class="md-link">' + label + ext + '</a>';
    });
    // Step 5: bold **xxx** (non-greedy, no newlines inside)
    s = s.replace(/\*\*([^*\n]+?)\*\*/g, '<strong>$1</strong>');
    // Step 6: italic *xxx* (avoid matching already-bolded)
    s = s.replace(/(^|[^*])\*([^*\n]+?)\*(?!\*)/g, '$1<em>$2</em>');
    // Step 7: restore code spans
    s = s.replace(/\x00CODE(\d+)\x00/g, function(m, i) {
      return '<code>' + codeStore[+i] + '</code>';
    });
    // Step 8: list items - convert "- " and "* " at line start to <li>
    const lines = s.split('\n');
    const out = [];
    let inUl = false, inOl = false;
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      const olMatch = line.match(/^(\d+)\.\s+(.+)$/);
      const ulMatch = line.match(/^[-*]\s+(.+)$/);
      if (olMatch) {
        if (inUl) { out.push('</ul>'); inUl = false; }
        if (!inOl) { out.push('<ol class="md-list">'); inOl = true; }
        out.push('<li>' + olMatch[2] + '</li>');
      } else if (ulMatch) {
        if (inOl) { out.push('</ol>'); inOl = false; }
        if (!inUl) { out.push('<ul class="md-list">'); inUl = true; }
        out.push('<li>' + ulMatch[1] + '</li>');
      } else {
        if (inUl) { out.push('</ul>'); inUl = false; }
        if (inOl) { out.push('</ol>'); inOl = false; }
        out.push(line);
      }
    }
    if (inUl) out.push('</ul>');
    if (inOl) out.push('</ol>');
    s = out.join('\n');
    // Step 9: collapse multiple spaces (preserve line breaks)
    s = s.replace(/[^\S\n]{2,}/g, ' ');

    // Step 10: Convert remaining newlines to <br> inside paragraphs
    // Split into paragraphs (blocks separated by blank lines or list boundaries)
    // Wrap each non-list paragraph in <p>
    const finalParts = [];
    const segs = s.split(/\n\n/);
    for (const seg of segs) {
      if (!seg.trim()) continue;
      if (/^<(ul|ol|pre)/.test(seg.trim())) {
        finalParts.push(seg.replace(/\n/g, ''));
      } else {
        // Single newline -> space, double newlines already split
        const para = seg.replace(/\n/g, ' ').trim();
        finalParts.push('<p>' + para + '</p>');
      }
    }
    return finalParts.join('');
  }

  function addTypingIndicator() {
    const area = document.getElementById('chatTypingArea');
    if (area) {
      area.style.display = 'flex';
      const messages = document.getElementById('chatMessages');
      if (messages) messages.scrollTop = messages.scrollHeight;
    }
  }

  function removeTypingIndicator() {
    const area = document.getElementById('chatTypingArea');
    if (area) area.style.display = 'none';
  }

  // ============================================================
  // Suggestions / Related actions
  // ============================================================
  function showSuggestions(suggestions) {
    const actionsEl = document.getElementById('chatActions');
    if (!actionsEl) return;
    actionsEl.innerHTML = '';
    if (!suggestions || !suggestions.length) return;
    suggestions.slice(0, 5).forEach(s => {
      const chip = el('button', { type: 'button', class: 'chat-action-chip' }, s);
      chip.addEventListener('click', () => {
        const inp = document.getElementById('chatInput');
        if (inp) {
          inp.value = s;
          sendMessage();
        }
      });
      actionsEl.appendChild(chip);
    });
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
    actions.slice(0, 3).forEach(a => {
      const link = el('a', { href: a.href || '#' });
      if (a.external) {
        link.setAttribute('target', '_blank');
        link.setAttribute('rel', 'noopener');
      }
      link.appendChild(document.createTextNode(a.label));
      const arrow = el('span', null, '→');
      link.appendChild(arrow);
      relatedEl.appendChild(link);
    });
    relatedEl.style.display = 'flex';
  }

  // ============================================================
  // Categories (chips at top)
  // ============================================================
  function renderCategories() {
    const container = document.getElementById('chatCatChips');
    if (!container) return;
    container.innerHTML = '';
    CATEGORY_CHIPS.forEach(cat => {
      const chip = el('button', { type: 'button', class: 'chat-cat-chip' }, cat.label);
      chip.addEventListener('click', () => {
        const inp = document.getElementById('chatInput');
        if (inp) {
          inp.value = cat.query;
          sendMessage();
        }
      });
      container.appendChild(chip);
    });
  }

  // ============================================================
  // Sending messages
  // ============================================================
  async function sendMessage() {
    const input = document.getElementById('chatInput');
    if (!input) return;
    const text = input.value.trim();
    if (!text) return;
    input.value = '';
    addMessage('user', text, timeNow());
    sessionLog.push({ role: 'user', text, time: timeNow() });

    showRelatedActions([]);
    showSuggestions([]);
    addTypingIndicator();

    const sendBtn = document.getElementById('chatSendBtn');
    if (sendBtn) sendBtn.disabled = true;

    try {
      const resp = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: text,
          page_context: pageContext(),
        }),
      });
      const result = await resp.json();
      removeTypingIndicator();

      if (result.valid) {
        const meta = buildMeta(result);
        addMessage('bot', '', meta, result.answer_html || escapeHtml(result.answer || ''));
        sessionLog.push({
          role: 'bot',
          text: result.answer,
          html: result.answer_html,
          intent: result.intent,
          sentiment: result.sentiment,
          time: timeNow(),
        });
        showSuggestions(result.suggestions || []);
        showRelatedActions(result.related_actions || []);

        // Auto-crisis notice: crisis intent → pulse bubble
        if (result.sentiment === 'crisis') {
          const bubble = document.getElementById('chatBubble');
          if (bubble) bubble.classList.add('has-unread');
        }
      } else {
        addMessage('bot', result.error || 'Maaf, ada error. Coba lagi ya.', 'error');
      }
    } catch (err) {
      removeTypingIndicator();
      addMessage('bot', 'Koneksi gagal. Cek internet kamu lalu coba lagi.', 'network-error');
    } finally {
      if (sendBtn) sendBtn.disabled = false;
    }
  }

  function buildMeta(result) {
    const moduleIcon = result.module_icon || '💬';
    const moduleName = result.module_name || '';
    const conf = Math.round((result.confidence || 0) * 100);
    const parts = [
      `${moduleIcon} ${moduleName}`.trim(),
      `${conf}% yakin`,
    ];
    if (result.secondary_intents && result.secondary_intents.length > 0) {
      parts.push(`+${result.secondary_intents.length} topik terkait`);
    }
    return parts.join(' · ');
  }

  // ============================================================
  // Clear / Export
  // ============================================================
  function clearChat() {
    const messages = document.getElementById('chatMessages');
    if (messages) messages.innerHTML = '';
    sessionLog = [];
    showSuggestions(QUICK_REPLIES);
    showRelatedActions([]);
    setTimeout(() => {
      addMessage('bot',
        'Halo! 👋 Chat sudah di-reset. Saya **Galbay AI Coach** — siap bantu lagi.\n\nMau tanya soal apa?',
        'reset',
      );
    }, 200);
  }

  function exportChat() {
    if (sessionLog.length === 0) {
      const messages = document.getElementById('chatMessages');
      const data = messages ? messages.innerText : '';
      if (!data.trim()) {
        addMessage('bot', 'Belum ada chat untuk di-export. Yuk mulai ngobrol dulu!', 'export-empty');
        return;
      }
    }

    let md = `# Galbay AI Coach - Chat Export\n`;
    md += `Exported: ${new Date().toLocaleString('id-ID')}\n\n---\n\n`;

    sessionLog.forEach(entry => {
      const who = entry.role === 'user' ? 'Anda' : 'Galbay Coach';
      md += `**${who}** (${entry.time}):\n\n${entry.text}\n\n`;
      if (entry.intent) {
        md += `*Intent: ${entry.intent} | Sentiment: ${entry.sentiment}*\n\n`;
      }
      md += `---\n\n`;
    });

    md += `\n*Disclaimer: Galbay AI Coach adalah asisten rule-based. Bukan pengganti nasihat profesional.*\n`;

    const blob = new Blob([md], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `galbay-chat-${Date.now()}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  // ============================================================
  // Voice input (Web Speech API)
  // ============================================================
  function setupVoice() {
    const voiceBtn = document.getElementById('chatVoiceBtn');
    if (!voiceBtn) return;
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      voiceBtn.style.display = 'none';
      return;
    }
    voiceBtn.addEventListener('click', () => {
      if (voiceRecorder) {
        voiceRecorder.stop();
        voiceRecorder = null;
        voiceBtn.classList.remove('recording');
        return;
      }
      voiceRecorder = new SpeechRecognition();
      voiceRecorder.lang = 'id-ID';
      voiceRecorder.interimResults = true;
      voiceRecorder.continuous = false;
      voiceBtn.classList.add('recording');
      const input = document.getElementById('chatInput');

      voiceRecorder.onresult = (event) => {
        let final = '';
        for (let i = event.resultIndex; i < event.results.length; i++) {
          if (event.results[i].isFinal) {
            final += event.results[i][0].transcript;
          }
        }
        if (final && input) {
          input.value = final;
        }
      };
      voiceRecorder.onend = () => {
        voiceBtn.classList.remove('recording');
        voiceRecorder = null;
        if (input && input.value.trim()) {
          sendMessage();
        }
      };
      voiceRecorder.onerror = () => {
        voiceBtn.classList.remove('recording');
        voiceRecorder = null;
      };
      try {
        voiceRecorder.start();
      } catch (e) {
        voiceBtn.classList.remove('recording');
        voiceRecorder = null;
      }
    });
  }

  // ============================================================
  // Open / Close
  // ============================================================
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

  // ============================================================
  // Welcome message
  // ============================================================
  function showWelcome() {
    if (document.getElementById('chatMessages').children.length > 0) return;
    const hour = new Date().getHours();
    let greeting = 'Halo';
    if (hour < 11) greeting = 'Selamat pagi';
    else if (hour < 15) greeting = 'Selamat siang';
    else if (hour < 18) greeting = 'Selamat sore';
    else greeting = 'Selamat malam';

    addMessage('bot',
      `${greeting}! 👋 Saya **Galbay AI Coach** — asisten 24/7 untuk masalah galbay, pinjol, dan recovery.\n\nSaya bisa bantu:\n- **Pinjol**: cek legal/ilegal, bunga wajar\n- **DC**: negosiasi, template chat, lapor\n- **Recovery**: keluar dari galbay 30/60/90 hari\n- **Mental**: stress, cemas, butuh curhat\n\nMau tanya apa?`,
      'welcome',
    );
    showSuggestions(QUICK_REPLIES);
  }

  // ============================================================
  // Init
  // ============================================================
  function init() {
    const bubble = document.getElementById('chatBubble');
    if (!bubble) return;

    renderCategories();
    setupVoice();

    bubble.addEventListener('click', () => {
      const panel = document.getElementById('chatPanel');
      if (panel && panel.classList.contains('open')) closeChat();
      else openChat();
    });

    const closeBtn = document.getElementById('chatCloseBtn');
    if (closeBtn) closeBtn.addEventListener('click', closeChat);

    const clearBtn = document.getElementById('chatClearBtn');
    if (clearBtn) clearBtn.addEventListener('click', clearChat);

    const exportBtn = document.getElementById('chatExportBtn');
    if (exportBtn) exportBtn.addEventListener('click', exportChat);

    const form = document.getElementById('chatForm');
    if (form) form.addEventListener('submit', (e) => { e.preventDefault(); sendMessage(); });

    document.addEventListener('keydown', (e) => {
      const panel = document.getElementById('chatPanel');
      if (e.key === 'Escape' && panel && panel.classList.contains('open')) closeChat();
    });

    setTimeout(showWelcome, 500);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();

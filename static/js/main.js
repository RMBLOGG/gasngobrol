// ─── GLOBAL UTILITIES ─────────────────────────────────────────────

const API = {
  async get(url) {
    const r = await fetch(url);
    return r.json();
  },
  async post(url, data) {
    const r = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    return r.json();
  }
};

function showToast(msg, type = 'info') {
  const toast = document.getElementById('appToast');
  const toastMsg = document.getElementById('toastMsg');
  if (!toast || !toastMsg) return;
  toastMsg.textContent = msg;
  toast.className = `toast align-items-center border-0 text-white bg-${type === 'error' ? 'danger' : type === 'success' ? 'success' : 'secondary'}`;
  new bootstrap.Toast(toast, { delay: 3000 }).show();
}

function formatTime(dateStr) {
  if (!dateStr) return '';
  const d = new Date(dateStr);
  const now = new Date();
  const diff = now - d;
  const mins = Math.floor(diff / 60000);
  const hours = Math.floor(diff / 3600000);
  const days = Math.floor(diff / 86400000);
  if (mins < 1) return 'Baru saja';
  if (mins < 60) return `${mins} menit`;
  if (hours < 24) return d.toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit' });
  if (days < 7) return d.toLocaleDateString('id-ID', { weekday: 'short' });
  return d.toLocaleDateString('id-ID', { day: '2-digit', month: 'short' });
}

function formatMessageTime(dateStr) {
  if (!dateStr) return '';
  return new Date(dateStr).toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit' });
}

function formatDateDivider(dateStr) {
  const d = new Date(dateStr);
  const now = new Date();
  const diff = Math.floor((now - d) / 86400000);
  if (diff === 0) return 'Hari ini';
  if (diff === 1) return 'Kemarin';
  return d.toLocaleDateString('id-ID', { day: '2-digit', month: 'long', year: 'numeric' });
}

function avatar(url, name, size = 48) {
  const src = url || `https://api.dicebear.com/7.x/avataaars/svg?seed=${encodeURIComponent(name || 'user')}`;
  return `<img src="${src}" class="avatar" style="width:${size}px;height:${size}px" alt="${name || ''}" onerror="this.src='https://api.dicebear.com/7.x/initials/svg?seed=${encodeURIComponent(name||'?')}'">`;
}

function escapeHtml(str) {
  return String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

// ─── GLOBAL SEARCH ────────────────────────────────────────────────
const searchBtn = document.getElementById('searchBtn');
const closeSearch = document.getElementById('closeSearch');
const globalSearch = document.getElementById('globalSearch');
const globalSearchInput = document.getElementById('globalSearchInput');
const searchResults = document.getElementById('searchResults');

if (searchBtn) {
  searchBtn.addEventListener('click', () => {
    globalSearch.classList.add('active');
    globalSearchInput.focus();
  });
}
if (closeSearch) {
  closeSearch.addEventListener('click', () => {
    globalSearch.classList.remove('active');
    globalSearchInput.value = '';
    if (searchResults) searchResults.innerHTML = '';
  });
}
if (globalSearchInput) {
  let timer;
  globalSearchInput.addEventListener('input', () => {
    clearTimeout(timer);
    const q = globalSearchInput.value.trim();
    if (q.length < 2) { searchResults.innerHTML = ''; return; }
    timer = setTimeout(async () => {
      const users = await API.get(`/api/users/search?q=${encodeURIComponent(q)}`);
      searchResults.innerHTML = users.map(u => `
        <div class="user-list-item" onclick="openChatWith('${u.id}')">
          <div class="avatar-wrap">
            ${avatar(u.avatar_url, u.display_name)}
            ${u.is_online ? '<span class="online-dot"></span>' : ''}
          </div>
          <div>
            <div class="fw-semibold">${escapeHtml(u.display_name)}</div>
            <div class="text-muted" style="font-size:13px">@${escapeHtml(u.username)}</div>
          </div>
        </div>
      `).join('') || '<div class="p-4 text-center text-muted">Tidak ditemukan</div>';
    }, 400);
  });
}

// ─── NEW CHAT MODAL SEARCH ────────────────────────────────────────
const newChatSearch = document.getElementById('newChatSearch');
const newChatResults = document.getElementById('newChatResults');
if (newChatSearch) {
  let timer2;
  newChatSearch.addEventListener('input', () => {
    clearTimeout(timer2);
    const q = newChatSearch.value.trim();
    if (q.length < 2) { newChatResults.innerHTML = ''; return; }
    timer2 = setTimeout(async () => {
      const users = await API.get(`/api/users/search?q=${encodeURIComponent(q)}`);
      newChatResults.innerHTML = users.map(u => `
        <div class="user-list-item" onclick="openChatWith('${u.id}')">
          <div class="avatar-wrap">
            ${avatar(u.avatar_url, u.display_name)}
            ${u.is_online ? '<span class="online-dot"></span>' : ''}
          </div>
          <div class="flex-1">
            <div class="fw-semibold">${escapeHtml(u.display_name)}</div>
            <div class="text-muted" style="font-size:13px">@${escapeHtml(u.username)}</div>
          </div>
          <button class="btn btn-sm" style="background:var(--bg-input);color:var(--text-primary);border-radius:20px;font-size:12px" onclick="addContact('${u.id}',event)">+ Kontak</button>
        </div>
      `).join('') || '<div class="p-4 text-center text-muted">Tidak ditemukan</div>';
    }, 400);
  });
}

async function openChatWith(userId) {
  const res = await API.post('/api/chats/open', { user_id: userId });
  if (res.success) {
    const modal = bootstrap.Modal.getInstance(document.getElementById('newChatModal'));
    if (modal) modal.hide();
    if (globalSearch) globalSearch.classList.remove('active');
    window.location.href = `/chat/${res.chat_id}`;
  } else {
    showToast(res.message || 'Gagal membuka chat', 'error');
  }
}

async function addContact(userId, e) {
  e.stopPropagation();
  const res = await API.post('/api/contacts/add', { contact_id: userId });
  showToast(res.success ? 'Kontak ditambahkan!' : res.message, res.success ? 'success' : 'error');
}

// ─── DARK MODE TOGGLE ─────────────────────────────────────────────
const darkToggle = document.getElementById('darkModeToggle');
if (darkToggle) {
  const saved = localStorage.getItem('theme') || 'dark';
  darkToggle.checked = saved === 'dark';
  document.documentElement.setAttribute('data-bs-theme', saved);
  darkToggle.addEventListener('change', () => {
    const t = darkToggle.checked ? 'dark' : 'light';
    document.documentElement.setAttribute('data-bs-theme', t);
    localStorage.setItem('theme', t);
  });
}

// ─── PWA ─────────────────────────────────────────────────────────
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/static/sw.js').catch(() => {});
}

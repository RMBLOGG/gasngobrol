# 💬 ChatKu - WhatsApp Clone

Chat real-time berbasis Flask + Supabase + Bootstrap

## Fitur
- ✅ Register & Login manual (SHA-256)
- ✅ Chat private 1-on-1
- ✅ Grup chat + buat polling
- ✅ Manajemen kontak
- ✅ Status (24 jam)
- ✅ Reply pesan
- ✅ Hapus pesan
- ✅ Edit profil
- ✅ Online/Offline indicator
- ✅ Bottom navigation mobile
- ✅ Dark mode + toggle
- ✅ PWA (installable)
- ✅ Search pengguna global
- ✅ Emoji picker
- ✅ Polling di grup

## Setup

### 1. Database Supabase
Buka Supabase SQL Editor → paste isi `schema.sql` → Run

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Atur Environment Variable
Edit file `.env`:
```
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_KEY=eyJ... (opsional)
SECRET_KEY=ganti_dengan_string_acak
```

### 4. Jalankan Lokal
```bash
python app.py
```
Buka: http://localhost:5000

## Deploy ke Vercel

1. Push ke GitHub
2. Buka vercel.com → Import repo
3. Tambah Environment Variables di Vercel:
   - `SUPABASE_URL`
   - `SUPABASE_ANON_KEY`
   - `SECRET_KEY`
4. Deploy!

## Struktur
```
chatapp/
├── app.py              # Flask backend + API routes
├── requirements.txt
├── vercel.json         # Konfigurasi Vercel
├── schema.sql          # SQL Supabase
├── .env                # Environment variables
├── static/
│   ├── css/main.css    # Dark theme CSS
│   ├── js/main.js      # Global JS
│   ├── manifest.json   # PWA manifest
│   └── sw.js           # Service worker
└── templates/
    ├── base.html        # Layout utama + bottom nav
    ├── chats.html       # Daftar chat + status
    ├── chat_room.html   # Room chat private
    ├── groups.html      # Daftar grup
    ├── group_room.html  # Room grup + polling
    ├── contacts.html    # Kontak
    ├── profile.html     # Profil
    └── auth/
        ├── login.html
        └── register.html
```

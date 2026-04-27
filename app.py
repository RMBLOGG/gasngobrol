from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_cors import CORS
from supabase import create_client, Client
from dotenv import load_dotenv
import os
import hashlib
import uuid
from datetime import datetime, timezone
import json

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "chatapp_secret_2024")
CORS(app)

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://mafnnqttvkdgqqxczqyt.supabase.co")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1hZm5ucXR0dmtkZ3FxeGN6cXl0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzE4NzQyMDEsImV4cCI6MjA4NzQ1MDIwMX0.YRh1oWVKnn4tyQNRbcPhlSyvr7V_1LseWN7VjcImb-Y")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

# ─── AUTH ─────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('chats'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        if not username or not password:
            return jsonify({'success': False, 'message': 'Username dan password wajib diisi'})
        try:
            result = supabase.table('users').select('*').eq('username', username).single().execute()
            user = result.data
            if not user:
                return jsonify({'success': False, 'message': 'Username tidak ditemukan'})
            if user['password'] != hash_password(password):
                return jsonify({'success': False, 'message': 'Password salah'})
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['display_name'] = user['display_name']
            session['avatar'] = user.get('avatar_url', '')
            # Update online status
            supabase.table('users').update({'is_online': True, 'last_seen': datetime.now(timezone.utc).isoformat()}).eq('id', user['id']).execute()
            return jsonify({'success': True, 'redirect': '/chats'})
        except Exception as e:
            return jsonify({'success': False, 'message': 'Username tidak ditemukan'})
    return render_template('auth/login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username', '').strip()
        display_name = data.get('display_name', '').strip()
        password = data.get('password', '')
        confirm = data.get('confirm_password', '')
        bio = data.get('bio', '').strip()
        if not username or not display_name or not password:
            return jsonify({'success': False, 'message': 'Semua field wajib diisi'})
        if len(username) < 3:
            return jsonify({'success': False, 'message': 'Username minimal 3 karakter'})
        if len(password) < 6:
            return jsonify({'success': False, 'message': 'Password minimal 6 karakter'})
        if password != confirm:
            return jsonify({'success': False, 'message': 'Password tidak cocok'})
        try:
            existing = supabase.table('users').select('id').eq('username', username).execute()
            if existing.data:
                return jsonify({'success': False, 'message': 'Username sudah dipakai'})
            user_id = str(uuid.uuid4())
            avatar_url = f"https://api.dicebear.com/7.x/avataaars/svg?seed={username}"
            supabase.table('users').insert({
                'id': user_id,
                'username': username,
                'display_name': display_name,
                'password': hash_password(password),
                'bio': bio,
                'avatar_url': avatar_url,
                'is_online': False,
                'created_at': datetime.now(timezone.utc).isoformat()
            }).execute()
            return jsonify({'success': True, 'redirect': '/login'})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)})
    return render_template('auth/register.html')

@app.route('/logout')
def logout():
    if 'user_id' in session:
        try:
            supabase.table('users').update({'is_online': False, 'last_seen': datetime.now(timezone.utc).isoformat()}).eq('id', session['user_id']).execute()
        except:
            pass
    session.clear()
    return redirect(url_for('login'))

# ─── MAIN PAGES ───────────────────────────────────────────────────────────────

@app.route('/chats')
@login_required
def chats():
    return render_template('chats.html', user=session)

@app.route('/groups')
@login_required
def groups():
    return render_template('groups.html', user=session)

@app.route('/contacts')
@login_required
def contacts():
    return render_template('contacts.html', user=session)

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=session)

@app.route('/chat/<chat_id>')
@login_required
def chat_room(chat_id):
    return render_template('chat_room.html', chat_id=chat_id, user=session)

@app.route('/group/<group_id>')
@login_required
def group_room(group_id):
    return render_template('group_room.html', group_id=group_id, user=session)

# ─── API: USERS ───────────────────────────────────────────────────────────────

@app.route('/api/users/search')
@login_required
def search_users():
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify([])
    try:
        result = supabase.table('users').select('id,username,display_name,avatar_url,is_online,bio').ilike('username', f'%{q}%').limit(20).execute()
        users = [u for u in result.data if u['id'] != session['user_id']]
        return jsonify(users)
    except Exception as e:
        return jsonify([])

@app.route('/api/users/me')
@login_required
def get_me():
    try:
        result = supabase.table('users').select('*').eq('id', session['user_id']).single().execute()
        user = result.data
        user.pop('password', None)
        return jsonify(user)
    except:
        return jsonify({})

@app.route('/api/users/me/update', methods=['POST'])
@login_required
def update_profile():
    data = request.get_json()
    display_name = data.get('display_name', '').strip()
    bio = data.get('bio', '').strip()
    if not display_name:
        return jsonify({'success': False, 'message': 'Nama tidak boleh kosong'})
    try:
        supabase.table('users').update({
            'display_name': display_name,
            'bio': bio,
            'updated_at': datetime.now(timezone.utc).isoformat()
        }).eq('id', session['user_id']).execute()
        session['display_name'] = display_name
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/users/<user_id>')
@login_required
def get_user(user_id):
    try:
        result = supabase.table('users').select('id,username,display_name,avatar_url,is_online,bio,last_seen').eq('id', user_id).single().execute()
        return jsonify(result.data)
    except:
        return jsonify({})

# ─── API: CONTACTS ─────────────────────────────────────────────────────────────

@app.route('/api/contacts')
@login_required
def get_contacts():
    try:
        result = supabase.table('contacts').select('*,contact:contact_id(id,username,display_name,avatar_url,is_online,last_seen,bio)').eq('user_id', session['user_id']).execute()
        return jsonify(result.data)
    except Exception as e:
        return jsonify([])

@app.route('/api/contacts/add', methods=['POST'])
@login_required
def add_contact():
    data = request.get_json()
    contact_id = data.get('contact_id')
    if not contact_id:
        return jsonify({'success': False, 'message': 'Contact ID diperlukan'})
    if contact_id == session['user_id']:
        return jsonify({'success': False, 'message': 'Tidak bisa tambah diri sendiri'})
    try:
        existing = supabase.table('contacts').select('id').eq('user_id', session['user_id']).eq('contact_id', contact_id).execute()
        if existing.data:
            return jsonify({'success': False, 'message': 'Sudah ada di kontak'})
        supabase.table('contacts').insert({
            'user_id': session['user_id'],
            'contact_id': contact_id,
            'created_at': datetime.now(timezone.utc).isoformat()
        }).execute()
        supabase.table('contacts').insert({
            'user_id': contact_id,
            'contact_id': session['user_id'],
            'created_at': datetime.now(timezone.utc).isoformat()
        }).execute()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/contacts/remove', methods=['POST'])
@login_required
def remove_contact():
    data = request.get_json()
    contact_id = data.get('contact_id')
    try:
        supabase.table('contacts').delete().eq('user_id', session['user_id']).eq('contact_id', contact_id).execute()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# ─── API: PRIVATE CHATS ───────────────────────────────────────────────────────

@app.route('/api/chats')
@login_required
def get_chats():
    try:
        result = supabase.table('private_chats').select(
            '*,user1:user1_id(id,username,display_name,avatar_url,is_online),user2:user2_id(id,username,display_name,avatar_url,is_online)'
        ).or_(f"user1_id.eq.{session['user_id']},user2_id.eq.{session['user_id']}").order('last_message_at', desc=True).execute()
        chats = []
        for chat in result.data:
            other = chat['user2'] if chat['user1_id'] == session['user_id'] else chat['user1']
            chats.append({
                'id': chat['id'],
                'other_user': other,
                'last_message': chat.get('last_message', ''),
                'last_message_at': chat.get('last_message_at', ''),
                'unread_count': chat.get('unread_count', 0)
            })
        return jsonify(chats)
    except Exception as e:
        return jsonify([])

@app.route('/api/chats/open', methods=['POST'])
@login_required
def open_chat():
    data = request.get_json()
    other_id = data.get('user_id')
    if not other_id:
        return jsonify({'success': False, 'message': 'User ID diperlukan'})
    try:
        existing = supabase.table('private_chats').select('id').or_(
            f"and(user1_id.eq.{session['user_id']},user2_id.eq.{other_id}),and(user1_id.eq.{other_id},user2_id.eq.{session['user_id']})"
        ).execute()
        if existing.data:
            return jsonify({'success': True, 'chat_id': existing.data[0]['id']})
        chat_id = str(uuid.uuid4())
        supabase.table('private_chats').insert({
            'id': chat_id,
            'user1_id': session['user_id'],
            'user2_id': other_id,
            'created_at': datetime.now(timezone.utc).isoformat()
        }).execute()
        return jsonify({'success': True, 'chat_id': chat_id})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/chats/<chat_id>/messages')
@login_required
def get_messages(chat_id):
    page = int(request.args.get('page', 1))
    limit = 50
    offset = (page - 1) * limit
    try:
        result = supabase.table('messages').select(
            '*,sender:sender_id(id,username,display_name,avatar_url)'
        ).eq('chat_id', chat_id).order('created_at', desc=False).range(offset, offset + limit - 1).execute()
        return jsonify(result.data)
    except Exception as e:
        return jsonify([])

@app.route('/api/chats/<chat_id>/send', methods=['POST'])
@login_required
def send_message(chat_id):
    data = request.get_json()
    content = data.get('content', '').strip()
    msg_type = data.get('type', 'text')
    reply_to = data.get('reply_to', None)
    if not content:
        return jsonify({'success': False, 'message': 'Pesan kosong'})
    try:
        msg_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        supabase.table('messages').insert({
            'id': msg_id,
            'chat_id': chat_id,
            'sender_id': session['user_id'],
            'content': content,
            'type': msg_type,
            'reply_to': reply_to,
            'is_read': False,
            'created_at': now
        }).execute()
        supabase.table('private_chats').update({
            'last_message': content if msg_type == 'text' else f'[{msg_type}]',
            'last_message_at': now
        }).eq('id', chat_id).execute()
        return jsonify({'success': True, 'message_id': msg_id})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/chats/<chat_id>/read', methods=['POST'])
@login_required
def mark_read(chat_id):
    try:
        supabase.table('messages').update({'is_read': True}).eq('chat_id', chat_id).neq('sender_id', session['user_id']).execute()
        return jsonify({'success': True})
    except:
        return jsonify({'success': False})

@app.route('/api/messages/<msg_id>/delete', methods=['POST'])
@login_required
def delete_message(msg_id):
    try:
        supabase.table('messages').update({'content': 'Pesan dihapus', 'is_deleted': True}).eq('id', msg_id).eq('sender_id', session['user_id']).execute()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# ─── API: GROUPS ──────────────────────────────────────────────────────────────

@app.route('/api/groups')
@login_required
def get_groups():
    try:
        member_result = supabase.table('group_members').select('group_id').eq('user_id', session['user_id']).execute()
        group_ids = [m['group_id'] for m in member_result.data]
        if not group_ids:
            return jsonify([])
        result = supabase.table('groups').select('*').in_('id', group_ids).order('last_message_at', desc=True).execute()
        return jsonify(result.data)
    except Exception as e:
        return jsonify([])

@app.route('/api/groups/create', methods=['POST'])
@login_required
def create_group():
    data = request.get_json()
    name = data.get('name', '').strip()
    description = data.get('description', '').strip()
    members = data.get('members', [])
    if not name:
        return jsonify({'success': False, 'message': 'Nama grup diperlukan'})
    try:
        group_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        avatar = f"https://api.dicebear.com/7.x/initials/svg?seed={name}"
        supabase.table('groups').insert({
            'id': group_id,
            'name': name,
            'description': description,
            'avatar_url': avatar,
            'created_by': session['user_id'],
            'created_at': now
        }).execute()
        all_members = list(set([session['user_id']] + members))
        for uid in all_members:
            role = 'admin' if uid == session['user_id'] else 'member'
            supabase.table('group_members').insert({
                'group_id': group_id,
                'user_id': uid,
                'role': role,
                'joined_at': now
            }).execute()
        return jsonify({'success': True, 'group_id': group_id})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/groups/<group_id>')
@login_required
def get_group(group_id):
    try:
        result = supabase.table('groups').select('*').eq('id', group_id).single().execute()
        members = supabase.table('group_members').select('*,user:user_id(id,username,display_name,avatar_url,is_online)').eq('group_id', group_id).execute()
        return jsonify({'group': result.data, 'members': members.data})
    except Exception as e:
        return jsonify({})

@app.route('/api/groups/<group_id>/messages')
@login_required
def get_group_messages(group_id):
    page = int(request.args.get('page', 1))
    limit = 50
    offset = (page - 1) * limit
    try:
        result = supabase.table('group_messages').select(
            '*,sender:sender_id(id,username,display_name,avatar_url)'
        ).eq('group_id', group_id).order('created_at', desc=False).range(offset, offset + limit - 1).execute()
        return jsonify(result.data)
    except Exception as e:
        return jsonify([])

@app.route('/api/groups/<group_id>/send', methods=['POST'])
@login_required
def send_group_message(group_id):
    data = request.get_json()
    content = data.get('content', '').strip()
    msg_type = data.get('type', 'text')
    reply_to = data.get('reply_to', None)
    if not content:
        return jsonify({'success': False, 'message': 'Pesan kosong'})
    try:
        msg_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        supabase.table('group_messages').insert({
            'id': msg_id,
            'group_id': group_id,
            'sender_id': session['user_id'],
            'content': content,
            'type': msg_type,
            'reply_to': reply_to,
            'created_at': now
        }).execute()
        supabase.table('groups').update({
            'last_message': content if msg_type == 'text' else f'[{msg_type}]',
            'last_message_at': now
        }).eq('id', group_id).execute()
        return jsonify({'success': True, 'message_id': msg_id})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/groups/<group_id>/members/add', methods=['POST'])
@login_required
def add_group_member(group_id):
    data = request.get_json()
    user_id = data.get('user_id')
    try:
        existing = supabase.table('group_members').select('id').eq('group_id', group_id).eq('user_id', user_id).execute()
        if existing.data:
            return jsonify({'success': False, 'message': 'Sudah jadi anggota'})
        supabase.table('group_members').insert({
            'group_id': group_id,
            'user_id': user_id,
            'role': 'member',
            'joined_at': datetime.now(timezone.utc).isoformat()
        }).execute()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/groups/<group_id>/leave', methods=['POST'])
@login_required
def leave_group(group_id):
    try:
        supabase.table('group_members').delete().eq('group_id', group_id).eq('user_id', session['user_id']).execute()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# ─── API: STATUS ──────────────────────────────────────────────────────────────

@app.route('/api/status/all')
@login_required
def get_all_status():
    try:
        contact_result = supabase.table('contacts').select('contact_id').eq('user_id', session['user_id']).execute()
        contact_ids = [c['contact_id'] for c in contact_result.data]
        contact_ids.append(session['user_id'])
        now = datetime.now(timezone.utc)
        result = supabase.table('user_status').select(
            '*,user:user_id(id,username,display_name,avatar_url)'
        ).in_('user_id', contact_ids).order('created_at', desc=True).execute()
        return jsonify(result.data)
    except Exception as e:
        return jsonify([])

@app.route('/api/status/add', methods=['POST'])
@login_required
def add_status():
    data = request.get_json()
    content = data.get('content', '').strip()
    status_type = data.get('type', 'text')
    bg_color = data.get('bg_color', '#075e54')
    if not content:
        return jsonify({'success': False, 'message': 'Status kosong'})
    try:
        supabase.table('user_status').insert({
            'id': str(uuid.uuid4()),
            'user_id': session['user_id'],
            'content': content,
            'type': status_type,
            'bg_color': bg_color,
            'expires_at': datetime.now(timezone.utc).isoformat(),
            'created_at': datetime.now(timezone.utc).isoformat()
        }).execute()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# ─── API: POLLS ───────────────────────────────────────────────────────────────

@app.route('/api/groups/<group_id>/polls/create', methods=['POST'])
@login_required
def create_poll(group_id):
    data = request.get_json()
    question = data.get('question', '').strip()
    options = data.get('options', [])
    if not question or len(options) < 2:
        return jsonify({'success': False, 'message': 'Pertanyaan dan minimal 2 opsi diperlukan'})
    try:
        poll_id = str(uuid.uuid4())
        supabase.table('polls').insert({
            'id': poll_id,
            'group_id': group_id,
            'created_by': session['user_id'],
            'question': question,
            'options': json.dumps(options),
            'votes': json.dumps({}),
            'created_at': datetime.now(timezone.utc).isoformat()
        }).execute()
        # Send as group message
        supabase.table('group_messages').insert({
            'id': str(uuid.uuid4()),
            'group_id': group_id,
            'sender_id': session['user_id'],
            'content': f'[POLL:{poll_id}]',
            'type': 'poll',
            'created_at': datetime.now(timezone.utc).isoformat()
        }).execute()
        return jsonify({'success': True, 'poll_id': poll_id})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/polls/<poll_id>/vote', methods=['POST'])
@login_required
def vote_poll(poll_id):
    data = request.get_json()
    option_index = data.get('option_index')
    try:
        poll = supabase.table('polls').select('*').eq('id', poll_id).single().execute().data
        votes = json.loads(poll['votes'])
        votes[session['user_id']] = option_index
        supabase.table('polls').update({'votes': json.dumps(votes)}).eq('id', poll_id).execute()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

if __name__ == '__main__':
    app.run(debug=True, port=5000)

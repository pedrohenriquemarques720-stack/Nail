# server.py
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
from datetime import datetime, timedelta
import sqlite3
import json
import uuid
import hashlib
import os
from functools import wraps

app = Flask(__name__, static_folder='.', template_folder='.')
CORS(app)

# ============================================
# DATABASE SETUP COMPLETO
# ============================================

def init_db():
    conn = sqlite3.connect('agenda.db')
    cursor = conn.cursor()
    
    # Tabela professionals (completa)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS professionals (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            business_name TEXT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            phone TEXT,
            whatsapp TEXT,
            instagram TEXT,
            facebook TEXT,
            address TEXT,
            bio_url TEXT UNIQUE,
            profile_photo TEXT,
            cover_photo TEXT,
            bio_description TEXT,
            work_hours TEXT,
            appointment_settings TEXT,
            payment_settings TEXT,
            notification_settings TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabela clients (completa)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clients (
            id TEXT PRIMARY KEY,
            professional_id TEXT,
            full_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            email TEXT,
            alternative_phone TEXT,
            birth_date TEXT,
            address TEXT,
            notes TEXT,
            allergies TEXT,
            total_visits INTEGER DEFAULT 0,
            total_spent REAL DEFAULT 0,
            last_visit TIMESTAMP,
            whatsapp_optin INTEGER DEFAULT 1,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (professional_id) REFERENCES professionals(id)
        )
    ''')
    
    # Tabela services (completa)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS services (
            id TEXT PRIMARY KEY,
            professional_id TEXT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL,
            promotion_price REAL,
            duration_minutes INTEGER NOT NULL,
            category TEXT,
            commission_percentage REAL DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (professional_id) REFERENCES professionals(id)
        )
    ''')
    
    # Tabela appointments (completa)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS appointments (
            id TEXT PRIMARY KEY,
            client_id TEXT,
            service_id TEXT,
            professional_id TEXT,
            start_time TIMESTAMP NOT NULL,
            end_time TIMESTAMP NOT NULL,
            status TEXT DEFAULT 'pending',
            payment_method TEXT,
            payment_status TEXT DEFAULT 'pending',
            amount_paid REAL DEFAULT 0,
            discount REAL DEFAULT 0,
            notes TEXT,
            reminder_sent INTEGER DEFAULT 0,
            cancelled_at TIMESTAMP,
            cancellation_reason TEXT,
            created_by TEXT DEFAULT 'client',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES clients(id),
            FOREIGN KEY (service_id) REFERENCES services(id),
            FOREIGN KEY (professional_id) REFERENCES professionals(id)
        )
    ''')
    
    # Tabela financial_records (completa)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS financial_records (
            id TEXT PRIMARY KEY,
            professional_id TEXT,
            appointment_id TEXT,
            type TEXT,
            amount REAL,
            category TEXT,
            subcategory TEXT,
            description TEXT,
            payment_method TEXT,
            due_date TEXT,
            paid_date TEXT,
            status TEXT DEFAULT 'pending',
            recurring INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (professional_id) REFERENCES professionals(id),
            FOREIGN KEY (appointment_id) REFERENCES appointments(id)
        )
    ''')
    
    # Tabela products
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id TEXT PRIMARY KEY,
            professional_id TEXT,
            name TEXT NOT NULL,
            description TEXT,
            purchase_price REAL NOT NULL,
            sale_price REAL NOT NULL,
            stock_quantity INTEGER DEFAULT 0,
            min_stock_quantity INTEGER DEFAULT 5,
            category TEXT,
            sku TEXT UNIQUE,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (professional_id) REFERENCES professionals(id)
        )
    ''')
    
    # Tabela sales_products
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sales_products (
            id TEXT PRIMARY KEY,
            appointment_id TEXT,
            product_id TEXT,
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            total_price REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (appointment_id) REFERENCES appointments(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    ''')
    
    # Tabela appointment_history
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS appointment_history (
            id TEXT PRIMARY KEY,
            appointment_id TEXT,
            changed_by TEXT,
            old_status TEXT,
            new_status TEXT,
            changes TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (appointment_id) REFERENCES appointments(id)
        )
    ''')
    
    # Tabela messages
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id TEXT PRIMARY KEY,
            professional_id TEXT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            category TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (professional_id) REFERENCES professionals(id)
        )
    ''')
    
    # Tabela blocked_slots
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS blocked_slots (
            id TEXT PRIMARY KEY,
            professional_id TEXT,
            start_time TIMESTAMP NOT NULL,
            end_time TIMESTAMP NOT NULL,
            reason TEXT,
            is_recurring INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (professional_id) REFERENCES professionals(id)
        )
    ''')
    
    # Tabela commissions
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS commissions (
            id TEXT PRIMARY KEY,
            professional_id TEXT,
            appointment_id TEXT,
            employee_name TEXT,
            commission_percentage REAL,
            commission_amount REAL,
            paid INTEGER DEFAULT 0,
            paid_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (professional_id) REFERENCES professionals(id),
            FOREIGN KEY (appointment_id) REFERENCES appointments(id)
        )
    ''')
    
    # Tabela reviews
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id TEXT PRIMARY KEY,
            professional_id TEXT,
            client_id TEXT,
            appointment_id TEXT,
            rating INTEGER NOT NULL,
            comment TEXT,
            response TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (professional_id) REFERENCES professionals(id),
            FOREIGN KEY (client_id) REFERENCES clients(id),
            FOREIGN KEY (appointment_id) REFERENCES appointments(id)
        )
    ''')
    
    # Inserir dados de exemplo
    cursor.execute("SELECT COUNT(*) FROM professionals")
    if cursor.fetchone()[0] == 0:
        # Profissional exemplo
        prof_id = str(uuid.uuid4())
        cursor.execute('''
            INSERT INTO professionals (id, name, business_name, email, password, phone, whatsapp, instagram, address, bio_url, bio_description, work_hours, appointment_settings)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            prof_id,
            'Ste Barbosa',
            'Ste Barbosa Nail Design',
            'ste@naildesigner.com',
            hashlib.sha256('admin123'.encode()).hexdigest(),
            '(11) 99999-9999',
            '5511999999999',
            '@stebarbosa',
            'Rua das Flores, 123 - São Paulo, SP',
            'stebarbosa',
            'Especialista em alongamento de unhas e nail art. Atendimento personalizado.',
            json.dumps({
                "monday": {"enabled": True, "start": "09:00", "end": "18:00"},
                "tuesday": {"enabled": True, "start": "09:00", "end": "18:00"},
                "wednesday": {"enabled": True, "start": "09:00", "end": "18:00"},
                "thursday": {"enabled": True, "start": "09:00", "end": "18:00"},
                "friday": {"enabled": True, "start": "09:00", "end": "18:00"},
                "saturday": {"enabled": True, "start": "09:00", "end": "14:00"},
                "sunday": {"enabled": False, "start": "09:00", "end": "13:00"}
            }),
            json.dumps({
                "advance_booking_days": 30,
                "min_cancellation_hours": 24,
                "min_advance_notice_minutes": 120,
                "slot_interval_minutes": 30
            })
        ))
        
        # Serviços exemplo
        services = [
            (str(uuid.uuid4()), prof_id, 'Alongamento em Gel', 'Alongamento com gel para unhas naturais', 180, None, 120, 'Alongamento', 0),
            (str(uuid.uuid4()), prof_id, 'Manutenção', 'Manutenção de alongamento', 120, None, 90, 'Manutenção', 0),
            (str(uuid.uuid4()), prof_id, 'Banho de Gel', 'Esmaltação em gel', 80, None, 60, 'Esmaltação', 0),
            (str(uuid.uuid4()), prof_id, 'Pedicure', 'Cuidados completos para os pés', 70, None, 60, 'Pedicure', 0),
            (str(uuid.uuid4()), prof_id, 'Francesinha', 'Unhas francesinhas', 90, None, 90, 'Alongamento', 0),
        ]
        
        for s in services:
            cursor.execute('''
                INSERT INTO services (id, professional_id, name, description, price, promotion_price, duration_minutes, category, commission_percentage)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', s)
        
        # Clientes exemplo
        clients = [
            (str(uuid.uuid4()), prof_id, 'Ana Silva', '(11) 98888-8888', 'ana@email.com', None, '1990-03-15', None, None, None, 3, 450, '2024-03-20'),
            (str(uuid.uuid4()), prof_id, 'Carla Souza', '(11) 97777-7777', 'carla@email.com', None, '1988-07-22', None, None, None, 5, 780, '2024-03-22'),
            (str(uuid.uuid4()), prof_id, 'Mariana Santos', '(11) 96666-6666', 'mariana@email.com', None, '1995-12-10', None, None, None, 2, 260, '2024-03-18'),
        ]
        
        for c in clients:
            cursor.execute('''
                INSERT INTO clients (id, professional_id, full_name, phone, email, birth_date, total_visits, total_spent, last_visit)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', c)
        
        # Agendamentos exemplo
        now = datetime.now()
        appointments = [
            (str(uuid.uuid4()), clients[0][0], services[0][0], prof_id, 
             datetime(now.year, now.month, now.day, 10, 0).isoformat(),
             datetime(now.year, now.month, now.day, 12, 0).isoformat(),
             'confirmed', 'PIX', 'paid', 180, 0),
            (str(uuid.uuid4()), clients[1][0], services[1][0], prof_id,
             datetime(now.year, now.month, now.day, 14, 0).isoformat(),
             datetime(now.year, now.month, now.day, 15, 30).isoformat(),
             'confirmed', 'Cartão', 'paid', 120, 0),
        ]
        
        for a in appointments:
            cursor.execute('''
                INSERT INTO appointments (id, client_id, service_id, professional_id, start_time, end_time, status, payment_method, payment_status, amount_paid, discount)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', a)
        
        # Mensagens pré-definidas
        messages = [
            (str(uuid.uuid4()), prof_id, 'Confirmação de horário', 'Olá {nome}, seu horário está confirmado para {data} às {hora}.', 'confirmacao'),
            (str(uuid.uuid4()), prof_id, 'Lembrete', 'Olá {nome}, lembrete: seu horário é amanhã às {hora}.', 'lembrete'),
            (str(uuid.uuid4()), prof_id, 'Cancelamento', 'Olá {nome}, seu horário foi cancelado conforme solicitado.', 'cancelamento'),
        ]
        
        for m in messages:
            cursor.execute('''
                INSERT INTO messages (id, professional_id, title, content, category)
                VALUES (?, ?, ?, ?, ?)
            ''', m)
    
    conn.commit()
    conn.close()

# ============================================
# HELPERS
# ============================================

def get_db():
    conn = sqlite3.connect('agenda.db')
    conn.row_factory = sqlite3.Row
    return conn

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # Verificar token de autenticação
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'Não autorizado'}), 401
        return f(*args, **kwargs)
    return decorated

# ============================================
# ROTAS PÚBLICAS
# ============================================

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/admin')
def admin():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('.', path)

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    conn = get_db()
    professional = conn.execute('''
        SELECT id, name, business_name, email, password FROM professionals WHERE email = ?
    ''', (email,)).fetchone()
    conn.close()
    
    if not professional:
        return jsonify({'error': 'Email não encontrado'}), 401
    
    hashed = hashlib.sha256(password.encode()).hexdigest()
    if professional['password'] != hashed:
        return jsonify({'error': 'Senha incorreta'}), 401
    
    return jsonify({
        'success': True,
        'professional_id': professional['id'],
        'name': professional['name'],
        'business_name': professional['business_name']
    })

@app.route('/api/professional/<slug>')
def get_professional(slug):
    conn = get_db()
    professional = conn.execute('''
        SELECT * FROM professionals WHERE bio_url = ? AND is_active = 1
    ''', (slug,)).fetchone()
    conn.close()
    
    if not professional:
        return jsonify({'error': 'Profissional não encontrada'}), 404
    
    # Buscar serviços
    conn = get_db()
    services = conn.execute('''
        SELECT * FROM services WHERE professional_id = ? AND is_active = 1
    ''', (professional['id'],)).fetchall()
    conn.close()
    
    return jsonify({
        'id': professional['id'],
        'name': professional['name'],
        'business_name': professional['business_name'],
        'phone': professional['phone'],
        'whatsapp': professional['whatsapp'],
        'instagram': professional['instagram'],
        'facebook': professional['facebook'],
        'address': professional['address'],
        'bio_url': professional['bio_url'],
        'profile_photo': professional['profile_photo'],
        'cover_photo': professional['cover_photo'],
        'bio_description': professional['bio_description'],
        'work_hours': json.loads(professional['work_hours']) if professional['work_hours'] else {},
        'services': [dict(s) for s in services]
    })

@app.route('/api/available-slots', methods=['GET'])
def get_available_slots():
    professional_id = request.args.get('professional_id')
    date = request.args.get('date')
    duration = int(request.args.get('duration', 60))
    
    if not professional_id or not date:
        return jsonify({'error': 'Parâmetros inválidos'}), 400
    
    conn = get_db()
    prof = conn.execute('SELECT work_hours FROM professionals WHERE id = ?', (professional_id,)).fetchone()
    if not prof:
        return jsonify({'error': 'Profissional não encontrada'}), 404
    
    work_hours = json.loads(prof['work_hours'])
    selected_date = datetime.fromisoformat(date)
    day_name = selected_date.strftime('%A').lower()
    
    day_config = work_hours.get(day_name, {})
    if not day_config.get('enabled', False):
        return jsonify({'slots': []})
    
    slots = []
    start_hour, start_min = map(int, day_config['start'].split(':'))
    end_hour, end_min = map(int, day_config['end'].split(':'))
    
    current = datetime(selected_date.year, selected_date.month, selected_date.day, start_hour, start_min)
    end = datetime(selected_date.year, selected_date.month, selected_date.day, end_hour, end_min)
    
    appointments = conn.execute('''
        SELECT start_time, end_time FROM appointments 
        WHERE professional_id = ? AND date(start_time) = date(?) AND status NOT IN ('cancelled', 'no_show')
    ''', (professional_id, date)).fetchall()
    
    while current + timedelta(minutes=duration) <= end:
        slot_end = current + timedelta(minutes=duration)
        has_conflict = False
        for apt in appointments:
            apt_start = datetime.fromisoformat(apt['start_time'])
            apt_end = datetime.fromisoformat(apt['end_time'])
            if current < apt_end and slot_end > apt_start:
                has_conflict = True
                break
        
        if not has_conflict:
            slots.append(current.strftime('%H:%M'))
        
        current += timedelta(minutes=30)
    
    conn.close()
    return jsonify({'slots': slots})

@app.route('/api/appointments', methods=['POST'])
def create_appointment():
    data = request.json
    
    conn = get_db()
    start_time = datetime.fromisoformat(data['start_time'])
    end_time = start_time + timedelta(minutes=data['duration'])
    
    conflict = conn.execute('''
        SELECT id FROM appointments 
        WHERE professional_id = ? AND start_time < ? AND end_time > ? AND status NOT IN ('cancelled', 'no_show')
    ''', (data['professional_id'], end_time.isoformat(), start_time.isoformat())).fetchone()
    
    if conflict:
        return jsonify({'error': 'Horário indisponível'}), 409
    
    client = conn.execute('SELECT id FROM clients WHERE phone = ? AND professional_id = ?', 
                          (data['client']['phone'], data['professional_id'])).fetchone()
    
    if client:
        client_id = client['id']
    else:
        client_id = str(uuid.uuid4())
        conn.execute('''
            INSERT INTO clients (id, professional_id, full_name, phone, email, birth_date, notes, whatsapp_optin)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (client_id, data['professional_id'], data['client']['full_name'], 
              data['client']['phone'], data['client'].get('email'), data['client'].get('birth_date'),
              data['client'].get('notes'), 1))
    
    appointment_id = str(uuid.uuid4())
    conn.execute('''
        INSERT INTO appointments (id, client_id, service_id, professional_id, start_time, end_time, notes, created_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (appointment_id, client_id, data['service_id'], data['professional_id'], 
          start_time.isoformat(), end_time.isoformat(), data['client'].get('notes'), 'client'))
    
    conn.commit()
    conn.close()
    
    whatsapp_link = f"https://wa.me/{data['professional_phone'].replace('+', '').replace('-', '').replace(' ', '')}?text={data['whatsapp_message']}"
    
    return jsonify({
        'success': True,
        'appointment_id': appointment_id,
        'whatsapp_link': whatsapp_link
    })

@app.route('/api/appointments/<appointment_id>')
def get_appointment(appointment_id):
    conn = get_db()
    apt = conn.execute('''
        SELECT a.*, c.full_name as client_name, c.phone as client_phone,
               s.name as service_name, s.price, s.duration_minutes,
               p.name as professional_name, p.address, p.phone as professional_phone
        FROM appointments a
        JOIN clients c ON a.client_id = c.id
        JOIN services s ON a.service_id = s.id
        JOIN professionals p ON a.professional_id = p.id
        WHERE a.id = ?
    ''', (appointment_id,)).fetchone()
    conn.close()
    
    if not apt:
        return jsonify({'error': 'Agendamento não encontrado'}), 404
    
    return jsonify(dict(apt))

# ============================================
# ROTAS ADMINISTRATIVAS
# ============================================

@app.route('/api/admin/dashboard/<professional_id>')
@require_auth
def admin_dashboard(professional_id):
    conn = get_db()
    
    # Receita total
    revenue = conn.execute('''
        SELECT COALESCE(SUM(amount_paid), 0) as total, COUNT(*) as count
        FROM appointments 
        WHERE professional_id = ? AND status = 'completed'
    ''', (professional_id,)).fetchone()
    
    # Despesas
    expenses = conn.execute('''
        SELECT COALESCE(SUM(amount), 0) as total
        FROM financial_records 
        WHERE professional_id = ? AND type = 'expense' AND status = 'paid'
    ''', (professional_id,)).fetchone()
    
    # Agendamentos por status
    appointments_status = conn.execute('''
        SELECT status, COUNT(*) as count
        FROM appointments 
        WHERE professional_id = ? AND date(start_time) >= date('now', '-30 days')
        GROUP BY status
    ''', (professional_id,)).fetchall()
    
    # Top serviços por receita
    top_services = conn.execute('''
        SELECT s.name, COUNT(a.id) as total_count, SUM(a.amount_paid) as total_revenue
        FROM appointments a
        JOIN services s ON a.service_id = s.id
        WHERE a.professional_id = ? AND a.status = 'completed'
        GROUP BY s.id
        ORDER BY total_revenue DESC
        LIMIT 5
    ''', (professional_id,)).fetchall()
    
    # Receita mensal (últimos 12 meses)
    monthly_revenue = conn.execute('''
        SELECT strftime('%Y-%m', start_time) as month, SUM(amount_paid) as total
        FROM appointments
        WHERE professional_id = ? AND status = 'completed'
        GROUP BY strftime('%Y-%m', start_time)
        ORDER BY month DESC
        LIMIT 12
    ''', (professional_id,)).fetchall()
    
    # Formas de pagamento
    payment_methods = conn.execute('''
        SELECT payment_method, COUNT(*) as count, SUM(amount_paid) as total
        FROM appointments
        WHERE professional_id = ? AND status = 'completed' AND payment_method IS NOT NULL
        GROUP BY payment_method
    ''', (professional_id,)).fetchall()
    
    # Aniversariantes do mês
    birthday_clients = conn.execute('''
        SELECT full_name, phone, birth_date,
               strftime('%d/%m', birth_date) as birthday
        FROM clients
        WHERE professional_id = ? 
          AND birth_date IS NOT NULL
          AND strftime('%m', birth_date) = strftime('%m', 'now')
        ORDER BY strftime('%d', birth_date)
    ''', (professional_id,)).fetchall()
    
    conn.close()
    
    return jsonify({
        'total_revenue': revenue['total'] if revenue else 0,
        'total_appointments': revenue['count'] if revenue else 0,
        'total_expenses': expenses['total'] if expenses else 0,
        'net_profit': (revenue['total'] if revenue else 0) - (expenses['total'] if expenses else 0),
        'appointments_by_status': [dict(s) for s in appointments_status],
        'top_services': [dict(s) for s in top_services],
        'monthly_revenue': [dict(m) for m in monthly_revenue],
        'payment_methods': [dict(p) for p in payment_methods],
        'birthday_clients': [dict(c) for c in birthday_clients]
    })

@app.route('/api/admin/appointments/<professional_id>')
@require_auth
def admin_appointments(professional_id):
    date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    
    conn = get_db()
    appointments = conn.execute('''
        SELECT a.*, c.full_name as client_name, c.phone as client_phone,
               s.name as service_name, s.price, s.duration_minutes
        FROM appointments a
        JOIN clients c ON a.client_id = c.id
        JOIN services s ON a.service_id = s.id
        WHERE a.professional_id = ? AND date(a.start_time) = date(?)
        ORDER BY a.start_time
    ''', (professional_id, date)).fetchall()
    conn.close()
    
    return jsonify([dict(a) for a in appointments])

@app.route('/api/admin/clients/<professional_id>')
@require_auth
def admin_clients(professional_id):
    search = request.args.get('search', '')
    
    conn = get_db()
    query = '''
        SELECT * FROM clients 
        WHERE professional_id = ?
    '''
    params = [professional_id]
    
    if search:
        query += ' AND (full_name LIKE ? OR phone LIKE ?)'
        params.append(f'%{search}%')
        params.append(f'%{search}%')
    
    query += ' ORDER BY total_spent DESC, last_visit DESC'
    
    clients = conn.execute(query, params).fetchall()
    conn.close()
    
    return jsonify([dict(c) for c in clients])

@app.route('/api/admin/client/<client_id>')
@require_auth
def admin_client_detail(client_id):
    conn = get_db()
    client = conn.execute('''
        SELECT * FROM clients WHERE id = ?
    ''', (client_id,)).fetchone()
    
    history = conn.execute('''
        SELECT a.*, s.name as service_name, s.price
        FROM appointments a
        JOIN services s ON a.service_id = s.id
        WHERE a.client_id = ?
        ORDER BY a.start_time DESC
        LIMIT 10
    ''', (client_id,)).fetchall()
    conn.close()
    
    return jsonify({
        'client': dict(client) if client else None,
        'history': [dict(h) for h in history]
    })

@app.route('/api/admin/services/<professional_id>')
@require_auth
def admin_services(professional_id):
    conn = get_db()
    services = conn.execute('''
        SELECT * FROM services WHERE professional_id = ?
        ORDER BY created_at DESC
    ''', (professional_id,)).fetchall()
    conn.close()
    
    return jsonify([dict(s) for s in services])

@app.route('/api/admin/service', methods=['POST'])
@require_auth
def admin_create_service():
    data = request.json
    
    service_id = str(uuid.uuid4())
    conn = get_db()
    conn.execute('''
        INSERT INTO services (id, professional_id, name, description, price, promotion_price, duration_minutes, category, commission_percentage, is_active)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (service_id, data['professional_id'], data['name'], data.get('description'), 
          data['price'], data.get('promotion_price'), data['duration_minutes'], 
          data.get('category'), data.get('commission_percentage', 0), data.get('is_active', 1)))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'id': service_id})

@app.route('/api/admin/service/<service_id>', methods=['PUT'])
@require_auth
def admin_update_service(service_id):
    data = request.json
    
    conn = get_db()
    conn.execute('''
        UPDATE services 
        SET name = ?, description = ?, price = ?, promotion_price = ?, 
            duration_minutes = ?, category = ?, commission_percentage = ?, is_active = ?
        WHERE id = ?
    ''', (data['name'], data.get('description'), data['price'], data.get('promotion_price'),
          data['duration_minutes'], data.get('category'), data.get('commission_percentage', 0),
          data.get('is_active', 1), service_id))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/api/admin/service/<service_id>', methods=['DELETE'])
@require_auth
def admin_delete_service(service_id):
    conn = get_db()
    conn.execute('DELETE FROM services WHERE id = ?', (service_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/api/admin/products/<professional_id>')
@require_auth
def admin_products(professional_id):
    conn = get_db()
    products = conn.execute('''
        SELECT * FROM products WHERE professional_id = ?
        ORDER BY name
    ''', (professional_id,)).fetchall()
    conn.close()
    
    return jsonify([dict(p) for p in products])

@app.route('/api/admin/product', methods=['POST'])
@require_auth
def admin_create_product():
    data = request.json
    
    product_id = str(uuid.uuid4())
    sku = data.get('sku') or f"PROD-{product_id[:8]}"
    
    conn = get_db()
    conn.execute('''
        INSERT INTO products (id, professional_id, name, description, purchase_price, sale_price, stock_quantity, min_stock_quantity, category, sku, is_active)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (product_id, data['professional_id'], data['name'], data.get('description'),
          data['purchase_price'], data['sale_price'], data.get('stock_quantity', 0),
          data.get('min_stock_quantity', 5), data.get('category'), sku, data.get('is_active', 1)))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'id': product_id})

@app.route('/api/admin/messages/<professional_id>')
@require_auth
def admin_messages(professional_id):
    conn = get_db()
    messages = conn.execute('''
        SELECT * FROM messages WHERE professional_id = ?
        ORDER BY category
    ''', (professional_id,)).fetchall()
    conn.close()
    
    return jsonify([dict(m) for m in messages])

@app.route('/api/admin/message', methods=['POST'])
@require_auth
def admin_create_message():
    data = request.json
    
    message_id = str(uuid.uuid4())
    conn = get_db()
    conn.execute('''
        INSERT INTO messages (id, professional_id, title, content, category, is_active)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (message_id, data['professional_id'], data['title'], data['content'], 
          data.get('category'), data.get('is_active', 1)))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'id': message_id})

@app.route('/api/admin/blocked-slots/<professional_id>')
@require_auth
def admin_blocked_slots(professional_id):
    conn = get_db()
    slots = conn.execute('''
        SELECT * FROM blocked_slots WHERE professional_id = ?
        ORDER BY start_time DESC
        LIMIT 50
    ''', (professional_id,)).fetchall()
    conn.close()
    
    return jsonify([dict(s) for s in slots])

@app.route('/api/admin/blocked-slot', methods=['POST'])
@require_auth
def admin_create_blocked_slot():
    data = request.json
    
    slot_id = str(uuid.uuid4())
    conn = get_db()
    conn.execute('''
        INSERT INTO blocked_slots (id, professional_id, start_time, end_time, reason, is_recurring)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (slot_id, data['professional_id'], data['start_time'], data['end_time'], 
          data.get('reason'), data.get('is_recurring', 0)))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'id': slot_id})

@app.route('/api/admin/financial/<professional_id>')
@require_auth
def admin_financial(professional_id):
    period = request.args.get('period', 'month')
    
    conn = get_db()
    
    if period == 'month':
        date_filter = "strftime('%Y-%m', created_at) = strftime('%Y-%m', 'now')"
    elif period == 'year':
        date_filter = "strftime('%Y', created_at) = strftime('%Y', 'now')"
    else:
        date_filter = "1=1"
    
    records = conn.execute(f'''
        SELECT * FROM financial_records 
        WHERE professional_id = ? AND {date_filter}
        ORDER BY created_at DESC
    ''', (professional_id,)).fetchall()
    
    conn.close()
    
    return jsonify([dict(r) for r in records])

@app.route('/api/admin/financial', methods=['POST'])
@require_auth
def admin_create_financial_record():
    data = request.json
    
    record_id = str(uuid.uuid4())
    conn = get_db()
    conn.execute('''
        INSERT INTO financial_records (id, professional_id, appointment_id, type, amount, category, subcategory, description, payment_method, due_date, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (record_id, data['professional_id'], data.get('appointment_id'), data['type'],
          data['amount'], data['category'], data.get('subcategory'), data.get('description'),
          data.get('payment_method'), data.get('due_date'), data.get('status', 'pending')))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'id': record_id})

@app.route('/api/admin/appointment/<appointment_id>/status', methods=['PUT'])
@require_auth
def admin_update_appointment_status(appointment_id):
    data = request.json
    new_status = data.get('status')
    notes = data.get('notes')
    
    conn = get_db()
    
    # Buscar status atual
    current = conn.execute('SELECT status FROM appointments WHERE id = ?', (appointment_id,)).fetchone()
    
    # Atualizar status
    conn.execute('''
        UPDATE appointments 
        SET status = ?, notes = COALESCE(?, notes)
        WHERE id = ?
    ''', (new_status, notes, appointment_id))
    
    # Registrar no histórico
    history_id = str(uuid.uuid4())
    conn.execute('''
        INSERT INTO appointment_history (id, appointment_id, changed_by, old_status, new_status, notes)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (history_id, appointment_id, 'admin', current['status'] if current else None, new_status, notes))
    
    # Se concluído, atualizar estatísticas do cliente
    if new_status == 'completed':
        apt = conn.execute('SELECT client_id, amount_paid FROM appointments WHERE id = ?', (appointment_id,)).fetchone()
        if apt:
            conn.execute('''
                UPDATE clients 
                SET total_visits = total_visits + 1,
                    total_spent = total_spent + ?,
                    last_visit = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (apt['amount_paid'], apt['client_id']))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/api/admin/settings/<professional_id>')
@require_auth
def admin_settings(professional_id):
    conn = get_db()
    prof = conn.execute('''
        SELECT work_hours, appointment_settings, payment_settings, notification_settings
        FROM professionals WHERE id = ?
    ''', (professional_id,)).fetchone()
    conn.close()
    
    return jsonify({
        'work_hours': json.loads(prof['work_hours']) if prof and prof['work_hours'] else {},
        'appointment_settings': json.loads(prof['appointment_settings']) if prof and prof['appointment_settings'] else {},
        'payment_settings': json.loads(prof['payment_settings']) if prof and prof['payment_settings'] else {},
        'notification_settings': json.loads(prof['notification_settings']) if prof and prof['notification_settings'] else {}
    })

@app.route('/api/admin/settings/<professional_id>', methods=['PUT'])
@require_auth
def admin_update_settings(professional_id):
    data = request.json
    
    conn = get_db()
    conn.execute('''
        UPDATE professionals 
        SET work_hours = ?, appointment_settings = ?, payment_settings = ?, notification_settings = ?
        WHERE id = ?
    ''', (json.dumps(data.get('work_hours', {})), json.dumps(data.get('appointment_settings', {})),
          json.dumps(data.get('payment_settings', {})), json.dumps(data.get('notification_settings', {})),
          professional_id))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

# ============================================
# INICIALIZAÇÃO
# ============================================

if __name__ == '__main__':
    init_db()
    print("✅ Banco de dados inicializado!")
    print("🚀 Servidor rodando em http://localhost:5000")
    print("📱 Acesse a página pública: http://localhost:5000/stebarbosa")
    print("🔐 Acesse o painel admin: http://localhost:5000/admin")
    print("   Email: ste@naildesigner.com | Senha: admin123")
    app.run(debug=True, host='0.0.0.0', port=5000)
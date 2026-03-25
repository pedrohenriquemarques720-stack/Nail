# app.py - Versão Streamlit Completa (sem Plotly)
import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import hashlib
import uuid
import json
import base64
from streamlit_option_menu import option_menu
import warnings
warnings.filterwarnings('ignore')

# ============================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================
st.set_page_config(
    page_title="Agenda Manicure Pro",
    page_icon="💅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# ESTILOS PERSONALIZADOS
# ============================================
st.markdown("""
<style>
    /* Cores principais */
    .stButton > button {
        background-color: #E91E63;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 8px 16px;
    }
    .stButton > button:hover {
        background-color: #D81B60;
        color: white;
    }
    
    /* Cards */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 16px;
        color: white;
        margin-bottom: 20px;
    }
    
    /* Títulos */
    h1, h2, h3 {
        color: #1a1a2e;
    }
    
    /* Sidebar */
    .css-1d391kg {
        background-color: white;
    }
    
    /* Badges */
    .badge-success {
        background-color: #d1fae5;
        color: #065f46;
        padding: 4px 8px;
        border-radius: 20px;
        font-size: 12px;
        display: inline-block;
    }
    .badge-warning {
        background-color: #fed7aa;
        color: #9b2c1d;
        padding: 4px 8px;
        border-radius: 20px;
        font-size: 12px;
        display: inline-block;
    }
    .badge-info {
        background-color: #dbeafe;
        color: #1e40af;
        padding: 4px 8px;
        border-radius: 20px;
        font-size: 12px;
        display: inline-block;
    }
    
    /* Gráficos personalizados */
    .progress-bar {
        height: 8px;
        background-color: #e5e7eb;
        border-radius: 4px;
        overflow: hidden;
        margin: 8px 0;
    }
    .progress-fill {
        height: 100%;
        background-color: #E91E63;
        border-radius: 4px;
        transition: width 0.3s;
    }
    .stat-card {
        background: white;
        border-radius: 12px;
        padding: 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        margin-bottom: 16px;
    }
    .service-item {
        background: white;
        border-radius: 12px;
        padding: 12px;
        margin-bottom: 8px;
        border: 1px solid #e5e7eb;
        transition: all 0.2s;
    }
    .service-item:hover {
        border-color: #E91E63;
        box-shadow: 0 2px 8px rgba(233,30,99,0.1);
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# INICIALIZAÇÃO DO BANCO DE DADOS
# ============================================
def init_db():
    conn = sqlite3.connect('agenda.db')
    cursor = conn.cursor()
    
    # Tabela professionals
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
    
    # Tabela clients
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
    
    # Tabela services
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
    
    # Tabela appointments
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
    
    # Tabela financial_records
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
    
    # Inserir dados de exemplo se não existir
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
            'Especialista em alongamento de unhas e nail art. Atendimento personalizado com produtos de alta qualidade.',
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
            (str(uuid.uuid4()), prof_id, 'Esmaltação em Gel', 'Esmaltação que dura até 15 dias', 50, None, 45, 'Esmaltação', 0),
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
            (str(uuid.uuid4()), prof_id, 'Fernanda Lima', '(11) 95555-5555', 'fernanda@email.com', None, '1992-03-25', None, None, None, 1, 180, '2024-03-25'),
            (str(uuid.uuid4()), prof_id, 'Patrícia Oliveira', '(11) 94444-4444', 'patricia@email.com', None, '1985-03-30', None, None, None, 4, 620, '2024-03-21'),
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
            (str(uuid.uuid4()), clients[2][0], services[2][0], prof_id,
             datetime(now.year, now.month, now.day, 16, 0).isoformat(),
             datetime(now.year, now.month, now.day, 17, 0).isoformat(),
             'pending', None, 'pending', 80, 0),
            (str(uuid.uuid4()), clients[3][0], services[4][0], prof_id,
             datetime(now.year, now.month, now.day + 1, 9, 0).isoformat(),
             datetime(now.year, now.month, now.day + 1, 10, 30).isoformat(),
             'confirmed', 'Dinheiro', 'pending', 90, 0),
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
            (str(uuid.uuid4()), prof_id, 'Aniversário', 'Feliz aniversário! 🎂 Venha ganhar um brinde especial!', 'aniversario'),
        ]
        
        for m in messages:
            cursor.execute('''
                INSERT INTO messages (id, professional_id, title, content, category)
                VALUES (?, ?, ?, ?, ?)
            ''', m)
        
        # Produtos exemplo
        products = [
            (str(uuid.uuid4()), prof_id, 'Esmalte Gel', 'Esmalte em gel de alta duração', 25.00, 45.00, 15, 5, 'Esmaltes', 'GEL001', 1),
            (str(uuid.uuid4()), prof_id, 'Top Coat', 'Finalizador brilhante', 18.00, 35.00, 10, 3, 'Finalizadores', 'TOP001', 1),
            (str(uuid.uuid4()), prof_id, 'Base Fortalecedora', 'Base para fortalecer unhas', 15.00, 30.00, 8, 2, 'Bases', 'BAS001', 1),
            (str(uuid.uuid4()), prof_id, 'Óleo para Cutículas', 'Hidratação para cutículas', 12.00, 25.00, 20, 5, 'Cuidados', 'OLE001', 1),
        ]
        
        for p in products:
            cursor.execute('''
                INSERT INTO products (id, professional_id, name, description, purchase_price, sale_price, stock_quantity, min_stock_quantity, category, sku, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', p)
    
    conn.commit()
    conn.close()

# ============================================
# FUNÇÕES AUXILIARES
# ============================================
def get_db():
    conn = sqlite3.connect('agenda.db')
    conn.row_factory = sqlite3.Row
    return conn

def format_currency(value):
    return f"R$ {value:,.2f}"

def format_date(date_str):
    if not date_str:
        return ""
    try:
        return datetime.fromisoformat(date_str).strftime('%d/%m/%Y')
    except:
        return date_str

def format_datetime(date_str):
    if not date_str:
        return ""
    try:
        return datetime.fromisoformat(date_str).strftime('%d/%m/%Y %H:%M')
    except:
        return date_str

def get_status_badge(status):
    badges = {
        'pending': '<span class="badge-warning">⏳ Pendente</span>',
        'confirmed': '<span class="badge-success">✅ Confirmado</span>',
        'in_progress': '<span class="badge-info">⚡ Em andamento</span>',
        'completed': '<span class="badge-success">🎉 Concluído</span>',
        'cancelled': '<span class="badge-warning">❌ Cancelado</span>',
        'no_show': '<span class="badge-warning">😞 Não compareceu</span>'
    }
    return badges.get(status, status)

def create_bar_chart(data, labels, title):
    """Cria um gráfico de barras usando HTML/CSS"""
    max_value = max(data) if data else 1
    bars_html = ""
    for i, value in enumerate(data):
        percentage = (value / max_value * 100) if max_value > 0 else 0
        bars_html += f"""
        <div style="margin-bottom: 12px;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                <span style="font-size: 12px;">{labels[i]}</span>
                <span style="font-size: 12px; font-weight: bold;">{format_currency(value)}</span>
            </div>
            <div class="progress-bar">
                <div class="progress-fill" style="width: {percentage}%;"></div>
            </div>
        </div>
        """
    
    return f"""
    <div class="stat-card">
        <h4 style="margin-bottom: 16px;">{title}</h4>
        {bars_html}
    </div>
    """

def create_pie_chart(data, labels, title):
    """Cria um gráfico de pizza usando HTML/CSS"""
    total = sum(data) if data else 1
    colors = ['#E91E63', '#FF4081', '#F50057', '#FF80AB', '#FFB7C5', '#FFC0CB']
    items_html = ""
    for i, value in enumerate(data):
        percentage = (value / total * 100) if total > 0 else 0
        color = colors[i % len(colors)]
        items_html += f"""
        <div style="display: flex; align-items: center; margin-bottom: 8px;">
            <div style="width: 12px; height: 12px; background-color: {color}; border-radius: 2px; margin-right: 8px;"></div>
            <span style="flex: 1; font-size: 12px;">{labels[i]}</span>
            <span style="font-size: 12px; font-weight: bold;">{percentage:.1f}%</span>
        </div>
        """
    
    # Criar um gráfico de pizza simples usando CSS
    pie_chart = f"""
    <div style="display: flex; gap: 20px; align-items: center;">
        <div style="width: 120px; height: 120px; border-radius: 50%; background: conic-gradient({', '.join([f'{colors[i % len(colors)]} 0% {sum(data[:i+1])/total*100}%' for i in range(len(data))])});">
        </div>
        <div style="flex: 1;">
            {items_html}
        </div>
    </div>
    """
    
    return f"""
    <div class="stat-card">
        <h4 style="margin-bottom: 16px;">{title}</h4>
        {pie_chart}
    </div>
    """

# ============================================
# AUTENTICAÇÃO
# ============================================
def check_auth():
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.user_id = None
        st.session_state.user_name = None
        st.session_state.view = 'booking'
    
    return st.session_state.authenticated

def login():
    st.title("🔐 Área Administrativa")
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("### Login")
        email = st.text_input("Email")
        password = st.text_input("Senha", type="password")
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("Entrar", use_container_width=True):
                conn = get_db()
                cursor = conn.cursor()
                cursor.execute("SELECT id, name, business_name, password FROM professionals WHERE email = ?", (email,))
                user = cursor.fetchone()
                conn.close()
                
                if user and user[3] == hashlib.sha256(password.encode()).hexdigest():
                    st.session_state.authenticated = True
                    st.session_state.user_id = user[0]
                    st.session_state.user_name = user[1] or user[2]
                    st.rerun()
                else:
                    st.error("Email ou senha incorretos")
        
        with col_btn2:
            if st.button("Voltar para Agendamento", use_container_width=True):
                st.session_state.view = 'booking'
                st.rerun()
        
        st.markdown("---")
        st.info("📝 **Demo:** ste@naildesigner.com / admin123")

def logout():
    st.session_state.authenticated = False
    st.session_state.user_id = None
    st.session_state.user_name = None
    st.rerun()

# ============================================
# PÁGINA PÚBLICA DE AGENDAMENTO
# ============================================
def render_booking_page():
    # Buscar profissional
    slug = "stebarbosa"
    
    conn = get_db()
    prof = conn.execute("SELECT * FROM professionals WHERE bio_url = ? AND is_active = 1", (slug,)).fetchone()
    conn.close()
    
    if not prof:
        st.error("Profissional não encontrada")
        return
    
    # Header
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(f"""
        <div style="text-align: center;">
            <div style="width: 100px; height: 100px; background: linear-gradient(135deg, #E91E63, #FF4081); border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; margin-bottom: 16px;">
                <span style="font-size: 48px; color: white;">💅</span>
            </div>
            <h1>{prof['business_name'] or prof['name']}</h1>
            <p style="color: gray;">{prof['bio_description'] or ''}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Links Sociais
        cols = st.columns(3)
        if prof['instagram']:
            with cols[0]:
                st.link_button("📷 Instagram", f"https://instagram.com/{prof['instagram'].replace('@', '')}", use_container_width=True)
        if prof['whatsapp']:
            with cols[1]:
                st.link_button("💬 WhatsApp", f"https://wa.me/{prof['whatsapp']}", use_container_width=True)
        if prof['address']:
            with cols[2]:
                st.link_button("📍 Endereço", None, disabled=True, use_container_width=True)
        
        st.markdown("---")
        
        # Área de Agendamento
        if st.button("🔐 Área do Profissional", use_container_width=True):
            st.session_state.view = 'admin'
            st.rerun()
    
    # Widget de Agendamento
    render_booking_widget(prof)

def render_booking_widget(prof):
    # Inicializar estado do agendamento
    if 'booking_step' not in st.session_state:
        st.session_state.booking_step = 1
        st.session_state.selected_service = None
        st.session_state.selected_date = None
        st.session_state.selected_time = None
        st.session_state.client_data = None
    
    # Steps
    steps = ["Escolha o Serviço", "Data e Horário", "Seus Dados", "Confirmação"]
    current_step = st.session_state.booking_step - 1
    
    cols = st.columns(4)
    for i, step in enumerate(steps):
        with cols[i]:
            if i < current_step:
                st.markdown(f"✅ {step}")
            elif i == current_step:
                st.markdown(f"🔴 **{step}**")
            else:
                st.markdown(f"⚪ {step}")
    
    st.markdown("---")
    
    # Step 1: Serviços
    if st.session_state.booking_step == 1:
        conn = get_db()
        services = conn.execute("SELECT * FROM services WHERE professional_id = ? AND is_active = 1", (prof['id'],)).fetchall()
        conn.close()
        
        st.subheader("Escolha um serviço")
        
        # Busca
        search = st.text_input("🔍 Buscar serviço", placeholder="Digite o nome do serviço...")
        
        # Filtro por categoria
        categories = ['Todos'] + list(set([s['category'] for s in services if s['category']]))
        selected_category = st.selectbox("Categoria", categories)
        
        # Lista de serviços
        for service in services:
            if search and search.lower() not in service['name'].lower():
                continue
            if selected_category != 'Todos' and service['category'] != selected_category:
                continue
            
            with st.container():
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**{service['name']}**")
                    if service['description']:
                        st.caption(service['description'])
                    st.caption(f"⏱️ {service['duration_minutes']} minutos")
                with col2:
                    st.markdown(f"<h3 style='color: #E91E63;'>{format_currency(service['price'])}</h3>", unsafe_allow_html=True)
                    if st.button(f"Agendar", key=f"service_{service['id']}", use_container_width=True):
                        st.session_state.selected_service = dict(service)
                        st.session_state.booking_step = 2
                        st.rerun()
                st.divider()
    
    # Step 2: Data e Horário
    elif st.session_state.booking_step == 2:
        service = st.session_state.selected_service
        
        st.subheader(f"Agendando: {service['name']}")
        st.caption(f"💰 {format_currency(service['price'])} • ⏱️ {service['duration_minutes']} minutos")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📅 Data")
            min_date = datetime.now() + timedelta(hours=2)
            max_date = datetime.now() + timedelta(days=30)
            selected_date = st.date_input("Selecione a data", min_value=min_date.date(), max_value=max_date.date())
            
            if selected_date:
                st.session_state.selected_date = selected_date.isoformat()
        
        with col2:
            st.markdown("### ⏰ Horário")
            if st.session_state.selected_date:
                conn = get_db()
                work_hours = json.loads(prof['work_hours'])
                day_name = selected_date.strftime('%A').lower()
                day_config = work_hours.get(day_name, {})
                
                if day_config.get('enabled', False):
                    slots = []
                    start_hour, start_min = map(int, day_config['start'].split(':'))
                    end_hour, end_min = map(int, day_config['end'].split(':'))
                    
                    current = datetime(selected_date.year, selected_date.month, selected_date.day, start_hour, start_min)
                    end = datetime(selected_date.year, selected_date.month, selected_date.day, end_hour, end_min)
                    
                    # Buscar agendamentos existentes
                    appointments = conn.execute("""
                        SELECT start_time, end_time FROM appointments 
                        WHERE professional_id = ? AND date(start_time) = date(?) AND status NOT IN ('cancelled', 'no_show')
                    """, (prof['id'], selected_date.isoformat())).fetchall()
                    
                    while current + timedelta(minutes=service['duration_minutes']) <= end:
                        slot_end = current + timedelta(minutes=service['duration_minutes'])
                        has_conflict = False
                        for apt in appointments:
                            apt_start = datetime.fromisoformat(apt['start_time'])
                            apt_end = datetime.fromisoformat(apt['end_time'])
                            if current < apt_end and slot_end > apt_start:
                                has_conflict = True
                                break
                        
                        if not has_conflict and current > datetime.now():
                            slots.append(current.strftime('%H:%M'))
                        
                        current += timedelta(minutes=30)
                    
                    if slots:
                        selected_time = st.selectbox("Horários disponíveis", slots)
                        if selected_time:
                            st.session_state.selected_time = selected_time
                    else:
                        st.warning("Nenhum horário disponível para esta data")
                else:
                    st.warning("Profissional não atende neste dia")
                conn.close()
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("← Voltar", use_container_width=True):
                st.session_state.booking_step = 1
                st.rerun()
        with col2:
            if st.session_state.selected_time:
                if st.button("Continuar →", use_container_width=True):
                    st.session_state.booking_step = 3
                    st.rerun()
    
    # Step 3: Dados do Cliente
    elif st.session_state.booking_step == 3:
        service = st.session_state.selected_service
        
        st.subheader("Seus dados")
        
        with st.form("client_form"):
            full_name = st.text_input("Nome completo *")
            phone = st.text_input("Telefone / WhatsApp *", placeholder="(11) 99999-9999")
            email = st.text_input("E-mail", placeholder="seu@email.com")
            birth_date = st.date_input("Data de nascimento", value=None)
            notes = st.text_area("Observações")
            whatsapp_optin = st.checkbox("Quero receber confirmações por WhatsApp", value=True)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("← Voltar", use_container_width=True):
                    st.session_state.booking_step = 2
                    st.rerun()
            with col2:
                if st.form_submit_button("Confirmar Agendamento", use_container_width=True):
                    if not full_name or not phone:
                        st.error("Preencha nome e telefone")
                    else:
                        # Criar agendamento
                        date_time = datetime.fromisoformat(f"{st.session_state.selected_date}T{st.session_state.selected_time}:00")
                        end_time = date_time + timedelta(minutes=service['duration_minutes'])
                        
                        conn = get_db()
                        
                        # Buscar ou criar cliente
                        client = conn.execute("SELECT id FROM clients WHERE phone = ? AND professional_id = ?", (phone, prof['id'])).fetchone()
                        
                        if client:
                            client_id = client['id']
                        else:
                            client_id = str(uuid.uuid4())
                            conn.execute("""
                                INSERT INTO clients (id, professional_id, full_name, phone, email, birth_date, notes, whatsapp_optin)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            """, (client_id, prof['id'], full_name, phone, email, birth_date.isoformat() if birth_date else None, notes, 1 if whatsapp_optin else 0))
                        
                        # Criar agendamento
                        appointment_id = str(uuid.uuid4())
                        conn.execute("""
                            INSERT INTO appointments (id, client_id, service_id, professional_id, start_time, end_time, notes, created_by)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (appointment_id, client_id, service['id'], prof['id'], date_time.isoformat(), end_time.isoformat(), notes, 'client'))
                        
                        conn.commit()
                        conn.close()
                        
                        st.session_state.booking_id = appointment_id
                        st.session_state.booking_step = 4
                        st.rerun()
    
    # Step 4: Confirmação
    elif st.session_state.booking_step == 4:
        service = st.session_state.selected_service
        
        st.success("✅ Agendamento Confirmado!")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
            ### 📋 Detalhes do Agendamento
            - **Serviço:** {service['name']}
            - **Data:** {format_date(st.session_state.selected_date)}
            - **Horário:** {st.session_state.selected_time}
            - **Valor:** {format_currency(service['price'])}
            """)
        
        with col2:
            st.markdown(f"""
            ### 💡 Próximos passos
            - Guarde o código: `{st.session_state.booking_id[:8]}`
            - Você receberá um lembrete por WhatsApp
            - Em caso de imprevistos, cancele com 24h de antecedência
            """)
        
        # Link WhatsApp
        if prof['whatsapp']:
            message = f"Olá! Acabei de agendar um {service['name']} para {format_date(st.session_state.selected_date)} às {st.session_state.selected_time}. Meu código é: {st.session_state.booking_id[:8]}"
            whatsapp_url = f"https://wa.me/{prof['whatsapp']}?text={message}"
            st.link_button("💬 Compartilhar no WhatsApp", whatsapp_url, use_container_width=True)
        
        if st.button("← Fazer novo agendamento", use_container_width=True):
            st.session_state.booking_step = 1
            st.session_state.selected_service = None
            st.session_state.selected_date = None
            st.session_state.selected_time = None
            st.rerun()

# ============================================
# PÁGINA ADMINISTRATIVA
# ============================================
def render_admin_page():
    # Sidebar com menu
    with st.sidebar:
        st.image("https://via.placeholder.com/150x150?text=💅", width=100)
        st.markdown(f"### Olá, {st.session_state.user_name}!")
        st.markdown("---")
        
        selected = option_menu(
            menu_title="Menu Principal",
            options=["Dashboard", "Agenda", "Clientes", "Serviços", "Produtos", "Financeiro", "Mensagens", "Configurações"],
            icons=["graph-up", "calendar3", "people", "scissors", "box", "cash-stack", "envelope", "gear"],
            menu_icon="list",
            default_index=0,
            styles={
                "container": {"padding": "0!important", "background-color": "#fafafa"},
                "icon": {"color": "#E91E63", "font-size": "18px"},
                "nav-link": {"font-size": "14px", "text-align": "left", "margin": "0px", "--hover-color": "#fef2f6"},
                "nav-link-selected": {"background-color": "#E91E63"},
            }
        )
        
        st.markdown("---")
        if st.button("🚪 Sair", use_container_width=True):
            logout()
            st.rerun()
    
    # Renderizar conteúdo baseado no menu selecionado
    if selected == "Dashboard":
        render_admin_dashboard()
    elif selected == "Agenda":
        render_admin_agenda()
    elif selected == "Clientes":
        render_admin_clientes()
    elif selected == "Serviços":
        render_admin_servicos()
    elif selected == "Produtos":
        render_admin_produtos()
    elif selected == "Financeiro":
        render_admin_financeiro()
    elif selected == "Mensagens":
        render_admin_mensagens()
    elif selected == "Configurações":
        render_admin_configuracoes()

def render_admin_dashboard():
    st.title("📊 Dashboard")
    
    conn = get_db()
    
    # Cards
    col1, col2, col3, col4 = st.columns(4)
    
    # Receita Total
    revenue = conn.execute("SELECT COALESCE(SUM(amount_paid), 0) FROM appointments WHERE professional_id = ? AND status = 'completed'", (st.session_state.user_id,)).fetchone()[0]
    with col1:
        st.metric("Receita Total", format_currency(revenue))
    
    # Despesas
    expenses = conn.execute("SELECT COALESCE(SUM(amount), 0) FROM financial_records WHERE professional_id = ? AND type = 'expense' AND status = 'paid'", (st.session_state.user_id,)).fetchone()[0]
    with col2:
        st.metric("Despesas", format_currency(expenses))
    
    # Lucro
    profit = revenue - expenses
    with col3:
        st.metric("Lucro Líquido", format_currency(profit))
    
    # Atendimentos
    appointments_count = conn.execute("SELECT COUNT(*) FROM appointments WHERE professional_id = ? AND status = 'completed'", (st.session_state.user_id,)).fetchone()[0]
    with col4:
        st.metric("Atendimentos", appointments_count)
    
    st.markdown("---")
    
    # Gráficos usando CSS puro
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Top 5 Serviços")
        top_services = conn.execute("""
            SELECT s.name, COUNT(a.id) as total, SUM(a.amount_paid) as revenue
            FROM appointments a
            JOIN services s ON a.service_id = s.id
            WHERE a.professional_id = ? AND a.status = 'completed'
            GROUP BY s.id
            ORDER BY revenue DESC
            LIMIT 5
        """, (st.session_state.user_id,)).fetchall()
        
        if top_services:
            services_names = [s['name'] for s in top_services]
            services_revenue = [s['revenue'] for s in top_services]
            st.markdown(create_bar_chart(services_revenue, services_names, "Receita por Serviço"), unsafe_allow_html=True)
        else:
            st.info("Nenhum dado disponível")
    
    with col2:
        st.subheader("Formas de Pagamento")
        payments = conn.execute("""
            SELECT payment_method, COUNT(*) as count, SUM(amount_paid) as total
            FROM appointments
            WHERE professional_id = ? AND status = 'completed' AND payment_method IS NOT NULL
            GROUP BY payment_method
        """, (st.session_state.user_id,)).fetchall()
        
        if payments:
            payment_methods = [p['payment_method'] for p in payments]
            payment_totals = [p['total'] for p in payments]
            st.markdown(create_pie_chart(payment_totals, payment_methods, "Distribuição de Pagamentos"), unsafe_allow_html=True)
        else:
            st.info("Nenhum dado disponível")
    
    st.markdown("---")
    
    # Aniversariantes do Mês
    st.subheader("🎂 Aniversariantes do Mês")
    birthdays = conn.execute("""
        SELECT full_name, phone, birth_date
        FROM clients
        WHERE professional_id = ? 
          AND birth_date IS NOT NULL
          AND strftime('%m', birth_date) = strftime('%m', 'now')
        ORDER BY strftime('%d', birth_date)
    """, (st.session_state.user_id,)).fetchall()
    
    if birthdays:
        for b in birthdays:
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.write(f"🎉 **{b['full_name']}**")
            with col2:
                st.write(format_date(b['birth_date']))
            with col3:
                if b['phone']:
                    st.link_button("💬 WhatsApp", f"https://wa.me/{b['phone'].replace('(', '').replace(')', '').replace('-', '').replace(' ', '')}", use_container_width=True)
    else:
        st.info("Nenhum aniversariante este mês")
    
    conn.close()

def render_admin_agenda():
    st.title("📅 Agenda")
    
    date = st.date_input("Data", datetime.now())
    
    conn = get_db()
    appointments = conn.execute("""
        SELECT a.*, c.full_name as client_name, c.phone as client_phone,
               s.name as service_name, s.price, s.duration_minutes
        FROM appointments a
        JOIN clients c ON a.client_id = c.id
        JOIN services s ON a.service_id = s.id
        WHERE a.professional_id = ? AND date(a.start_time) = date(?)
        ORDER BY a.start_time
    """, (st.session_state.user_id, date.isoformat())).fetchall()
    conn.close()
    
    if appointments:
        for apt in appointments:
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([1, 2, 2, 1, 1])
                with col1:
                    st.markdown(f"### ⏰ {datetime.fromisoformat(apt['start_time']).strftime('%H:%M')}")
                with col2:
                    st.markdown(f"**👤 {apt['client_name']}**")
                    st.caption(f"📞 {apt['client_phone']}")
                with col3:
                    st.markdown(f"**💅 {apt['service_name']}**")
                    st.caption(f"💰 {format_currency(apt['price'])} • ⏱️ {apt['duration_minutes']} min")
                with col4:
                    st.markdown(get_status_badge(apt['status']), unsafe_allow_html=True)
                with col5:
                    new_status = st.selectbox(
                        "Status",
                        ["pending", "confirmed", "in_progress", "completed", "cancelled"],
                        index=["pending", "confirmed", "in_progress", "completed", "cancelled"].index(apt['status']) if apt['status'] in ["pending", "confirmed", "in_progress", "completed", "cancelled"] else 0,
                        key=f"status_{apt['id']}",
                        label_visibility="collapsed"
                    )
                    if new_status != apt['status']:
                        conn = get_db()
                        conn.execute("UPDATE appointments SET status = ? WHERE id = ?", (new_status, apt['id']))
                        if new_status == 'completed':
                            conn.execute("""
                                UPDATE clients 
                                SET total_visits = total_visits + 1,
                                    total_spent = total_spent + ?,
                                    last_visit = CURRENT_TIMESTAMP
                                WHERE id = ?
                            """, (apt['amount_paid'] or apt['price'], apt['client_id']))
                        conn.commit()
                        conn.close()
                        st.rerun()
                st.divider()
    else:
        st.info("Nenhum agendamento para esta data")

def render_admin_clientes():
    st.title("👥 Clientes")
    
    search = st.text_input("🔍 Buscar cliente", placeholder="Nome ou telefone...")
    
    conn = get_db()
    query = "SELECT * FROM clients WHERE professional_id = ?"
    params = [st.session_state.user_id]
    
    if search:
        query += " AND (full_name LIKE ? OR phone LIKE ?)"
        params.append(f"%{search}%")
        params.append(f"%{search}%")
    
    query += " ORDER BY total_spent DESC, last_visit DESC"
    
    clients = conn.execute(query, params).fetchall()
    conn.close()
    
    if clients:
        for client in clients:
            with st.expander(f"📋 {client['full_name']}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Telefone:** {client['phone']}")
                    st.write(f"**Email:** {client['email'] or '-'}")
                    st.write(f"**Aniversário:** {format_date(client['birth_date']) or '-'}")
                with col2:
                    st.write(f"**Visitas:** {client['total_visits']}")
                    st.write(f"**Gasto Total:** {format_currency(client['total_spent'])}")
                    st.write(f"**Última Visita:** {format_date(client['last_visit']) or '-'}")
                
                st.write(f"**Observações:** {client['notes'] or '-'}")
                
                if client['phone']:
                    st.link_button("💬 WhatsApp", f"https://wa.me/{client['phone'].replace('(', '').replace(')', '').replace('-', '').replace(' ', '')}", use_container_width=True)
    else:
        st.info("Nenhum cliente encontrado")

def render_admin_servicos():
    st.title("💅 Serviços")
    
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("+ Novo Serviço", use_container_width=True):
            st.session_state.show_service_form = True
    
    conn = get_db()
    services = conn.execute("SELECT * FROM services WHERE professional_id = ? ORDER BY created_at DESC", (st.session_state.user_id,)).fetchall()
    conn.close()
    
    if services:
        for service in services:
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                with col1:
                    st.markdown(f"**{service['name']}**")
                    st.caption(service['description'] or "Sem descrição")
                    st.caption(f"⏱️ {service['duration_minutes']} min")
                with col2:
                    st.markdown(f"**{service['category'] or '-'}**")
                with col3:
                    st.markdown(f"<h3 style='color: #E91E63;'>{format_currency(service['price'])}</h3>", unsafe_allow_html=True)
                with col4:
                    if st.button(f"✏️ Editar", key=f"edit_{service['id']}", use_container_width=True):
                        st.session_state.editing_service = dict(service)
                st.divider()
    else:
        st.info("Nenhum serviço cadastrado")
    
    # Modal de criação/edição
    if st.session_state.get('show_service_form', False):
        with st.form("service_form"):
            st.subheader("Novo Serviço")
            name = st.text_input("Nome")
            description = st.text_area("Descrição")
            category = st.selectbox("Categoria", ["Alongamento", "Manutenção", "Esmaltação", "Pedicure", "Outros"])
            duration = st.number_input("Duração (minutos)", min_value=15, value=60)
            price = st.number_input("Preço", min_value=0.0, value=100.0)
            commission = st.number_input("Comissão (%)", min_value=0.0, value=0.0)
            is_active = st.checkbox("Ativo", value=True)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("Salvar", use_container_width=True):
                    conn = get_db()
                    conn.execute("""
                        INSERT INTO services (id, professional_id, name, description, price, duration_minutes, category, commission_percentage, is_active)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (str(uuid.uuid4()), st.session_state.user_id, name, description, price, duration, category, commission, 1 if is_active else 0))
                    conn.commit()
                    conn.close()
                    st.session_state.show_service_form = False
                    st.rerun()
            with col2:
                if st.form_submit_button("Cancelar", use_container_width=True):
                    st.session_state.show_service_form = False
                    st.rerun()
    
    # Modal de edição
    if st.session_state.get('editing_service'):
        service = st.session_state.editing_service
        with st.form("edit_service_form"):
            st.subheader(f"Editando: {service['name']}")
            name = st.text_input("Nome", value=service['name'])
            description = st.text_area("Descrição", value=service['description'] or "")
            category = st.selectbox("Categoria", ["Alongamento", "Manutenção", "Esmaltação", "Pedicure", "Outros"], index=["Alongamento", "Manutenção", "Esmaltação", "Pedicure", "Outros"].index(service['category']) if service['category'] in ["Alongamento", "Manutenção", "Esmaltação", "Pedicure", "Outros"] else 0)
            duration = st.number_input("Duração (minutos)", min_value=15, value=service['duration_minutes'])
            price = st.number_input("Preço", min_value=0.0, value=service['price'])
            commission = st.number_input("Comissão (%)", min_value=0.0, value=service['commission_percentage'])
            is_active = st.checkbox("Ativo", value=bool(service['is_active']))
            
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.form_submit_button("Salvar", use_container_width=True):
                    conn = get_db()
                    conn.execute("""
                        UPDATE services 
                        SET name = ?, description = ?, price = ?, duration_minutes = ?, category = ?, commission_percentage = ?, is_active = ?
                        WHERE id = ?
                    """, (name, description, price, duration, category, commission, 1 if is_active else 0, service['id']))
                    conn.commit()
                    conn.close()
                    st.session_state.editing_service = None
                    st.rerun()
            with col2:
                if st.form_submit_button("Excluir", use_container_width=True):
                    conn = get_db()
                    conn.execute("DELETE FROM services WHERE id = ?", (service['id'],))
                    conn.commit()
                    conn.close()
                    st.session_state.editing_service = None
                    st.rerun()
            with col3:
                if st.form_submit_button("Cancelar", use_container_width=True):
                    st.session_state.editing_service = None
                    st.rerun()

def render_admin_produtos():
    st.title("🛍️ Produtos")
    
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("+ Novo Produto", use_container_width=True):
            st.session_state.show_product_form = True
    
    conn = get_db()
    products = conn.execute("SELECT * FROM products WHERE professional_id = ? ORDER BY name", (st.session_state.user_id,)).fetchall()
    conn.close()
    
    if products:
        for product in products:
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
                with col1:
                    st.markdown(f"**{product['name']}**")
                    st.caption(product['description'] or "Sem descrição")
                    st.caption(f"SKU: {product['sku']}")
                with col2:
                    st.markdown(f"**Compra:** {format_currency(product['purchase_price'])}")
                with col3:
                    st.markdown(f"**Venda:** {format_currency(product['sale_price'])}")
                with col4:
                    stock_color = "🔴" if product['stock_quantity'] <= product['min_stock_quantity'] else "🟢"
                    st.markdown(f"{stock_color} **Estoque:** {product['stock_quantity']}")
                with col5:
                    if st.button(f"✏️", key=f"edit_prod_{product['id']}", use_container_width=True):
                        st.session_state.editing_product = dict(product)
                st.divider()
    else:
        st.info("Nenhum produto cadastrado")
    
    # Modal de criação
    if st.session_state.get('show_product_form', False):
        with st.form("product_form"):
            st.subheader("Novo Produto")
            name = st.text_input("Nome")
            description = st.text_area("Descrição")
            sku = st.text_input("SKU", placeholder="Código único do produto")
            category = st.selectbox("Categoria", ["Esmaltes", "Finalizadores", "Bases", "Cuidados", "Outros"])
            purchase_price = st.number_input("Preço de Compra", min_value=0.0, value=0.0)
            sale_price = st.number_input("Preço de Venda", min_value=0.0, value=0.0)
            stock = st.number_input("Quantidade em Estoque", min_value=0, value=0)
            min_stock = st.number_input("Estoque Mínimo", min_value=0, value=5)
            is_active = st.checkbox("Ativo", value=True)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("Salvar", use_container_width=True):
                    conn = get_db()
                    conn.execute("""
                        INSERT INTO products (id, professional_id, name, description, sku, category, purchase_price, sale_price, stock_quantity, min_stock_quantity, is_active)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (str(uuid.uuid4()), st.session_state.user_id, name, description, sku or f"PROD-{uuid.uuid4().hex[:8]}", category, purchase_price, sale_price, stock, min_stock, 1 if is_active else 0))
                    conn.commit()
                    conn.close()
                    st.session_state.show_product_form = False
                    st.rerun()
            with col2:
                if st.form_submit_button("Cancelar", use_container_width=True):
                    st.session_state.show_product_form = False
                    st.rerun()
    
    # Modal de edição
    if st.session_state.get('editing_product'):
        product = st.session_state.editing_product
        with st.form("edit_product_form"):
            st.subheader(f"Editando: {product['name']}")
            name = st.text_input("Nome", value=product['name'])
            description = st.text_area("Descrição", value=product['description'] or "")
            sku = st.text_input("SKU", value=product['sku'] or "")
            category = st.selectbox("Categoria", ["Esmaltes", "Finalizadores", "Bases", "Cuidados", "Outros"], index=["Esmaltes", "Finalizadores", "Bases", "Cuidados", "Outros"].index(product['category']) if product['category'] in ["Esmaltes", "Finalizadores", "Bases", "Cuidados", "Outros"] else 0)
            purchase_price = st.number_input("Preço de Compra", min_value=0.0, value=product['purchase_price'])
            sale_price = st.number_input("Preço de Venda", min_value=0.0, value=product['sale_price'])
            stock = st.number_input("Quantidade em Estoque", min_value=0, value=product['stock_quantity'])
            min_stock = st.number_input("Estoque Mínimo", min_value=0, value=product['min_stock_quantity'])
            is_active = st.checkbox("Ativo", value=bool(product['is_active']))
            
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.form_submit_button("Salvar", use_container_width=True):
                    conn = get_db()
                    conn.execute("""
                        UPDATE products 
                        SET name = ?, description = ?, sku = ?, category = ?, purchase_price = ?, sale_price = ?, stock_quantity = ?, min_stock_quantity = ?, is_active = ?
                        WHERE id = ?
                    """, (name, description, sku, category, purchase_price, sale_price, stock, min_stock, 1 if is_active else 0, product['id']))
                    conn.commit()
                    conn.close()
                    st.session_state.editing_product = None
                    st.rerun()
            with col2:
                if st.form_submit_button("Excluir", use_container_width=True):
                    conn = get_db()
                    conn.execute("DELETE FROM products WHERE id = ?", (product['id'],))
                    conn.commit()
                    conn.close()
                    st.session_state.editing_product = None
                    st.rerun()
            with col3:
                if st.form_submit_button("Cancelar", use_container_width=True):
                    st.session_state.editing_product = None
                    st.rerun()

def render_admin_financeiro():
    st.title("💰 Financeiro")
    
    period = st.selectbox("Período", ["Este Mês", "Este Ano", "Todos"])
    
    if period == "Este Mês":
        date_filter = "strftime('%Y-%m', created_at) = strftime('%Y-%m', 'now')"
    elif period == "Este Ano":
        date_filter = "strftime('%Y', created_at) = strftime('%Y', 'now')"
    else:
        date_filter = "1=1"
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("+ Nova Receita", use_container_width=True):
            st.session_state.show_income_form = True
    with col2:
        if st.button("+ Nova Despesa", use_container_width=True):
            st.session_state.show_expense_form = True
    
    conn = get_db()
    records = conn.execute(f"""
        SELECT * FROM financial_records 
        WHERE professional_id = ? AND {date_filter}
        ORDER BY created_at DESC
    """, (st.session_state.user_id,)).fetchall()
    conn.close()
    
    if records:
        # Resumo
        total_income = sum(r['amount'] for r in records if r['type'] == 'income' and r['status'] == 'paid')
        total_expense = sum(r['amount'] for r in records if r['type'] == 'expense' and r['status'] == 'paid')
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Receitas", format_currency(total_income))
        with col2:
            st.metric("Total Despesas", format_currency(total_expense))
        with col3:
            st.metric("Saldo", format_currency(total_income - total_expense))
        
        st.markdown("---")
        
        for record in records:
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 1, 1])
                with col1:
                    st.write(f"📅 {format_date(record['created_at'])}")
                with col2:
                    icon = "💰" if record['type'] == 'income' else "💸"
                    st.write(f"{icon} {record['type'].upper()}")
                with col3:
                    st.write(f"📂 {record['category']}")
                with col4:
                    color = "green" if record['type'] == 'income' else "red"
                    st.markdown(f"<span style='color: {color}; font-weight: bold;'>{format_currency(record['amount'])}</span>", unsafe_allow_html=True)
                with col5:
                    badge = "✅" if record['status'] == 'paid' else "⏳"
                    st.write(f"{badge} {record['status']}")
                st.divider()
    else:
        st.info("Nenhum registro financeiro")
    
    # Modal de receita
    if st.session_state.get('show_income_form', False):
        with st.form("income_form"):
            st.subheader("Nova Receita")
            amount = st.number_input("Valor", min_value=0.0, value=0.0)
            category = st.selectbox("Categoria", ["Serviço Prestado", "Venda de Produto", "Outros"])
            description = st.text_input("Descrição")
            payment_method = st.selectbox("Forma de Pagamento", ["PIX", "Dinheiro", "Cartão Crédito", "Cartão Débito"])
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("Salvar", use_container_width=True):
                    conn = get_db()
                    conn.execute("""
                        INSERT INTO financial_records (id, professional_id, type, amount, category, description, payment_method, status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (str(uuid.uuid4()), st.session_state.user_id, 'income', amount, category, description, payment_method, 'paid'))
                    conn.commit()
                    conn.close()
                    st.session_state.show_income_form = False
                    st.rerun()
            with col2:
                if st.form_submit_button("Cancelar", use_container_width=True):
                    st.session_state.show_income_form = False
                    st.rerun()
    
    # Modal de despesa
    if st.session_state.get('show_expense_form', False):
        with st.form("expense_form"):
            st.subheader("Nova Despesa")
            amount = st.number_input("Valor", min_value=0.0, value=0.0)
            category = st.selectbox("Categoria", ["Material", "Aluguel", "Água/Luz", "Internet", "Marketing", "Outros"])
            description = st.text_input("Descrição")
            due_date = st.date_input("Data de Vencimento")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("Salvar", use_container_width=True):
                    conn = get_db()
                    conn.execute("""
                        INSERT INTO financial_records (id, professional_id, type, amount, category, description, due_date, status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (str(uuid.uuid4()), st.session_state.user_id, 'expense', amount, category, description, due_date.isoformat(), 'pending'))
                    conn.commit()
                    conn.close()
                    st.session_state.show_expense_form = False
                    st.rerun()
            with col2:
                if st.form_submit_button("Cancelar", use_container_width=True):
                    st.session_state.show_expense_form = False
                    st.rerun()

def render_admin_mensagens():
    st.title("💬 Mensagens Pré-definidas")
    
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("+ Nova Mensagem", use_container_width=True):
            st.session_state.show_message_form = True
    
    conn = get_db()
    messages = conn.execute("SELECT * FROM messages WHERE professional_id = ? ORDER BY category", (st.session_state.user_id,)).fetchall()
    conn.close()
    
    if messages:
        for msg in messages:
            with st.container():
                col1, col2, col3 = st.columns([2, 3, 1])
                with col1:
                    st.markdown(f"**{msg['title']}**")
                    st.caption(msg['category'])
                with col2:
                    st.caption(msg['content'][:100] + "..." if len(msg['content']) > 100 else msg['content'])
                with col3:
                    badge = "✅" if msg['is_active'] else "❌"
                    st.write(f"{badge} {'Ativa' if msg['is_active'] else 'Inativa'}")
                    if st.button(f"✏️", key=f"edit_msg_{msg['id']}", use_container_width=True):
                        st.session_state.editing_message = dict(msg)
                st.divider()
    else:
        st.info("Nenhuma mensagem cadastrada")
    
    # Modal de criação
    if st.session_state.get('show_message_form', False):
        with st.form("message_form"):
            st.subheader("Nova Mensagem")
            title = st.text_input("Título")
            category = st.selectbox("Categoria", ["confirmacao", "lembrete", "cancelamento", "aniversario", "promocao"])
            content = st.text_area("Conteúdo", help="Use {nome}, {data}, {hora} como variáveis")
            is_active = st.checkbox("Ativa", value=True)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("Salvar", use_container_width=True):
                    conn = get_db()
                    conn.execute("""
                        INSERT INTO messages (id, professional_id, title, content, category, is_active)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (str(uuid.uuid4()), st.session_state.user_id, title, content, category, 1 if is_active else 0))
                    conn.commit()
                    conn.close()
                    st.session_state.show_message_form = False
                    st.rerun()
            with col2:
                if st.form_submit_button("Cancelar", use_container_width=True):
                    st.session_state.show_message_form = False
                    st.rerun()
    
    # Modal de edição
    if st.session_state.get('editing_message'):
        msg = st.session_state.editing_message
        with st.form("edit_message_form"):
            st.subheader(f"Editando: {msg['title']}")
            title = st.text_input("Título", value=msg['title'])
            category = st.selectbox("Categoria", ["confirmacao", "lembrete", "cancelamento", "aniversario", "promocao"], index=["confirmacao", "lembrete", "cancelamento", "aniversario", "promocao"].index(msg['category']))
            content = st.text_area("Conteúdo", value=msg['content'])
            is_active = st.checkbox("Ativa", value=bool(msg['is_active']))
            
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.form_submit_button("Salvar", use_container_width=True):
                    conn = get_db()
                    conn.execute("""
                        UPDATE messages 
                        SET title = ?, content = ?, category = ?, is_active = ?
                        WHERE id = ?
                    """, (title, content, category, 1 if is_active else 0, msg['id']))
                    conn.commit()
                    conn.close()
                    st.session_state.editing_message = None
                    st.rerun()
            with col2:
                if st.form_submit_button("Excluir", use_container_width=True):
                    conn = get_db()
                    conn.execute("DELETE FROM messages WHERE id = ?", (msg['id'],))
                    conn.commit()
                    conn.close()
                    st.session_state.editing_message = None
                    st.rerun()
            with col3:
                if st.form_submit_button("Cancelar", use_container_width=True):
                    st.session_state.editing_message = None
                    st.rerun()

def render_admin_configuracoes():
    st.title("⚙️ Configurações")
    
    conn = get_db()
    prof = conn.execute("SELECT work_hours, appointment_settings, payment_settings, notification_settings FROM professionals WHERE id = ?", (st.session_state.user_id,)).fetchone()
    conn.close()
    
    work_hours = json.loads(prof['work_hours']) if prof and prof['work_hours'] else {}
    appointment_settings = json.loads(prof['appointment_settings']) if prof and prof['appointment_settings'] else {}
    
    st.subheader("Horários de Funcionamento")
    
    days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    day_names = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
    
    updated_hours = {}
    
    for i, day in enumerate(days):
        with st.container():
            col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
            with col1:
                enabled = st.checkbox(day_names[i], value=work_hours.get(day, {}).get('enabled', i < 5), key=f"enabled_{day}")
            with col2:
                start = st.time_input("Início", value=datetime.strptime(work_hours.get(day, {}).get('start', '09:00'), '%H:%M').time(), key=f"start_{day}", disabled=not enabled)
            with col3:
                end = st.time_input("Fim", value=datetime.strptime(work_hours.get(day, {}).get('end', '18:00'), '%H:%M').time(), key=f"end_{day}", disabled=not enabled)
            updated_hours[day] = {
                "enabled": enabled,
                "start": start.strftime('%H:%M'),
                "end": end.strftime('%H:%M')
            }
    
    st.subheader("Configurações de Agendamento")
    
    col1, col2 = st.columns(2)
    with col1:
        advance_days = st.number_input("Dias de antecedência máxima", min_value=1, max_value=90, value=appointment_settings.get('advance_booking_days', 30))
        min_cancel = st.number_input("Horas mínimas para cancelamento", min_value=0, max_value=72, value=appointment_settings.get('min_cancellation_hours', 24))
    with col2:
        min_advance = st.number_input("Minutos de antecedência mínima", min_value=0, max_value=240, value=appointment_settings.get('min_advance_notice_minutes', 120))
        slot_interval = st.number_input("Intervalo entre slots (minutos)", min_value=15, max_value=60, value=appointment_settings.get('slot_interval_minutes', 30))
    
    updated_settings = {
        "advance_booking_days": advance_days,
        "min_cancellation_hours": min_cancel,
        "min_advance_notice_minutes": min_advance,
        "slot_interval_minutes": slot_interval
    }
    
    if st.button("Salvar Configurações", use_container_width=True):
        conn = get_db()
        conn.execute("""
            UPDATE professionals 
            SET work_hours = ?, appointment_settings = ?
            WHERE id = ?
        """, (json.dumps(updated_hours), json.dumps(updated_settings), st.session_state.user_id))
        conn.commit()
        conn.close()
        st.success("Configurações salvas com sucesso!")
        st.rerun()

# ============================================
# MAIN
# ============================================
def main():
    # Inicializar banco de dados
    init_db()
    
    # Determinar view
    if 'view' not in st.session_state:
        st.session_state.view = 'booking'
    
    # Verificar autenticação
    if st.session_state.view == 'admin':
        if not check_auth():
            login()
        else:
            render_admin_page()
    else:
        render_booking_page()

if __name__ == "__main__":
    main()

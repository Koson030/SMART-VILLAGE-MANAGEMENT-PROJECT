# app.py
from flask import Flask, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
from datetime import datetime, date, time
import bcrypt
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """
    Configuration class for the Flask application.
    Uses environment variables for sensitive data.
    """
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'postgresql://your_username:your_password@localhost:5432/smart_village')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get('SECRET_KEY', 'development_secret_key')
    UPLOAD_FOLDER = 'uploads' # New: Folder for file uploads
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024 # 16 MB max upload size

class SmartVillageApp:
    """
    Main application class for the Smart Village backend,
    encapsulating Flask app, SQLAlchemy, and SocketIO.
    """
    def __init__(self):
        self.app = Flask(__name__)
        self.app.config.from_object(Config)
        CORS(self.app, resources={r"/*": {"origins": "*"}})
        self.db = SQLAlchemy(self.app)
        self.socketio = SocketIO(self.app, cors_allowed_origins="*", async_mode='threading')
        
        # Ensure upload folder exists
        if not os.path.exists(self.app.config['UPLOAD_FOLDER']):
            os.makedirs(self.app.config['UPLOAD_FOLDER'])

        self._setup_models()
        self._setup_routes()
        self._setup_socketio_events()

    def _setup_models(self):
        """
        Defines the SQLAlchemy database models.
        """
        class Users(self.db.Model):
            __tablename__ = 'users'
            user_id = self.db.Column(self.db.Integer, primary_key=True)
            name = self.db.Column(self.db.String(255), nullable=False)
            username = self.db.Column(self.db.String(50), unique=True, nullable=False)
            password_hash = self.db.Column(self.db.String(255), nullable=False)
            role = self.db.Column(self.db.String(20), nullable=False, default='resident')
            phone = self.db.Column(self.db.String(20))
            address = self.db.Column(self.db.Text)
            email = self.db.Column(self.db.String(255))
            avatar = self.db.Column(self.db.String(255))
            status = self.db.Column(self.db.String(50), default='pending') # New: User status

            def set_password(self, password):
                self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

            def check_password(self, password):
                return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))

        class Announcements(self.db.Model):
            __tablename__ = 'announcements'
            announcement_id = self.db.Column(self.db.Integer, primary_key=True)
            title = self.db.Column(self.db.String(255), nullable=False)
            content = self.db.Column(self.db.Text, nullable=False)
            published_date = self.db.Column(self.db.DateTime, default=datetime.utcnow)
            author_id = self.db.Column(self.db.Integer, self.db.ForeignKey('users.user_id'))
            tag = self.db.Column(self.db.String(50))
            tag_color = self.db.Column(self.db.String(20))
            tag_bg = self.db.Column(self.db.String(20))
            # Relationship to get author name
            author = self.db.relationship('Users', backref='announcements_authored', lazy=True)

        class RepairRequests(self.db.Model):
            __tablename__ = 'repair_requests'
            request_id = self.db.Column(self.db.Integer, primary_key=True)
            user_id = self.db.Column(self.db.Integer, self.db.ForeignKey('users.user_id'))
            title = self.db.Column(self.db.String(255), nullable=False)
            category = self.db.Column(self.db.String(50))
            description = self.db.Column(self.db.Text, nullable=False)
            submitted_date = self.db.Column(self.db.DateTime, default=datetime.utcnow)
            status = self.db.Column(self.db.String(50), default='pending')
            image_paths = self.db.Column(self.db.Text) # Stored as JSON string or comma-separated
            # Relationship to get user name
            user = self.db.relationship('Users', backref='repair_requests', lazy=True)

        class BookingRequests(self.db.Model):
            __tablename__ = 'booking_requests'
            booking_id = self.db.Column(self.db.Integer, primary_key=True)
            user_id = self.db.Column(self.db.Integer, self.db.ForeignKey('users.user_id'))
            location = self.db.Column(self.db.String(255), nullable=False)
            date = self.db.Column(self.db.Date)
            start_time = self.db.Column(self.db.Time)
            end_time = self.db.Column(self.db.Time)
            purpose = self.db.Column(self.db.Text)
            attendee_count = self.db.Column(self.db.Integer)
            status = self.db.Column(self.db.String(50), default='pending')
            # Relationship to get user name
            user = self.db.relationship('Users', backref='booking_requests', lazy=True)

        class Bills(self.db.Model): # New: Bills Model
            __tablename__ = 'bills'
            bill_id = self.db.Column(self.db.Integer, primary_key=True)
            item_name = self.db.Column(self.db.String(255), nullable=False)
            amount = self.db.Column(self.db.Numeric(10, 2), nullable=False)
            due_date = self.db.Column(self.db.Date)
            recipient_id = self.db.Column(self.db.String(50), nullable=False) # 'all' or user_id
            issued_by_user_id = self.db.Column(self.db.Integer, self.db.ForeignKey('users.user_id'))
            status = self.db.Column(self.db.String(50), default='unpaid') # unpaid, paid, pending_verification
            issued_by = self.db.relationship('Users', backref='bills_issued', lazy=True)

        class Payments(self.db.Model):
            __tablename__ = 'payments'
            payment_id = self.db.Column(self.db.Integer, primary_key=True)
            user_id = self.db.Column(self.db.Integer, self.db.ForeignKey('users.user_id'))
            bill_id = self.db.Column(self.db.Integer, self.db.ForeignKey('bills.bill_id'), nullable=True) # New: Link to Bills
            amount = self.db.Column(self.db.Numeric(10, 2), nullable=False)
            payment_method = self.db.Column(self.db.String(50))
            payment_date = self.db.Column(self.db.DateTime, default=datetime.utcnow)
            status = self.db.Column(self.db.String(50)) # pending, paid, rejected
            slip_path = self.db.Column(self.db.String(255))
            # Relationships
            user = self.db.relationship('Users', backref='payments', lazy=True)
            bill = self.db.relationship('Bills', backref='payments', lazy=True)


        class CalendarEvents(self.db.Model):
            __tablename__ = 'calendar_events'
            event_id = self.db.Column(self.db.Integer, primary_key=True)
            event_name = self.db.Column(self.db.String(255), nullable=False)
            event_date = self.db.Column(self.db.DateTime)
            location = self.db.Column(self.db.String(255))
            description = self.db.Column(self.db.Text)

        class Documents(self.db.Model):
            __tablename__ = 'documents'
            document_id = self.db.Column(self.db.Integer, primary_key=True)
            document_name = self.db.Column(self.db.String(255), nullable=False)
            file_path = self.db.Column(self.db.String(255), nullable=False)
            uploaded_by_user_id = self.db.Column(self.db.Integer, self.db.ForeignKey('users.user_id'))
            upload_date = self.db.Column(self.db.DateTime, default=datetime.utcnow)
            category = self.db.Column(self.db.String(50)) # New: Document category
            uploaded_by = self.db.relationship('Users', backref='documents_uploaded', lazy=True)

        class ChatMessages(self.db.Model):
            __tablename__ = 'chat_messages'
            message_id = self.db.Column(self.db.Integer, primary_key=True)
            sender_id = self.db.Column(self.db.Integer, self.db.ForeignKey('users.user_id'))
            receiver_id = self.db.Column(self.db.Integer, self.db.ForeignKey('users.user_id'), nullable=True)
            content = self.db.Column(self.db.Text, nullable=False)
            timestamp = self.db.Column(self.db.DateTime, default=datetime.utcnow)
            room_name = self.db.Column(self.db.String(100), default='general')
            sender = self.db.relationship('Users', foreign_keys=[sender_id], backref='sent_messages', lazy=True)
            receiver = self.db.relationship('Users', foreign_keys=[receiver_id], backref='received_messages', lazy=True)


        class SecurityVisitors(self.db.Model):
            __tablename__ = 'security_visitors'
            visitor_id = self.db.Column(self.db.Integer, primary_key=True)
            user_id = self.db.Column(self.db.Integer, self.db.ForeignKey('users.user_id'))
            name = self.db.Column(self.db.String(255), nullable=False)
            phone = self.db.Column(self.db.String(20))
            visit_date = self.db.Column(self.db.Date)
            visit_time = self.db.Column(self.db.Time)
            purpose = self.db.Column(self.db.Text)
            user = self.db.relationship('Users', backref='visitors_registered', lazy=True)

        class SecurityIncidents(self.db.Model):
            __tablename__ = 'security_incidents'
            incident_id = self.db.Column(self.db.Integer, primary_key=True)
            user_id = self.db.Column(self.db.Integer, self.db.ForeignKey('users.user_id'))
            description = self.db.Column(self.db.Text, nullable=False)
            reported_date = self.db.Column(self.db.DateTime, default=datetime.utcnow)
            evidence_paths = self.db.Column(self.db.Text)
            user = self.db.relationship('Users', backref='incidents_reported', lazy=True)

        class VotingPolls(self.db.Model):
            __tablename__ = 'voting_polls'
            poll_id = self.db.Column(self.db.Integer, primary_key=True)
            title = self.db.Column(self.db.String(255), nullable=False)
            description = self.db.Column(self.db.Text)
            start_date = self.db.Column(self.db.Date)
            end_date = self.db.Column(self.db.Date)

        class VotingOptions(self.db.Model):
            __tablename__ = 'voting_options'
            option_id = self.db.Column(self.db.Integer, primary_key=True)
            poll_id = self.db.Column(self.db.Integer, self.db.ForeignKey('voting_polls.poll_id'))
            option_text = self.db.Column(self.db.String(255), nullable=False)

        class VotingResults(self.db.Model):
            __tablename__ = 'voting_results'
            result_id = self.db.Column(self.db.Integer, primary_key=True)
            poll_id = self.db.Column(self.db.Integer, self.db.ForeignKey('voting_polls.poll_id'))
            option_id = self.db.Column(self.db.Integer, self.db.ForeignKey('voting_options.option_id'))
            user_id = self.db.Column(self.db.Integer, self.db.ForeignKey('users.user_id'))

        # Expose models as attributes of the class instance
        self.Users = Users
        self.Announcements = Announcements
        self.RepairRequests = RepairRequests
        self.BookingRequests = BookingRequests
        self.Bills = Bills # New
        self.Payments = Payments
        self.CalendarEvents = CalendarEvents
        self.Documents = Documents
        self.ChatMessages = ChatMessages
        self.SecurityVisitors = SecurityVisitors
        self.SecurityIncidents = SecurityIncidents
        self.VotingPolls = VotingPolls
        self.VotingOptions = VotingOptions
        self.VotingResults = VotingResults

    def _setup_routes(self):
        """
        Defines the RESTful API routes for the Flask application.
        """
        # Serve uploaded files
        @self.app.route('/uploads/<filename>')
        def uploaded_file(filename):
            return send_from_directory(self.app.config['UPLOAD_FOLDER'], filename)

        @self.app.route('/users', methods=['GET', 'POST'])
        def handle_users():
            if request.method == 'POST':
                data = request.json
                if self.Users.query.filter_by(username=data['username']).first():
                    return jsonify({"message": "Username already exists"}), 409
                    
                new_user = self.Users(
                    name=data['name'],
                    username=data['username'],
                    role=data.get('role', 'resident'),
                    phone=data.get('phone'),
                    address=data.get('address'),
                    email=data.get('email'),
                    avatar=data.get('avatar', data['name'][0].upper()), # Default avatar from first letter of name
                    status=data.get('status', 'pending') # New: Set status
                )
                new_user.set_password(data['password'])
                self.db.session.add(new_user)
                self.db.session.commit()
                return jsonify({"message": "User registered successfully", "user_id": new_user.user_id}), 201
            
            elif request.method == 'GET':
                users = self.Users.query.all()
                result = [
                    {
                        "user_id": user.user_id,
                        "name": user.name,
                        "username": user.username,
                        "role": user.role,
                        "phone": user.phone,
                        "address": user.address,
                        "email": user.email,
                        "avatar": user.avatar,
                        "status": user.status # New: Include status
                    } for user in users
                ]
                return jsonify(result)

        @self.app.route('/users/<int:user_id>', methods=['GET', 'PUT', 'DELETE'])
        def handle_single_user(user_id):
            user = self.Users.query.get_or_404(user_id)
            if request.method == 'GET':
                return jsonify({
                    "user_id": user.user_id,
                    "name": user.name,
                    "username": user.username,
                    "role": user.role,
                    "phone": user.phone,
                    "address": user.address,
                    "email": user.email,
                    "avatar": user.avatar,
                    "status": user.status # New: Include status
                })
            elif request.method == 'PUT':
                data = request.json
                user.name = data.get('name', user.name)
                user.username = data.get('username', user.username)
                user.role = data.get('role', user.role)
                user.phone = data.get('phone', user.phone)
                user.address = data.get('address', user.address)
                user.email = data.get('email', user.email)
                user.avatar = data.get('avatar', user.avatar)
                user.status = data.get('status', user.status) # New: Update status
                
                if 'password' in data and data['password']:
                    user.set_password(data['password'])
                self.db.session.commit()
                return jsonify({"message": "User updated successfully"}), 200
            elif request.method == 'DELETE':
                self.db.session.delete(user)
                self.db.session.commit()
                return jsonify({"message": "User deleted successfully"}), 204

        @self.app.route('/login', methods=['POST'])
        def login():
            data = request.json
            username = data.get('username')
            password = data.get('password')

            user = self.Users.query.filter_by(username=username).first()
            if user and user.check_password(password):
                if user.status == 'pending':
                    return jsonify({"message": "บัญชีของคุณยังไม่ได้รับการอนุมัติ"}), 403
                if user.status == 'suspended':
                    return jsonify({"message": "บัญชีของคุณถูกระงับ"}), 403
                return jsonify({
                    "message": "Login successful", 
                    "user_id": user.user_id, 
                    "username": user.username,
                    "name": user.name,
                    "role": user.role,
                    "avatar": user.avatar if user.avatar else user.name[0].upper()
                }), 200
            return jsonify({"message": "Invalid username or password"}), 401

        @self.app.route('/announcements', methods=['GET', 'POST'])
        def manage_announcements():
            if request.method == 'POST':
                data = request.json
                tag_colors = {
                    'สำคัญ': {'color': '#1976d2', 'bg': '#e3f2fd'},
                    'กิจกรรม': {'color': '#2e7d32', 'bg': '#e8f5e8'},
                    'แจ้งเตือน': {'color': '#856404', 'bg': '#fff3cd'}
                }
                tag_info = tag_colors.get(data.get('tag'), {'color': '#666', 'bg': '#eee'})

                new_announcement = self.Announcements(
                    title=data['title'],
                    content=data['content'],
                    published_date=datetime.fromisoformat(data['published_date']) if 'published_date' in data else datetime.utcnow(),
                    author_id=data.get('author_id'),
                    tag=data.get('tag'),
                    tag_color=tag_info['color'],
                    tag_bg=tag_info['bg']
                )
                self.db.session.add(new_announcement)
                self.db.session.commit()
                
                author_name = new_announcement.author.name if new_announcement.author else 'Unknown Author'
                self.socketio.emit('new_announcement', {
                    'announcement_id': new_announcement.announcement_id,
                    'title': new_announcement.title,
                    'content': new_announcement.content,
                    'published_date': new_announcement.published_date.isoformat(),
                    'author_id': new_announcement.author_id,
                    'author_name': author_name, # New: Include author name
                    'tag': new_announcement.tag,
                    'tag_color': new_announcement.tag_color,
                    'tag_bg': new_announcement.tag_bg
                }, broadcast=True)

                return jsonify({"message": "Announcement created successfully", "announcement_id": new_announcement.announcement_id}), 201
            
            elif request.method == 'GET':
                announcements = self.Announcements.query.order_by(self.Announcements.published_date.desc()).all()
                result = [
                    {
                        "announcement_id": ann.announcement_id,
                        "title": ann.title,
                        "content": ann.content,
                        "published_date": ann.published_date.isoformat(),
                        "author_id": ann.author_id,
                        "author_name": ann.author.name if ann.author else 'Unknown Author', # New: Include author name
                        "tag": ann.tag,
                        "tag_color": ann.tag_color,
                        "tag_bg": ann.tag_bg
                    } for ann in announcements
                ]
                return jsonify(result)

        @self.app.route('/announcements/<int:announcement_id>', methods=['PUT', 'DELETE'])
        def handle_single_announcement(announcement_id):
            announcement = self.Announcements.query.get_or_404(announcement_id)
            if request.method == 'PUT':
                data = request.json
                announcement.title = data.get('title', announcement.title)
                announcement.content = data.get('content', announcement.content)
                if 'published_date' in data:
                    announcement.published_date = datetime.fromisoformat(data['published_date'])
                announcement.author_id = data.get('author_id', announcement.author_id)
                announcement.tag = data.get('tag', announcement.tag)
                
                tag_colors = {
                    'สำคัญ': {'color': '#1976d2', 'bg': '#e3f2fd'},
                    'กิจกรรม': {'color': '#2e7d32', 'bg': '#e8f5e8'},
                    'แจ้งเตือน': {'color': '#856404', 'bg': '#fff3cd'}
                }
                tag_info = tag_colors.get(announcement.tag, {'color': '#666', 'bg': '#eee'})
                announcement.tag_color = tag_info['color']
                announcement.tag_bg = tag_info['bg']

                self.db.session.commit()
                author_name = announcement.author.name if announcement.author else 'Unknown Author'
                self.socketio.emit('announcement_updated', {
                    'announcement_id': announcement.announcement_id,
                    'title': announcement.title,
                    'content': announcement.content,
                    'published_date': announcement.published_date.isoformat(),
                    'author_id': announcement.author_id,
                    'author_name': author_name, # New: Include author name
                    'tag': announcement.tag,
                    'tag_color': announcement.tag_color,
                    'tag_bg': announcement.tag_bg
                }, broadcast=True)
                return jsonify({"message": "Announcement updated successfully"}), 200
            
            elif request.method == 'DELETE':
                self.db.session.delete(announcement)
                self.db.session.commit()
                self.socketio.emit('announcement_deleted', {'announcement_id': announcement_id}, broadcast=True)
                return jsonify({"message": "Announcement deleted successfully"}), 204

        @self.app.route('/repair-requests', methods=['GET', 'POST'])
        def manage_repair_requests():
            if request.method == 'POST':
                data = request.json
                new_request = self.RepairRequests(
                    user_id=data['user_id'],
                    title=data['title'],
                    category=data['category'],
                    description=data['description'],
                    status='pending',
                    image_paths=data.get('image_paths')
                )
                self.db.session.add(new_request)
                self.db.session.commit()
                
                user_name = new_request.user.name if new_request.user else 'Unknown User'
                self.socketio.emit('new_repair_request', {
                    'request_id': new_request.request_id,
                    'user_id': new_request.user_id,
                    'user_name': user_name, # New: Include user name
                    'title': new_request.title,
                    'status': new_request.status,
                    'submitted_date': new_request.submitted_date.isoformat()
                }, room='admins')
                return jsonify({"message": "Repair request submitted successfully", "request_id": new_request.request_id}), 201
            
            elif request.method == 'GET':
                requests = self.RepairRequests.query.all()
                result = []
                for req in requests:
                    user = req.user # Use relationship
                    result.append({
                        "request_id": req.request_id,
                        "user_id": req.user_id,
                        "user_name": user.name if user else "Unknown User",
                        "title": req.title,
                        "category": req.category,
                        "description": req.description,
                        "status": req.status,
                        "submitted_date": req.submitted_date.isoformat(),
                        "image_paths": req.image_paths
                    })
                return jsonify(result)

        @self.app.route('/repair-requests/<int:request_id>', methods=['PUT', 'DELETE'])
        def handle_single_repair_request(request_id):
            req = self.RepairRequests.query.get_or_404(request_id)
            if request.method == 'PUT':
                data = request.json
                req.title = data.get('title', req.title)
                req.category = data.get('category', req.category)
                req.description = data.get('description', req.description)
                req.status = data.get('status', req.status)
                req.image_paths = data.get('image_paths', req.image_paths)
                self.db.session.commit()
                
                self.socketio.emit('repair_status_updated', {
                    'request_id': req.request_id,
                    'user_id': req.user_id,
                    'status': req.status,
                    'title': req.title
                }, room=f'user_{req.user_id}') # Emit to specific user room
                
                return jsonify({"message": "Repair request updated successfully"}), 200
            elif request.method == 'DELETE':
                self.db.session.delete(req)
                self.db.session.commit()
                return jsonify({"message": "Repair request deleted successfully"}), 204

        @self.app.route('/booking-requests', methods=['GET', 'POST'])
        def manage_booking_requests():
            if request.method == 'POST':
                data = request.json
                new_booking = self.BookingRequests(
                    user_id=data['user_id'],
                    location=data['location'],
                    date=datetime.fromisoformat(data['date']).date(),
                    start_time=datetime.fromisoformat(data['start_time']).time(),
                    end_time=datetime.fromisoformat(data['end_time']).time(),
                    purpose=data.get('purpose'),
                    attendee_count=data.get('attendee_count'),
                    status='pending'
                )
                self.db.session.add(new_booking)
                self.db.session.commit()
                
                user_name = new_booking.user.name if new_booking.user else 'Unknown User'
                self.socketio.emit('new_booking_request', {
                    'booking_id': new_booking.booking_id,
                    'user_id': new_booking.user_id,
                    'user_name': user_name, # New: Include user name
                    'location': new_booking.location,
                    'status': new_booking.status
                }, room='admins')
                return jsonify({"message": "Booking request submitted successfully", "booking_id": new_booking.booking_id}), 201
            
            elif request.method == 'GET':
                bookings = self.BookingRequests.query.all()
                result = []
                for booking in bookings:
                    user = booking.user # Use relationship
                    result.append({
                        "booking_id": booking.booking_id,
                        "user_id": booking.user_id,
                        "user_name": user.name if user else "Unknown User",
                        "location": booking.location,
                        "date": booking.date.isoformat(),
                        "start_time": booking.start_time.isoformat(),
                        "end_time": booking.end_time.isoformat(),
                        "purpose": booking.purpose,
                        "attendee_count": booking.attendee_count,
                        "status": booking.status
                    })
                return jsonify(result)

        @self.app.route('/booking-requests/<int:booking_id>', methods=['PUT', 'DELETE'])
        def handle_single_booking_request(booking_id):
            booking = self.BookingRequests.query.get_or_404(booking_id)
            if request.method == 'PUT':
                data = request.json
                booking.location = data.get('location', booking.location)
                booking.date = datetime.fromisoformat(data['date']).date() if 'date' in data else booking.date
                booking.start_time = datetime.fromisoformat(data['start_time']).time() if 'start_time' in data else booking.start_time
                booking.end_time = datetime.fromisoformat(data['end_time']).time() if 'end_time' in data else booking.end_time
                booking.purpose = data.get('purpose', booking.purpose)
                booking.attendee_count = data.get('attendee_count', booking.attendee_count)
                booking.status = data.get('status', booking.status)
                self.db.session.commit()
                
                self.socketio.emit('booking_status_updated', {
                    'booking_id': booking.booking_id,
                    'user_id': booking.user_id,
                    'status': booking.status,
                    'location': booking.location
                }, room=f'user_{booking.user_id}')
                return jsonify({"message": "Booking request updated successfully"}), 200
            elif request.method == 'DELETE':
                self.db.session.delete(booking)
                self.db.session.commit()
                return jsonify({"message": "Booking request deleted successfully"}), 204

        @self.app.route('/bills', methods=['GET', 'POST']) # New: Bills API
        def manage_bills():
            if request.method == 'POST':
                data = request.json
                new_bill = self.Bills(
                    item_name=data['item_name'],
                    amount=data['amount'],
                    due_date=datetime.fromisoformat(data['due_date']).date(),
                    recipient_id=data.get('recipient_id', 'all'),
                    issued_by_user_id=data['issued_by_user_id'],
                    status='unpaid'
                )
                self.db.session.add(new_bill)
                self.db.session.commit()

                # Emit SocketIO event for new bill
                self.socketio.emit('new_bill_created', {
                    'bill_id': new_bill.bill_id,
                    'item_name': new_bill.item_name,
                    'amount': str(new_bill.amount),
                    'due_date': new_bill.due_date.isoformat(),
                    'recipient_id': new_bill.recipient_id,
                    'status': new_bill.status
                }, broadcast=True) # Broadcast to all relevant users (admins, specific recipient)
                return jsonify({"message": "Bill created successfully", "bill_id": new_bill.bill_id}), 201
            
            elif request.method == 'GET':
                bills = self.Bills.query.all()
                result = []
                for bill in bills:
                    issued_by_user = bill.issued_by
                    result.append({
                        "bill_id": bill.bill_id,
                        "item_name": bill.item_name,
                        "amount": str(bill.amount),
                        "due_date": bill.due_date.isoformat(),
                        "recipient_id": bill.recipient_id,
                        "issued_by_user_id": bill.issued_by_user_id,
                        "issued_by_user_name": issued_by_user.name if issued_by_user else "Unknown",
                        "status": bill.status
                    })
                return jsonify(result)

        @self.app.route('/bills/<int:bill_id>', methods=['PUT', 'DELETE']) # New: Bills API
        def handle_single_bill(bill_id):
            bill = self.Bills.query.get_or_404(bill_id)
            if request.method == 'PUT':
                data = request.json
                bill.item_name = data.get('item_name', bill.item_name)
                bill.amount = data.get('amount', bill.amount)
                bill.due_date = datetime.fromisoformat(data['due_date']).date() if 'due_date' in data else bill.due_date
                bill.recipient_id = data.get('recipient_id', bill.recipient_id)
                bill.status = data.get('status', bill.status) # Allow status update, e.g., by admin
                self.db.session.commit()

                self.socketio.emit('bill_updated', {
                    'bill_id': bill.bill_id,
                    'item_name': bill.item_name,
                    'amount': str(bill.amount),
                    'status': bill.status
                }, broadcast=True)
                return jsonify({"message": "Bill updated successfully"}), 200
            elif request.method == 'DELETE':
                bill_name = bill.item_name # Store name before deleting
                self.db.session.delete(bill)
                self.db.session.commit()
                self.socketio.emit('bill_deleted', {'bill_id': bill_id, 'item_name': bill_name}, broadcast=True)
                return jsonify({"message": "Bill deleted successfully"}), 204

        @self.app.route('/payments', methods=['GET', 'POST'])
        def manage_payments():
            if request.method == 'POST':
                data = request.json
                new_payment = self.Payments(
                    user_id=data['user_id'],
                    bill_id=data.get('bill_id'), # New: Link to bill
                    amount=data['amount'],
                    payment_method=data.get('payment_method'),
                    status=data.get('status', 'pending'),
                    slip_path=data.get('slip_path')
                )
                self.db.session.add(new_payment)
                self.db.session.commit()

                user_name = new_payment.user.name if new_payment.user else 'Unknown User'
                self.socketio.emit('new_payment_receipt', {
                    'payment_id': new_payment.payment_id,
                    'user_id': new_payment.user_id,
                    'user_name': user_name, # New: Include user name
                    'amount': str(new_payment.amount),
                    'status': new_payment.status,
                    'bill_id': new_payment.bill_id # New: Include bill_id
                }, room='admins')
                return jsonify({"message": "Payment recorded successfully", "payment_id": new_payment.payment_id}), 201
            
            elif request.method == 'GET':
                # Allow filtering by user_id
                user_id = request.args.get('user_id')
                if user_id:
                    payments = self.Payments.query.filter_by(user_id=user_id).all()
                else:
                    payments = self.Payments.query.all()

                result = []
                for payment in payments:
                    user = payment.user
                    bill = payment.bill # New: Get bill info
                    result.append({
                        "payment_id": payment.payment_id,
                        "user_id": payment.user_id,
                        "user_name": user.name if user else "Unknown User",
                        "bill_id": payment.bill_id, # New: Include bill_id
                        "bill_item_name": bill.item_name if bill else None, # New: Include bill item name
                        "amount": str(payment.amount),
                        "payment_method": payment.payment_method,
                        "payment_date": payment.payment_date.isoformat(),
                        "status": payment.status,
                        "slip_path": payment.slip_path
                    })
                return jsonify(result)

        @self.app.route('/payments/approve/<int:payment_id>', methods=['PUT']) # New: Approve payment API
        def approve_payment(payment_id):
            payment = self.Payments.query.get_or_404(payment_id)
            data = request.json
            new_status = data.get('status', 'paid') # Default to 'paid'

            if new_status not in ['paid', 'rejected']:
                return jsonify({"message": "Invalid status for payment approval"}), 400

            payment.status = new_status
            if payment.bill: # If linked to a bill, update bill status
                payment.bill.status = new_status
            self.db.session.commit()

            self.socketio.emit('payment_approved', {
                'payment_id': payment.payment_id,
                'user_id': payment.user_id,
                'bill_id': payment.bill_id,
                'status': payment.status
            }, broadcast=True) # Broadcast to relevant users
            return jsonify({"message": f"Payment {payment_id} status updated to {new_status}"}), 200

        @self.app.route('/calendar-events', methods=['GET', 'POST'])
        def manage_calendar_events():
            if request.method == 'POST':
                data = request.json
                new_event = self.CalendarEvents(
                    event_name=data['event_name'],
                    event_date=datetime.fromisoformat(data['event_date']),
                    location=data.get('location'),
                    description=data.get('description')
                )
                self.db.session.add(new_event)
                self.db.session.commit()
                self.socketio.emit('new_calendar_event', {
                    'event_id': new_event.event_id,
                    'event_name': new_event.event_name,
                    'event_date': new_event.event_date.isoformat(),
                    'location': new_event.location
                }, broadcast=True)
                return jsonify({"message": "Calendar event created successfully", "event_id": new_event.event_id}), 201
            
            elif request.method == 'GET':
                events = self.CalendarEvents.query.all()
                result = [
                    {
                        "event_id": event.event_id,
                        "event_name": event.event_name,
                        "event_date": event.event_date.isoformat(),
                        "location": event.location,
                        "description": event.description
                    } for event in events
                ]
                return jsonify(result)

        @self.app.route('/documents', methods=['GET', 'POST'])
        def manage_documents():
            if request.method == 'POST':
                data = request.json
                new_doc = self.Documents(
                    document_name=data['document_name'],
                    file_path=data['file_path'],
                    uploaded_by_user_id=data['uploaded_by_user_id'],
                    category=data.get('category') # New: Add category
                )
                self.db.session.add(new_doc)
                self.db.session.commit()
                return jsonify({"message": "Document uploaded successfully", "document_id": new_doc.document_id}), 201
            
            elif request.method == 'GET':
                docs = self.Documents.query.all()
                result = []
                for doc in docs:
                    user = doc.uploaded_by
                    result.append({
                        "document_id": doc.document_id,
                        "document_name": doc.document_name,
                        "file_path": doc.file_path,
                        "uploaded_by_user_id": doc.uploaded_by_user_id,
                        "uploaded_by_user_name": user.name if user else "Unknown User",
                        "upload_date": doc.upload_date.isoformat(),
                        "category": doc.category # New: Include category
                    })
                return jsonify(result)

        @self.app.route('/documents/<int:document_id>', methods=['DELETE'])
        def delete_document(document_id):
            doc = self.Documents.query.get_or_404(document_id)
            self.db.session.delete(doc)
            self.db.session.commit()
            return jsonify({"message": "Document deleted successfully"}), 204

        @self.app.route('/security-visitors', methods=['GET', 'POST'])
        def manage_security_visitors():
            if request.method == 'POST':
                data = request.json
                new_visitor = self.SecurityVisitors(
                    user_id=data['user_id'],
                    name=data['name'],
                    phone=data.get('phone'),
                    visit_date=datetime.fromisoformat(data['visit_date']).date(),
                    visit_time=datetime.fromisoformat(data['visit_time']).time(),
                    purpose=data.get('purpose')
                )
                self.db.session.add(new_visitor)
                self.db.session.commit()
                
                user_name = new_visitor.user.name if new_visitor.user else 'Unknown User'
                self.socketio.emit('new_visitor_registered', {
                    'visitor_id': new_visitor.visitor_id,
                    'name': new_visitor.name,
                    'visit_date': new_visitor.visit_date.isoformat(),
                    'user_id': new_visitor.user_id,
                    'user_name': user_name # New: Include user name
                }, room='admins')
                return jsonify({"message": "Visitor registered successfully", "visitor_id": new_visitor.visitor_id}), 201
            
            elif request.method == 'GET':
                visitors = self.SecurityVisitors.query.all()
                result = [
                    {
                        "visitor_id": visitor.visitor_id,
                        "user_id": visitor.user_id,
                        "user_name": visitor.user.name if visitor.user else "Unknown User", # New: Include user name
                        "name": visitor.name,
                        "phone": visitor.phone,
                        "visit_date": visitor.visit_date.isoformat(),
                        "visit_time": visitor.visit_time.isoformat(),
                        "purpose": visitor.purpose
                    } for visitor in visitors
                ]
                return jsonify(result)

        @self.app.route('/security-incidents', methods=['GET', 'POST'])
        def manage_security_incidents():
            if request.method == 'POST':
                data = request.json
                new_incident = self.SecurityIncidents(
                    user_id=data['user_id'],
                    description=data['description'],
                    evidence_paths=data.get('evidence_paths')
                )
                self.db.session.add(new_incident)
                self.db.session.commit()
                
                user_name = new_incident.user.name if new_incident.user else 'Unknown User'
                self.socketio.emit('new_incident_reported', {
                    'incident_id': new_incident.incident_id,
                    'user_id': new_incident.user_id,
                    'user_name': user_name, # New: Include user name
                    'description': new_incident.description,
                    'reported_date': new_incident.reported_date.isoformat()
                }, room='admins')
                return jsonify({"message": "Incident reported successfully", "incident_id": new_incident.incident_id}), 201
            
            elif request.method == 'GET':
                incidents = self.SecurityIncidents.query.all()
                result = [
                    {
                        "incident_id": inc.incident_id,
                        "user_id": inc.user_id,
                        "user_name": inc.user.name if inc.user else "Unknown User", # New: Include user name
                        "description": inc.description,
                        "reported_date": inc.reported_date.isoformat(),
                        "evidence_paths": inc.evidence_paths
                    } for inc in incidents
                ]
                return jsonify(result)

        @self.app.route('/voting-polls', methods=['GET', 'POST'])
        def manage_voting_polls():
            if request.method == 'POST':
                data = request.json
                new_poll = self.VotingPolls(
                    title=data['title'],
                    description=data.get('description'),
                    start_date=datetime.fromisoformat(data['start_date']).date(),
                    end_date=datetime.fromisoformat(data['end_date']).date()
                )
                self.db.session.add(new_poll)
                self.db.session.commit()
                
                # Add options if provided
                if 'options' in data and isinstance(data['options'], list):
                    for option_text in data['options']:
                        new_option = self.VotingOptions(poll_id=new_poll.poll_id, option_text=option_text)
                        self.db.session.add(new_option)
                    self.db.session.commit()

                return jsonify({"message": "Voting poll created successfully", "poll_id": new_poll.poll_id}), 201
            
            elif request.method == 'GET':
                polls = self.VotingPolls.query.all()
                result = []
                for poll in polls:
                    options = self.VotingOptions.query.filter_by(poll_id=poll.poll_id).all()
                    total_votes = self.VotingResults.query.filter_by(poll_id=poll.poll_id).count()
                    
                    options_data = []
                    for option in options:
                        vote_count = self.VotingResults.query.filter_by(option_id=option.option_id).count()
                        options_data.append({
                            "option_id": option.option_id,
                            "option_text": option.option_text,
                            "vote_count": vote_count
                        })

                    result.append({
                        "poll_id": poll.poll_id,
                        "title": poll.title,
                        "description": poll.description,
                        "start_date": poll.start_date.isoformat(),
                        "end_date": poll.end_date.isoformat(),
                        "options": options_data, # New: Include options and their counts
                        "total_votes": total_votes # New: Include total votes
                    })
                return jsonify(result)

        @self.app.route('/voting-options', methods=['POST'])
        def add_voting_option():
            data = request.json
            new_option = self.VotingOptions(
                poll_id=data['poll_id'],
                option_text=data['option_text']
            )
            self.db.session.add(new_option)
            self.db.session.commit()
            return jsonify({"message": "Voting option added successfully", "option_id": new_option.option_id}), 201

        @self.app.route('/voting-results', methods=['GET', 'POST'])
        def manage_voting_results():
            if request.method == 'POST':
                data = request.json
                # Check if user already voted in this poll
                existing_vote = self.VotingResults.query.filter_by(
                    poll_id=data['poll_id'],
                    user_id=data['user_id']
                ).first()
                if existing_vote:
                    return jsonify({"message": "You have already voted in this poll."}), 409

                new_result = self.VotingResults(
                    poll_id=data['poll_id'],
                    option_id=data['option_id'],
                    user_id=data['user_id']
                )
                self.db.session.add(new_result)
                self.db.session.commit()
                return jsonify({"message": "Vote recorded successfully", "result_id": new_result.result_id}), 201
            
            elif request.method == 'GET':
                results = self.VotingResults.query.all()
                result = [
                    {
                        "result_id": res.result_id,
                        "poll_id": res.poll_id,
                        "option_id": res.option_id,
                        "user_id": res.user_id
                    } for res in results
                ]
                return jsonify(result)
        
        @self.app.route('/chat-messages', methods=['GET'])
        def get_chat_messages():
            """API to get historical chat messages."""
            messages = self.ChatMessages.query.order_by(self.ChatMessages.timestamp.asc()).all()
            result = []
            for msg in messages:
                sender_user = msg.sender
                sender_name = sender_user.name if sender_user else 'Unknown User'
                sender_avatar = sender_user.avatar if sender_user else (sender_name[0].upper() if sender_name else '?')
                result.append({
                    'message_id': msg.message_id,
                    'sender_id': msg.sender_id,
                    'sender_name': sender_name,
                    'sender_avatar': sender_avatar,
                    'content': msg.content,
                    'timestamp': msg.timestamp.isoformat(),
                    'room_name': msg.room_name
                })
            return jsonify(result)

    def _setup_socketio_events(self):
        """
        Defines the SocketIO event handlers.
        """
        @self.socketio.on('connect')
        def handle_connect():
            print(f'Client {request.sid} connected')
            # A client can join their specific user room for notifications
            # and general chat room. Admin clients can join 'admins' room.
            # This logic should ideally be tied to authentication.
            # For now, assuming client sends user_id and role after connect.

        @self.socketio.on('disconnect')
        def handle_disconnect():
            print(f'Client {request.sid} disconnected')

        @self.socketio.on('send_message')
        def handle_send_message(data):
            sender_id = data.get('sender_id')
            content = data.get('content')
            room_name = data.get('room_name', 'general_chat')

            if not sender_id or not content:
                emit('error', {'message': 'Missing sender_id or content'})
                return

            try:
                new_message = self.ChatMessages(
                    sender_id=sender_id,
                    content=content,
                    room_name=room_name
                )
                self.db.session.add(new_message)
                self.db.session.commit()

                sender_user = self.Users.query.get(sender_id)
                sender_name = sender_user.name if sender_user else 'Unknown User'
                sender_avatar = sender_user.avatar if sender_user else (sender_name[0].upper() if sender_name else '?')

                message_payload = {
                    'message_id': new_message.message_id,
                    'sender_id': new_message.sender_id,
                    'sender_name': sender_name,
                    'sender_avatar': sender_avatar,
                    'content': new_message.content,
                    'timestamp': new_message.timestamp.isoformat(),
                    'room_name': new_message.room_name
                }
                
                self.socketio.emit('receive_message', message_payload, room=room_name)
            except Exception as e:
                self.db.session.rollback()
                print(f"Error saving message: {e}")
                emit('error', {'message': 'Failed to send message'})

        @self.socketio.on('join_chat_room')
        def handle_join_chat_room(data):
            room_name = data.get('room_name')
            if room_name:
                join_room(room_name)
                print(f"Client {request.sid} joined room: {room_name}")
                emit('status', {'msg': f'Joined {room_name}'}, room=request.sid)

        @self.socketio.on('leave_chat_room')
        def handle_leave_chat_room(data):
            room_name = data.get('room_name')
            if room_name:
                leave_room(room_name)
                print(f"Client {request.sid} left room: {room_name}")
                emit('status', {'msg': f'Left {room_name}'}, room=request.sid)
        
        # New: Event for clients to join their personal user room
        @self.socketio.on('join_user_room')
        def handle_join_user_room(data):
            user_id = data.get('user_id')
            if user_id:
                room_name = f'user_{user_id}'
                join_room(room_name)
                print(f"Client {request.sid} joined user room: {room_name}")
                emit('status', {'msg': f'Joined personal room {room_name}'}, room=request.sid)

    def run(self):
        """
        Runs the Flask application with SocketIO.
        """
        with self.app.app_context():
            self.db.create_all() # ตรวจสอบและสร้างตารางหากยังไม่มี
            
            # Initial dummy users for testing
            if not self.Users.query.filter_by(username='admin').first():
                admin_user = self.Users(name='Admin User', username='admin', role='admin', email='admin@example.com', avatar='A', status='approved')
                admin_user.set_password('admin123')
                self.db.session.add(admin_user)
                self.db.session.commit()
                print("Admin user created: username='admin', password='admin123'")
            
            if not self.Users.query.filter_by(username='resident').first():
                resident_user = self.Users(name='Resident User', username='resident', role='resident', email='resident@example.com', avatar='R', status='approved')
                resident_user.set_password('resident123')
                self.db.session.add(resident_user)
                self.db.session.commit()
                print("Resident user created: username='resident', password='resident123'")
                
        self.socketio.run(self.app, host='0.0.0.0', port=5000, debug=True)

if __name__ == '__main__':
    # Instantiate and run the SmartVillageApp
    smart_village_app = SmartVillageApp()
    smart_village_app.run()


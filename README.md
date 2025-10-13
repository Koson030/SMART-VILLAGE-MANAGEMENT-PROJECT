Smart Village Management System

📋 คำอธิบายโปรเจค
Smart Village Management System เป็นระบบจัดการหมู่บ้านจัดสรรออนไลน์แบบครบวงจร ออกแบบมาเพื่อช่วยให้ผู้อยู่อาศัยและผู้ดูแลระบบสามารถจัดการข้อมูล การแจ้งซ่อม การจองพื้นที่ส่วนกลาง การชำระเงิน และประกาศข่าวสารได้อย่างสะดวกรวดเร็ว พร้อมระบบแจ้งเตือนแบบเรียลไทม์ผ่าน WebSocket
ระบบนี้พัฒนาขึ้นเพื่อแก้ไขปัญหาการจัดการหมู่บ้านแบบดั้งเดิมที่ใช้กระดาษและการติดต่อสื่อสารที่ไม่มีประสิทธิภาพ โดยนำเทคโนโลยีเว็บแอปพลิเคชันสมัยใหม่มาประยุกต์ใช้ รองรับการเข้าถึงได้ทั้งมือถือและเดสก์ท็อป

✨ คุณสมบัติหลัก
สำหรับผู้ใช้งานทั่วไป (Resident)

🔐 ระบบล็อกอินที่ปลอดภัย - Authentication พร้อมการจัดการ Session
📢 ดูประกาศและข่าวสาร - อัปเดตข้อมูลจากนิติบุคคลแบบเรียลไทม์
🔧 แจ้งซ่อม - สร้างคำขอซ่อมพร้อมอัปโหลดรูปภาพประกอบ ติดตามสถานะงาน
📅 จองพื้นที่ส่วนกลาง - จองห้องประชุม, สนามกีฬา, คลับเฮ้าส์ พร้อมระบบตรวจสอบเวลาทับซ้อน
💰 ดูและชำระบิล - ตรวจสอบค่าใช้จ่าย อัปโหลดสลิปการชำระเงิน
🔔 แจ้งเตือนแบบเรียลไทม์ - รับการอัปเดตสถานะต่างๆ ทันที

สำหรับผู้ดูแลระบบ (Admin)

👥 จัดการผู้อยู่อาศัย - เพิ่ม/แก้ไข/ลบข้อมูลผู้ใช้
📝 จัดการประกาศ - สร้าง/แก้ไข/ลบประกาศพร้อมระบบแท็กและหมวดหมู่
⚙️ จัดการคำขอซ่อม - อัปเดตสถานะ (รอรับเรื่อง/กำลังดำเนินการ/เสร็จสิ้น)
🏢 จัดการการจองพื้นที่ - อนุมัติ/ปฏิเสธการจอง
💳 จัดการบิลและการชำระเงิน - สร้างบิล, อนุมัติ/ปฏิเสธการชำระเงิน
📊 แดชบอร์ดสถิติ - ภาพรวมผู้ใช้, งานซ่อมค้าง, บิลค้างชำระ พร้อมกราฟ


🛠️ เทคโนโลジีที่ใช้
Backend

Python 3.8+ - ภาษาหลักสำหรับ Backend
Flask - Web Framework
Flask-SQLAlchemy - ORM สำหรับจัดการฐานข้อมูล
Flask-SocketIO - WebSocket สำหรับ Real-time Communication
Werkzeug - Security และ Password Hashing

Frontend

HTML5 - โครงสร้างหน้าเว็บ
CSS3 - Responsive Design ใช้งานได้ทุกอุปกรณ์
Vanilla JavaScript - Logic และ API Calls (OOP Pattern)
Chart.js - แสดงผลกราฟและสถิติ
Font Awesome - ไอคอนสวยงาม

Database

SQLite - ฐานข้อมูลไฟล์เดียว (smart_village.db) เหมาะสำหรับ Development

อื่นๆ

Flask-CORS - รองรับ Cross-Origin Requests
Socket.IO - Real-time Bidirectional Communication
UUID - สร้าง Unique Identifiers


📦 การติดตั้งและรันโปรเจค
ข้อกำหนดเบื้องต้น

Python 3.8 ขึ้นไป (พร้อม pip)
Web Browser (แนะนำ Chrome หรือ Firefox)
Git (สำหรับ Clone โปรเจค)

ขั้นตอนการติดตั้ง
1. Clone โปรเจค
bash git clone [https://github.com/yourusername/smart-village.git](https://github.com/csongph/SMART-VILLAGE-MANAGEMENT-PROJECT.git)
cd smart-village
2. ติดตั้ง Dependencies
สร้างไฟล์ requirements.txt:
textFlask==2.3.3
Flask-SQLAlchemy==3.0.5
Flask-CORS==4.0.0
Flask-SocketIO==5.3.6
Werkzeug==2.3.7
python-socketio==5.8.0
requests==2.31.0
pytest==7.4.3
pytest-html==4.1.1
จากนั้นรันคำสั่ง:
bashpip install -r requirements.txt
3. รัน Backend Server
bashpython app.py

ระบบจะสร้างฐานข้อมูล smart_village.db อัตโนมัติ
เซิร์ฟเวอร์จะรันที่ http://localhost:5000
ถ้าเห็นข้อความ "Smart Village Backend is running!" แสดงว่าติดตั้งสำเร็จ

4. เปิด Frontend
เปิดเบราว์เซอร์และไปที่:
http://localhost:5000
หรือเปิดไฟล์ index.html โดยตรง (แต่แนะนำใช้ผ่าน Server เพื่อให้ Socket.IO ทำงานได้ปกติ)

👤 บัญชีเริ่มต้น (Default Users)
บทบาทUsernamePasswordสิทธิ์การใช้งานAdminadminadmin123สิทธิ์เต็มรูปแบบ (จัดการทุกอย่าง)Residentresidentresident123สิทธิ์ผู้อยู่อาศัย (ใช้งานบริการ)

⚠️ หมายเหตุ: กรุณาเปลี่ยนรหัสผ่านเริ่มต้นทันทีเมื่อใช้งานจริง


📁 โครงสร้างโปรเจค
smart-village/
├── app.py                    # Backend API (Flask + SocketIO)
├── smart_village.db          # ฐานข้อมูล SQLite (สร้างอัตโนมัติ)
├── requirements.txt          # Python Dependencies
├── README.md                 # เอกสารนี้
│
├── static/
│   ├── uploads/              # ไฟล์อัปโหลด (รูปภาพ/สลิปโอนเงิน)
│   ├── style.css             # CSS Styles (Responsive Design)
│   ├── script.js             # JavaScript Logic (OOP Pattern)
│   └── logo.png              # โลโก้โปรเจค (ถ้าม��)
│
├── templates/
│   └── index.html            # Frontend UI (Single Page Application)
│
└── tests/
    ├── test_backend.py       # Backend Unit/Integration Tests
    └── test_frontend.py      # Frontend UI Tests (Selenium)

🚀 การใช้งาน
1. ล็อกอินเข้าสู่ระบบ

เข้าไปที่หน้า Login
เลือกบัญชี Admin หรือ Resident
หลังจากล็อกอินสำเร็จ จะเห็นเมนู Sidebar ตามสิทธิ์ของผู้ใช้

2. หน้าหลัก (Dashboard)
สำหรับ Admin:

แสดงสถิติภาพรวม: จำนวนผู้อยู่อาศัย, งานซ่อมค้าง, บิลค้างชำระ
กราฟแสดงข้อมูลสถิติ
กิจกรรมล่าสุดในระบบ

สำหรับ Resident:

ประกาศและข่าวสารล่าสุด
สถานะงานซ่อมของตัวเอง
บิลค้างชำระ

3. การใช้งานฟีเจอร์หลัก
📢 ประกาศและข่าวสาร

Admin: สร้าง/แก้ไข/ลบประกาศ พร้อมเลือกหมวดหมู่และสีแท็ก
Resident: ดูและค้นหาประกาศทั้งหมด

🔧 แจ้งซ่อม

Resident: สร้างคำขอซ่อม + อัปโหลดรูปภาพประกอบ (ถ้ามี)
Admin: ดูคำขอทั้งหมด อัปเดตสถานะ (รอรับเรื่อง → กำลังดำเนินการ → เสร็จสิ้น)
ทั้งสองฝ่าย: รับการแจ้งเตือนเมื่อสถานะเปลี่ยนแปลง

📅 จองพื้นที่

เลือกสถานที่ (ห้องประชุม/สนาม/คลับเฮ้าส์)
เลือกวันที่และช่วงเวลา
ระบบจะตรวจสอบการทับซ้อนอัตโนมัติ

💰 ชำระเงิน

Resident: ดูบิลค้างชำระ → อัปโหลดสลิปโอนเงิน (PromptPay/ธนาคาร)
Admin: อนุมัติหรือปฏิเสธการชำระเงิน

👥 จัดการผู้ใช้ (Admin เท่านั้น)

เพิ่มผู้อยู่อาศัยใหม่
แก้ไขข้อมูลผู้ใช้
ลบผู้ใช้ออกจากระบบ

4. Real-time Features (WebSocket)

การแจ้งเตือนอัปเดตสถานะต่างๆ แบบเรียลไทม์
รองรับการเชื่อมต่อหลายผู้ใช้พร้อมกัน
ไม่ต้อง Refresh หน้าเพื่อดูข้อมูลใหม่


🧪 การทดสอบ
Backend Tests (Pytest)
bashpytest tests/test_backend.py -v --html=report.html --self-contained-html
ครอบคลุม:

Authentication & Authorization
User Management
Announcements CRUD
Repair Requests
Bookings System
Bills & Payments
File Upload Security

รายงานผล: ดูไฟล์ report.html
Frontend Tests (Selenium)
bash# ต้องรัน Backend Server ก่อน
pip install selenium

Network

ถ้าพอร์ต 5000 ถูกใช้งานอยู่ ให้แก้ไขใน app.py:

pythonsocketio.run(app, host='0.0.0.0', port=8080, debug=True)

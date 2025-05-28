# Chat Bot Database Integration

This document explains the SQLite database integration for your chat bot application, designed specifically for vehicle insurance claims and roadside assistance cases.

## 🗄️ Database Structure

The database consists of 6 main tables that store all chat and case information:

### 1. **chat_sessions**
Stores information about each chat session:
- `session_id` (TEXT PRIMARY KEY): Unique identifier for each chat session
- `customer_name` (TEXT): Customer's name
- `registration_number` (TEXT): Vehicle registration number
- `started_at` (TIMESTAMP): When the session started
- `ended_at` (TIMESTAMP): When the session ended
- `status` (TEXT): 'active' or 'ended'

### 2. **chat_messages**
Stores all chat messages:
- `id` (INTEGER PRIMARY KEY): Auto-incrementing message ID
- `session_id` (TEXT): Links to chat_sessions
- `sender` (TEXT): 'user' or 'assistant'
- `message` (TEXT): The actual message content
- `timestamp` (TIMESTAMP): When the message was sent

### 3. **cases**
Main case information (based on your requirements):
- `id` (INTEGER PRIMARY KEY): Auto-incrementing case ID
- `session_id` (TEXT): Links to chat_sessions
- `case_type` (TEXT): 'AC' (Accident Care), 'RA' (Road Assistance), or 'OTHER'
- `registration_number` (TEXT): Vehicle registration
- `customer_name` (TEXT): Customer name
- `description` (TEXT): Case description
- `location` (TEXT): Where the incident occurred
- `final_destination` (TEXT): Where the vehicle needs to go

### 4. **case_analysis**
Inferred data that the chatbot should derive:
- `case_id` (INTEGER): Links to cases
- `possible_vehicle_malfunction` (TEXT): What might be wrong
- `possible_problem_resolution` (TEXT): How to fix it
- `recommended_auto_repair_shop` (TEXT): Where to take the vehicle
- `is_destination_within_prefecture` (BOOLEAN): Location analysis

### 5. **case_flags**
Critical decision flags:
- `case_id` (INTEGER): Links to cases
- `delay_voucher_used` (BOOLEAN): If customer waited >1 hour
- `geolocation_link_sent` (BOOLEAN): If location link was needed
- `sworn_declaration_needed` (BOOLEAN): If special declaration required
- `is_fast_track` (BOOLEAN): If case qualifies for 24h processing
- `is_fraud` (BOOLEAN): If fraud indicators detected

### 6. **case_summary**
Summary and metadata:
- `case_id` (INTEGER): Links to cases
- `communication_quality` (TEXT): How the interaction went
- `tags` (TEXT): JSON array of keywords
- `short_summary` (TEXT): 50-120 word summary

## 🚀 How to Use

### 1. **Installation**
No additional dependencies needed - SQLite comes with Python!

### 2. **Testing the Database**
Run the test script to see the database in action:
```bash
python test_database.py
```

### 3. **Starting the Application**
```bash
python app.py
```

### 4. **Using the Chat Interface**
- Visit `http://localhost:5000` for the main chat interface
- Visit `http://localhost:5000/admin` for the admin dashboard

## 📊 Admin Dashboard Features

The admin dashboard (`/admin` route) provides:

- **Real-time Statistics**: Total sessions, active sessions, customer info completion
- **Session List**: All chat sessions with customer details and status
- **Message History**: Click any session to view full conversation
- **Auto-refresh**: Updates every 30 seconds
- **Session Status**: Visual indicators for active/ended sessions

## 🔧 API Endpoints

### Chat Endpoints
- `GET /` - Main chat interface
- `GET /start_chat` - Initialize new chat session
- `POST /chat` - Send chat message
- `POST /end_session` - End current session

### Data Endpoints
- `GET /get_chat_history` - Get messages for session
- `GET /get_sessions` - Get all sessions (admin)
- `POST /create_case` - Create new case with information

### Admin Endpoints
- `GET /admin` - Admin dashboard interface

## 💡 Key Features

### 1. **Automatic Session Management**
- Each user gets a unique session ID
- Sessions persist across browser refreshes
- Conversation history is maintained in memory and database

### 2. **Intelligent Case Detection**
The system is designed to detect and categorize cases based on your requirements:

**AC (Accident Care) Cases:**
- Traffic accidents
- Vehicle damage while parked
- Collision incidents

**RA (Road Assistance) Cases:**
- Flat tires
- Running out of fuel
- Vehicle breakdowns

### 3. **Smart Flags and Analysis**
The database structure supports automatic detection of:
- **Fast Track Cases**: Rear-end collisions, parked vehicle damage
- **Fraud Indicators**: Suspicious patterns or relationships
- **Special Requirements**: Geolocation needs, sworn declarations

### 4. **Comprehensive Logging**
Every interaction is logged with:
- Timestamps
- Message content
- Session context
- User information

## 🔍 Database Queries Examples

### Get all active sessions:
```python
from database import ChatDatabase
db = ChatDatabase()
sessions = db.get_all_sessions()
active_sessions = [s for s in sessions if s['status'] == 'active']
```

### Get chat history for a session:
```python
messages = db.get_chat_history(session_id)
for msg in messages:
    print(f"{msg['sender']}: {msg['message']}")
```

### Create a complete case:
```python
# Create the main case
case_id = db.create_case(
    session_id=session_id,
    case_type="AC",
    registration_number="ABC-1234",
    customer_name="John Doe",
    description="Accident on highway",
    location="Highway A1",
    final_destination="Athens"
)

# Add analysis
db.update_case_analysis(
    case_id=case_id,
    malfunction="Rear damage",
    resolution="Towing required",
    repair_shop="Local Garage",
    within_prefecture=True
)

# Set flags
db.update_case_flags(
    case_id=case_id,
    fast_track=True,
    fraud=False
)
```

## 🛡️ Data Security

- All data is stored locally in SQLite
- No external database connections required
- Session data is isolated per user
- Admin dashboard requires server access

## 📈 Monitoring and Analytics

The database structure allows for:
- Response time analysis
- Case type distribution
- Customer satisfaction tracking
- Operational efficiency metrics
- Fraud detection patterns

## 🔧 Customization

You can easily extend the database by:
1. Adding new tables in `database.py`
2. Creating new endpoints in `app.py`
3. Updating the admin dashboard to show new data

## 🐛 Troubleshooting

**Database file not found?**
- The database file is created automatically on first run
- Default location: `chat_database.db` in the project root

**Session not persisting?**
- Make sure Flask sessions are enabled (secret key is set)
- Check browser cookies are enabled

**Admin dashboard not loading data?**
- Verify the `/get_sessions` endpoint is accessible
- Check browser console for JavaScript errors

## 📝 Next Steps

With this database integration, you can now:
1. Track all customer interactions
2. Build comprehensive case management
3. Generate reports and analytics
4. Implement advanced fraud detection
5. Create automated case routing
6. Build customer service dashboards

The foundation is in place for a full-featured customer service and case management system! 
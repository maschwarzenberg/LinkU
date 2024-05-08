from flask import Flask, redirect, render_template, request, session, url_for
from flask_socketio import SocketIO, emit, join_room, leave_room, send
import subprocess

app = Flask(__name__)
app.secret_key = "your_secret_key"
socketio = SocketIO(app)

# Example storage for rooms
rooms = {}  # key: room_name, value: field_of_study

@app.route('/chat')
def chat():
    username = session.get('username', 'Anonymous')
    field_of_study = session.get('field_of_study', None)
    if not field_of_study:
        return "You must specify your field of study to join a chat room.", 400

    available_rooms = {room: study for room, study in rooms.items() if study == field_of_study}
    return render_template('chat.html', username=username, rooms=available_rooms)

@socketio.on('join')
def on_join(data):
    username = data['username']
    room = data['room']
    if rooms.get(room) != session.get('field_of_study'):
        emit('error', {'msg': 'You cannot join this room.'})
        return
    join_room(room)
    emit('message', {'username': username, 'msg': f'{username} has entered the room.', 'room': room}, room=room)

@socketio.on('message')
def handle_message(data):
    username = data['username']
    msg = data['msg']
    room = data['room']
    emit('message', {'username': username, 'msg': msg}, room=room)

@app.route('/create_room', methods=['POST'])
def create_room():
    room_name = request.form['room_name']
    field_of_study = session.get('field_of_study')
    if not field_of_study:
        return "You must have a field of study to create a room.", 400
    rooms[room_name] = field_of_study
    return redirect('/chat')

# LinkedIn OAuth 2.0 configuration
CLIENT_ID = "77jbo7kk3f4e6o"
REDIRECT_URI = "http://localhost:5000/callback"
AUTHORIZATION_URL = "https://www.linkedin.com/oauth/v2/authorization"
SCOPES = ["profile"]

# Route for rendering the login template
@app.route("/login")
def login():
    session.clear()  # Clear all session data
    authorization_params = {
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": " ".join(SCOPES),
        "state": "your_state_parameter"  # Add CSRF protection
    }
    authorization_url = f"{AUTHORIZATION_URL}?{'&'.join([f'{key}={value}' for key, value in authorization_params.items()])}"
    return redirect(authorization_url)

@app.route("/callback")
def callback():
    # Handle the callback logic here
    # After successful authentication, redirect to the profile creation page
    return redirect("/profile")

@app.route("/profile", methods=["GET", "POST"])
def profile():
    if "profile_created" in session:
        return redirect("/profile_created")

    if request.method == "POST":
        username = request.form.get("username")  # New line to capture username
        field_of_study = request.form.get("field_of_study")
        academic_interests = request.form.get("academic_interests")
        career_goals = request.form.get("career_goals")

        session['username'] = username  # Store username in session
        session['field_of_study'] = field_of_study
        session['academic_interests'] = academic_interests
        session['career_goals'] = career_goals
        session["profile_created"] = True

        return redirect("/profile_created")

    return render_template("profile.html")

@app.route("/profile_created")
def profile_created():
    if not session.get("profile_created"):
        return redirect("/profile")

    username = session.get('username', "Unknown User")
    field_of_study = session.get("field_of_study", "Unknown field")
    return render_template("profile_created.html", username=username, field_of_study=field_of_study)

@app.route('/set_username', methods=['POST'])
def set_username():
    username = request.form.get('username')
    if username:  # Check if the username is provided
        session['username'] = username  # Store the username in session
        return redirect('/chat')  # Redirect to the chat page
    return "Please provide a valid username.", 400  # Return an error if no username


@app.route("/")
def index():
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login</title>
</head>
<body>
    <h1>Welcome to the login screen!</h1>
    <p>Please click the button below to log in with LinkedIn:</p>
    <form action="/login" method="get">
        <button type="submit">Log in with LinkedIn</button>
    </form>
</body>
</html>"""

if __name__ == "__main__":
    socketio.run(app, debug=True)

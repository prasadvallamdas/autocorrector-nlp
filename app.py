import pymysql  # Import pymysql
from flask import Flask, render_template, request, jsonify, flash,redirect,url_for, session
from spellchecker import SpellChecker
import speech_recognition as sr
from nltk.corpus import wordnet
from googletrans import Translator


# Initialize a translator instance
translator = Translator()


app = Flask(__name__, static_url_path='/static')
spell = SpellChecker()

# ... (your existing Flask app setup code) ...
# Database configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Durga.durga5',
    'db': 'my_database',
    'cursorclass': pymysql.cursors.DictCursor
}
connection = pymysql.connect(**db_config)
app.secret_key = 'teja@2002'


# A dictionary to simulate a simple user database
users = {
    'user1': 'password1',
    'user2': 'password2',
}
@app.route('/')
def main():
    # Redirect to the login page when users access the main URL
    return redirect('/login')

# Function to retrieve the user's unique identifier (user_id) based on their username
def get_user_id(username):
    try:
        connection = pymysql.connect(**db_config)
        with connection.cursor() as cursor:
            cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
            user_data = cursor.fetchone()

            if user_data:
                return user_data['id']
    except Exception as e:
        flash("An error occurred while processing your request.")
    
    return None

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # Check if the username already exists
        if user_exists(username):
            flash("Username already exists. Please choose a different username.")
        else:
            # If the username is not already taken, proceed with the signup process
            try:
                connection = pymysql.connect(**db_config)
                with connection.cursor() as cursor:
                    sql = "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)"
                    cursor.execute(sql, (username, email, password))
                    connection.commit()
                    user_id = cursor.lastrowid
                    session['user_id'] = user_id
                    return redirect('/login')
            except Exception as e:
                return str(e)
            finally:
                if connection:
                    connection.close()

    return render_template('signup.html')
# Function to check if a username already exists in the database
def user_exists(username):
    try:
        connection = pymysql.connect(**db_config)
        with connection.cursor() as cursor:
            cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
            user_data = cursor.fetchone()
            return user_data is not None
    except Exception as e:
        flash("An error occurred while processing your request.")
    finally:
        if connection:
            connection.close()
    return False


# Function to verify user credentials against the database
def verify_user(username, password):
    try:
        connection = pymysql.connect(**db_config)
        with connection.cursor() as cursor:
            cursor.execute("SELECT password FROM users WHERE username = %s", (username,))
            user_data = cursor.fetchone()

            if user_data:
                stored_password = user_data['password']
                if stored_password == password:
                    return True
            else:
                return False  # User not found
    except Exception as e:
        flash("An error occurred while processing your request.")
    finally:
        if connection:
            connection.close()

    return False

@app.route('/login', methods=['GET', 'POST'])
def login():
    username = None  # Initialize the username as None

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if verify_user(username, password):
            # Get the user's unique identifier (user_id) from your database
            user_id = get_user_id(username)  # You need to implement this function

            if user_id:
                # Store the user's unique identifier in the session
                session['user_id'] = user_id

                # Pass the username to the index page
                return redirect(url_for('index', username=username))

        # If the user is not authenticated, or if the user_id is not found, the login will fail.
        flash("Invalid username or password. Please try again.")

    return render_template('login.html')



def is_authenticated():
    return 'user_id' in session



@app.route('/')
def home():
    if is_authenticated():
        # If the user is authenticated, redirect to the index page
        return redirect('/index')
    else:
        # If the user is not authenticated, render the login page
        return render_template('login.html')

@app.route('/index')
def index():
    if is_authenticated():
        # Get the username from the URL parameter
        username = request.args.get('username')

        # If the user is authenticated, retrieve the username and pass it to the template
        return render_template('index.html', username=username)
    else:
        # If the user is not authenticated, redirect to the login page
        return redirect('/')

@app.route('/logout')
def logout():
    session.clear()  # Clear the user session
    return redirect('/login')  # Redirect to the login page after logout




# Function to save a shortcut to the database, associating it with the user_id
def save_shortcut_to_database(user_id, shortcut):
    try:
        connection = pymysql.connect(**db_config)
        with connection.cursor() as cursor:
            # Define the SQL statement to insert the shortcut into the database
            sql = "INSERT INTO shortcuts (user_id, shortcut, abbreviation) VALUES (%s, %s, %s)"
            
            # Execute the SQL statement
            cursor.execute(sql, (user_id, shortcut['shortcut'], shortcut['abbreviation']))

        # Commit the changes to the database
        connection.commit()
    except Exception as e:
        flash("An error occurred while saving the shortcut to the database.")
    finally:
        if connection:
            connection.close()


# Function to retrieve user shortcuts from the database
def getUserShortcutsFromDatabase(user_id):
    try:
        connection = pymysql.connect(**db_config)
        with connection.cursor() as cursor:
            sql = "SELECT shortcut, abbreviation FROM shortcuts WHERE user_id = %s"
            cursor.execute(sql, (user_id,))
            shortcuts = cursor.fetchall()
            return shortcuts
    except Exception as e:
        return []
    finally:
        if connection:
            connection.close()
@app.route('/save_shortcuts', methods=['POST'])
def save_shortcuts():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'message': 'User not authenticated'}), 401

    # Get the shortcuts data from the request
    data = request.get_json()
    shortcuts = data.get('shortcuts')

    if not shortcuts:
        return jsonify({'message': 'No shortcuts provided'}), 400

    # Now, you can save the shortcuts to your database, associating them with the user_id
    for shortcut in shortcuts:
        save_shortcut_to_database(user_id, shortcut)

    return jsonify({'message': 'Shortcuts saved successfully.'})

# API endpoint to retrieve shortcuts
@app.route('/get_shortcuts', methods=['GET'])
def get_shortcuts():
    user_id = session.get('user_id')  # Get the user's ID from the session

    if not user_id:
        return jsonify({'message': 'User not authenticated'}), 401

    shortcuts = getUserShortcutsFromDatabase(user_id)
    return jsonify(shortcuts)
# Function to translate text into English
def translate_to_english(text):
    try:
        # Detect the language of the input text
        detected_language = translator.detect(text).lang

        # If the detected language is not English, translate it to English
        if detected_language != 'en':
            translation = translator.translate(text, src=detected_language, dest='en')  # Translate to English
            return translation.text

        # If the detected language is already English, return the input text as is
        return text

    except Exception as e:
        return str(e)
def get_voice_input_and_translate():
    recognizer = sr.Recognizer()
    user_input = ""  # Initialize the variable here with an empty string
    with sr.Microphone() as source:
        print("Speak something:")
        try:
            audio = recognizer.listen(source, timeout=4)
            user_input = recognizer.recognize_google(audio)

            # Translate the spoken input to English
            translated_text = translate_to_english(user_input)

            return translated_text if translated_text != user_input else user_input

        except sr.WaitTimeoutError:
            print("Timeout: No speech detected")
            return text
        except sr.UnknownValueError:
            print("Error: Could not understand audio")
            return text
        except Exception as e:
            print("Error:", str(e))
            return ""




@app.route('/get_voice_input', methods=['GET'])
def get_voice_input_route():
    translated_or_original = get_voice_input_and_translate()
    return jsonify(translated_or_original)
  
# Function to check spelling using pyspellchecker
def check_spelling(word):
    return not spell.unknown([word])

# Function to generate suggestions and meanings based on pyspellchecker and WordNet
def generate_suggestions(word):
    suggestions = list(spell.candidates(word))  # Convert set to list
    valid_suggestions = []

    for suggestion in suggestions:
        if check_spelling(suggestion):  # Check if the suggestion is correctly spelled
            synsets = wordnet.synsets(suggestion)
            if synsets:
                valid_suggestions.append({
                    'word': suggestion,
                    'meaning': synsets[0].definition()
                })

    return valid_suggestions[:10] 

@app.route('/get_suggestions', methods=['GET'])
def get_suggestions():
    selected_word = request.args.get('word')
    suggestions = generate_suggestions(selected_word)
    return jsonify(suggestions)



if __name__ == "__main__":
    app.secret_key = 'teja@2002'
    app.run(debug=True)
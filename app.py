from flask import Flask, render_template, request, jsonify, session
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import re

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Needed for session storage

# Load AI Model
model_name = "google/gemma-3-1b-it"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)
pipe = pipeline("text-generation", model=model, tokenizer=tokenizer, max_new_tokens=100)

# Ensure session is initialized before each request
@app.before_request
def before_request():
    if "context" not in session:
        reset_game()

def reset_game():
    """Resets game state."""
    session["context"] = ["You wake up in a dark, mysterious forest after being transported through an unknown portal. The only way to survive is to find the portal and escape within 10 moves. Every action you take shapes your journey, and the AI will dynamically respond to your choices."]
    session["moves"] = 0
    session["game_over"] = False
    session["inventory"] = []  # Player inventory

def get_ai_response(player_input, context):
    """Generates a structured response using the AI model."""
    
    prompt = f"""
    You are an AI Game Master for the text-based adventure game 'Stranded on Xenon-5'.
    Provide immersive, game-relevant responses to player actions.
    
    Current Game Context:
    {' '.join(context[-5:])}
    
    Player Action: {player_input}
    
    Game AI Response:
    """

    raw_response = pipe(prompt)[0]['generated_text']

    # Remove the prompt text from the response
    response = raw_response.replace(prompt, "").strip()

    # Remove formatting artifacts and redundant instructions
    response = re.sub(r"```.*?```", "", response, flags=re.DOTALL)  # Remove triple backticks
    response = re.sub(r"Please respond as the AI Game Master.*?", "", response, flags=re.DOTALL)  # Remove instructions
    response = re.sub(r"Game AI Response:", "", response, flags=re.DOTALL)  # Remove redundant labels

    formatted_text = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", response)  # Format bold text

    return formatted_text


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start', methods=['POST'])
def start_game():
    """Starts the game."""
    reset_game()
    return jsonify({
        "response": "You wake up in a dark, mysterious forest after being transported through an unknown portal. The only way to survive is to find the portal and escape within 10 moves. Every action you take shapes your journey, and the AI will dynamically respond to your choices.",
        "options": ["Start Journey 🚀"]
    })


@app.route('/restart', methods=['POST'])
def restart_game():
    """Restarts the game."""
    reset_game()
    return jsonify({
        "response": "Game restarted! You wake up again in the mysterious forest. What do you do?",
        "options": ["Look around", "Search for clues", "Call for help"]
    })

@app.route('/chat', methods=['POST'])
def chat():
    """Handles player choices and game progression."""
    if session["game_over"]:
        return jsonify({"response": "Game Over! Restart to play again.", "game_over": True})

    player_input = request.json.get("player_input", "").strip()
    if not player_input:
        return jsonify({"error": "Choose an option!"})

    if player_input.lower() in ["quit", "exit"]:
        return jsonify({"response": "Game Over. Thanks for playing!", "game_over": True})

     # Game responses
    if "Search for the portal" in player_input:
        if session["moves"] < 5:  # Prevent instant win
            return jsonify({"response": "You look around, but the dense forest hides all signs of an exit. Maybe exploring further will help."})
        else:
            return jsonify({"response": "You stumble upon a faint glowing portal hidden between the trees! Without hesitation, you step through and escape. Congratulations!"})

    ai_response = get_ai_response(player_input, session["context"])
    session["context"] = [f"Player: {player_input}\nGame AI: {ai_response}"]

    session["moves"] += 1

    if "portal" in player_input.lower() and session["moves"] <= 10:
        session["game_over"] = True
        return jsonify({"response": "Congratulations! You found the portal and escaped the forest!", "game_over": True})

    if session["moves"] >= 10:
        session["game_over"] = True
        return jsonify({"response": ai_response + "\n\nGame Over! You failed to find the portal in 10 moves.", "game_over": True})

    return jsonify({
        "response": ai_response,
        "options": ["Search for the portal", "Look around", "Explore the forest", "Call for help"]
    })

@app.route('/quit', methods=['POST'])
def get_hint():
    """Provides a hint."""
    hint = get_ai_response("Give me a hint", session["context"])
    return jsonify({"response": f"Quit {hint}"})

@app.route('/inventory', methods=['POST'])
def inventory():
    """Manages the player's inventory."""
    return jsonify({"response": f"Your inventory: {', '.join(session['inventory']) if session['inventory'] else 'Empty'}"})

if __name__ == '__main__':
    app.run(debug=True)

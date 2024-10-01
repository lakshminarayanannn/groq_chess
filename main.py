import streamlit as st
import chess
import chess.svg
import chess.pgn
import base64
import os
import requests
import time
import logging
from chess_game import ChessGame
from ai_module import AIModule
from game_ui import GameUI

class Config:
    PAGE_TITLE = "♟️ Chess Game"
    PAGE_ICON = "static/favicon.ico"
    LAYOUT = "wide"
    MENU_ITEMS = {
        'About': "## Chess Game with AI\nDeveloped by [Groqlabs](https://wow.groq.com/groq-labs/)"
    }
    LOG_FILE = 'ai_responses.log'

def fetch_groq_models(api_key):
    url = "https://api.groq.com/openai/v1/models"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        models = [model['id'] for model in data.get('data', []) if model.get('active', False)]
        return models
    except requests.exceptions.RequestException as err:
        st.error(f"An error occurred: {err}")
    return None

def reset_app():
    keys_to_reset = ['game', 'ai_module', 'ui', 'logging_initialized']
    for key in keys_to_reset:
        if key in st.session_state:
            del st.session_state[key]
    st.experimental_rerun()

def main():
    st.set_page_config(
        page_title=Config.PAGE_TITLE,
        page_icon=Config.PAGE_ICON,
        layout=Config.LAYOUT,
        menu_items=Config.MENU_ITEMS
    )

    # Inject JavaScript to load API key from localStorage
    load_key_js = """
    <script>
        const apiKey = localStorage.getItem('groq_api_key');
        if (apiKey) {
            const streamlitApiKeyInput = window.parent.document.querySelectorAll('input[type="password"]')[0];
            streamlitApiKeyInput.value = apiKey;
            streamlitApiKeyInput.dispatchEvent(new Event('input', { bubbles: true }));
        }
    </script>
    """
    st.markdown(load_key_js, unsafe_allow_html=True)

    if 'api_key_set' not in st.session_state:
        st.session_state.api_key_set = False

    if not st.session_state.api_key_set:
        st.title("Welcome to the ♟️ Chess Game with AI")

        with st.form(key='api_key_form'):
            api_key = st.text_input("Enter your Groq API Key", type='password')
            submit_button = st.form_submit_button(label='Submit')

        if submit_button:
            if api_key.strip():
                # Store API key in localStorage using JavaScript
                store_key_js = f"""
                <script>
                    localStorage.setItem('groq_api_key', '{api_key.strip()}');
                </script>
                """
                st.markdown(store_key_js, unsafe_allow_html=True)

                st.session_state.api_key = api_key.strip()
                os.environ["GROQ_API_KEY"] = st.session_state.api_key
                st.session_state.api_key_set = True
                st.success("API Key set successfully! Proceeding to model selection...")
                st.experimental_rerun()
            else:
                st.error("Please enter a valid Groq API Key.")
        st.stop()

    if 'model_selected' not in st.session_state:
        st.session_state.model_selected = False

    if not st.session_state.model_selected:
        st.title("Select an AI Model")

        with st.spinner("Fetching available models..."):
            models = fetch_groq_models(st.session_state.api_key)

        if models is not None and len(models) > 0:
            with st.form(key='model_selection_form'):
                selected_model = st.selectbox("Choose a model", options=models)
                submit_model_button = st.form_submit_button(label='Select Model')

            if submit_model_button:
                st.session_state.selected_model = selected_model
                st.session_state.model_selected = True
                st.success(f"Model '{selected_model}' selected successfully! Starting the game...")
                st.experimental_rerun()
        else:
            st.error("No active models found or failed to fetch models.")
            st.stop()
        st.stop()

    selected_model = st.session_state.selected_model
    Config.GROQ_API_KEY = st.session_state.api_key

    if 'logging_initialized' not in st.session_state:
        logging.basicConfig(
            filename=Config.LOG_FILE,
            filemode='a',
            format='%(asctime)s - %(levelname)s - %(message)s',
            level=logging.INFO
        )
        st.session_state.logging_initialized = True

    if 'game' not in st.session_state:
        st.session_state.game = ChessGame(st)
    if 'ai_module' not in st.session_state:
        st.session_state.ai_module = AIModule(st, model=selected_model)
    if 'ui' not in st.session_state:
        st.session_state.ui = GameUI(st.session_state.game, st.session_state.ai_module, st)

    game = st.session_state.game
    ui = st.session_state.ui

    if not game.game_started:
        ui.initial_setup()
    else:
        if not game.game_over:
            ui.main_game()
            st.button("Reset Game Setup", on_click=reset_app)
        else:
            st.write("### 🏁 Game Over")
            st.write(f"**Result:** {game.result}")
            logging.info(f"Game Over: {game.result}")
            if st.button("Restart Game"):
                ui.reset_game()
                st.experimental_rerun()
            st.button("Reset Game Setup", on_click=reset_app)

if __name__ == "__main__":
    main()

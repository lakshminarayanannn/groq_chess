import base64
import os
def set_custom_css(self=None):
    self.st.markdown(
        """
        <style>
        /* Set the background color */
        body {
            background-color: #F5F5F5;
        }

        /* Header styling with Flexbox for vertical alignment */
        .header {
            background-color: #FFFFFF; /* White background */
            padding: 20px;
            text-align: center;
            color: black; /* Black text for readability */
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1); /* Subtle shadow for depth */
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
        }

        /* Hide the Sidebar */
        [data-testid="stSidebar"] {
            display: none;
        }

        /* Main content styling */
        .main .block-container {
            padding-top: 20px;
        }

        /* Button styling */
        .stButton>button {
            background-color: #FF6F00;
            color: white;
            border: none;
            padding: 8px 16px;
            margin: 4px 2px;
            cursor: pointer;
            border-radius: 4px; /* Rounded corners */
            font-weight: bold;
        }
        .stButton>button:hover {
            background-color: #E65100;
        }

        /* Move history table styling */
        .move-history-table {
            max-height: 300px; /* Increased max-height for better visibility */
            overflow-y: auto;
            margin-bottom: 20px;
            box-sizing: border-box; /* Include padding and border in element's total width and height */
            padding-bottom: 8px; /* Ensure bottom border is visible */
        }
        .move-history-table table {
            width: 100%;
            border-collapse: collapse;
            box-sizing: border-box;
        }
        .move-history-table th, .move-history-table td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: center;
        }
        .move-history-table th {
            background-color: #FFCC80;
        }

        /* AI suggestion styling */
        .suggestion-container {
            background-color: #FFF3E0;
            padding: 10px;
            margin-bottom: 10px;
            border-radius: 5px;
        }

        /* Font styling */
        body, h1, h2, h3, h4, h5, h6, p, div, input, label {
            font-family: 'Arial', sans-serif;
        }

        /* Small font for explanations */
        .small-font {
            font-size: 0.9em;
            color: #555;
        }

        /* Separator between suggestions */
        .suggestion-separator {
            margin: 10px 0;
            border-bottom: 1px solid #ddd;
        }

        /* Custom scrollbar for move-history-table */
        .move-history-table::-webkit-scrollbar {
            width: 8px;
        }

        .move-history-table::-webkit-scrollbar-track {
            background: #f1f1f1; 
        }
        
        .move-history-table::-webkit-scrollbar-thumb {
            background: #888; 
            border-radius: 4px;
        }

        .move-history-table::-webkit-scrollbar-thumb:hover {
            background: #555; 
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
def get_base64_image(image_path):
    """Encodes an image file to Base64."""
    try:
        with open(image_path, "rb") as image_file:
            encoded = base64.b64encode(image_file.read()).decode()
        return encoded
    except FileNotFoundError:
        return None

def display_header(self=None):
    """Displays the header with the logo and title."""
    logo_path = os.path.join("static", "logo.png")
    logo_base64 = get_base64_image(logo_path)

    if logo_base64:
        header_html = f"""
        <div class='header'>
            <img src="data:image/png;base64,{logo_base64}" width="200" alt="Logo">
            <h1>♟️ Chess Game</h1>
        </div>
        """
        self.st.markdown(header_html, unsafe_allow_html=True)
    else:
        # If logo is not found, display only the title with an error message
        header_html = """
        <div class='header'>
            <h1>♟️ Chess Game</h1>
            <p style="color: red;">Logo image not found.</p>
        </div>
        """
        self.st.markdown(header_html, unsafe_allow_html=True)


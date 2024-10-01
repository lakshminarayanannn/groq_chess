
# Chess Game with AI

This project allows you to play a chess game powered by Groq's LLM API for AI-based move suggestions. The project uses Streamlit for the web interface and integrates AI to enhance the chess playing experience.

## Prerequisites

Before running the project, ensure you have the following:

- Python 3.11.5 (the project has been tested with this version)
- Groq API key

## Setup

1. Set up your Groq API key as an environment variable:

   ```bash
   export GROQ_API_KEY=<YOUR_API_KEY>
   ```

   Replace `<YOUR_API_KEY>` with your actual Groq API key.

2. Create a virtual environment:

   ```bash
   python3 -m venv venv
   ```

3. Activate the virtual environment:

   ```bash
   source venv/bin/activate
   ```

4. Install the required dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

To run the application locally, use the following command:

```bash
streamlit run main.py --server.port 8080 --server.address 0.0.0.0
```

This command starts the Streamlit application and makes it accessible at `http://localhost:8080`.

## Usage

1. Launch the application by accessing `http://localhost:8080` in your web browser.
2. Enter your Groq API key, select an AI model, and start playing the chess game.

## Docker

To make it easier to run the application without setting up a local environment, you can use the pre-built Docker image.

### Docker Hub

You can pull the Docker image directly from Docker Hub:

- **Docker Hub Link**: [https://hub.docker.com/r/rlakshmin/gamify](https://hub.docker.com/r/rlakshmin/gamify)

### Pull the Docker Image

To pull the latest Docker image for this project, run the following command:

```bash
docker pull rlakshmin/gamify:latest
```

### Run the Application with Docker

To run the application using Docker, use the following command:

```bash
docker run -p 8501:8501 rlakshmin/gamify:latest
```

This command will run the application and expose it on port `8501`. You can then access the application in your web browser at `http://localhost:8501`.

## Features

### Current Features

- **AI Move Suggestions**: Get AI-powered suggestions for the next move during your gameplay.
- **AI vs AI**: Simulate battles between AI models to observe strategies and outcomes.
- **Human vs AI**: Play against the AI, enhancing your own strategy and understanding.
- **Timer Support**: Utilize a timer for more dynamic and time-sensitive gameplay, similar to traditional chess tournaments.

### Future Developments

1. **Score Prediction**: Real-time board evaluation in pawn units to show the balance of power between players.
2. **Winning Probability**: Dynamic calculation of each player's chances of winning based on the current game state.
3. **Blunder Detection**: Alerts players to critical mistakes and explains how the position has worsened, along with suggestions for improvement.
4. **Opening Explorer**: Provides success rates and insights into various openings based on historical data and similar game outcomes.

## Contributing

If you'd like to contribute to this project, please follow these steps:

1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Make your changes and commit them with descriptive commit messages.
4. Push your changes to your forked repository.
5. Submit a pull request to the main repository, explaining your changes and their benefits.

## Contact

If you have any questions or suggestions regarding this project, please feel free to contact the project maintainer at [neillakshmi@gmail.com](mailto:neillakshmi@gmail.com)

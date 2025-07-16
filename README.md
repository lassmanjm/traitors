# Traitors Moderator discord bot

This is a discord bot meant to moderate a game of traitors based on the show [Traitors (UK)](https://en.wikipedia.org/wiki/The_Traitors_(British_TV_series)). 
Includes ChatGPT powered features to enable unique and natural interactions with the host, Claudia!

## Setup
1) Create discord server where game will be played (instructions coming soon)
1) Create a discord bot with appropriate permissions and install in the server (instructions coming soon)
1) Launch the bot with one of the following methods:

## Launch the Bot
### Docker (reccomended)
Docker compose file:
```
services:
  traitors:
    image: lassmanjm/traitors:latest
    container_name: traitors
    env_file: ./.env
    volumes:
      - ${saved_game_directory}:/saved_games
    restart: unless-stopped
networks: {}
```
Replace the saved_game_directory variable with a path to your saved game folder.

Create a .env file in the same directory:
```
TRAITORS_SERVER_ID="{$server_id}"
TRAITORS_BOT_TOKEN="${bot_token}"
OPENAI_API_KEY="${openai_key}"
```
Replacing the server_id, bot_token, and openai_key (optional to enable ChatGPT features).

## Direct run:
1) Clone this repo
1) Create a python3 virtual environment (must be python3.12 or newer)
1) install the requirements.txt with pip
1) Run the claudia_bot python script: `python3 claudia_bot.py --bot_token="${TRAITORS_BOT_TOKEN}" --server_id="${TRAITORS_SERVER_ID}"`

## Game controls
Control the game through use of slash commands (type `/` and select a command), to start a new game, initiate a murder or banishment, and more!

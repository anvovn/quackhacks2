# Escape the EMU

Game created by An, Jared, Nate, and Gabe during Quackhacks 2 at the University of Oregon.

## How to play

The game excellently uses GitHub Codespaces in order to run the game on your own machine without needing to install docker!

1. Launch the codespace

2. Wait for it to setup and run ./game.sh (If it doesn't work chmod +x the file)

3. Before you click the url (http://127.0.0.1:5000/), go into the ports section next to terminal and set both ports to public

4. Now lauch the provided URL from the ./game.sh output (or the same one in step 3) and you are playing our game!

5. To stop and delete the docker image, simply execute the ./cleanup script with the flag s for stop and c for cleanup (delete)

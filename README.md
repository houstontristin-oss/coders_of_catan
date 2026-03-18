# coders_of_catan

Software Engineering Final Project - Recreating the board game Catan within python

Created by Tristin Houston, Amanda Barth, Apoorva Joshi, and Nicolas Fay

## State of the Game

#### Saturday 3/7/2026

Overall the game works through the "setup phase" and assumes 4 players will play the game. You are able to 

* run Catan 
* have a random board
* place starting settlements around the board with their adjacent road
* receive starting resources from your second settlement

The game loop aftewords can run through player turns but no resources are delt. This is not a fully functioning game.

## Coming Soon

Goals for next sprint are to get a complete game loop with

* random dice rolls and resources
* development cards
* trading with other players
* trading with bank and ports
* longest road victory points
* largest army victory points
* cities
* winning the game


## Setup

*Note: We recommend you use a virtual enviroment before installing dependencies*

* after extracting files from the zip, open a terminal in the coders_of_catan home directory
* run ```pip install -r requirements.txt```
* if this runs without errors then you can run the game by running in a terminal ```python main.py```(**Windows**) or ```python3 main.py```(**MacOS/Linux**)

## Build Help

#### if you run into trouble, make sure you have python and C++ Compilers installed on your machine

* Python, 
  * **Windows, MacOS**: install from the pyton install manager from the python website or the microsoft store
  * **Linux (Ubuntu/Debian)**: Update your repository and install using: 
    * ```sudo apt update``` 
    * ```sudo apt install python3```
* C++ Compilers, 
    * **Windows**: Download and install [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/) and during installation make sure the, **"Desktop development with C++"** workload is checked
    * **macOS**: Open your terminal and run ```xcode-select --install.```
    * **Linux (Ubuntu/Debian)**: Run ```sudo apt update && sudo apt install build-essential python3-dev.```

## Resources

### Sprites and Visuals

* [www.patreon.com/posts/bonus-catan-46683414](https://www.patreon.com/posts/bonus-catan-46683414)
* [game-icons.net](https://game-icons.net/)

### Board and Game Logic

* [www.redblobgames.com/grids/hexagons](https://www.redblobgames.com/grids/hexagons/)
* [code.tutsplus.com/introduction-to-axial-coordinates-for-hexagonal-tile-based-games](https://code.tutsplus.com/introduction-to-axial-coordinates-for-hexagonal-tile-based-games--cms-28820t)

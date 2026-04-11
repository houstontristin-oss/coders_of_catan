# coders_of_catan

Software Engineering Final Project - Recreating the board game Catan within python

Created by Tristin Houston, Amanda Barth, Apoorva Joshi, and Nicolas Fay

## State of the Game

#### Sunday 4/12/2026

There are two modes of game play. From the game mode screen you can select to play with four people or with three computers and one person. Once you select a game mode, the setup phase begins.

During the setup phase, the starting player is selected randomly to mimic the dice roll that usually determines the first player. Next, each player will get a turn to place a settlement and a road. Once all players have gotten a turn to place, the cycle repeats itself, starting with the last player. 

Now that all players have placed their starting settlements and roads, the game begins. If you are playing against computer players, there with be 'Next Move' and 'Next Player' buttons. 'Next Move' will update the log and can be selected until the button turns grey. The 'Next Player' button allows you to fast forward through a computer players turn and displays the entire computer turn logs. If you click the 'Next Player' button again it will go to the next players turn. The computer player may attempt to trade with you, which you can click accept or deny on the pop up.

On a human players turn, there are three options in the bottom left corner that allows you to buy Development Cards, Build Roads, Settlements, and Cities, make maritime trades, or barter trades. Once you buy a development card, you will need to wait until your next turn to use it and you can only play one a turn. If you have the resources to buy a road, settlement, or city, the options will be no longer greyed out in the Build Menu. This will then prompt you to place what you bought on a valid edge or node of the board. To complete a maritime trade, select from the top row of items what you want to give away and select from the bottom row what you want to get in return from the bank. Once you have access to a port, the numbers will automatically update so that you can trade two or three of one resource for any resource. To trade with another player, use the Barter Trade menu to select the amount you want to give away and the amount you want to recieve and then offer it to another player. Computers will automatically decide if they want to accept or deny, but if you are playing with another human player, a pop up for them will appear to either accept or deny the trade. At the end of your turn, select the 'End Turn' Button in the bottom right corner.

If anyone rolls a seven, the robber protocol is triggered. First, the computer players and players must discard half their cards if they have more than seven in their hand. Next, the player that rolled the seven must move the robber to a different tile on the board. Lastly, the player will be prompted to steal from another player if the tile they moved the robber to has another players settlement on it.

Once a player gets to 10 victory points and selects either 'Next Player' or 'End Turn', the game will end.

## Coming Soon

Ideas for future development...


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
 
## Pylint Suppression Codes
* C0103: invalid name
* C0114: missing module docstring
* C0116: missing method/function docstring
* R0801: similar lines in 2 files
* R0902: too many instance attributes
* R0911: too many return statements 
* R0912: too many branches
* R0913: too many arguments
* R0914: too many local variables
* R0915: too many statements 
* R0917: too many positional arguments 
* R1702: too many nested blocks
* W0201: attribute defined outside init
* W0718: catching too broad exception

## Resources

### Sprites and Visuals

* [www.patreon.com/posts/bonus-catan-46683414](https://www.patreon.com/posts/bonus-catan-46683414)
* [game-icons.net](https://game-icons.net/)

### Board and Game Logic

* [www.redblobgames.com/grids/hexagons](https://www.redblobgames.com/grids/hexagons/)
* [code.tutsplus.com/introduction-to-axial-coordinates-for-hexagonal-tile-based-games](https://code.tutsplus.com/introduction-to-axial-coordinates-for-hexagonal-tile-based-games--cms-28820t)

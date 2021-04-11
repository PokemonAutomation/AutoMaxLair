# AutoMaxLair
AutoMaxLair is designed for shiny hunting legendary Pokemon in Dynamax Adventures found in Pokemon Sword and Shield: The Crown Tundra. The program runs on a computer connected to the Switch through a microcontroller (outgoing controls to the Switch) and an HDMI capture card (incoming video from the Switch).
## Required Hardware
* Programmable microcontroller. Supported chips are atmega32u4 (Teensy 2.0), atmega16u2 (Arduino Uno second chip), and at90usb1286 (Teensy 2.0++).
* USB to serial conversion device. See RemoteControl documentation for details or refer to the section on serial communication in the [Pokemon Automation SwSh Scripts](https://github.com/Mysticial/Pokemon-Automation-SwSh-Arduino-Scripts) user manual.
* HDMI capture card. You can also use a cheap USB device instead.
* A computer that you can run continuously for many hours.
## Required Software
* Teensy Loader (or similar, depending on your microcontroller) for programming the microcontroller.
* Tesseract OCR. Compiled executables can be downloaded from the [UB Mannheim Github](https://github.com/UB-Mannheim/tesseract/wiki).
* Python 3.6-3.8
* Some python packages (the full list is in requirements.txt)
## Setup
1.	Install Python, ensuring you check the box to add Python to your PATH environment variable (possibly specific to Windows).
1.	Install the required Python modules. If you are using Windows, you can run install-requirements.bat which will install the modules for you.
1.	Program the microcontroller with the appropriate version of RemoteControl_XXX.hex and plug it into the Switch.
1.	Plug the USB cable attached to the Teensy’s serial port into the computer.
1.	Ensure the screen size is set to 100% under the Switch’s TV settings. Not doing so will result in misaligned text detection rectangles.
1.	Fill your inventory with Poke Balls so the bot can run uninterrupted.
1.	Make sure the setting for automatically sending Pokemon to your box is turned on.
1.	Go to the Max Lair and stop in front of the scientist, then disconnect any wireless controllers and plug the Switch into the dock.
1.	Rename Config.sample.toml to Config.toml, then open it with a text editor and modify the values to suit your setup.
1.	Plug the HDMI of your switch into the capture card, but do not view the input from any other application (or else the bot will not be able to access the video). Many capture cards will work out of the box; however, certain capture cards can’t be read by OpenCV for some reason. In this case, the virtual camera function of Open Broadcasting Software can be used.
1.	Run auto_max_lair.py, either directly or in your IDE of choice (which is better for debugging).
1.	Check the placement of the coloured rectangles as show in Figure 1, Figure 2, Figure 3, Figure 4, Figure 5, and Figure 6.
	*	If the rectangle positions are off, first double check that the Switch’s TV settings are correct—the screen size should be 100%.
	*	If that doesn’t fix the issue, you can tweak the rectangle coordinates in da_controller.py by adjusting the values in the __init__ method.
	*	The changes will come into effect when the bot is restarted.
## Operation
The bot will run until it finds a shiny legendary or until it runs out of resources. Depending on the boss, it should take a day or two on average if you have the shiny charm (15 minutes per run, variable success rate but usually above 50%, 1/100 shiny chance for the legendary). It will also keep any other shiny Pokemon it finds but will continue running after (when using the default mode). Figure 6 shows an example screenshot of the summary screen of a shiny Legendary Pokemon.

If you want to quit the program prematurely, press the Q key while the focus is on the Output window. The program will quit before the next scheduled action.

![Figure 1](/doc/Figure&#32;1&#32;-&#32;Initial&#32;Pokemon&#32;Selection.png)

Figure 1: Screen capture of the initial Pokemon selection screen. The green rectangles should contain the full name of each Pokemon and the yellow rectangles should contain their abilities.

![Figure 2](/doc/Figure&#32;2&#32;-&#32;Opponent&#32;Detection.png)

Figure 2: Screen capture of the in-battle opponent information screen. The green rectangle should contain the name of the Pokemon and the cyan rectangles should contain its types.

![Figure 3](/doc/Figure&#32;3&#32;-&#32;Ball&#32;Selection.png)

Figure 3: Screen capture of the ball selection screen. The red rectangle should contain the full name of the ball.

![Figure 4](/doc/Figure&#32;4&#32;-&#32;Post-Battle&#32;Pokemon&#32;Selection.png)

Figure 4: Screen capture of the mid-run Pokemon selection screen. The green rectangle should contain the full name of the new Pokemon and the yellow rectangle should contain its ability.

![Figure 5](/doc/Figure&#32;5&#32;-&#32;Non-Shiny&#32;Pokemon.png)

Figure 5: Screen capture of the Pokemon summary screen at the end of the run. The green rectangle will contain a red shiny sparkle symbol if the Pokemon is shiny. If it is not shiny, the rectangle will overlap slightly with the black symbol.

![Figure 6](/doc/Figure&#32;6&#32;-&#32;Shiny&#32;Pokemon.png)

Figure 6: Screen capture saved at the end of a successful run. The bot detects the red shiny star on the left side of the screen. The program will quit if it detects the star while checking the legendary’s summary; if the legendary is not shiny but another Pokemon is, the program will take that shiny Pokemon and start another run.

In addition to the standard mode which always finishes the Dynamax Adventure without resetting the game, three additional modes can be implemented by updating the appropriate field in Config.ini. These modes are summarized in Table 1.

Table 1: Summary of the benefits and drawbacks of using the different operation modes.
Mode|Benefits|Drawbacks
----|--------|---------
Default|Accumulates Dynite Ore.|Lower win rate, especially against difficult bosses. Wastes balls used to catch the legendary.
Strong Boss|Higher win rate. Wastes fewer balls used to catch the legendary.|Can consume Dynite Ore*
Ball Saver|Higher win rate. Wastes no balls used to catch the legendary.|Can rapidly consume Dynite Ore. Ignores non-legendary shiny Pokemon.
Keep Path|Highest win rate if you find a good seed beforehand. Wastes no balls used to catch the legendary.|Rapidly consumes Dynite Ore. Ignores non-legendary shiny Pokemon.
Find Path|Useful for finding a path to use "Keep Path" mode on.|Utility mode that is not needed for general use.

*The strong boss and ball saver modes can be made Dynite Ore-neutral (i.e., neither produces nor consumes) by setting the amount of starting Dynite Ore to zero in Config.ini. Difficult bosses may also cause the bot to lose, causing ore to accumulate but at a reduced rate.

## TODO
### Major Features
* Improved move selection
	*	Stat changes, status, weather, field effects, terrain and current teammates are not currently considered in damage calculations.
*	Improved selection of Pokemon
	*	HP and status of the current Pokemon is not currently measured. This information could better inform decisions on whether to take a new Pokemon.
	*	When considering a potential new Pokemon, only the player’s current Pokemon is compared. The rest of the team could be considered to see whether another member would benefit more from the Pokemon.
*	(Not sure if this idea is a good one) online capability
	*	Connecting with other players online might be beneficial for having more intelligent teammates but may be inconsiderate if the bot makes poor choices.
### Minor Updates and Bug Fixes
*	PP use is currently overestimated because the bot deducts PP when the move is selected as opposed to when it is used.
*	Boss move usage is not fully reflected by their movesets.
	*	Bosses use their 5th move only when at low HP with boss-dependent frequency and timing.
*	Items are not chosen intelligently
*	Balls count could be read instead of being inputed in the config file.
*	Improved goal selection (shiny and perfect attack, shiny, etc)

## Contributors
AutoMaxLair was initially written by [ercdndrs](https://github.com/ercdndrs). It has been supported by code contributions from [pifopi](https://github.com/pifopi) and [denvoros](https://github.com/denvoros), as well as advice and testing by multiple users in the [Pokemon Automation Discord](https://discord.gg/PokemonAutomation) and extra code contributions from users Miguel90 and fawress. The microcontroller code is based on the [AutoController](https://github.com/brianuuu/AutoController_swsh) program family published by [brianuuu](https://github.com/brianuuu).
## Changelog
### v0.2-beta
*	Initial stable public release.
*	Greatly improved Pokemon and move selection from development versions.
### v0.3
*	Implemented optional ball selection for both rental Pokemon and boss Pokemon.
*	Fixed a bug where Wide Guard users would Dynamax and use Max Guard instead.
	*	Wide Guard is now weighted fairly well.
*	Refactoring.
### v0.4
*	Added alternate modes that reset the game to preserve rare balls and/or good seeds.
	*	This mode was added with help of user fawress on the Pokemon Automation Discord.
	*	The “ball saver” mode force quits and restarts the game if the legendary is caught but is not shiny.
	*	The “strong boss” mode force quits and restarts the game if the legendary is caught and none of the Pokemon are shiny
	*	Both modes can “lock on” to a good path, since the path is conserved if the game is reset before the end of the run.
	*	Be mindful that repeated resets will incur a Dynite Ore cost, in contrast to the regular mode that accumulates Dynite Ore.
	*	The “strong boss” mode is recommended for difficult bosses where even a good seed can sometimes lose.
	*	This mode will increase the win rate against any boss, but repeated wins will quickly deplete all your Dynite Ore.
*	Fixed move scoring issues, including incorrect calculations that undervalued Max Steelspike derived from Steel Roller and overvalued Triple Axel.
*	Fixed an issue where Max Moves were overvalued by a factor of 100.
*	Added a counter for shiny Pokemon caught.
*	Adjusted detection rectangles to properly detect text when the Switch screen size is 100% (rectangles were previously optimized for a non-standard size of 96%).
*	Mitigated an issue where the bot would occasionally get stuck after dropping a button press in the battle routine.
*	Fixed an issue that caused Pokemon caught along the run to be scored incorrectly when determining whether to swap rental Pokemon or not.
### v0.5
*	Redesigned the way that the different sequences are processed to make the program run more smoothly and consistently.
	*	The visual display and button presses are now handled by different threads, which reduces FPS drops when text is being read and allows the button sequences to be handled in a linear fashion (instead of relying on a timer and substages to dictate the next step).
*	Updated the “ball saver” and “strong boss” modes to gracefully handle running out of Dynite Ore.
*	“Ball saver” mode quits when there is insufficient ore to continue resetting.
*	“Strong boss” mode finishes the run without resetting if there is insufficient ore for another reset.
*	Miscellaneous bug fixes and improvements
### v0.6
* Added support for multiple languages within the Pokemon data files.
	* All information about Pokemon is now fetched from PokeAPI.
	* Supported and verified languages include English, French, Spanish, Korean, and German.
	* Italian and Mandarin may also work but have not been tested.
* Changed how a loss (losing all 4 lives) is detected, increasing consistency.
* Detect move names, improving the accuracy of Pokemon identification.
* Updated Ball Saver mode to skip catching the boss if it can't afford to reset the game, allowing it to be run indefinitely.
* Added "Keep Path" and "Find Path" modes, which are useful against very strong bosses (e.g., Zygarde).
* Add the ability to take a pokemon from the scientist if your current pokemon is worse than average.
* Add the ability to hunt for specific stats legendary.
* Add a way to send discord message with a picture showing your latest catch.
### v0.7
* Paths through the den are now read, scored, and selected.
* Refactored code to improve readability and facilitate extension to tasks other than Dynamax Adventures in the future.
* Added support for variable hold time for button presses. The computer now sends two bytes per command, with the second byte specifying the hold time.
* Added dependencies for the microcontroller code so it can be altered and recompiled without any external tools (besides WinAVR).
* Precalculated data files are now stored in human-readable JSON format.
* Tweaked how Pokemon are scored.
* Stats checking now takes nature into account.
* Changed how certain events are detected, improving efficiency and reducing reliance on Tesseract.
* Improved path selection.
* Improved config file.
* Improved stats checking.
* More improvements on the way!
### v0.8
* Weather and terrain are now taken into consideration.
* The teammates are now detected.
* Improve the config file validation by asserting at the startup.
* Add a UI to be able to easily edit the config file.
* Detect ball type using sprites instead of text
* Automatically detect ball numbers instead of relying on users to input them in the config file
* Add compatibility for the PABotBase hex file as opposed to the custom RemoteControl hex

## Acknowledgements

Thanks to [PokéSprite](https://github.com/msikma/pokesprite) for hosting the sprites of the Pokémon and balls, [PokéAPI](https://pokeapi.co/) for hosting data on Pokémon, abilities, and moves. We also thank [LUFA](http://www.lufa-lib.org/) for their ARV framework with which the microcontroller code would not work without.

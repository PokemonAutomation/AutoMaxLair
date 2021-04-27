# AutoMaxLair
AutoMaxLair is a bot for shiny hunting legendary Pokemon in Dynamax Adventures found in Pokemon Sword and Shield: The Crown Tundra. The program runs on a computer connected to the Switch through a microcontroller (outgoing controls to the Switch) and an HDMI capture card (incoming video from the Switch).

We have migrated our setup and operation instructions to a wiki. [Please refer there for detailed setup and troubleshooting instructions](https://github.com/PokemonAutomation/AutoMaxLair/wiki). 

## Acknowledgements

Thanks to [PokéSprite](https://github.com/msikma/pokesprite) for hosting the sprites of the Pokémon and balls and [PokéAPI](https://pokeapi.co/) for hosting data on Pokémon, abilities, and moves. We also thank [LUFA](http://www.lufa-lib.org/) for their AVR framework with which the microcontroller code would not work without. Finally, we thank [brianuuu](https://github.com/brianuuu) for the [AutoController](https://github.com/brianuuu/AutoController_swsh) program family on which our microcontroller code is based on.

## Contributors
AutoMaxLair was initially written by [ercdndrs](https://github.com/ercdndrs). It has been supported by code contributions from [pifopi](https://github.com/pifopi) and [denvoros](https://github.com/denvoros), as well as advice and testing by multiple users in the [Pokemon Automation Discord](https://discord.gg/PokemonAutomation) and extra code contributions from users Miguel90 and fawress.

## Supporting us
We do not take donations of any kind for this project. The only support we request is by sharing our work with your friends if you have enjoyed using it. Further, in the spirit of transparency, we would prefer that you disclose the use of our tool (or at least an indication of automation) when sharing photos of Pokemon caught using it. If such a disclosure is not permissible, we ask that you avoid any explicit or implicit claims that such Pokemon were caught manually.

## TODO
### Major Features
* Improved move selection
	*	Stat changes, status, field effects, and current teammates are not currently considered in damage calculations.
*	Improved selection of Pokemon
	*	Status of the current Pokemon is not currently measured. This information could better inform decisions on whether to take a new Pokemon.
### Minor Updates and Bug Fixes
*	PP use is currently overestimated because the bot deducts PP when the move is selected as opposed to when it is used.
*	Boss move usage is not fully reflected by their movesets.
	*	Bosses use their 5th move only when at low HP with boss-dependent frequency and timing.
*	Items are not chosen intelligently
*	Improved goal selection (shiny and perfect attack, shiny, etc)

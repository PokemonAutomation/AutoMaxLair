class Field(object):
    def __init__(self) -> None:
        self.weather = "clear"
        self.terrain = "clear"

    def is_weather_clear(self) -> bool:
        return self.weather == "clear"

    def is_weather_sunlight(self) -> bool:
        return self.weather == "sunlight"

    def is_weather_rain(self) -> bool:
        return self.weather == "rain"

    def is_weather_sandstorm(self) -> bool:
        return self.weather == "sandstorm"

    def is_weather_hail(self) -> bool:
        return self.weather == "hail"

    def set_weather_clear(self) -> bool:
        self.weather = "clear"

    def set_weather_sunlight(self) -> bool:
        self.weather = "sunlight"

    def set_weather_rain(self) -> bool:
        self.weather = "rain"

    def set_weather_sandstorm(self) -> bool:
        self.weather = "sandstorm"

    def set_weather_hail(self) -> bool:
        self.weather = "hail"

    def is_terrain_clear(self) -> bool:
        return self.terrain == "clear"

    def is_terrain_electric(self) -> bool:
        return self.terrain == "electric"

    def is_terrain_grassy(self) -> bool:
        return self.terrain == "grassy"

    def is_terrain_misty(self) -> bool:
        return self.terrain == "misty"

    def is_terrain_psychic(self) -> bool:
        return self.terrain == "psychic"

    def set_terrain_clear(self) -> bool:
        self.terrain = "clear"

    def set_terrain_electric(self) -> bool:
        self.terrain = "electric"

    def set_terrain_grassy(self) -> bool:
        self.terrain = "grassy"

    def set_terrain_misty(self) -> bool:
        self.terrain = "misty"

    def set_terrain_psychic(self) -> bool:
        self.terrain = "psychic"

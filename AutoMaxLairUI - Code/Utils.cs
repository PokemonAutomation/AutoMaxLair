namespace AutoMaxLair
{
    class Utils
    {
        static public string UppercaseFirstLetter(string s)
        {
            // Check for empty string.
            if (string.IsNullOrEmpty(s))
            {
                return string.Empty;
            }
            // Return char and concat substring.
            return char.ToUpper(s[0]) + s.Substring(1);
        }

        static public string ConvertBossNameToBossId(string bossName)
        {
            return bossName switch
            {
                "Tornadus" => "tornadus-incarnate",
                "Landorus" => "landorus-incarnate",
                "Thundurus" => "thundurus-incarnate",
                "Giratina" => "giratina-altered",
                "Zygarde" => "zygarde-50",
                _ => bossName.ToLower(),
            };
        }

        static public string ConvertBossIdToBossName(string bossId)
        {
            return bossId switch
            {
                "tornadus-incarnate" => "Tornadus",
                "landorus-incarnate" => "Landorus",
                "thundurus-incarnate" => "Thundurus",
                "giratina-altered" => "Giratina",
                "zygarde-50" => "Zygarde",
                _ => UppercaseFirstLetter(bossId),
            };
        }

        static public string ConvertBallNameToBallId(string ballName)
        {
            return ballName.ToLower() + "-ball";
        }

        static public string ConvertBallIdToBallName(string ballId)
        {
            return UppercaseFirstLetter(ballId).Replace("-ball", "");
        }
    }
}

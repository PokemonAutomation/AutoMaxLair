using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.Linq;
using System.Text;
using System.Windows.Forms;
using System.IO;
using AForge.Video;
using AForge.Video.DirectShow;
using System.Threading.Tasks;
using IronPython.Hosting;
using Microsoft.Scripting.Hosting;
using System.Diagnostics;
using Tommy;
using System.Collections;

namespace AutoDA
{
    public partial class AutoDA : Form
    {
        public AutoDA()
        {
            InitializeComponent();
            customizeDesign();
            getConfig();
        }

        //FilterInfoCollection filterInfoCollection;
        //VideoCaptureDevice videoCaptureDevice;


        private void AutoDA_Load(object sender, EventArgs e)
        {
            //Code to see a video capture of the Switch - currently reducing the .exe to only toml changing.
            /* boxVideoOutput.SizeMode = PictureBoxSizeMode.StretchImage;
            filterInfoCollection = new FilterInfoCollection(FilterCategory.VideoInputDevice);
            foreach (FilterInfo filterInfo in filterInfoCollection)
                boxVideoCapture.Items.Add(filterInfo.Name);
            boxVideoCapture.SelectedIndex = 0;
            videoCaptureDevice = new VideoCaptureDevice(); */
        }

        private void VideoCaptureDevice_NewForm(object sender, NewFrameEventArgs eventArgs)
        {
            boxVideoOutput.Image = (Bitmap)eventArgs.Frame.Clone();
        }

        private void customizeDesign()
        {
            btnStop.Visible = false;
        }

        // Method to get the preset for the UI from the Config.toml
        private void getConfig()
        {
            // Read from Config.toml file
            string path = Directory.GetCurrentDirectory();
            string configData = "";

            // Check if Config.toml exist, if not use Config.sample.toml
            if (File.Exists(path + @"\Config.toml"))
            {
                configData = path + @"\Config.toml";
            }
            else
            {
                configData = path + @"\Config.sample.toml";
            }
            

            using (StreamReader reader = new StreamReader(File.OpenRead(configData)))
            {

                TomlTable t = TOML.Parse(reader);

                // Create Lists for each stat +,=,-
                List<string> arr = new List<string>();
                List<string> arr1 = new List<string>();
                List<string> arr2 = new List<string>();
                List<string> arr3 = new List<string>();
                List<string> arr4 = new List<string>();
                List<string> arr5 = new List<string>();

                // Loops to get all nodes from TomlNode into the list
                foreach (TomlNode node in t["stats"]["ATTACK_STATS"]["positive"])
                {
                    arr.Add(node);
                }
                foreach (TomlNode node in t["stats"]["ATTACK_STATS"]["neutral"])
                {
                    arr1.Add(node);
                }
                foreach (TomlNode node in t["stats"]["ATTACK_STATS"]["negative"])
                {
                    arr2.Add(node);
                }
                
                foreach (TomlNode node in t["stats"]["SPEED_STATS"]["positive"])
                {
                    arr3.Add(node);
                }
                
                foreach (TomlNode node in t["stats"]["SPEED_STATS"]["neutral"])
                {
                    arr4.Add(node);
                }
                
                foreach (TomlNode node in t["stats"]["SPEED_STATS"]["negative"])
                {
                    arr5.Add(node);
                }

                // Join all strings in list and display in box
                boxAttackPos.Text = String.Join(",", arr);
                boxAttackNeut.Text = String.Join(",", arr1);
                boxAttackNeg.Text = String.Join(",", arr2);
                boxSpeedPos.Text = String.Join(",", arr3);
                boxSpeedNeut.Text = String.Join(",", arr4);
                boxSpeedNeg.Text = String.Join(",", arr5);

                string poke = "";
                if (t["BOSS"] == "tornadus-incarnate")
                    poke = "tornadus";
                if (t["BOSS"] == "landorus-incarnate")
                    poke = "landorus";
                if (t["BOSS"] == "thundurus-incarnate")
                    poke = "thundurus";
                if (t["BOSS"] == "giratina-altered")
                    poke = "giratina";
                if (t["BOSS"] == "zygarde-50")
                    poke = "zygarde";

                boxPokemon.Text = poke;
                boxBaseBall.Text = t["BASE_BALL"];
                boxBaseBallValue.Text = t["BASE_BALLS"];
                boxLegendBall.Text = t["LEGENDARY_BALL"];
                boxLegendBallValue.Text = t["LEGENDARY_BALLS"];
                boxMode.Text = t["MODE"];
                boxComPort.Text = t["COM_PORT"];
                boxVideoIndex.Text = t["VIDEO_INDEX"];
                boxTesseract.Text = t["TESSERACT_PATH"];
                boxVideoScale.Text = t["advanced"]["VIDEO_SCALE"];
                boxVideoDelay.Text = t["advanced"]["VIDEO_EXTRA_DELAY"];
                boxBossIndex.Text = t["advanced"]["BOSS_INDEX"];
                boxDyniteOre.Text = t["advanced"]["DYNITE_ORE"];
                boxConsecutiveResets.Text = t["advanced"]["CONSECUTIVE_RESETS"];
                checkBoxDebugLogs.Checked = t["advanced"]["ENABLE_DEBUG_LOGS"];
                boxCheckAttack.Checked = t["stats"]["CHECK_ATTACK_STAT"];
                boxCheckSpeed.Checked = t["stats"]["CHECK_SPEED_STAT"];
                boxWebhookID.Text = t["discord"]["WEBHOOK_ID"];
                boxWebhookToken.Text = t["discord"]["WEBHOOK_TOKEN"];
                boxUserID.Text = t["discord"]["USER_ID"];
                boxPingName.Text = t["discord"]["USER_SHORT_NAME"];
                boxPingSettings.Text = t["discord"]["UPDATE_LEVELS"];
                boxGameLanguage.Text = t["language"]["LANGUAGE"];
            }
        }

        private void validate()
        {

            string[] atkPos = boxAttackPos.Text.Split(',').ToArray();
            string[] atkNeut = boxAttackNeut.Text.Split(',').ToArray();
            string[] atkNeg = boxAttackNeg.Text.Split(',').ToArray();
            string[] speedPos = boxSpeedPos.Text.Split(',').ToArray();
            string[] speedNeut = boxSpeedNeut.Text.Split(',').ToArray();
            string[] speedNeg = boxSpeedNeg.Text.Split(',').ToArray();

            int i, x, y, z, q, w, t, u, o, p, l, k, h;
            float a, b, j, g;

            bool bossValue = int.TryParse(boxBossIndex.Text, out i);
            bool baseBall = int.TryParse(boxBaseBallValue.Text, out x);
            bool legendBall = int.TryParse(boxLegendBallValue.Text, out y);
            bool videoIndex = int.TryParse(boxVideoIndex.Text, out z);
            bool dynite = int.TryParse(boxDyniteOre.Text, out q);
            bool resets = int.TryParse(boxConsecutiveResets.Text, out w);
            bool webhookID = float.TryParse(boxWebhookID.Text, out j);
            //bool webhookToken = int.TryParse(boxWebhookToken.Text, out h);
            bool userID = float.TryParse(boxWebhookToken.Text, out g);

            bool videoScale = float.TryParse(boxVideoScale.Text, out a);
            bool videoDelay = float.TryParse(boxVideoDelay.Text, out b);

            bool aPosInts = atkPos.All(x => int.TryParse(x.ToString(), out t));
            bool aNeutInts = atkNeut.All(x => int.TryParse(x.ToString(), out u));
            bool aNegInts = atkNeg.All(x => int.TryParse(x.ToString(), out o));
            bool sPosInts = speedPos.All(x => int.TryParse(x.ToString(), out p));
            bool sNeutInts = speedNeut.All(x => int.TryParse(x.ToString(), out l));
            bool sNegInts = speedNeg.All(x => int.TryParse(x.ToString(), out k));

            // Base Ball Validation
            if (baseBall == false && boxBaseBall.Text.Equals(boxLegendBall.Text) || baseBall == true && x < 4 && boxBaseBall.Text.Equals(boxLegendBall.Text) 
                || baseBall == true && x > 999 && boxBaseBall.Text.Equals(boxLegendBall.Text))
                MessageBox.Show("Your Base Ball Value needs to be a number between 4 and 999!", "Error: Base Ball Value", MessageBoxButtons.OK, MessageBoxIcon.Error);
            else if (baseBall == false || baseBall == true && x < 3 || baseBall == true && x > 999)
                MessageBox.Show("Your Base Ball Value needs to be a number between 3 and 999!", "Error: Base Ball Value", MessageBoxButtons.OK, MessageBoxIcon.Error);

            // Legendary Ball Validation
            else if (legendBall == false && boxBaseBall.Text.Equals(boxLegendBall.Text) || legendBall == true && y < 4 && boxBaseBall.Text.Equals(boxLegendBall.Text) 
                || legendBall == true && y > 999 && boxBaseBall.Text.Equals(boxLegendBall.Text))
                MessageBox.Show("Your Legend Ball Value needs to be a number between 4 and 999!", "Error: Legend Ball Value", MessageBoxButtons.OK, MessageBoxIcon.Error);
            else if (legendBall == false || legendBall == true && y < 1 || legendBall == true && y > 999)
                MessageBox.Show("Your Legend Ball Value needs to be a number between 1 and 999!", "Error: Legend Ball Value", MessageBoxButtons.OK, MessageBoxIcon.Error);

            // Video Index Validation
            else if (videoIndex == false)
                MessageBox.Show("Your Video Index needs to be a number!", "Error: Video Index", MessageBoxButtons.OK, MessageBoxIcon.Error);

            // Video Scale Validation
            else if (videoScale == false)
                MessageBox.Show("Your Video Scale must be a number (e.g. 0.5).", "Error: Video Scale", MessageBoxButtons.OK, MessageBoxIcon.Error);

            // Video Delay Validation
            else if (videoDelay == false)
                MessageBox.Show("Your Video Delay must be a number (e.g. 0.5).", "Error: Video Extra Delay", MessageBoxButtons.OK, MessageBoxIcon.Error);

            // Dynite Ore Validation
            else if (dynite == false && boxMode.Text == "Keep Path" || dynite == true && q < 0 && boxMode.Text == "Keep Path" || dynite == true && q > 999 && boxMode.Text == "Keep Path")
                MessageBox.Show("Your Dynite Ore needs to be a number between 0 and 999!", "Error: Dynite Ore", MessageBoxButtons.OK, MessageBoxIcon.Error);
            else if (dynite == false || dynite == true && q > 999)
                MessageBox.Show("Your Dynite Ore needs to be a number less than 999!", "Error: Dynite Ore", MessageBoxButtons.OK, MessageBoxIcon.Error);

            // Consecutive Resets Validation
            else if (resets == false || resets == true && w < 0)
                MessageBox.Show("Your Consecutive Resets needs to be a number which is 0 or greater than 0!", "Error: Consecutive Resets", MessageBoxButtons.OK, MessageBoxIcon.Error);

            // Attack Stats Validation
            else if (aPosInts == false || aNeutInts == false || aNegInts == false)
                MessageBox.Show("Your Attack Stats need to be a number and be split with a comma (e.g. 120, 121).", "Error: Attack Stats", MessageBoxButtons.OK, MessageBoxIcon.Error);

            // Speed Stats Validation
            else if (sPosInts == false || sNeutInts == false || sNegInts == false)
                MessageBox.Show("Your Speed Stats need to be a number and be split with a comma (e.g. 120, 121).", "Error: Speed Stats", MessageBoxButtons.OK, MessageBoxIcon.Error);

            // Webhook Validation
            else if (webhookID == false)
                MessageBox.Show("Your Webhook ID should be a string of numbers.", "Error: Webhook ID", MessageBoxButtons.OK, MessageBoxIcon.Error);
            //else if (webhookToken == false)
                //MessageBox.Show("Your Webhook Token should be a string of numbers.", "Error: Webhook Token", MessageBoxButtons.OK, MessageBoxIcon.Error);

            // Discord Validation
            else if (userID == false || boxUserID.Text.Length != 18)
                MessageBox.Show("Your Discord User ID should be a string of numbers with the length 18.", "Error: User ID", MessageBoxButtons.OK, MessageBoxIcon.Error);

            else
                setConfig();
        }

        // Method to change the Config.toml
        private void setConfig()
        {
            
            // Read the sample to get the language settings + the paths
     
            string samplePath = Directory.GetCurrentDirectory() + @"\Config.sample.toml";

            using (StreamReader reader = new StreamReader(File.OpenRead(samplePath)))
            {
                TomlTable tt = TOML.Parse(reader);

                // Change the table in the toml file
                string path = Directory.GetCurrentDirectory();
                string configData = path + @"\Config.toml";

                int boss = 0;
                if (boxBossIndex.Text == "Top")
                {
                    boss = 0;
                }
                if (boxBossIndex.Text == "Middle")
                {
                    boss = 1;
                }
                if (boxBossIndex.Text == "Bottom")
                {
                    boss = 2;
                }

                TomlTable t = new TomlTable();

                // Get all values in a string-array
                string[] atkPos = boxAttackPos.Text.Split(',').ToArray();
                string[] atkNeut = boxAttackNeut.Text.Split(',').ToArray();
                string[] atkNeg = boxAttackNeg.Text.Split(',').ToArray();
                string[] speedPos = boxSpeedPos.Text.Split(',').ToArray();
                string[] speedNeut = boxSpeedNeut.Text.Split(',').ToArray();
                string[] speedNeg = boxSpeedNeg.Text.Split(',').ToArray();

                // General Settings
                string poke = "";

                if (boxPokemon.Text == "Tornadus")
                    poke = "tornadus-incarnate";
                else if (boxPokemon.Text == "Thundurus")
                    poke = "thundurus-incarnate";
                else if (boxPokemon.Text == "Landorus")
                    poke = "landorus-incarnate";
                else if (boxPokemon.Text == "Giratina")
                    poke = "giratina-altered";
                else if (boxPokemon.Text == "Zygarde")
                    poke = "zygarde-50";
                else
                    poke = boxPokemon.Text;

                t["BOSS"] = poke.ToLower();
                t["BASE_BALL"] = boxBaseBall.Text.ToLower() + "-ball";
                t["BASE_BALLS"] = int.Parse(boxBaseBallValue.Text);
                t["LEGENDARY_BALL"] = boxLegendBall.Text.ToLower() + "-ball";
                t["LEGENDARY_BALLS"] = int.Parse(boxLegendBallValue.Text);
                t["MODE"] = boxMode.Text.ToUpper();
                t["COM_PORT"] = boxComPort.Text;
                t["VIDEO_INDEX"] = int.Parse(boxVideoIndex.Text);
                t["TESSERACT_PATH"] = boxTesseract.Text;

                // Advanced Settings
                t["advanced"]["VIDEO_SCALE"] = float.Parse(boxVideoScale.Text);
                t["advanced"]["VIDEO_EXTRA_DELAY"] = float.Parse(boxVideoDelay.Text);
                t["advanced"]["BOSS_INDEX"] = boss;
                t["advanced"]["DYNITE_ORE"] = int.Parse(boxDyniteOre.Text);
                t["advanced"]["CONSECUTIVE_RESETS"] = int.Parse(boxConsecutiveResets.Text);
                t["advanced"]["ENABLE_DEBUG_LOGS"] = checkBoxDebugLogs.Checked;

                // Stat Settings
                t["stats"]["CHECK_ATTACK_STAT"] = boxCheckAttack.Checked;
                t["stats"]["CHECK_SPEED_STAT"] = boxCheckSpeed.Checked;

                // Create TomlNodes for each stat +,=,-
                TomlNode node = new TomlNode[] { };
                TomlNode node1 = new TomlNode[] { };
                TomlNode node2 = new TomlNode[] { };
                TomlNode node3 = new TomlNode[] { };
                TomlNode node4 = new TomlNode[] { };
                TomlNode node5 = new TomlNode[] { };

                // Get all values from the array into int and add it to the node
                for (int i = 0; i < atkPos.Length; i++)
                {

                    node.Add(int.Parse(atkPos[i]));

                }
                for (int i = 0; i < atkNeut.Length; i++)
                {

                    node1.Add(int.Parse(atkNeut[i]));

                }
                for (int i = 0; i < atkNeg.Length; i++)
                {

                    node2.Add(int.Parse(atkNeg[i]));

                }
                for (int i = 0; i < speedPos.Length; i++)
                {

                    node3.Add(int.Parse(speedPos[i]));

                }
                for (int i = 0; i < speedNeut.Length; i++)
                {

                    node4.Add(int.Parse(speedNeut[i]));

                }
                for (int i = 0; i < speedNeg.Length; i++)
                {

                    node5.Add(int.Parse(speedNeg[i]));

                }

                // Stats
                t["stats"]["ATTACK_STATS"]["positive"] = node;
                t["stats"]["ATTACK_STATS"]["neutral"] = node1;
                t["stats"]["ATTACK_STATS"]["negative"] = node2;
                t["stats"]["SPEED_STATS"]["positive"] = node3;
                t["stats"]["SPEED_STATS"]["neutral"] = node4;
                t["stats"]["SPEED_STATS"]["negative"] = node5;

                // Discord Settings
                t["discord"]["WEBHOOK_ID"] = boxWebhookID.Text;
                t["discord"]["WEBHOOK_TOKEN"] = boxWebhookToken.Text;
                t["discord"]["USER_ID"] = boxUserID.Text;
                t["discord"]["USER_SHORT_NAME"] = boxPingName.Text;
                t["discord"]["UPDATE_LEVELS"] = boxPingSettings.Text;

                // Pokémon Data Settings
                string dataPathBoss = tt["pokemon_data_paths"]["Boss_Pokemon"];
                string dataPathRental = tt["pokemon_data_paths"]["Rental_Pokemon"];
                string dataPathBossMatchup = tt["pokemon_data_paths"]["Boss_Matchup_LUT"];
                string dataPathRentalMatchup = tt["pokemon_data_paths"]["Rental_Matchup_LUT"];
                string dataPathRentalScore = tt["pokemon_data_paths"]["Rental_Pokemon_Scores"];
                string dataPathTree = tt["pokemon_data_paths"]["path_tree_path"];
                string dataPathBalls = tt["pokemon_data_paths"]["balls_path"];
                string dataPathIcon = tt["pokemon_data_paths"]["type_icon_path"];
                string dataPathSprite = tt["pokemon_data_paths"]["pokemon_sprite_path"];
                string dataPathMiscIcon = tt["pokemon_data_paths"]["misc_icon_dir"];


                t["pokemon_data_paths"]["Boss_Pokemon"] = dataPathBoss;
                t["pokemon_data_paths"]["Rental_Pokemon"] = dataPathRental;
                t["pokemon_data_paths"]["Boss_Matchup_LUT"] = dataPathBossMatchup;
                t["pokemon_data_paths"]["Rental_Matchup_LUT"] = dataPathRentalMatchup;
                t["pokemon_data_paths"]["Rental_Pokemon_Scores"] = dataPathRentalScore;
                t["pokemon_data_paths"]["path_tree_path"] = dataPathTree;
                t["pokemon_data_paths"]["balls_path"] = dataPathBalls;
                t["pokemon_data_paths"]["type_icon_path"] = dataPathIcon;
                t["pokemon_data_paths"]["pokemon_sprite_path"] = dataPathSprite;
                t["pokemon_data_paths"]["misc_icon_dir"] = dataPathMiscIcon;

                // Game Language Settings
                t["language"]["LANGUAGE"] = boxGameLanguage.Text;

                // English
                string engTess = tt["English"]["TESSERACT_LANG_NAME"];
                string engData = tt["English"]["DATA_LANG_NAME"];
                string engBack = tt["English"]["BACKPACKER"];
                string engScience = tt["English"]["SCIENTIST"];
                string engPath = tt["English"]["PATH"];
                string engFaint = tt["English"]["FAINT"];
                string engStart = tt["English"]["START_PHRASE"];
                string engClear = tt["English"]["WEATHER_CLEAR"];
                string engSun = tt["English"]["WEATHER_SUNLIGHT"];
                string engRain = tt["English"]["WEATHER_RAIN"];
                string engSand = tt["English"]["WEATHER_SANDSTORM"];
                string engHail = tt["English"]["WEATHER_HAIL"];
                string engTClear = tt["English"]["TERRAIN_CLEAR"];
                string engElectric = tt["English"]["TERRAIN_ELECTRIC"];
                string engGrassy = tt["English"]["TERRAIN_GRASSY"];
                string engMisty = tt["English"]["TERRAIN_MISTY"];
                string engPsychic = tt["English"]["TERRAIN_PSYCHIC"];

                t["English"]["TESSERACT_LANG_NAME"] = engTess;
                t["English"]["DATA_LANG_NAME"] = engData;
                t["English"]["BACKPACKER"] = engBack;
                t["English"]["SCIENTIST"] = engScience;
                t["English"]["PATH"] = engPath;
                t["English"]["FAINT"] = engFaint;
                t["English"]["START_PHRASE"] = engStart;
                t["English"]["WEATHER_CLEAR"] = engClear;
                t["English"]["WEATHER_SUNLIGHT"] = engSun;
                t["English"]["WEATHER_RAIN"] = engRain;
                t["English"]["WEATHER_SANDSTORM"] = engSand;
                t["English"]["WEATHER_HAIL"] = engHail;
                t["English"]["TERRAIN_CLEAR"] = engTClear;
                t["English"]["TERRAIN_ELECTRIC"] = engElectric;
                t["English"]["TERRAIN_GRASSY"] = engGrassy;
                t["English"]["TERRAIN_MISTY"] = engMisty;
                t["English"]["TERRAIN_PSYCHIC"] = engPsychic;

                // Spanish
                string spaTess = tt["Spanish"]["TESSERACT_LANG_NAME"];
                string spaData = tt["Spanish"]["DATA_LANG_NAME"];
                string spaBack = tt["Spanish"]["BACKPACKER"];
                string spaScience = tt["Spanish"]["SCIENTIST"];
                string spaPath = tt["Spanish"]["PATH"];
                string spaFaint = tt["Spanish"]["FAINT"];
                string spaStart = tt["Spanish"]["START_PHRASE"];
                string spaClear = tt["Spanish"]["WEATHER_CLEAR"];
                string spaSun = tt["Spanish"]["WEATHER_SUNLIGHT"];
                string spaRain = tt["Spanish"]["WEATHER_RAIN"];
                string spaSand = tt["Spanish"]["WEATHER_SANDSTORM"];
                string spaHail = tt["Spanish"]["WEATHER_HAIL"];
                string spaTClear = tt["Spanish"]["TERRAIN_CLEAR"];
                string spaElectric = tt["Spanish"]["TERRAIN_ELECTRIC"];
                string spaGrassy = tt["Spanish"]["TERRAIN_GRASSY"];
                string spaMisty = tt["Spanish"]["TERRAIN_MISTY"];
                string spaPsychic = tt["Spanish"]["TERRAIN_PSYCHIC"];

                t["Spanish"]["TESSERACT_LANG_NAME"] = spaTess;
                t["Spanish"]["DATA_LANG_NAME"] = spaData;
                t["Spanish"]["BACKPACKER"] = spaBack;
                t["Spanish"]["SCIENTIST"] = spaScience;
                t["Spanish"]["PATH"] = spaPath;
                t["Spanish"]["FAINT"] = spaFaint;
                t["Spanish"]["START_PHRASE"] = spaStart;
                t["Spanish"]["WEATHER_CLEAR"] = spaClear;
                t["Spanish"]["WEATHER_SUNLIGHT"] = spaSun;
                t["Spanish"]["WEATHER_RAIN"] = spaRain;
                t["Spanish"]["WEATHER_SANDSTORM"] = spaSand;
                t["Spanish"]["WEATHER_HAIL"] = spaHail;
                t["Spanish"]["TERRAIN_CLEAR"] = spaTClear;
                t["Spanish"]["TERRAIN_ELECTRIC"] = spaElectric;
                t["Spanish"]["TERRAIN_GRASSY"] = spaGrassy;
                t["Spanish"]["TERRAIN_MISTY"] = spaMisty;
                t["Spanish"]["TERRAIN_PSYCHIC"] = spaPsychic;

                // French
                string freTess = tt["French"]["TESSERACT_LANG_NAME"];
                string freData = tt["French"]["DATA_LANG_NAME"];
                string freBack = tt["French"]["BACKPACKER"];
                string freScience = tt["French"]["SCIENTIST"];
                string frePath = tt["French"]["PATH"];
                string freFaint = tt["French"]["FAINT"];
                string freStart = tt["French"]["START_PHRASE"];
                string freClear = tt["French"]["WEATHER_CLEAR"];
                string freSun = tt["French"]["WEATHER_SUNLIGHT"];
                string freRain = tt["French"]["WEATHER_RAIN"];
                string freSand = tt["French"]["WEATHER_SANDSTORM"];
                string freHail = tt["French"]["WEATHER_HAIL"];
                string freTClear = tt["French"]["TERRAIN_CLEAR"];
                string freElectric = tt["French"]["TERRAIN_ELECTRIC"];
                string freGrassy = tt["French"]["TERRAIN_GRASSY"];
                string freMisty = tt["French"]["TERRAIN_MISTY"];
                string frePsychic = tt["French"]["TERRAIN_PSYCHIC"];

                t["French"]["TESSERACT_LANG_NAME"] = freTess;
                t["French"]["DATA_LANG_NAME"] = freData;
                t["French"]["BACKPACKER"] = freBack;
                t["French"]["SCIENTIST"] = freScience;
                t["French"]["PATH"] = frePath;
                t["French"]["FAINT"] = freFaint;
                t["French"]["START_PHRASE"] = freStart;
                t["French"]["WEATHER_CLEAR"] = freClear;
                t["French"]["WEATHER_SUNLIGHT"] = freSun;
                t["French"]["WEATHER_RAIN"] = freRain;
                t["French"]["WEATHER_SANDSTORM"] = freSand;
                t["French"]["WEATHER_HAIL"] = freHail;
                t["French"]["TERRAIN_CLEAR"] = freTClear;
                t["French"]["TERRAIN_ELECTRIC"] = freElectric;
                t["French"]["TERRAIN_GRASSY"] = freGrassy;
                t["French"]["TERRAIN_MISTY"] = freMisty;
                t["French"]["TERRAIN_PSYCHIC"] = frePsychic;

                // Korean
                string korTess = tt["Korean"]["TESSERACT_LANG_NAME"];
                string korData = tt["Korean"]["DATA_LANG_NAME"];
                string korBack = tt["Korean"]["BACKPACKER"];
                string korScience = tt["Korean"]["SCIENTIST"];
                string korPath = tt["Korean"]["PATH"];
                string korFaint = tt["Korean"]["FAINT"];
                string korStart = tt["Korean"]["START_PHRASE"];
                string korClear = tt["Korean"]["WEATHER_CLEAR"];
                string korSun = tt["Korean"]["WEATHER_SUNLIGHT"];
                string korRain = tt["Korean"]["WEATHER_RAIN"];
                string korSand = tt["Korean"]["WEATHER_SANDSTORM"];
                string korHail = tt["Korean"]["WEATHER_HAIL"];
                string korTClear = tt["Korean"]["TERRAIN_CLEAR"];
                string korElectric = tt["Korean"]["TERRAIN_ELECTRIC"];
                string korGrassy = tt["Korean"]["TERRAIN_GRASSY"];
                string korMisty = tt["Korean"]["TERRAIN_MISTY"];
                string korPsychic = tt["Korean"]["TERRAIN_PSYCHIC"];

                t["Korean"]["TESSERACT_LANG_NAME"] = korTess;
                t["Korean"]["DATA_LANG_NAME"] = korData;
                t["Korean"]["BACKPACKER"] = korBack;
                t["Korean"]["SCIENTIST"] = korScience;
                t["Korean"]["PATH"] = korPath;
                t["Korean"]["FAINT"] = korFaint;
                t["Korean"]["START_PHRASE"] = korStart;
                t["Korean"]["WEATHER_CLEAR"] = korClear;
                t["Korean"]["WEATHER_SUNLIGHT"] = korSun;
                t["Korean"]["WEATHER_RAIN"] = korRain;
                t["Korean"]["WEATHER_SANDSTORM"] = korSand;
                t["Korean"]["WEATHER_HAIL"] = korHail;
                t["Korean"]["TERRAIN_CLEAR"] = korTClear;
                t["Korean"]["TERRAIN_ELECTRIC"] = korElectric;
                t["Korean"]["TERRAIN_GRASSY"] = korGrassy;
                t["Korean"]["TERRAIN_MISTY"] = korMisty;
                t["Korean"]["TERRAIN_PSYCHIC"] = korPsychic;

                // German
                string gerTess = tt["German"]["TESSERACT_LANG_NAME"];
                string gerData = tt["German"]["DATA_LANG_NAME"];
                string gerBack = tt["German"]["BACKPACKER"];
                string gerScience = tt["German"]["SCIENTIST"];
                string gerPath = tt["German"]["PATH"];
                string gerFaint = tt["German"]["FAINT"];
                string gerStart = tt["German"]["START_PHRASE"];
                string gerClear = tt["German"]["WEATHER_CLEAR"];
                string gerSun = tt["German"]["WEATHER_SUNLIGHT"];
                string gerRain = tt["German"]["WEATHER_RAIN"];
                string gerSand = tt["German"]["WEATHER_SANDSTORM"];
                string gerHail = tt["German"]["WEATHER_HAIL"];
                string gerTClear = tt["German"]["TERRAIN_CLEAR"];
                string gerElectric = tt["German"]["TERRAIN_ELECTRIC"];
                string gerGrassy = tt["German"]["TERRAIN_GRASSY"];
                string gerMisty = tt["German"]["TERRAIN_MISTY"];
                string gerPsychic = tt["German"]["TERRAIN_PSYCHIC"];

                t["German"]["TESSERACT_LANG_NAME"] = gerTess;
                t["German"]["DATA_LANG_NAME"] = gerData;
                t["German"]["BACKPACKER"] = gerBack;
                t["German"]["SCIENTIST"] = gerScience;
                t["German"]["PATH"] = gerPath;
                t["German"]["FAINT"] = gerFaint;
                t["German"]["START_PHRASE"] = gerStart;
                t["German"]["WEATHER_CLEAR"] = gerClear;
                t["German"]["WEATHER_SUNLIGHT"] = gerSun;
                t["German"]["WEATHER_RAIN"] = gerRain;
                t["German"]["WEATHER_SANDSTORM"] = gerSand;
                t["German"]["WEATHER_HAIL"] = gerHail;
                t["German"]["TERRAIN_CLEAR"] = gerTClear;
                t["German"]["TERRAIN_ELECTRIC"] = gerElectric;
                t["German"]["TERRAIN_GRASSY"] = gerGrassy;
                t["German"]["TERRAIN_MISTY"] = gerMisty;
                t["German"]["TERRAIN_PSYCHIC"] = gerPsychic;


                using (StreamWriter writer = new StreamWriter(File.Open(configData, FileMode.Create)))
                {
                    t.WriteTo(writer);
                    writer.Flush();
                }

            }
 
        }

        // Method to minimize panels (Drop Down Menu) - not needed rn
        private void showSubMenu(Panel subMenu)
        {
            if (subMenu.Visible == false)
            {
                subMenu.Visible = true;
            }
            else
                subMenu.Visible = false;
        }


        private void btnSetting_Click(object sender, EventArgs e)
        {
            //showSubMenu(panelSettingSubmenu);
        }

        private void btnStart_Click(object sender, EventArgs e)
        {
            btnStart.Visible = false;
            btnStop.Visible = true;

            //runAutoMaxLair();

        }
        // Method to start the auto_max_lair.py script. After opening py, console insta crashes. Not sure why.
        private void runAutoMaxLair()
        {
            string pythonPath = Directory.GetCurrentDirectory() + @"\auto_max_lair.py";
            string python = "PATH_TO_PYTHON.EXE"; //placeholder
            string test = "PATH_TO_PYTHON.PY"; //placeholder

            ProcessStartInfo info = new ProcessStartInfo();
            Process pythonee;
            info.FileName = python;
            info.Arguments = test;
            info.CreateNoWindow = false;
            info.UseShellExecute = true;

            Console.WriteLine("Python is starting");
            pythonee = Process.Start(info);
            pythonee.WaitForExit();
            pythonee.Close();

            /* Process p = new Process();
            p.StartInfo = new ProcessStartInfo(python, test)
            {
                RedirectStandardOutput = true,
                UseShellExecute = false
                //CreateNoWindow = true
            };
            p.Start();

            string output = p.StandardOutput.ReadToEnd();
            p.WaitForExit();

            Console.WriteLine(output);

            Console.ReadLine(); */
        }


        private void btnStop_Click(object sender, EventArgs e)
        {
            btnStart.Visible = true;
            btnStop.Visible = false;
        }

        private void boxPokemon_SelectedIndexChanged(object sender, EventArgs e)
        {

        }

        private void btnAdvancedSettings_Click(object sender, EventArgs e)
        {
            //showSubMenu(panelAdvancedSettingsSubmenu);
        }

        // Does the setConfig() Method when you press the "Save-Button"
        private void btnSave_Click(object sender, EventArgs e)
        {
            validate();
        }

        /* private void boxVideoCapture_SelectedIndexChanged(object sender, EventArgs e)
        {
            if (videoCaptureDevice != null)
                videoCaptureDevice.SignalToStop();
            videoCaptureDevice = new VideoCaptureDevice(filterInfoCollection[boxVideoCapture.SelectedIndex].MonikerString);
            videoCaptureDevice.NewFrame += VideoCaptureDevice_NewForm;
            videoCaptureDevice.Start();
        } */

        private void AutoDA_FormClosing(object sender, FormClosingEventArgs e)
        {
            //     videoCaptureDevice.SignalToStop();
        }

        private void btnDiscord_Click(object sender, EventArgs e)
        {
            //showSubMenu(panelDiscordSubmenu);
        }

        private void btnStats_Click(object sender, EventArgs e)
        {
            //showSubMenu(panelStatSubmenu);
        }

        private void boxVideoCapture_SelectedIndexChanged(object sender, EventArgs e)
        {

        }

        private void boxAttackNeg_TextChanged(object sender, EventArgs e)
        {

        }

        private void boxSpeedNeg_TextChanged(object sender, EventArgs e)
        {

        }

        private void toolTip_Popup(object sender, PopupEventArgs e)
        {

        }

        private void label10_Click(object sender, EventArgs e)
        {

        }

        private void btnTesseract_Click(object sender, EventArgs e)
        {
            FolderBrowserDialog fbd = new FolderBrowserDialog();
            fbd.RootFolder = Environment.SpecialFolder.ProgramFiles;
            if (fbd.ShowDialog() == System.Windows.Forms.DialogResult.OK)
                boxTesseract.Text = fbd.SelectedPath;
        }

        private void boxMode_SelectedIndexChanged(object sender, EventArgs e)
        {

        }
    }
}

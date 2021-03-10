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

                boxPokemon.Text = t["BOSS"];
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

            int i, x, y, z, q, w, t, u, o, p, l, k, j, h, g;
            float a, b;

            bool bossValue = int.TryParse(boxBossIndex.Text, out i);
            bool baseBall = int.TryParse(boxBaseBallValue.Text, out x);
            bool legendBall = int.TryParse(boxLegendBallValue.Text, out y);
            bool videoIndex = int.TryParse(boxVideoIndex.Text, out z);
            bool dynite = int.TryParse(boxDyniteOre.Text, out q);
            bool resets = int.TryParse(boxConsecutiveResets.Text, out w);
            bool webhookID = int.TryParse(boxWebhookID.Text, out j);
            bool webhookToken = int.TryParse(boxWebhookToken.Text, out h);
            bool userID = int.TryParse(boxWebhookToken.Text, out g);

            bool videoScale = float.TryParse(boxVideoScale.Text, out a);
            bool videoDelay = float.TryParse(boxVideoDelay.Text, out b);

            bool aPosInts = atkPos.All(x => int.TryParse(x.ToString(), out t));
            bool aNeutInts = atkNeut.All(x => int.TryParse(x.ToString(), out u));
            bool aNegInts = atkNeg.All(x => int.TryParse(x.ToString(), out o));
            bool sPosInts = speedPos.All(x => int.TryParse(x.ToString(), out p));
            bool sNeutInts = speedNeut.All(x => int.TryParse(x.ToString(), out l));
            bool sNegInts = speedNeg.All(x => int.TryParse(x.ToString(), out k));

            // Base Ball Validation
            if (baseBall == false && boxBaseBall.Text.Equals(boxLegendBall.Text) || int.Parse(boxBaseBallValue.Text) < 4 && boxBaseBall.Text.Equals(boxLegendBall.Text) 
                || int.Parse(boxBaseBallValue.Text) > 999 && boxBaseBall.Text.Equals(boxLegendBall.Text))
                MessageBox.Show("Your Base Ball Value needs to be a number between 4 and 999!", "Error: Base Ball Value", MessageBoxButtons.OK, MessageBoxIcon.Error);
            else if (baseBall == false || int.Parse(boxBaseBallValue.Text) < 3 || int.Parse(boxBaseBallValue.Text) > 999)
                MessageBox.Show("Your Base Ball Value needs to be a number between 3 and 999!", "Error: Base Ball Value", MessageBoxButtons.OK, MessageBoxIcon.Error);

            // Legendary Ball Validation
            else if (legendBall == false && boxBaseBall.Text.Equals(boxLegendBall.Text) || int.Parse(boxLegendBallValue.Text) < 4 && boxBaseBall.Text.Equals(boxLegendBall.Text) 
                || int.Parse(boxLegendBallValue.Text) > 999 && boxBaseBall.Text.Equals(boxLegendBall.Text))
                MessageBox.Show("Your Legend Ball Value needs to be a number between 4 and 999!", "Error: Legend Ball Value", MessageBoxButtons.OK, MessageBoxIcon.Error);
            else if (legendBall == false || int.Parse(boxLegendBallValue.Text) < 1 || int.Parse(boxLegendBallValue.Text) > 999)
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
            else if (dynite == false && boxMode.Text == "Keep Path" || int.Parse(boxDyniteOre.Text) < 0 && boxMode.Text == "Keep Path" || int.Parse(boxDyniteOre.Text) > 999 && boxMode.Text == "Keep Path")
                MessageBox.Show("Your Dynite Ore needs to be a number between 0 and 999!", "Error: Dynite Ore", MessageBoxButtons.OK, MessageBoxIcon.Error);
            else if (dynite == false || int.Parse(boxDyniteOre.Text) > 999)
                MessageBox.Show("Your Dynite Ore needs to be a number less than 999!", "Error: Dynite Ore", MessageBoxButtons.OK, MessageBoxIcon.Error);

            // Consecutive Resets Validation
            else if (resets == false || int.Parse(boxLegendBallValue.Text) < 0)
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
            else if (webhookToken == false)
                MessageBox.Show("Your Webhook Token should be a string of numbers.", "Error: Webhook Token", MessageBoxButtons.OK, MessageBoxIcon.Error);

            // Discord Validation
            else if (userID == false || boxUserID.Text.Length != 18)
                MessageBox.Show("Your Discord User ID should be a string of numbers with the length 18.", "Error: User ID", MessageBoxButtons.OK, MessageBoxIcon.Error);

            else
                setConfig();
        }

        // Method to change the Config.toml
        private void setConfig()
        {
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
            t["BOSS"] = boxPokemon.Text;
            t["BASE_BALL"] = boxBaseBall.Text;
            t["BASE_BALLS"] = int.Parse(boxBaseBallValue.Text);
            t["LEGENDARY_BALL"] = boxLegendBall.Text;
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

            // Game Language Setting
            t["language"]["LANGUAGE"] = boxGameLanguage.Text;

            // Pokémon Data Settings
            t["pokemon_data_paths"]["Boss_Pokemon"] = "data/boss_pokemon.json";
            t["pokemon_data_paths"]["Rental_Pokemon"] = "data/rental_pokemon.json";
            t["pokemon_data_paths"]["Boss_Matchup_LUT"] = "data/boss_matchup_LUT.json";
            t["pokemon_data_paths"]["Rental_Matchup_LUT"] = "data/rental_matchup_LUT.json";
            t["pokemon_data_paths"]["Rental_Pokemon_Scores"] = "data/rental_pokemon_scores.json";
            t["pokemon_data_paths"]["path_tree_path"] = "data/path_tree.json";
            t["pokemon_data_paths"]["balls_path"] = "data/balls.json";
            t["pokemon_data_paths"]["type_icon_path"] = "data/type_icons.pickle";
            t["pokemon_data_paths"]["pokemon_sprite_path"] = "data/pokemon_sprites.pickle";
            t["pokemon_data_paths"]["misc_icon_dir"] = "data/misc_icons/";

            // Other Language Settings
            // English
            t["English"]["TESSERACT_LANG_NAME"] = "eng";
            t["English"]["DATA_LANG_NAME"] = "en";
            t["English"]["BACKPACKER"] = "backpacker";
            t["English"]["SCIENTIST"] = "swapping";
            t["English"]["PATH"] = "path";
            t["English"]["FAINT"] = "The storm";
            t["English"]["START_PHRASE"] = "Would you like to embark";
            t["English"]["WEATHER_CLEAR"] = "sunlight faded|rain stopped|sandstorm subsided|hail stopped";
            t["English"]["WEATHER_SUNLIGHT"] = "sunlight turned";
            t["English"]["WEATHER_RAIN"] = "started to rain";
            t["English"]["WEATHER_SANDSTORM"] = "sandstorm kicked";
            t["English"]["WEATHER_HAIL"] = "started to hail";
            t["English"]["TERRAIN_CLEAR"] = "electricity disappeared|grass disappeared|mist disappeared|weirdness disappeared";
            t["English"]["TERRAIN_ELECTRIC"] = "electric current ran";
            t["English"]["TERRAIN_GRASSY"] = "Grass grew";
            t["English"]["TERRAIN_MISTY"] = "Mist swirled";
            t["English"]["TERRAIN_PSYCHIC"] = "got weird";

            // Spanish
            t["Spanish"]["TESSERACT_LANG_NAME"] = "spa";
            t["Spanish"]["DATA_LANG_NAME"] = "sp";
            t["Spanish"]["BACKPACKER"] = "mis objetos";
            t["Spanish"]["SCIENTIST"] = "préstamo";
            t["Spanish"]["PATH"] = "quieres seguir";
            t["Spanish"]["FAINT"] = "La tormenta";
            t["Spanish"]["START_PHRASE"] = "emprender";
            t["Spanish"]["WEATHER_CLEAR"] = "PLACEHOLDER";
            t["Spanish"]["WEATHER_SUNLIGHT"] = "PLACEHOLDER";
            t["Spanish"]["WEATHER_RAIN"] = "PLACEHOLDER";
            t["Spanish"]["WEATHER_SANDSTORM"] = "PLACEHOLDER";
            t["Spanish"]["WEATHER_HAIL"] = "PLACEHOLDER";
            t["Spanish"]["TERRAIN_CLEAR"] = "PLACEHOLDER";
            t["Spanish"]["TERRAIN_ELECTRIC"] = "PLACEHOLDER";
            t["Spanish"]["TERRAIN_GRASSY"] = "PLACEHOLDER";
            t["Spanish"]["TERRAIN_MISTY"] = "PLACEHOLDER";
            t["Spanish"]["TERRAIN_PSYCHIC"] = "PLACEHOLDER";

            // French
            t["French"]["TESSERACT_LANG_NAME"] = "fra";
            t["French"]["DATA_LANG_NAME"] = "fr";
            t["French"]["BACKPACKER"] = "Randonneuse";
            t["French"]["SCIENTIST"] = "intéresse";
            t["French"]["PATH"] = "Quel chemin";
            t["French"]["FAINT"] = "au-dessus|intenable";
            t["French"]["START_PHRASE"] = "vous lancer";
            t["French"]["WEATHER_CLEAR"] = "affaiblissent|est arrêtée|sable se calme";
            t["French"]["WEATHER_SUNLIGHT"] = "soleil brillent";
            t["French"]["WEATHER_RAIN"] = "pleuvoir";
            t["French"]["WEATHER_SANDSTORM"] = "tempête de sable se prépare";
            t["French"]["WEATHER_HAIL"] = "gr.ler";
            t["French"]["TERRAIN_CLEAR"] = "est dissipée|gazon disparaît|brume qui recouvrait|redevient normal";
            t["French"]["TERRAIN_ELECTRIC"] = "électricité parcourt";
            t["French"]["TERRAIN_GRASSY"] = "beau gazon";
            t["French"]["TERRAIN_MISTY"] = "couvre de brume";
            t["French"]["TERRAIN_PSYCHIC"] = "réagir de";

            // Korean
            t["Korean"]["TESSERACT_LANG_NAME"] = "kor";
            t["Korean"]["DATA_LANG_NAME"] = "ko";
            t["Korean"]["BACKPACKER"] = "백팩커";
            t["Korean"]["SCIENTIST"] = "교환하|교핟하 ";
            t["Korean"]["PATH"] = "길로";
            t["Korean"]["FAINT"] = "폭풍이|폭풍을|폭품이|폭품을";
            t["Korean"]["START_PHRASE"] = "시작하시겠습니까";
            t["Korean"]["WEATHER_CLEAR"] = "PLACEHOLDER";
            t["Korean"]["WEATHER_SUNLIGHT"] = "PLACEHOLDER";
            t["Korean"]["WEATHER_RAIN"] = "PLACEHOLDER";
            t["Korean"]["WEATHER_SANDSTORM"] = "PLACEHOLDER";
            t["Korean"]["WEATHER_HAIL"] = "PLACEHOLDER";
            t["Korean"]["TERRAIN_CLEAR"] = "PLACEHOLDER";
            t["Korean"]["TERRAIN_ELECTRIC"] = "PLACEHOLDER";
            t["Korean"]["TERRAIN_GRASSY"] = "PLACEHOLDER";
            t["Korean"]["TERRAIN_MISTY"] = "PLACEHOLDER";
            t["Korean"]["TERRAIN_PSYCHIC"] = "PLACEHOLDER";

            // German
            t["German"]["TESSERACT_LANG_NAME"] = "deu";
            t["German"]["DATA_LANG_NAME"] = "de";
            t["German"]["BACKPACKER"] = "Backpackerin";
            t["German"]["SCIENTIST"] = "austauschen";
            t["German"]["PATH"] = "Weg";
            t["German"]["FAINT"] = "Eure Gruppe wurde vom Sturm";
            t["German"]["START_PHRASE"] = "Möchtest du zu einem";
            t["German"]["WEATHER_CLEAR"] = "Sonnenlicht verliert|auf zu regnen|Sandsturm legt sich|auf zu hageln";
            t["German"]["WEATHER_SUNLIGHT"] = "Sonnenlicht wird";
            t["German"]["WEATHER_RAIN"] = "an zu regnen";
            t["German"]["WEATHER_SANDSTORM"] = "Sandsturm kommt auf";
            t["German"]["WEATHER_HAIL"] = "an zu hageln";
            t["German"]["TERRAIN_CLEAR"] = "feld ist wieder";
            t["German"]["TERRAIN_ELECTRIC"] = "Elektrische Energie";
            t["German"]["TERRAIN_GRASSY"] = "Dichtes Gras";
            t["German"]["TERRAIN_MISTY"] = "Nebel aus";
            t["German"]["TERRAIN_PSYCHIC"] = "seltsam an";

            using (StreamWriter writer = new StreamWriter(File.Open(configData, FileMode.Create)))
            {
                t.WriteTo(writer);
                writer.Flush();
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
    }
}

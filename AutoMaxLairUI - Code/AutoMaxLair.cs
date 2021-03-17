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
using AutoMaxLair;

namespace AutoDA
{
    public partial class MainWindow : Form
    {
        public MainWindow()
        {
            InitializeComponent();
            getConfig();
        }

        FilterInfoCollection filterInfoCollection;


        private void AutoDA_Load(object sender, EventArgs e)
        {
            Initialize_Add();
            int i = 0;
            // Get every Video Capture device and put it into the combobox (with right order)
            filterInfoCollection = new FilterInfoCollection(FilterCategory.VideoInputDevice);
            foreach (FilterInfo filterInfo in filterInfoCollection)
            {
                boxVideoCapture.Items.Insert(i, filterInfo.Name);
                i = i++;
            }

            boxVideoCapture.SelectedIndex = 0;

            
            bool darktheme;
            darktheme = AutoMaxLair.Properties.Settings.Default.DarkTheme;

            if (darktheme == true)
            {
                ApplyTheme(zcolor(11, 8, 20), zcolor(11, 8, 20), zcolor(11, 8, 20), zcolor(36, 33, 40), zcolor(36, 33, 40), zcolor(36, 33, 40), zcolor(250, 63, 82));
                btnSave.BackgroundImage = AutoMaxLair.Properties.Resources.Save1;
                btnSettings.BackgroundImage = AutoMaxLair.Properties.Resources.Settings1;
            }
            else
            {
                ApplyTheme(Color.White, Color.LightGray, Color.LightGray, Color.White, Color.LightGray, Color.White, Color.Black);
                btnSave.BackgroundImage = AutoMaxLair.Properties.Resources.Save2;
                btnSettings.BackgroundImage = AutoMaxLair.Properties.Resources.Settings2;
            }

            
                
            
            boxVideoCapture.SelectedIndex = 0;
            //Add(filterInfo.Name);
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

                boxPokemon.Text = Utils.ConvertBossIdToBossName(t["BOSS"]);
                boxBaseBall.Text = Utils.ConvertBallIdToBallName(t["BASE_BALL"]);
                boxBaseBallValue.Text = t["BASE_BALLS"];
                boxLegendBall.Text = Utils.ConvertBallIdToBallName(t["LEGENDARY_BALL"]);
                boxLegendBallValue.Text = t["LEGENDARY_BALLS"];
                boxMode.Text = t["MODE"];
                boxComPort.Text = t["COM_PORT"];
                boxTesseract.Text = t["TESSERACT_PATH"];
                boxVideoScale.Text = t["advanced"]["VIDEO_SCALE"];
                boxVideoDelay.Text = t["advanced"]["VIDEO_EXTRA_DELAY"];
                boxBossIndex.Text = t["advanced"]["BOSS_INDEX"];
                boxDyniteOre.Text = t["advanced"]["DYNITE_ORE"];
                boxConsecutiveResets.Text = t["advanced"]["CONSECUTIVE_RESETS"];
                boxMaxDynite.Text = t["advanced"]["MAXIMUM_ORE_COST"];
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


            bool bossValue = int.TryParse(boxBossIndex.Text, out int i);
            bool baseBall = int.TryParse(boxBaseBallValue.Text, out int x);
            bool legendBall = int.TryParse(boxLegendBallValue.Text, out int y);
            bool dynite = int.TryParse(boxDyniteOre.Text, out int q);
            bool resets = int.TryParse(boxConsecutiveResets.Text, out int w);
            bool maxdynite = int.TryParse(boxMaxDynite.Text, out int h);
            bool webhookID = float.TryParse(boxWebhookID.Text, out float j);
            bool userID = float.TryParse(boxUserID.Text, out float g);

            bool videoScale = float.TryParse(boxVideoScale.Text, out float a);
            bool videoDelay = float.TryParse(boxVideoDelay.Text, out float b);

            bool aPosInts = atkPos.All(x => int.TryParse(x.ToString(), out int t));
            bool aNeutInts = atkNeut.All(x => int.TryParse(x.ToString(), out int u));
            bool aNegInts = atkNeg.All(x => int.TryParse(x.ToString(), out int o));
            bool sPosInts = speedPos.All(x => int.TryParse(x.ToString(), out int p));
            bool sNeutInts = speedNeut.All(x => int.TryParse(x.ToString(), out int l));
            bool sNegInts = speedNeg.All(x => int.TryParse(x.ToString(), out int k));

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
            else if (maxdynite == false | maxdynite == true && h > 10 | maxdynite == true && h < 0)
                MessageBox.Show("Your maximum Dynite Ore needs to be a number between 0 and 10!", "Error: Dynite Ore", MessageBoxButtons.OK, MessageBoxIcon.Error);

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

                t = tt;

                // Get all values in a string-array
                string[] atkPos = boxAttackPos.Text.Split(',').ToArray();
                string[] atkNeut = boxAttackNeut.Text.Split(',').ToArray();
                string[] atkNeg = boxAttackNeg.Text.Split(',').ToArray();
                string[] speedPos = boxSpeedPos.Text.Split(',').ToArray();
                string[] speedNeut = boxSpeedNeut.Text.Split(',').ToArray();
                string[] speedNeg = boxSpeedNeg.Text.Split(',').ToArray();

                // General Settings
                t["BOSS"].AsString.Value = Utils.ConvertBossNameToBossId(boxPokemon.Text);
                t["BASE_BALL"].AsString.Value = Utils.ConvertBallNameToBallId(boxBaseBall.Text);
                t["BASE_BALLS"].AsInteger.Value = int.Parse(boxBaseBallValue.Text);
                t["LEGENDARY_BALL"].AsString.Value = Utils.ConvertBallNameToBallId(boxLegendBall.Text);
                t["LEGENDARY_BALLS"].AsInteger.Value = int.Parse(boxLegendBallValue.Text);
                t["MODE"].AsString.Value = boxMode.Text.ToUpper();
                t["COM_PORT"].AsString.Value = boxComPort.Text;
                t["VIDEO_INDEX"].AsInteger.Value = boxVideoCapture.SelectedIndex;
                t["TESSERACT_PATH"].AsString.Value = boxTesseract.Text;

                // Advanced Settings
                t["advanced"]["VIDEO_SCALE"].AsFloat.Value = float.Parse(boxVideoScale.Text);
                t["advanced"]["VIDEO_EXTRA_DELAY"].AsFloat.Value = float.Parse(boxVideoDelay.Text);
                t["advanced"]["BOSS_INDEX"].AsInteger.Value = boss;
                t["advanced"]["DYNITE_ORE"].AsInteger.Value = int.Parse(boxDyniteOre.Text);
                t["advanced"]["CONSECUTIVE_RESETS"].AsInteger.Value = int.Parse(boxConsecutiveResets.Text);
                t["advanced"]["MAXIMUM_ORE_COST"].AsInteger.Value = int.Parse(boxMaxDynite.Text);
                t["advanced"]["ENABLE_DEBUG_LOGS"].AsBoolean.Value = checkBoxDebugLogs.Checked;

                // Stat Settings
                t["stats"]["CHECK_ATTACK_STAT"].AsBoolean.Value = boxCheckAttack.Checked;
                t["stats"]["CHECK_SPEED_STAT"].AsBoolean.Value = boxCheckSpeed.Checked;

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
                t["discord"]["WEBHOOK_ID"].AsString.Value = boxWebhookID.Text;
                t["discord"]["WEBHOOK_TOKEN"].AsString.Value = boxWebhookToken.Text;
                t["discord"]["USER_ID"].AsString.Value = boxUserID.Text;
                t["discord"]["USER_SHORT_NAME"].AsString.Value = boxPingName.Text;
                t["discord"]["UPDATE_LEVELS"].AsString.Value = boxPingSettings.Text;

                // Game Language Settings
                t["language"]["LANGUAGE"].AsString.Value = boxGameLanguage.Text;

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

        // Does the setConfig() Method when you press the "Save-Button"
        private void btnSave_Click(object sender, EventArgs e)
        {
            validate();
        }

        private void toolTip_Popup(object sender, PopupEventArgs e)
        {

        }
        private void btnTesseract_Click(object sender, EventArgs e)
        {
            FolderBrowserDialog fbd = new FolderBrowserDialog();
            fbd.RootFolder = Environment.SpecialFolder.ProgramFiles;
            if (fbd.ShowDialog() == System.Windows.Forms.DialogResult.OK)
                boxTesseract.Text = fbd.SelectedPath;
        }

        private void labelTessaract_Click(object sender, EventArgs e)
        {

        }

        private void boxTesseract_TextChanged(object sender, EventArgs e)
        {

        }

        private void labelGameLanguage_Click(object sender, EventArgs e)
        {

        }

        private void boxGameLanguage_SelectedIndexChanged(object sender, EventArgs e)
        {

        }

        private void btnSettings_Click(object sender, EventArgs e)
        {
            Settings form = new Settings();
            form.Show(this);
        }

        Color zcolor(int r, int g, int b)
        {
            return Color.FromArgb(r, g, b);
        }

        List<Control> panels, panels2;
        List<Control> buttons;
        List<Control> labels;
        List<Control> comboboxes;
        List<Control> textboxes;
        List<Control> checkboxes;

        void Initialize_Add()
        {
            panels = new List<Control>();
            panels2 = new List<Control>();
            buttons = new List<Control>();
            labels = new List<Control>();
            comboboxes = new List<Control>();
            textboxes = new List<Control>();
            checkboxes = new List<Control>();


            panels.Add(panelLogo);
            panels.Add(panelSideMenu);
            panels.Add(panelRightSide);
            panels.Add(panelRightTop);

            panels2.Add(panelAdvancedSettingsSubmenu);
            panels2.Add(panelDiscordSubmenu);
            panels2.Add(panelSettingSubmenu);
            panels2.Add(panelStatSubmenu);

            buttons.Add(btnAdvancedSettings);
            buttons.Add(btnDiscord);
            buttons.Add(btnSave);
            buttons.Add(btnSetting);
            buttons.Add(btnStats);
            buttons.Add(btnTesseract);
            buttons.Add(btnSettings);

            labels.Add(labelAttackNeg);
            labels.Add(labelAttackNeut);
            labels.Add(labelAttackPos);
            labels.Add(labelSpeedNeg);
            labels.Add(labelSpeedNeut);
            labels.Add(labelSpeedPos);
            labels.Add(labelBaseBall);
            labels.Add(labelBossIndex);
            labels.Add(labelComPort);
            labels.Add(labelConsecutiveResets);
            labels.Add(labelDyniteOre);
            labels.Add(labelGameLanguage);
            labels.Add(labelHuntingPoke);
            labels.Add(labelLegendBall);
            panels.Add(labelLogo);
            labels.Add(labelMode);
            labels.Add(labelPokémon);
            labels.Add(labelRun);
            labels.Add(labelShinies);
            labels.Add(labelShiniesFound);
            labels.Add(labelTessaract);
            labels.Add(labelVideoDelay);
            labels.Add(labelVideoIndex);
            labels.Add(labelVideoScale);
            labels.Add(labelWinPercentage);
            labels.Add(labelWebID);
            labels.Add(labelWebToken);
            labels.Add(labelUser);
            labels.Add(labelID);
            labels.Add(labelMessages);
            labels.Add(labelAtk);
            labels.Add(labelSpeed);

            comboboxes.Add(boxBossIndex);
            comboboxes.Add(boxPokemon);
            comboboxes.Add(boxBaseBall);
            comboboxes.Add(boxLegendBall);
            comboboxes.Add(boxMode);
            comboboxes.Add(boxVideoCapture);
            comboboxes.Add(boxGameLanguage);
            comboboxes.Add(boxPingSettings);

            textboxes.Add(boxBaseBallValue);
            textboxes.Add(boxLegendBallValue);
            textboxes.Add(boxComPort);
            textboxes.Add(boxTesseract);
            textboxes.Add(boxVideoScale);
            textboxes.Add(boxVideoDelay);
            textboxes.Add(boxDyniteOre);
            textboxes.Add(boxConsecutiveResets);
            textboxes.Add(boxAttackNeg);
            textboxes.Add(boxAttackNeut);
            textboxes.Add(boxAttackPos);
            textboxes.Add(boxSpeedNeg);
            textboxes.Add(boxSpeedNeut);
            textboxes.Add(boxSpeedPos);
            textboxes.Add(boxWebhookID);
            textboxes.Add(boxWebhookToken);
            textboxes.Add(boxUserID);
            textboxes.Add(boxPingName);

            checkboxes.Add(checkBoxDebugLogs);
            checkboxes.Add(boxCheckAttack);
            checkboxes.Add(boxCheckSpeed);
        }

        public void ApplyTheme(Color back, Color pan, Color btn, Color lab, Color cbox, Color tbox, Color textC)
        {
            this.BackColor = lab;
            this.ForeColor = textC;

            foreach (Control item in panels)
            {
                item.BackColor = pan;
                item.ForeColor = textC;
            }

            foreach (Control item in panels2)
            {
                item.BackColor = tbox;
                item.ForeColor = textC;
            }

            foreach (Control item in buttons)
            {
                item.BackColor = btn;
                item.ForeColor = textC;
            }

            foreach (Control item in labels)
            {
                item.BackColor = lab;
                item.ForeColor = textC;
            }

            foreach (Control item in comboboxes)
            {
                item.BackColor = cbox;
                item.ForeColor = textC;
            }

            foreach (Control item in textboxes)
            {
                item.BackColor = tbox;
                item.ForeColor = textC;
            }

            foreach (Control item in checkboxes)
            {
                item.BackColor = lab;
                item.ForeColor = textC;
            }
        }
    }

   
}

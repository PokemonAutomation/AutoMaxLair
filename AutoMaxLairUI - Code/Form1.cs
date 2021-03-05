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

        // Method to get the preset for the UI
        private void getConfig()
        {
            // Read from txt file
            string path = Directory.GetCurrentDirectory();
            string configData = path + @"\config.txt";
            string[] arrConfig = File.ReadAllLines(configData);

            // Put the Strings to the boxes
            boxPokemon.Text = arrConfig[0];
            boxBaseBall.Text = arrConfig[1];
            boxBaseBallValue.Text = arrConfig[2];
            boxLegendBall.Text = arrConfig[3];
            boxLegendBallValue.Text = arrConfig[4];
            boxMode.Text = arrConfig[5];
            boxComPort.Text = arrConfig[6];
            boxVideoIndex.Text = arrConfig[7];
            boxTesseract.Text = arrConfig[8];
            boxVideoScale.Text = arrConfig[9];
            boxVideoDelay.Text = arrConfig[10];
            boxBossIndex.Text = arrConfig[11];
            boxDyniteOre.Text = arrConfig[12];
            boxConsecutiveResets.Text = arrConfig[13];
            if (arrConfig[14] == "true")
            {
                checkBoxDebugLogs.Checked = true;
            }
            if (arrConfig[14] == "false")
            {
                checkBoxDebugLogs.Checked = false;
            }
            if (arrConfig[15] == "true")
            {
                boxCheckAttack.Checked = true;
            }
            if (arrConfig[15] == "false")
            {
                boxCheckAttack.Checked = false;
            }
            if (arrConfig[16] == "true")
            {
                boxCheckSpeed.Checked = true;
            }
            if (arrConfig[16] == "false")
            {
                boxCheckSpeed.Checked = false;
            }
            boxAttackPos.Text = arrConfig[17];
            boxAttackNeut.Text = arrConfig[18];
            boxAttackNeg.Text = arrConfig[19];
            boxSpeedPos.Text = arrConfig[20];
            boxSpeedNeut.Text = arrConfig[21];
            boxSpeedNeg.Text = arrConfig[22];
            boxWebhookID.Text = arrConfig[23];
            boxWebhookToken.Text = arrConfig[24];
            boxUserID.Text = arrConfig[25];
            boxPingName.Text = arrConfig[26];
            boxPingSettings.Text = arrConfig[27];
            boxGameLanguage.Text = arrConfig[28];
        }

        // Method to save the preset for the UI
        private void setConfig()
        {
            // Save strings to txt
            string path = Directory.GetCurrentDirectory();
            string configData = path + @"\config.txt";
            string[] arrConfig = File.ReadAllLines(configData);

            string selectedPokemon = this.boxPokemon.GetItemText(this.boxPokemon.SelectedItem);
            string selectedBaseBall = this.boxBaseBall.GetItemText(this.boxBaseBall.SelectedItem);
            string selectedLegendBall = this.boxLegendBall.GetItemText(this.boxLegendBall.SelectedItem);
            string selectedMode = this.boxMode.GetItemText(this.boxMode.SelectedItem);
            string selectedBaseBallValue = boxBaseBallValue.Text;
            string selectedLegendBallValue = boxLegendBallValue.Text;
            string selectedComPort = boxComPort.Text;
            string selectedVideoIndex = boxVideoIndex.Text;
            string selectedVideoScale = boxVideoScale.Text;
            string selectedTessaract = boxTesseract.Text;
            string selectedVideoDelay = boxVideoDelay.Text;
            string selectedBossIndex = this.boxBossIndex.GetItemText(this.boxBossIndex.SelectedItem);
            string selectedDyniteOre = boxDyniteOre.Text;
            string selectedResets = boxConsecutiveResets.Text;
            string selectedDebugLogs = "true";
            string selectedAttackStat = "true";
            string selectedSpeedStat = "true";
            if (checkBoxDebugLogs.Checked == true)
            {
                selectedDebugLogs = "true";
            }
            else
            {
                selectedDebugLogs = "false";
            }
            if (boxCheckAttack.Checked == true)
            {
                 selectedAttackStat= "true";
            }
            else
            {
                selectedAttackStat = "false";
            }
            if (boxCheckSpeed.Checked == true)
            {
                selectedSpeedStat = "true";
            }
            else
            {
                selectedSpeedStat = "false";
            }
            string selectedAttackPos = boxAttackPos.Text;
            string selectedAttackNeut = boxAttackNeut.Text;
            string selectedAttackNeg = boxAttackNeg.Text;
            string selectedSpeedPos = boxSpeedPos.Text;
            string selectedSpeedNeut = boxSpeedNeut.Text;
            string selectedSpeedNeg = boxSpeedNeg.Text;
            string selectedWebhookID = boxWebhookID.Text;
            string selectedWebhookToken = boxWebhookToken.Text;
            string selectedUserID = boxUserID.Text;
            string selectedUsername = boxPingName.Text;
            string selectedPing = boxPingSettings.Text;
            string selectedLanguage = boxGameLanguage.Text;

            arrConfig[0] = selectedPokemon;
            arrConfig[1] = selectedBaseBall;
            arrConfig[2] = selectedBaseBallValue;
            arrConfig[3] = selectedLegendBall;
            arrConfig[4] = selectedLegendBallValue;
            arrConfig[5] = selectedMode;
            arrConfig[6] = selectedComPort;
            arrConfig[7] = selectedVideoIndex;
            arrConfig[8] = selectedTessaract;
            arrConfig[9] = selectedVideoScale;
            arrConfig[10] = selectedVideoDelay;
            arrConfig[11] = selectedBossIndex;
            arrConfig[12] = selectedDyniteOre;
            arrConfig[13] = selectedResets;
            arrConfig[14] = selectedDebugLogs;
            arrConfig[15] = selectedAttackStat;
            arrConfig[16] = selectedSpeedStat;
            arrConfig[17] = selectedAttackPos;
            arrConfig[18] = selectedAttackNeut;
            arrConfig[19] = selectedAttackNeg;
            arrConfig[20] = selectedSpeedPos;
            arrConfig[21] = selectedSpeedNeut;
            arrConfig[22] = selectedSpeedNeg;
            arrConfig[23] = selectedWebhookID;
            arrConfig[24] = selectedWebhookToken;
            arrConfig[25] = selectedUserID;
            arrConfig[26] = selectedUsername;
            arrConfig[27] = selectedPing;
            arrConfig[28] = selectedLanguage;
            File.WriteAllLines(configData, arrConfig);

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

        // The heart of the code. This method rewrites the specific lines in the TOML file to match them with the UI. e.g. BOSS = "dialga", etc.
        public static void lineChanger(string pokemon, string baseBall, string legendBall, string baseBallValue, 
            string legendBallValue, string mode, string comPort, string videoIndex, string tessaract, string videoScale, string videoDelay, string bossIndex, 
            string dyniteOre, string resets, string debugLogs, string attack, string speed, int atkpos, int atkneut, int atkneg, int speedpos, int speedneut,
            int speedneg, string webid, string webtoken, string userid, string username, string ping, string language)
        {
            string configFile = Directory.GetCurrentDirectory() + @"\Config.toml";
            int editPokemon = 23;
            int editBaseBall = 29;
            int editBaseBallValue = 32;
            int editLegendBall = 38;
            int editLegendBallValue = 42;
            int editMode = 59;
            int editComPort = 66;
            int editVideoIndex = 70;
            int editTessaract = 76;
            int editVideoScale = 85;
            int editVideoDelay = 91;
            int editBossIndex = 95;
            int editDyniteOre = 98;
            int editResets = 102;
            int editDebugLogs = 106;
            int editAttack = 115;
            int editSpeed = 118;
            int editAttackPos = 126;
            int editAttackNeut = 127;
            int editAttackNeg = 128;
            int editSpeedPos = 136;
            int editSpeedNeut = 137;
            int editSpeedNeg = 138;
            int editWebID = 149;
            int editWebToken = 150;
            int editUserID = 154;
            int editUsername = 158;
            int editPing = 165;
            int editLanguage = 173;

            string[] arrLine = File.ReadAllLines(configFile);
            arrLine[editPokemon - 1] = "BOSS = \"" + pokemon + "\"";
            arrLine[editBaseBall - 1] = "BASE_BALL = \"" + baseBall + "\"";
            arrLine[editBaseBallValue - 1] = "BASE_BALLS = " + baseBallValue;
            arrLine[editLegendBall - 1] = "LEGENDARY_BALL = \"" + legendBall + "\"";
            arrLine[editLegendBallValue - 1] = "LEGENDARY_BALLS = " + legendBallValue;
            arrLine[editMode - 1] = "MODE = \"" + mode + "\"";
            arrLine[editComPort - 1] = "COM_PORT = \"" + comPort + "\"";
            arrLine[editVideoIndex - 1] = "VIDEO_INDEX = " + videoIndex;
            arrLine[editTessaract - 1] = "TESSERACT_PATH = \"" + tessaract + "\"";
            arrLine[editVideoScale - 1] = "VIDEO_SCALE = " + videoScale;
            arrLine[editVideoDelay - 1] = "VIDEO_EXTRA_DELAY = " + videoDelay;
            arrLine[editBossIndex - 1] = "BOSS_INDEX = " + bossIndex;
            arrLine[editDyniteOre - 1] = "DYNITE_ORE = " + dyniteOre;
            arrLine[editResets - 1] = "CONSECUTIVE_RESETS = " + resets;
            arrLine[editDebugLogs - 1] = "ENABLE_DEBUG_LOGS = " + debugLogs;
            arrLine[editAttack - 1] = "CHECK_ATTACK_STAT = " + attack;
            arrLine[editSpeed - 1] = "CHECK_SPEED_STAT = " + speed;
            arrLine[editAttackPos - 1] = "positive = [" + atkpos + ", " + ++atkpos + "]";
            arrLine[editAttackNeut - 1] = "neutral = [" + atkneut + ", " + ++atkneut + "]";
            arrLine[editAttackNeg - 1] = "negative = [" + atkneg + ", " + ++atkneg + "]";
            arrLine[editSpeedPos - 1] = "positive = [" + speedpos + ", " + ++speedpos + "]";
            arrLine[editSpeedNeut - 1] = "neutral = [" + speedneut + ", " + ++speedneut + "]";
            arrLine[editSpeedNeg - 1] = "negative = [" + speedneg + ", " + ++speedneg + "]";
            arrLine[editWebID - 1] = "WEBHOOK_ID = \"" + webid + "\"";
            arrLine[editWebToken - 1] = "WEBHOOK_TOKEN = \"" + webtoken + "\"";
            arrLine[editUserID - 1] = "USER_ID = \"" + userid + "\"";
            arrLine[editUsername - 1] = "USER_SHORT_NAME = \"" + username + "\"";
            arrLine[editPing - 1] = "UPDATE_LEVELS = \"" + ping + "\"";
            arrLine[editLanguage - 1] = "LANGUAGE = \"" + language + "\"";
            File.WriteAllLines(configFile, arrLine);
        }

        // Saves the preset for the UI and changes the TOML
        private void btnSave_Click(object sender, EventArgs e)
        {
            setConfig();

            // Getting strings + ints from the boxes
            string selectedPokemon = this.boxPokemon.GetItemText(this.boxPokemon.SelectedItem);
            string selectedBaseBall = this.boxBaseBall.GetItemText(this.boxBaseBall.SelectedItem);
            string selectedLegendBall = this.boxLegendBall.GetItemText(this.boxLegendBall.SelectedItem);
            string selectedMode = this.boxMode.GetItemText(this.boxMode.SelectedItem);
            string selectedBaseBallValue = boxBaseBallValue.Text;
            string selectedLegendBallValue = boxLegendBallValue.Text;
            string selectedComPort = boxComPort.Text;
            string selectedVideoIndex = boxVideoIndex.Text;
            string selectedTessaract = boxTesseract.Text;
            string selectedVideoScale = boxVideoScale.Text;
            string selectedVideoDelay = boxVideoDelay.Text;
            string selectedBossIndex = this.boxBossIndex.GetItemText(this.boxBossIndex.SelectedItem);
            string selectedBoss = "0";
            if (selectedBossIndex == "Top")
            {
                selectedBoss = "0";
            }
            else if (selectedBossIndex == "Middle")
            {
                selectedBoss = "1";
            }
            else if (selectedBossIndex == "Bottom")
            {
                selectedBoss = "2";
            }
            string selectedDyniteOre = boxDyniteOre.Text;
            string selectedResets = boxConsecutiveResets.Text;
            string selectedDebugLogs = "true";
            if (checkBoxDebugLogs.Checked == true)
            {
                selectedDebugLogs = "true";
            }
            else
            {
                selectedDebugLogs = "false";
            }
            string selectedAttackStats = "true";
            if (boxCheckAttack.Checked == true)
            {
                selectedAttackStats = "true";
            }
            else
            {
                selectedAttackStats = "false";
            }
            string selectedSpeedStats = "true";
            if (boxCheckSpeed.Checked == true)
            {
                selectedSpeedStats = "true";
            }
            else
            {
                selectedSpeedStats = "false";
            }
            string selectedAttackPos = boxAttackPos.Text;
            string selectedAttackNeut = boxAttackNeut.Text;
            string selectedAttackNeg = boxAttackNeg.Text;
            string selectedSpeedPos = boxSpeedPos.Text;
            string selectedSpeedNeut = boxSpeedNeut.Text;
            string selectedSpeedNeg = boxSpeedNeg.Text;
            string selectedWebhookID = boxWebhookID.Text;
            string selectedWebhookToken = boxWebhookToken.Text;
            string selectedUserID = boxUserID.Text;
            string selectedUsername = boxPingName.Text;
            string selectedPing = boxPingSettings.Text;
            string selectedLanguage = boxGameLanguage.Text;
            int attackPos = int.Parse(selectedAttackPos);
            int attackNeut = int.Parse(selectedAttackNeut);
            int attackNeg = int.Parse(selectedAttackNeg);
            int speedPos = int.Parse(selectedSpeedPos);
            int speedNeut = int.Parse(selectedSpeedNeut);
            int speedNeg = int.Parse(selectedSpeedNeg);

            lineChanger(selectedPokemon.ToLower(), selectedBaseBall, selectedLegendBall, selectedBaseBallValue, selectedLegendBallValue,
                selectedMode.ToUpper(), selectedComPort, selectedVideoIndex, selectedTessaract, selectedVideoScale, selectedVideoDelay, selectedBoss,
                selectedDyniteOre, selectedResets, selectedDebugLogs, selectedAttackStats, selectedSpeedStats, attackPos, attackNeut,
                attackNeg, speedPos, speedNeut, speedNeg, selectedWebhookID, selectedWebhookToken, selectedUserID, selectedUsername,
                selectedPing, selectedLanguage);
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
    }
}

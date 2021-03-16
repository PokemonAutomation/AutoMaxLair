using AutoDA;
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.Text;
using System.Windows.Forms;

namespace AutoMaxLair
{
    public partial class Settings : Form
    {
        List<Control> panels, panels2;
        List<Control> buttons;
        List<Control> labels;
        List<Control> comboboxes;
        List<Control> textboxes;
        List<Control> checkboxes;

        

        public Settings()
        {
            InitializeComponent();
            
           
        }

        


        void Initialize_Add()
        {
            panels = new List<Control>();
            panels2 = new List<Control>();
            buttons = new List<Control>();
            labels = new List<Control>();
            comboboxes = new List<Control>();
            textboxes = new List<Control>();
            checkboxes = new List<Control>();

            MainWindow main = (MainWindow)this.Owner;

            panels.Add(main.panelLogo);
            panels.Add(main.panelSideMenu);
            panels.Add(main.panelRightSide);
            panels.Add(main.panelRightTop);

            panels2.Add(main.panelAdvancedSettingsSubmenu);
            panels2.Add(main.panelDiscordSubmenu);
            panels2.Add(main.panelSettingSubmenu);
            panels2.Add(main.panelStatSubmenu);
            panels2.Add(panel1);

            buttons.Add(main.btnAdvancedSettings);
            buttons.Add(main.btnDiscord);
            buttons.Add(main.btnSave);
            buttons.Add(main.btnSetting);
            buttons.Add(main.btnStats);
            buttons.Add(main.btnTesseract);
            buttons.Add(main.btnSettings);

            labels.Add(main.labelAttackNeg);
            labels.Add(main.labelAttackNeut);
            labels.Add(main.labelAttackPos);
            labels.Add(main.labelSpeedNeg);
            labels.Add(main.labelSpeedNeut);
            labels.Add(main.labelSpeedPos);
            labels.Add(main.labelBaseBall);
            labels.Add(main.labelBossIndex);
            labels.Add(main.labelComPort);
            labels.Add(main.labelConsecutiveResets);
            labels.Add(main.labelDyniteOre);
            labels.Add(main.labelMaxDynite);
            labels.Add(main.labelGameLanguage);
            labels.Add(main.labelHuntingPoke);
            labels.Add(main.labelLegendBall);
            panels.Add(main.labelLogo);
            labels.Add(main.labelMode);
            labels.Add(main.labelPokémon);
            labels.Add(main.labelRun);
            labels.Add(main.labelShinies);
            labels.Add(main.labelShiniesFound);
            labels.Add(main.labelTessaract);
            labels.Add(main.labelVideoDelay);
            labels.Add(main.labelVideoIndex);
            labels.Add(main.labelVideoScale);
            labels.Add(main.labelWinPercentage);
            labels.Add(main.labelWebID);
            labels.Add(main.labelWebToken);
            labels.Add(main.labelUser);
            labels.Add(main.labelID);
            labels.Add(main.labelMessages);
            labels.Add(main.labelAtk);
            labels.Add(main.labelSpeed);

            comboboxes.Add(main.boxBossIndex);
            comboboxes.Add(main.boxPokemon);
            comboboxes.Add(main.boxBaseBall);
            comboboxes.Add(main.boxLegendBall);
            comboboxes.Add(main.boxMode);
            comboboxes.Add(main.boxVideoCapture);
            comboboxes.Add(main.boxGameLanguage);
            comboboxes.Add(main.boxPingSettings);

            textboxes.Add(main.boxBaseBallValue);
            textboxes.Add(main.boxLegendBallValue);
            textboxes.Add(main.boxComPort);
            textboxes.Add(main.boxTesseract);
            textboxes.Add(main.boxVideoScale);
            textboxes.Add(main.boxVideoDelay);
            textboxes.Add(main.boxDyniteOre);
            textboxes.Add(main.boxMaxDynite);
            textboxes.Add(main.boxConsecutiveResets);
            textboxes.Add(main.boxAttackNeg);
            textboxes.Add(main.boxAttackNeut);
            textboxes.Add(main.boxAttackPos);
            textboxes.Add(main.boxSpeedNeg);
            textboxes.Add(main.boxSpeedNeut);
            textboxes.Add(main.boxSpeedPos);
            textboxes.Add(main.boxWebhookID);
            textboxes.Add(main.boxWebhookToken);
            textboxes.Add(main.boxUserID);
            textboxes.Add(main.boxPingName);

            checkboxes.Add(main.checkBoxDebugLogs);
            checkboxes.Add(main.boxCheckAttack);
            checkboxes.Add(main.boxCheckSpeed);
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

        public void ChangeColor()
        {
            if (radioDark.Checked == true)
            {
                MainWindow main = (MainWindow)this.Owner;
                ApplyTheme(zcolor(11, 8, 20), zcolor(11, 8, 20), zcolor(11, 8, 20), zcolor(36, 33, 40), zcolor(36, 33, 40), zcolor(36, 33, 40), zcolor(250, 63, 82));
                main.btnSave.BackgroundImage = AutoMaxLair.Properties.Resources.Save1;
                main.btnSettings.BackgroundImage = AutoMaxLair.Properties.Resources.Settings1;
                Properties.Settings.Default.DarkTheme = true;
                Properties.Settings.Default.Save();
            }
            else if (radioLight.Checked == true)
            {
                MainWindow main = (MainWindow)this.Owner;
                ApplyTheme(Color.White, Color.LightGray, Color.LightGray, Color.White, Color.LightGray, Color.White, Color.Black);
                main.btnSave.BackgroundImage = AutoMaxLair.Properties.Resources.Save2;
                main.btnSettings.BackgroundImage = AutoMaxLair.Properties.Resources.Settings2;
                Properties.Settings.Default.DarkTheme = false;
                Properties.Settings.Default.Save();
            }
        }

        Color zcolor(int r, int g, int b)
        {
            return Color.FromArgb(r, g, b);
        }

        private void radioDark_CheckedChanged(object sender, EventArgs e)
        {
            ChangeColor();
        }

        private void radioLight_CheckedChanged(object sender, EventArgs e)
        {
            ChangeColor();
        }

        private void Settings_Load(object sender, EventArgs e)
        {
            Initialize_Add();

            if (Properties.Settings.Default.DarkTheme == true)
                radioDark.Checked = true;
            else if (Properties.Settings.Default.DarkTheme == false)
                radioLight.Checked = true;

        }
    }

}

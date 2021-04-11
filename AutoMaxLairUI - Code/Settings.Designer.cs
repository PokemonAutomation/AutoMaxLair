
namespace AutoMaxLair
{
    partial class Settings
    {
        /// <summary>
        /// Required designer variable.
        /// </summary>
        private System.ComponentModel.IContainer components = null;

        /// <summary>
        /// Clean up any resources being used.
        /// </summary>
        /// <param name="disposing">true if managed resources should be disposed; otherwise, false.</param>
        protected override void Dispose(bool disposing)
        {
            if (disposing && (components != null))
            {
                components.Dispose();
            }
            base.Dispose(disposing);
        }

        #region Windows Form Designer generated code

        /// <summary>
        /// Required method for Designer support - do not modify
        /// the contents of this method with the code editor.
        /// </summary>
        private void InitializeComponent()
        {
            System.ComponentModel.ComponentResourceManager resources = new System.ComponentModel.ComponentResourceManager(typeof(Settings));
            this.panel1 = new System.Windows.Forms.Panel();
            this.groupTheme = new System.Windows.Forms.GroupBox();
            this.radioDark = new System.Windows.Forms.RadioButton();
            this.radioLight = new System.Windows.Forms.RadioButton();
            this.panel1.SuspendLayout();
            this.groupTheme.SuspendLayout();
            this.SuspendLayout();
            // 
            // panel1
            // 
            this.panel1.BackColor = System.Drawing.Color.FromArgb(((int)(((byte)(36)))), ((int)(((byte)(33)))), ((int)(((byte)(40)))));
            this.panel1.Controls.Add(this.groupTheme);
            this.panel1.Dock = System.Windows.Forms.DockStyle.Top;
            this.panel1.Location = new System.Drawing.Point(0, 0);
            this.panel1.Name = "panel1";
            this.panel1.Size = new System.Drawing.Size(234, 135);
            this.panel1.TabIndex = 0;
            // 
            // groupTheme
            // 
            this.groupTheme.Controls.Add(this.radioDark);
            this.groupTheme.Controls.Add(this.radioLight);
            this.groupTheme.FlatStyle = System.Windows.Forms.FlatStyle.Flat;
            this.groupTheme.Location = new System.Drawing.Point(12, 12);
            this.groupTheme.Name = "groupTheme";
            this.groupTheme.Size = new System.Drawing.Size(200, 100);
            this.groupTheme.TabIndex = 1;
            this.groupTheme.TabStop = false;
            this.groupTheme.Text = "Theme";
            // 
            // radioDark
            // 
            this.radioDark.AutoSize = true;
            this.radioDark.Checked = true;
            this.radioDark.FlatStyle = System.Windows.Forms.FlatStyle.Flat;
            this.radioDark.Location = new System.Drawing.Point(12, 34);
            this.radioDark.Name = "radioDark";
            this.radioDark.Size = new System.Drawing.Size(87, 19);
            this.radioDark.TabIndex = 0;
            this.radioDark.TabStop = true;
            this.radioDark.Text = "Dark Theme";
            this.radioDark.UseVisualStyleBackColor = true;
            this.radioDark.CheckedChanged += new System.EventHandler(this.radioDark_CheckedChanged);
            // 
            // radioLight
            // 
            this.radioLight.AutoSize = true;
            this.radioLight.FlatStyle = System.Windows.Forms.FlatStyle.Flat;
            this.radioLight.Location = new System.Drawing.Point(12, 59);
            this.radioLight.Name = "radioLight";
            this.radioLight.Size = new System.Drawing.Size(90, 19);
            this.radioLight.TabIndex = 0;
            this.radioLight.TabStop = true;
            this.radioLight.Text = "Light Theme";
            this.radioLight.UseVisualStyleBackColor = true;
            this.radioLight.CheckedChanged += new System.EventHandler(this.radioLight_CheckedChanged);
            // 
            // Settings
            // 
            this.AutoScaleDimensions = new System.Drawing.SizeF(7F, 15F);
            this.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font;
            this.BackColor = System.Drawing.Color.FromArgb(((int)(((byte)(11)))), ((int)(((byte)(8)))), ((int)(((byte)(20)))));
            this.ClientSize = new System.Drawing.Size(234, 133);
            this.Controls.Add(this.panel1);
            this.ForeColor = System.Drawing.Color.FromArgb(((int)(((byte)(250)))), ((int)(((byte)(63)))), ((int)(((byte)(82)))));
            this.FormBorderStyle = System.Windows.Forms.FormBorderStyle.FixedSingle;
            this.Icon = ((System.Drawing.Icon)(resources.GetObject("$this.Icon")));
            this.Name = "Settings";
            this.StartPosition = System.Windows.Forms.FormStartPosition.CenterScreen;
            this.Text = "Settings";
            this.Load += new System.EventHandler(this.Settings_Load);
            this.panel1.ResumeLayout(false);
            this.groupTheme.ResumeLayout(false);
            this.groupTheme.PerformLayout();
            this.ResumeLayout(false);

        }

        #endregion

        private System.Windows.Forms.Panel panel1;
        private System.Windows.Forms.GroupBox groupTheme;
        private System.Windows.Forms.RadioButton radioDark;
        private System.Windows.Forms.RadioButton radioLight;
    }
}
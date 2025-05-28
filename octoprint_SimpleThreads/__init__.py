# coding=utf-8
from __future__ import absolute_import

### (Don't forget to remove me)
# This is a basic skeleton for your plugin's __init__.py. You probably want to adjust the class name of your plugin
# as well as the plugin mixins it's subclassing from. This is really just a basic skeleton to get you started,
# defining your plugin as a template plugin, settings and asset plugin. Feel free to add or remove mixins
# as necessary.
#
# Take a look at the documentation on what other plugin mixins are available.

import octoprint.plugin
import logging

class SimplethreadsPlugin(octoprint.plugin.SettingsPlugin,
    octoprint.plugin.AssetPlugin,
    octoprint.plugin.StartupPlugin,
    octoprint.plugin.SimpleApiPlugin,
    octoprint.plugin.TemplatePlugin
):

    ##~~ SettingsPlugin mixin
    def __init__(self):
        self.depth = float(0)
        self.pitch = float(0)
        self.cut_depth = float(0)
        self.passes = int(1)
        self.position = "external"
        self.lead_in = float(0)
        self.feed_rate = int(2)
        self.exit_length = float(0)
        self.pause_step = False
        self.starts = int(1)
        self.retract = float(5.0)
    ##~~ SettingsPlugin mixin
    def initialize(self):
        self.datafolder = self.get_plugin_data_folder()

    def get_settings_defaults(self):
        return {
            # put your plugin's default settings here
        }

    ##~~ AssetPlugin mixin

    def get_assets(self):
        # Define your plugin's asset files to automatically include in the
        # core UI here.
        return {
            "js": ["js/SimpleThreads.js"],
            "css": ["css/SimpleThreads.css"],
            "less": ["less/SimpleThreads.less"]
        }
    
    def generate_threads(self):
        gcode = []
        gcode.append("M3 S24000")
        gcode.append("G90")
        gcode.append("G21")
        gcode.append("STOPBANGLE")
        #gcode.append("G92 X0 Z0 A0")
        Z_sign = 1
        x_steps = 0
        name="EXT"
        if self.position == "internal":
            Z_sign = -1
            name="INT"

        Z_val = self.cut_depth*Z_sign
        lead_val = 0
        if self.passes > 1:
            #figure out the depth based on self.cut_depth
            Z_val = Z_sign*self.cut_depth/self.passes

        if self.lead_in:
            #calculate initial lead_in based on internal/external and the value given
            #need to know if it is greater than 1 pitch length
            lead_val = self.lead_in/self.passes
            x_steps = self.lead_in/self.pitch
            lead_num = lead_val/x_steps

        self.pitch = self.pitch*self.starts

        for s in range(self.starts):
            
            current_A = s*360/self.starts
            if s:
                current_A = 360/self.starts
            gcode.append(f"(Thread Start {s+1})")
            gcode.append(f"G0 A{current_A}")
            gcode.append(f"G92 A0")

            for i in range(self.passes):
                i=i+1
                #if last pass and we are going to pause for CA application
                if self.passes > 1 and i == self.passes and self.pause_step:
                    gcode.append("(Pause Before final Pass)")
                    gcode.append(f"G0 Z{self.retract*Z_sign} X10")
                    gcode.append("M0")
                    gcode.append(f"G93 G90 G1 A720 F{self.feed_rate}")
                    gcode.append("M0")
                    gcode.append("G92 A0")
                    gcode.append("G0 X0 Z0")
                gcode.append(f"(Starting Pass {i})")
                current_x = 0
                Xval = 0
                Aval = 360
                feed = self.feed_rate
                xstep = x_steps
                exit_gcode = None
                last_pass = False

                while current_x < self.depth:
                    next_x = self.pitch+current_x
                    Aval = 360
                    Xval = next_x
                    #handle fractional depth
                    if next_x > self.depth:
                        remaining_distance = self.depth - current_x
                        self._logger.info(f"Remaining distance is {remaining_distance}")
                        Xval = self.depth
                        # Fraction of full pass
                        Aval = 360 * remaining_distance / self.pitch
                        self._logger.info(f"Aval is {Aval}")
                        # Feed rate compensation
                        feed = self.feed_rate * (360 / Aval)
                        last_pass = True
                    gcode.append(f"G1 Z{-1*i*Z_val:.4f} F300")
                    gcode.append(f"G93 G90 G1 X-{Xval:0.4f} A{Aval:0.4f} F{int(feed)}")
                    if not last_pass:
                        gcode.append("G92 A0")
                    current_x = next_x
               
                #exit depth move
                if self.exit_length:
                    Aval = Aval+self.exit_length
                    gcode.append(f"G93 G90 G1 Z0 A{Aval:0.4f} F{self.feed_rate}")
                #move to safe position
                gcode.append(f"G0 Z{self.retract*Z_sign}")
                gcode.append(f"G93 G90 X0 A0 F{self.feed_rate}")


        gcode.append("M5")
        gcode.append("M30")
        output_name = "{0}_THREADS_P{1:.2f}_L{2}_D{3}_S{4}.gcode".format(name, self.pitch, self.depth, self.cut_depth, self.starts)
        path_on_disk = "{}/{}".format(self._settings.getBaseFolder("watched"), output_name)

        with open(path_on_disk,"w") as newfile:
            for line in gcode:
                newfile.write(f"\n{line}")

    def get_api_commands(self):
        return dict(
            create_threads=[]
        )
    
    def on_api_command(self, command, data):
        
        if command == "create_threads":
            #print(data)
            self.depth = float(data["depth"])
            self.cut_depth = float(data["cut_depth"])
            self.passes = int(data["passes"])
            self.pitch = float(data["pitch"])
            self.feed_rate = int(data["feed_rate"])
            self.lead_in = bool(data["lead_in"])
            self.exit_length = float(data["exit"])
            self.pause_step = bool(data["pause_step"])
            self.position = data["position"]
            self.starts = int(data["starts"])
            self.retract = float(data["retract"])
            self.generate_threads()
    ##~~ Softwareupdate hook

    def get_update_information(self):
        # Define the configuration for your plugin to use with the Software Update
        # Plugin here. See https://docs.octoprint.org/en/master/bundledplugins/softwareupdate.html
        # for details.
        return {
            "SimpleThreads": {
                "displayName": "Simplethreads Plugin",
                "displayVersion": self._plugin_version,

                # version check: github repository
                "type": "github_release",
                "user": "paukstelis",
                "repo": "OctoPrint-Simplethreads",
                "current": self._plugin_version,

                # update method: pip
                "pip": "https://github.com/paukstelis/OctoPrint-Simplethreads/archive/{target_version}.zip",
            }
        }


# If you want your plugin to be registered within OctoPrint under a different name than what you defined in setup.py
# ("OctoPrint-PluginSkeleton"), you may define that here. Same goes for the other metadata derived from setup.py that
# can be overwritten via __plugin_xyz__ control properties. See the documentation for that.
__plugin_name__ = "Simplethreads Plugin"


# Set the Python version your plugin is compatible with below. Recommended is Python 3 only for all new plugins.
# OctoPrint 1.4.0 - 1.7.x run under both Python 3 and the end-of-life Python 2.
# OctoPrint 1.8.0 onwards only supports Python 3.
__plugin_pythoncompat__ = ">=3,<4"  # Only Python 3

def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = SimplethreadsPlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
    }

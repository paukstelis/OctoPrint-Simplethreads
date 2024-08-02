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

class SimplethreadsPlugin(octoprint.plugin.SettingsPlugin,
    octoprint.plugin.AssetPlugin,
    octoprint.plugin.StartupPlugin,
    octoprint.plugin.SimpleApiPlugin,
    octoprint.plugin.TemplatePlugin
):

    ##~~ SettingsPlugin mixin
    def __init__(self):
        self.depth = int(0)
        self.pitch = float(0)
        self.cut_depth = float(0)
        self.passes = int(1)
        self.position = "external"
        self.lead_in = float(0)
        self.feed_rate = int(2)
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
        gcode.append("G92 X0 Z0 A0")
        A_dir = "A-360"
        Z_sign = -1
        x_steps = 0
        name="EXT"
        if self.position == "internal":
            A_dir = "A360"
            Z_sign = 1
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

        for i in range(self.passes):
            i=i+1
            gcode.append(f"(Starting Pass {i})")
            current_x = 0
            xstep = x_steps
            #gcode.append(f"G1 Z{i*Z_val:.4f}")
            while current_x+self.pitch <= self.depth:
                current_x = self.pitch+current_x
                if self.lead_in and current_x < self.lead_in:
                    #forces 45 degree lead in
                    lead_diff = Z_sign*lead_num*xstep
                    mod_z = i*(Z_val+lead_diff)
                    gcode.append("(Lead-in move)")
                    gcode.append(f"G1 Z{mod_z:.4f} F300")
                    gcode.append(f"G93 G1 X-{current_x:0.4f} {A_dir} F{self.feed_rate}")
                    gcode.append("G92 A0")
                    xstep -= 1
                else:
                    gcode.append(f"G1 Z{i*Z_val:.4f} F300")
                    gcode.append(f"G93 G1 X-{current_x:0.4f} {A_dir} F{self.feed_rate}")
                    gcode.append("G92 A0")
               
            #move to safe position
            gcode.append(f"G0 Z{5*Z_sign*-1}") #this is kind of silly
            #go back to start
            gcode.append(f"G0 X0")
        gcode.append("M5")
        gcode.append("M30")
        output_name = "{0}_THREADS_P{1:.2f}_L{2}_D{3}.gcode".format(name, self.pitch, self.depth, self.cut_depth)
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
            self.position = data["position"]
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

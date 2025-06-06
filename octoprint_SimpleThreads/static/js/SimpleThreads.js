/*
 * View model for OctoPrint-Simplethreads
 *
 * Author: P. Paukstelis
 * License: AGPLv3
 */
$(function() {
    function SimplethreadsViewModel(parameters) {
        var self = this;
        self.depth = ko.observable(0);
        self.pitch = ko.observable(0.0);
        self.cut_depth = ko.observable(0);
        self.position = ko.observable("external");
        self.lead_in = ko.observable(0);
        self.passes = ko.observable(1);
        self.feed_rate = ko.observable(2);
        self.exit_length = ko.observable(0);
        self.pause_step = ko.observable(0);
        self.starts = ko.observable(1);
        self.retract = ko.observable(5);

        tab = document.getElementById("tab_plugin_SimpleThreads_link");
        tab.innerHTML = tab.innerHTML.replaceAll("Simplethreads Plugin", "SimpleThreads");
        // assign the injected parameters, e.g.:
        self.loginStateViewModel = parameters[0];
        self.settingsViewModel = parameters[1];

        self.writeGCode = function() {
                   
            var data = {
                depth: self.depth(),
                cut_depth: self.cut_depth(),
                passes: self.passes(),
                pitch: self.pitch(),
                feed_rate: self.feed_rate(),
                lead_in: self.lead_in(),
                position: self.position(),
                exit: self.exit_length(),
                pause_step: self.pause_step(),
                starts: self.starts(),
                retract: self.retract(),
            };

            OctoPrint.simpleApiCommand("SimpleThreads", "create_threads", data)
                .done(function(response) {
                    console.log("GCode written successfully.");
                })
                .fail(function() {
                    console.error("Failed to write GCode.");
                });
        };
    }

    /* view model class, parameters for constructor, container to bind to
     * Please see http://docs.octoprint.org/en/master/plugins/viewmodels.html#registering-custom-viewmodels for more details
     * and a full list of the available options.
     */
    OCTOPRINT_VIEWMODELS.push({
        construct: SimplethreadsViewModel,
        // ViewModels your plugin depends on, e.g. loginStateViewModel, settingsViewModel, ...
        dependencies: ["filesViewModel","accessViewModel"],
        // Elements to bind to, e.g. #settings_plugin_gcode_ripper, #tab_plugin_gcode_ripper, ...
        elements: [ "#tab_plugin_SimpleThreads", ]
    });
});

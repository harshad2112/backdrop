'use strict';

// Background service: opens the Backdrop slideshow.
// Waits first so the TV's own startup app (e.g. Samsung TV Plus) doesn't cover it.

var APP_ID = 'cl9IMZpNhA.Backdrop';
var FIRST_DELAY_MS = 20000;
var RETRY_DELAY_MS = 10000;
var MAX_TRIES = 6;

module.exports.onStart = function() {
	var tries = 0;

	function stop() {
		tizen.application.getCurrentApplication().exit();
	}

	function launch() {
		tries++;
		var control = new tizen.ApplicationControl('http://tizen.org/appcontrol/operation/view');
		tizen.application.launchAppControl(control, APP_ID, stop, function(error) {
			console.log('[Backdrop] launch failed (try ' + tries + '): ' + error);
			if (tries < MAX_TRIES) {
				setTimeout(launch, RETRY_DELAY_MS);
			} else {
				stop();
			}
		});
	}

	setTimeout(launch, FIRST_DELAY_MS);
};

module.exports.onRequest = function() {};
module.exports.onExit = function() {};

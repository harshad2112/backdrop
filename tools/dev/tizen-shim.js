/*
 * Development only: a stand-in for the Tizen TV APIs Backdrop uses, so the app runs in a desktop
 * browser via tools/dev_server.py. Never packaged into the TV app.
 *
 * Files live on the dev server (dev-storage/), which also downloads (no CORS limits) and unzips.
 * Paths are the same virtual paths the app uses on the TV, e.g. "downloads/backdrop-a/01.jpg".
 */
(function() {
	'use strict';

	function query(op, params) {
		var q = 'op=' + op;
		Object.keys(params || {}).forEach(function(k) {
			q += '&' + k + '=' + encodeURIComponent(params[k]);
		});
		return '/fs?' + q;
	}

	function call(op, params, ok, fail) {
		fetch(query(op, params)).then(function(r) { return r.json(); }).then(function(res) {
			if (res.ok) { if (ok) ok(res.result); }
			else if (fail) fail({ name: res.error, message: res.message });
		}, function(e) {
			if (fail) fail({ name: 'NetworkError', message: String(e) });
		});
	}

	function callSync(op, params) { // a few Tizen calls (createDirectory) are synchronous
		var xhr = new XMLHttpRequest();
		xhr.open('GET', query(op, params), false);
		xhr.send();
		var res = JSON.parse(xhr.responseText);
		if (!res.ok) throw { name: res.error, message: res.message };
		return res.result;
	}

	function basename(path) {
		return path.replace(/\/+$/, '').split('/').pop();
	}

	// ----- File (Tizen Filesystem API, the subset Backdrop uses) -----

	function File(path, isFile, size) {
		this.fullPath = path.replace(/\/+$/, '');
		this.name = basename(this.fullPath);
		this.isFile = isFile;
		this.isDirectory = !isFile;
		this.fileSize = size || 0;
	}

	File.prototype.toURI = function() {
		return '/files/' + this.fullPath.split('/').map(encodeURIComponent).join('/');
	};

	File.prototype.listFiles = function(ok, fail) {
		var dir = this.fullPath;
		call('list', { path: dir }, function(entries) {
			ok(entries.map(function(e) { return new File(dir + '/' + e.name, e.isFile, e.size); }));
		}, fail);
	};

	File.prototype.createDirectory = function(name) {
		var path = this.fullPath + '/' + name;
		if (callSync('mkdir', { path: path }).existed) throw { name: 'IOError', message: 'exists' };
		return new File(path, false);
	};

	File.prototype.deleteDirectory = function(path, recursive, ok, fail) {
		call('rmdir', { path: path }, ok, fail);
	};

	File.prototype.deleteFile = function(path, ok, fail) {
		call('rm', { path: path }, ok, fail);
	};

	File.prototype.moveTo = function(from, to, overwrite, ok, fail) {
		call('move', { from: from, to: to, overwrite: !!overwrite }, ok, fail);
	};

	File.prototype.copyTo = function(from, to, overwrite, ok, fail) {
		call('copy', { from: from, to: to, overwrite: !!overwrite }, ok, fail);
	};

	File.prototype.readAsText = function(ok, fail) {
		call('read', { path: this.fullPath }, function(r) { ok(r.text); }, fail);
	};

	// ----- the tizen object -----

	var downloadId = 0;
	var KEYS = { MediaPlayPause: 10252, MediaPlay: 415, MediaPause: 19, Info: 457 };

	window.tizen = {
		filesystem: {
			resolve: function(path, ok, fail) {
				call('stat', { path: path }, function(s) {
					if (!s.exists) { if (fail) fail({ name: 'NotFoundError', message: path }); return; }
					ok(new File(path, !s.isDir));
				}, fail);
			}
		},

		DownloadRequest: function(url, destination, fileName) {
			this.url = url;
			this.destination = destination;
			this.fileName = fileName;
		},

		download: {
			start: function(request, listener) {
				var id = ++downloadId;
				call('download', { url: request.url, dir: request.destination, name: request.fileName || '' },
					function(r) { listener.oncompleted(id, request.destination + '/' + r.name); },
					function(e) { listener.onfailed(id, e); });
				return id;
			},
			cancel: function() {}
		},

		archive: {
			open: function(path, mode, ok) {
				ok({
					extractAll: function(dest, done, fail) { call('unzip', { zip: path, dest: dest }, done, fail); },
					close: function() {}
				});
			}
		},

		tvinputdevice: {
			registerKey: function() {},
			getKey: function(name) { return { code: KEYS[name] }; }
		},

		application: {
			getCurrentApplication: function() {
				return {
					hide: function() { console.log('[dev] app.hide() - on the TV the app goes to the background'); },
					exit: function() { console.log('[dev] app.exit()'); }
				};
			}
		}
	};

	// ----- keyboard -> TV remote key codes -----

	var REMOTE = {
		Escape: 10009, Backspace: 10009,     // Back
		' ': 10252, p: 10252, P: 10252,      // Play/Pause
		i: 457, I: 457                       // INFO
	};

	window.addEventListener('keydown', function(e) {
		if (e.__remote || !(e.key in REMOTE)) return; // arrows and Enter already match the remote
		var tag = (e.target && e.target.tagName) || '';
		if (tag === 'INPUT' || tag === 'TEXTAREA') return;
		e.stopImmediatePropagation();
		e.preventDefault();
		var remote = document.createEvent('Event');
		remote.initEvent('keydown', true, true);
		Object.defineProperty(remote, 'keyCode', { value: REMOTE[e.key] });
		remote.__remote = true;
		document.dispatchEvent(remote);
	}, true);

	// ----- render at TV resolution (1920x1080), scaled to fit the window -----

	var style = document.createElement('style');
	style.textContent = 'html{background:#111}html,body{width:1920px!important;height:1080px!important;}' +
		'body{position:relative;}';
	document.head.appendChild(style);

	function fit() {
		var scale = Math.min(window.innerWidth / 1920, window.innerHeight / 1080);
		document.documentElement.style.zoom = scale;
	}
	window.addEventListener('resize', fit);
	fit();

	console.log('[dev] Tizen stand-in loaded. Keys: arrows, Enter = OK, Space/P = Play/Pause, ' +
		'Esc/Backspace = Back, I = INFO');
})();

// ==UserScript==
// @name        Download Mesh in Level
// @namespace   Violentmonkey Scripts
// @match       https://playcanvas.com/editor/scene/*
// @grant       none
// @version     1.0
// @author      Clay
// @description 20/10/2021, 11:40:21
// ==/UserScript==

(function () {

	// Download a file form a url.
	function saveFile(url_file_map) {

		var url = url_file_map["url"];
		var filename = url_file_map["filename"]

		return new Promise(function (resolve, reject) {
			// Get file name from url.
			var xhr = new XMLHttpRequest();
			xhr.responseType = 'blob';
			xhr.onload = function () {
				resolve(xhr);
			};
			xhr.onerror = reject;
			xhr.open('GET', url);
			xhr.send();
		}).then(function (xhr) {
			// var filename = url.substring(url.lastIndexOf("/") + 1).split("?")[0];
			var a = document.createElement('a');
			a.href = window.URL.createObjectURL(xhr.response); // xhr.response is a blob
			a.download = filename; // Set the file name.
			a.style.display = 'none';
			document.body.appendChild(a);
			a.click();
			return xhr;
		});
	}

	/* download all async
    function download(url_file_maps) {
      return Promise.all(url_file_maps.map(saveFile));
    }
    */

	// download one by one
	function download(url_file_maps) {
		var cur = Promise.resolve();
		url_file_maps.forEach(function (url_file_map) {
			cur = cur.then(function () {
				return saveFile(url_file_map);
			});
		});
		return cur;
	}

	async function donwload_assets() {

		/*
        * BEGIN SETTINGS
        * @TAEGET_LAYER_INDEX: the index you want to download
        * @ download_all: if you want to download all the file
        * */
		const TARGET_LAYER_INDEX = 1000;
		const download_all = true;
		/*
        * END SETTINGS
        * */

		entity_list = editor.entities.list();
		model_asset_list = []

		for (let i = 0; i < entity_list.length; i++) {
			ent = entity_list[i];
			if (ent.has('components.model')) {
				// get model resource id
				layers = ent.get('components.model.layers');
				if (download_all || layers.includes(TARGET_LAYER_INDEX)) {
					assetid = ent.get("components.model.asset");
					if (assetid) {
						model_asset_list.push(assetid);
					}
				}
			}
		}

		// unique fitler
		function only_unique(value, index, self) {
			return self.indexOf(value) === index;
		}

		let unique_ids = model_asset_list.filter(only_unique);

		urls = new Array(unique_ids.length)

		for (let i = 0; i < unique_ids.length; i++) {
			url = '/api/assets/' + unique_ids[i] + '/download?branchId=' + config.self.branch.id;
			filename = unique_ids[i] + '.zip';
			urls[i] = {'url': url, 'filename': filename};
		}
		console.log("start downloading:" + unique_ids.length + "files")
		download(urls).then(function () {
			alert("all files downloaded");
		}).catch(function (e) {
			alert("something went wrong: " + e);
		});

	}

	function createButton() {
		const btn = new pcui.Button({text: 'Download Mirror Models'});
		btn.style.position = 'absolute';
		btn.style.bottom = '10px';
		btn.style.right = '10px';
		editor.call('layout.viewport').append(btn);
		btn.on('click', () => {
			donwload_assets();
		});
	}

	// Wait until the Editor is available before adding the button
	editor.once('load', () => createButton());
})();

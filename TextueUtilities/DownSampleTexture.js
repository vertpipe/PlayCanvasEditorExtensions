// ==UserScript==
// @name        Down Sample Texture
// @namespace   Violentmonkey Scripts
// @match       *://*/*
// @grant       none
// @version     1.0
// @author      Clay & Leonidas (Great thanks to Leonidas for all his help.)
// @require https://docs.opencv.org/4.x/opencv.js
// @description 2022/4/28 19:06:09
// ==/UserScript==
(function () {

    // load image from URL
    async function loadImage(imageUrl) {
        let img;
        const imageLoadPromise = new Promise(resolve => {
            img = new Image();
            img.onload = resolve;
            img.src = imageUrl;
        });
        await imageLoadPromise;
        return img;
    }

    // get data from canvas to blob
    // reference: https://github.com/nolanlawson/blob-util/blob/99c06472d18329eda1421286692bd875d76d5c9c/src/blob-util.ts
    function canvasToBlob(canvas, type, quality) {
        if (typeof canvas.toBlob === 'function') {
            return new Promise(function (resolve) {
                canvas.toBlob(resolve, type, quality)
            });
        }
        return Promise.resolve(dataURLToBlob(canvas.toDataURL(type, quality)))
    }

    // load image to canvas
    async function loadImageToCanvas(imageUrl) {

        let image = await loadImage(imageUrl);

        const canvas = document.createElement('canvas');
        canvas.width = image.width;
        canvas.height = image.height;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(image, 0, 0, image.width, image.height);

        return canvas;

    }

    // load and scale the image and return a blob
    async function loadAndScaleImageToBlob(imageUrl, scale, format) {

        // read image
        let canvas = await loadImageToCanvas(imageUrl);
        let src = cv.imread(canvas);

        // assign mimeType, currently only support png and jpeg
        let mimeType = "image/" + format;

        // resize image
        let dst = new cv.Mat();
        let dsize = new cv.Size(
            Math.max(1, Math.floor(src.cols * scale)),
            Math.max(1, Math.floor(src.rows * scale))
        );
        console.log(dsize);
        // opencv interplation flags: https://docs.opencv.org/3.4/da/d54/group__imgproc__transform.html
        const CV_INTERPOLATION_FLAG = cv.INTER_AREA; // change the interpolation flage here
        cv.resize(src, dst, dsize, 0, 0, CV_INTERPOLATION_FLAG);

        // blit onto new Cnavas
        const newCanvas = document.createElement('canvas');
        newCanvas.width = canvas.width;
        newCanvas.height = canvas.height;
        cv.imshow(newCanvas, dst);
        let blob = await canvasToBlob(newCanvas, mimeType);

        // clean Up
        src.delete();
        dst.delete();

        return blob;

    }

    function findMinimalMips(selectedTextures) {
        if (selectedTextures.length <= 0) return 0;

        var minMipLevels = 8;

        for (let i = 0; i < selectedTextures.length; i++) {
            const mipLevels = Math.log2(Math.max(selectedAssets[0].get("meta.width"), selectedAssets[0].get("meta.height"))) + 1;
            minEdge = Math.min(minEdge, mipLevels);
        }

        return minMipLevels;

    }

    async function downsampleAndUpload(selectedAsset, scale) {
        var imageUrl = selectedAsset.get('file.url');
        var imageName = selectedAsset.get('name');
        var format = selectedAsset.get("meta.format");

        // currently we only support png and jpeg
        if (!(format === "jpeg" || format == "png")) return;

        // create new image name
        const REGEX_EXT = /\.[a-z]+$/;
        const ext = imageName.match(REGEX_EXT);

        // componse size string to rename the file
        const width = Math.max(1, Math.floor(selectedAsset.get("meta.width") * scale));
        const height = Math.max(1, Math.floor(selectedAsset.get("meta.height") * scale));
        const sizeStr = width.toString() + "x" + height.toString();

        // remove the old size string;
        const REGEX_SIZE = /[_][1-9]+[x][1-9]+/;  // e.g. 128x128

        var newImageName = imageName.replace(REGEX_SIZE, "");

        if (ext) {
            newImageName = newImageName.slice(0, -ext[0].length) + "_" + sizeStr + ext[0];
        } else // handle the no file extension in name case
        {
            newImageName = newImageName + "_" + sizeStr;
        }

        // Load the image using opencv.js and process it
        async function process() {

            const file = await loadAndScaleImageToBlob(imageUrl, scale, format);
            file.lastModifiedDate = new Date();
            file.name = newImageName;

            const currentFolder = editor.call('assets:panel:currentFolder');

            var newAsset = await editor.assets.upload({
                name: newImageName,
                file: file,
                type: 'texture',
                folder: currentFolder,
                preload: true
            });

            // replace the asset with new texture
            if (newAsset) {
                selectedAsset.apiAsset.replace(newAsset);
            }
        }

        process();

    }

    function AddTextureContextMenu() {
        var assetPanel = editor.call('layout.assets');
        var selectedAssets = assetPanel._selectedAssets;

        // var lowerMipLevels = findMinimalMips(selectedAssets) - 1; // exclude Mip 0

        // construct items
        var menuItems = [];
        for (let k = 1; k <= 5; k++) {

            var menuItem = new pcui.MenuItem({
                text: "1/" + (2 ** k),
                icon: null,
                dividor: 2 ** k,
                onSelect: (item, currentAsset) => {
                    var selectedAssets = assetPanel._selectedAssets;
                    for (let i = 0; i < selectedAssets.length; i++) {
                        // do the process one by one?
                        downsampleAndUpload(selectedAssets[i], 1.0 / 2 ** k);
                    }
                }
            });
            menuItems.push(menuItem);
        }

        var menuData = {
            text: 'Down Sample Texture',
            icon: 'E288',
            items: menuItems,
            onIsVisible: (item, currentAsset) => {

                var selectedAssets = assetPanel._selectedAssets;
                var numAssets = selectedAssets.length;
                var bVisible = selectedAssets.length >= 1;
                for (let i = 0; i < numAssets; i++) {
                    if (selectedAssets[i]._data.type !== "texture") {
                        bVisible = false;
                        break
                    }
                }
                return bVisible;
            },

            onSelect: (item, currentAsset) => {

            }
        };

        editor.call('assets:contextmenu:add', menuData);
    }

    // Add menu after the editor is loaded
    editor.once('load', () => AddTextureContextMenu());
})();

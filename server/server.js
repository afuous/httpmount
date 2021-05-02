let fs = require("fs");
let fsp = fs.promises;

let config;
try {
    let configFile = require("path").join(__dirname, "config.json");
    if (!fs.existsSync(configFile)) {
        console.error("httpmount: config.json not found");
        process.exit();
    }
    config = JSON.parse(fs.readFileSync(configFile));
    if (!("root" in config) || !("password" in config) || !("timestamps" in config)) {
        console.error("httpmount: config.json missing required fields");
        process.exit();
    }
} catch (e) {
    console.error("httpmount: error reading config.json\n");
    console.error(e);
    process.exit();
}

let basePath = config.root;
let password = config.password;
let timestamps = config.timestamps;

if (basePath[basePath.length - 1] == "/") {
    basePath = basePath.slice(0, basePath.length - 1);
}

async function app(req, res) {
    if (req.method != "GET") {
        return;
    }

    if (req.headers['authorization'] != password) {
        return;
    }

    let path = decodeURIComponent(require("url").parse(req.url).pathname);

    if (path.endsWith("/")) {
        try {
            let files = await fsp.readdir(basePath + path);
            let obj = await Promise.all(files.map(file => (async function() {
                let stat = await fsp.stat(basePath + path + file);
                let obj = {};
                obj.name = file;
                if (stat.isDirectory()) {
                    obj.directory = true;
                } else {
                    obj.directory = false;
                    obj.size = stat.size;
                }
                if (timestamps) {
                    obj.atime = stat.atime;
                    obj.mtime = stat.mtime;
                    obj.ctime = stat.ctime;
                }
                return obj;
            })()));
            res.setHeader("content-type", "application/json");
            res.end(JSON.stringify(obj));
        } catch (e) {
            if (e.code == "ENOTDIR") {
                res.writeHead(400);
            } else if (e.code == "ENOENT") {
                res.writeHead(404);
            } else {
                res.writeHead(500);
            }
            res.end();
        }
    } else {
        let range = req.headers["range"];
        if (!range || !range.startsWith("bytes=")) {
            res.writeHead(400);
            res.end();
        }
        let split = range.slice("bytes=".length).split("-");
        let start = parseInt(split[0]);
        let end = parseInt(split[1]);
        if (isNaN(start) || isNaN(end)) {
            res.writeHead(400);
            res.end();
        }
        try {
            fs.createReadStream(basePath + path, {
                start: start,
                end: end,
            }).pipe(res);
        } catch (e) {
            res.writeHead(400);
            res.end();
        }
    }
}

module.exports = app;

if (require.main === module) {
    require("http").createServer(app).listen(process.argv[2]);
}

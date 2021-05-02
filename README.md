# httpmount

FUSE filesystem to mount remote directories read-only over HTTP or HTTPS.

## Installing client dependencies
The client depends on [FUSE](https://github.com/libfuse/libfuse) and python packages [python-fuse](https://github.com/libfuse/python-fuse) and [requests](https://github.com/psf/requests).

#### Arch Linux
`pacman -S fuse2 python-fuse python-requests`

#### Debian
`apt-get install fuse python3-fuse python3-requests`

#### Mac
* Install [macFUSE](https://github.com/osxfuse/osxfuse/releases)
* Install [homebrew](https://brew.sh/) and run `brew install pkg-config`
* Run `pip3 install requests`
* In a temporary directory, run `git clone https://github.com/libfuse/python-fuse; cd python-fuse; pip3 install .`

## Client usage
Basic usage: `httpmount.py -u <server url> -p <password> <mountpoint>`

There are also convenience scripts `mountall.py` and `umountall.py` that can automatically mount and unmount from multiple servers. These scripts require a `client/config.json` similar to `client/config.example.json`, an array of objects with the following properties: `mountpoint` is the local location where the filesystem will be mounted, `url` is the URL of the server, and `password` is the password required by the server. If `mountpoint` does not specify a full path, the mountpoint will be created automatically at `client/mnt/<mountpoint>`.

## Running the server
The only dependency for the server is nodejs. Start the server with `node server/server.js <port number>`. It's recommended to run the server behind a reverse proxy that provides TLS encryption. The server requires a `server/config.json` similar to `server/config.example.json`. In `config.json`, `root` is the directory that clients can read, `password` is the password clients must provide, and `timestamp` is whether the server will send file timestamps to the client.

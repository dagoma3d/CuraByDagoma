## Installation instructions

There are two ways to install the package.

* Using apt-get :
```
cp [mypath]/Cura-by-dagoma-{MACHINE_NAME}-debian_{BUILD_ARCHITECTURE}.deb /var/cache/apt/archives/
sudo apt-get install curabydago-{MACHINE_NAME_LOWERCASE}
```

* Using dpkg :
```
sudo dpkg -i [mypath]/Cura-by-dagoma-{MACHINE_NAME}-debian_{BUILD_ARCHITECTURE}.deb
sudo apt-get install -f
```

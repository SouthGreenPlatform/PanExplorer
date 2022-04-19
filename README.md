# PanExplorer

Web application to explore bacterial pangenomes

Official instance of PanExplorer: [https://panexplorer.southgreen.fr](https://panexplorer.southgreen.fr)

## Table of contents

- [Introduction](#introduction)
- [Running the workflow](#running)
- [Web application deployment](#deployment)

## Introduction

## Running the workflow

1- Git clone

```
git clone https://github.com/SouthGreenPlatform/PanExplorer.git
cd PanExplorer
```

## Web application deployment

1- Git clone

```
git clone https://github.com/SouthGreenPlatform/PanExplorer.git
cd PanExplorer
```

2- Copy directories into dedicated HTML and CGI directories

```
mkdir <PANEXPLORER_HTML_DIR>
cd <PANEXPLORER_PATH>/html
cp * <PANEXPLORER_HTML_DIR>
```

```
mkdir <PANEXPLORER_CGI_BIN_DIR>
cd <PANEXPLORER_PATH>/cgi-bin
cp * <PANEXPLORER_CGI_BIN_DIR>
```

3- Edit the Configuration file and javascript

```
cd <PANEXPLORER_CGI_BIN_DIR>/Config
vi Configuration.pm
```



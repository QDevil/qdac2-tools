# Tools for QDevil QDAC-II

This repository contains additional tools and examples for QDAC-II.  See https://qdevil.com/w82mkw6a/ for more information and examples.

## List of tools

- `usb-detector`: Detect a QDAC-II connected through USB and display port and setup information.

## How to use

Most applications and examples are written in Python 3, so you will need to set up a virtual python environment, see First-time Setup below.

Each subfolder contains a separate tool or example.

For instance, to use the USB Detector, enter the python virtual environment and run the app in the subfolder:

### Linux / macOS

In a Terminal:

	$ source venv/bin/activate
	$ python src/usb-detector.py

### Windows

In PowerShell:

	PS> venv\Scripts\activate.bat
	PS> python src\usb-detector.py


## First-time Setup

### Linux / macOS

In a Terminal:

	$ scripts/setup-virtual-env.sh
	$ scripts/install-libs.sh

### Windows

In PowerShell:

	PS> python -m venv venv
	PS> scripts\install-libs.bat

# Tools for QDAC-II & QSwitch

This repository contains additional tools and examples for QDAC-II and QSwitch.  See https://qm.quantum-machines.co/qe-documentation-firmware for more information and examples.

## List of tools

- `usb_detector`: Detect a QDAC-II or QSwitch connected through USB and display port and setup information.
- `qdac2`: Simple wrapper around pyvisa to handle connection and communication with QDAC-II.
- `qswitch`: Simple wrapper around pyvisa to handle connection and communication with QSwitch.

## First-time Setup

### Linux / macOS

In a Terminal:

	$ scripts/setup-virtual-env.sh
	$ scripts/install-libs.sh

### Windows

In PowerShell:

	PS> python -m venv venv
	PS> scripts\install-libs.bat
	
	
## How to use

The `*_standalone.py` python programs can be run directly using Python, as long as their dependencies are installed.

The other applications and examples are written in Python 3, so you should set up a virtual python environment for their use, see First-time Setup above.  The tools are located in the `src` directory.  See the individual source files for instructions on usage.

To use the USB Detector, enter the python virtual environment and run the app in the subfolder:

### Linux / macOS

In a Terminal:

	$ source venv/bin/activate
	$ python src/usb_detector.py

### Windows

In PowerShell:

	PS> venv\Scripts\activate.ps1
	PS> python src\usb_detector.py

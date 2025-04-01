# C-V2X Interoperability Testing Tool

This repository contains a set of semi-automated Cellular Vehicle-to-Everything (C-V2X) interoperability testing
tools developed at the National Institute of Standards and Technology (NIST) IoT Devices Interoperability testbed.
This software is written in Python and can be used to automatically test C-V2X communication and interoperability,
and collect C-V2X packet traces from commercial On-Board Units (OBUs) and Road-Side Units (RSUs) based on the IEEE
1609.2, IEEE 1609.3, and SAE J2735 standards to assess the interoperability of C-V2X devices.

## How to Use

1. Clone this repository.

    ```shell
    git clone https://github.com/usnistgov/C-V2XInteroperabilityTestingTool.git
    cd C-V2XInteroperabilityTestingTool
    ```

2. Ensure Python 3.12 and [PDM](https://pdm-project.org/) are installed.
   For example, you can install PDM with [pipx](https://pipx.pypa.io/):

    ```shell
    pipx install pdm
    ```

   Alternatively, if you prefer using [uv](https://docs.astral.sh/uv/):

    ```shell
    uv tool install pdm
    ```

3. Install all required dependencies.

    ```shell
    pdm install
    ```

4. Run the tool.

    ```shell
    pdm run src/cohda-test-runner.py
    ```

# SampleProject

## About

This application provide a possibility to run tests remotely. It uses xml-rpc protocol and contains Web UI that can be used for tests execution. Result of every executed step in WebUI is visible in realtime (websocket).

## How to use

1. Run a web_ui server from app.py. Example: ```python3 app.py --port=8000```
2. Create a python file with test methods you want to run remotely. For example use SimpleTest.py in root folder. It runs on port 1337. Example: ```python3 SimpleExample.py```
3. Open web_ui server in web browser. Example: ```http://localhost:8000```
4. In first text field you can type an address of running app with test methods. Press connect button. List of test methods should appear.
5. Choose test methods you want to run and press RunTests button. Results should appear in realtime on the right side. Test is marked as failed if method throwed an Exception. If not - test is marked as passed.

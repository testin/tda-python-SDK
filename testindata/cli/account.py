import os
import json

def _config_filepath():
    home = "USERPROFILE" if os.name == "nt" else "HOME"
    configDir = os.path.join(os.environ[home], ".tda/")
    if not os.path.exists(configDir):
        os.makedirs(configDir)

    return os.path.join(configDir, "tda.conf")


def _noLoginMessage():
    print(" you have not set your account yet, set your account with:\n")
    print("  tda config <access_key> [host] \n")
    print(" more about this command, use：\n")
    print("  tda config --help")
    exit()


def _check():
    configFile = _config_filepath()
    if not os.path.exists(configFile):
        _noLoginMessage()

    with open(configFile, "r") as config:
        try:
            jsonObj = json.load(config)
        except:
            _noLoginMessage()

        if "access_key" not in jsonObj.keys():
            _noLoginMessage()

        if jsonObj["access_key"] == None or jsonObj["access_key"] == "":
            _noLoginMessage()

    return True


def _getConf():
    configFile = _config_filepath()
    if _check():
        with open(configFile, "r") as config:
            return json.load(config)

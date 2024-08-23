import os
def decode_apk(apk_path):
    apk_name = os.path.basename(apk_path)
    # Runs the apktool on a given apk
    apktoolcmd = f"java -jar apktool.jar d -f {apk_path} -o {'decoded_apks/' + os.path.splitext(apk_name)[0]}"
    res = os.system(apktoolcmd)
        # if res != 0: raise ApkToolException(apktoolcmd)

    # Checks if we should keep the smali files belonging to the android support libraries

# Exception class to signify an Apktool Exception
class ApkToolException(Exception):
    def __init__(self, command):
        self.command = command

    def __str__(self):
        return repr(self.command)
"""
This file is declared global class that will be used for all others module.
"""
from PIL import Image
from tempfile import NamedTemporaryFile
import os, json, base64, time
############################################################## Global class ##############################################################
class Fundamental ():
    @staticmethod
    def getCurrentTimestamp():
        return int(time.time())
    
    @staticmethod
    def isFile(file_path):
        return os.path.isfile(file_path)
        
    @staticmethod
    def isImage(file_path):
        try:
            item = Image.open(file_path)
            item.close()
            ret_val = True
        except FileNotFoundError:
            ret_val = False
        
        return ret_val
    
    @staticmethod
    def convertPictoSmallerFile(file_path, size=250):
        """ Resize with respect to original's aspect ration"""
        image = Image.open(file_path)
        image.thumbnail((size, size))
        try:
            image.save(file_path)
            new_file_path = file_path
        except:
            image.save(file_path + ".png")
            new_file_path = file_path + ".png"
        
        return new_file_path
    
    @staticmethod
    def convertImageToBase64(file_path, base64_only=False):
        try:
            item = Image.open(file_path)
            item.close()
            is_image = True
        except FileNotFoundError:
            is_image = False

        src_string = ""
        if (is_image):
            b64_encode_string = ""
            with open(file_path, mode="rb") as fp:
                b64_encode_string = base64.b64encode(fp.read()).decode("utf-8")
            
            if (base64_only == False):
                src_string = "\"data:image/png;base64, " + b64_encode_string + "\""
            else:
                src_string = b64_encode_string
        else:
            src_string = ""

        return src_string

    @staticmethod
    def isDir(directory_path):
        return os.path.isdir(directory_path)
    
    @staticmethod
    def referFile(this_file):
        base_path = os.path.dirname(os.path.abspath(__file__))
        return base_path + "/../" + this_file
    
    @staticmethod
    def loadConfiguration(json_file):
        configuration_return = {}
        # /app/??
        with open(os.path.dirname(os.path.abspath(__file__)) + "/../" + json_file) as fp:
            configuration_return = json.load(fp)
        
        return configuration_return
    
    """Give the file path and return you the component directory"""
    @staticmethod
    def getAnyPathDir(path):
        if (os.path.isfile(path) or 
             os.path.isdir(path)):
            path = os.path.dirname(path)
        else:
            path = ""
        return path
    
    @staticmethod
    def convertB64ToFile(base64_string, ret_fp=False):
        if (base64_string != ""):
            with NamedTemporaryFile() as tmp:
                tmp.close() # Make name
            with open(tmp.name, "wb") as fp:
                base64_string = base64_string.split(",")[1]
                fp.write(base64.b64decode(base64_string))

            try:
                if (ret_fp == True):
                    fp = open(tmp.name, "rb")
                else:
                    fp = tmp.name
            except:
                if (ret_fp == True):
                    fp = None
                else:
                    fp = ""
        else:
            if (ret_fp == True):
                fp = None
            else:
                fp = ""

        return fp
   

if __name__ == "__main__":
    pass
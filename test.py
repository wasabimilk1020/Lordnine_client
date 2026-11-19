import sys
import img_search_utils
import time
from button_func import *
import win32gui
from PIL import ImageGrab,ImageEnhance,Image,ImageOps,ImageFilter
import utils

# img_search_utils.preprocess_image("hunting.png",r"C:\Users\wntuw\Documents\Lordnine_client\image_files\hunting.png")

x, y, width, height = 835,700, 250, 150 #매칭 위치

match_list=["hunting.png"]

match_result=img_search_utils.img_matchTemplate(match_list, x, y, width, height)
print(match_result)
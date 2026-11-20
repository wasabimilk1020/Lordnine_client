import sys
import img_search_utils
import time
from button_func import *
import win32gui
from PIL import ImageGrab,ImageEnhance,Image,ImageOps,ImageFilter
import utils

# result=img_search_utils.find_hsv_center(1749, 701, 41, 37, lower=(14, 176, 60), upper=(26, 249, 183), min_area=300) #주황색 hsv 공격 중
# print(result)
# img_search_utils.preprocess_image("template_20261120_171747.png", r"C:\Users\wntuw\Documents\Lordnine_client\image_files\chk.png")
match_list=["chk.png"]

match_result=img_search_utils.img_matchTemplate(match_list, 1669, 0, 229, 180)
print(match_result)
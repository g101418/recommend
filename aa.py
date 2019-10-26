# import re
# def get_str_list(str):
#     a = re.sub('[^A-Za-z0-9\u4e00-\u9fa5]', ' ', str) # 去除非中文非数字非英文，转为空格
#     aa = re.sub('[A-Za-z0-9]', '', str).replace(' ','') # 提取所有中文字符
#     b = re.sub(r'[\u4e00-\u9fa5]',' ',a) # 去除所有中文字符，转为空格
#     c = b.split() # 按空格将字符串分为list，按照数字、单词分开
#     result = c + list(aa)
#     return result

# aa=get_str_list("  Caidie Bakery采蝶轩  ")
# print(aa)


fenmu = 7
min_length = 3

normal_ratio = min((fenmu/min_length-1)/4+1, 1.5)

print(normal_ratio)

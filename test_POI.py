import sys
# sys.path.append('/usr/local/lib/python3.7/site-packages')
import pandas as pd
import numpy as np
import requests
import json
import csv
import re

key_tjk = "a814004049f36f3d659a791988f0242f"
key_wbw = "acdcd465bfca0329da28bee35e02ba56"
key_mzj = "e3385baba2476786d60770b3919084ab"

shop_path = "RS_data/dianping-shop.xlsx"
poi_restaurant_path = "./new_poi_info.csv"
area_dict = {'南京': '320100', '玄武区': '320102', '秦淮区': '320104', '建邺区': '320105', '鼓楼区': '320106', '浦口区': '320111',
             '栖霞区': '320113', '雨花台区': '320114', '江宁区': '320115', '六合区': '320116', '溧水区': '320117', '高淳区': '320118'}
shop_data = pd.read_excel(shop_path)
poiId_set = set()    # poi_id集合，去重

num = 0
total = 1000

f_url = open("./result_jsons.txt", 'w+')
f_results_true = open("./results_true.txt", "w+")
f_results_false = open("./results_false.txt", "w+")


def gate(name_ratio, address_ratio, distance_ratio, dict_ratio):
    name_gate = 0.7
    address_gate = 0.15
    distance_gate = 0.2
    dict_gate = 0.1

    # 保送项目
    if name_ratio >= 0.76 and distance_ratio <= 0.008 and distance_ratio >= 0:
        return True
    if name_ratio >= 0.76 and address_ratio >= 0.6:
        return True

    # 加分项目
    if address_ratio >= 0.76 and distance_ratio <= 0.017 and distance_ratio >= 0:
        name_ratio = name_ratio + 0.15
    if address_ratio >= 0.2 and distance_ratio <= 0.01 and distance_ratio >= 0:
        name_ratio = name_ratio + 0.12
        dict_ratio = dict_ratio + 0.1
    if name_ratio >= 0.8 and distance_ratio <= 0.01 and distance_ratio >= 0:
        address_ratio = address_ratio + 0.7
    if address_ratio >= 0.9 and distance_ratio <= 0.01 and distance_ratio >= 0:
        name_ratio = name_ratio + 0.25

    # 门限判断
    if dict_ratio >= 0 and dict_ratio <= dict_gate:
        return False
    elif name_ratio <= name_gate:
        return False
    elif distance_ratio >= 0 and distance_ratio >= distance_gate:
        return False
    elif address_ratio >= 0 and address_ratio <= address_gate:
        return False
    return True


def get_str_list(str):
    a = re.sub('[^A-Za-z0-9\u4e00-\u9fa5]', ' ', str)  # 去除非中文非数字非英文，转为空格
    aa = re.sub('[A-Za-z0-9]', '', str).replace(' ', '')  # 提取所有中文字符
    b = re.sub(r'[\u4e00-\u9fa5]', ' ', a)  # 去除所有中文字符，转为空格
    c = b.split()  # 按空格将字符串分为list，按照数字、单词分开
    result = c + list(aa)
    return result


def Jaccrad(model, reference):
    if type(model) is not str:
        return 0.0
    if type(reference) is not str:
        return 0.0

    grams_model = get_str_list(model)
    grams_reference = get_str_list(reference)

    temp = 0
    for i in grams_reference:
        if i in grams_model:
            temp = temp+1
    fenmu = len(grams_model)+len(grams_reference)-temp  # 并集

    min_length = min(len(grams_model), len(grams_reference))

    normal_ratio = min((fenmu/min_length-1)/5+1, 1.45)

    jaccard_coefficient = float(temp/fenmu)*normal_ratio  # 交集

    return jaccard_coefficient


def poi_distance(df1_longitude, df1_latitude, df2_longitude, df2_latitude):
    distance = np.sqrt(np.square(df2_latitude-df1_latitude) +
                       np.square(df2_longitude-df1_longitude))
    return distance


with open(poi_restaurant_path, "w", newline="", encoding='utf-8-sig') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["poi_id", "poi_name", "poi_parent", "distance", "poi_recommend_food", "poi_big_category", "poi_mid_category",
                     "poi_sub_category", "poi_typecode", "poi_biz_type", "poi_address", "poi_longitude", "poi_latitude",
                     "poi_tel", "poi_adcode", "poi_adname", "poi_gridcode", "poi_cpid", "poi_floor", "poi_business_area",
                     "poi_rating", "poi_cost"])
    api_count = 0
    for index, row in shop_data.iterrows():
        num = num + 1
        if num > total:
            exit()

        # 处理excel数据
        shop_Name = row['shopName'].replace(" ", "")    # 处理后的数据每个单元格前后存在空格
        shop_Area = row['Range'].replace(" ", "") if (
            type(row['Range']) == str) else "南京"
        shop_Area_Id = area_dict.get(shop_Area)
        shop_Longitude = row['纬度'].replace(" ", "")
        shop_Latitude = row['经度'].replace(" ", "")
        shop_Address = row['地址'].replace(" ", "")

        if api_count < 29999:
            api_count += 1
            key = key_tjk
        if api_count >= 29999:
            api_count += 1
            key = key_wbw

        # api调用，模拟get请求
        url = 'https://restapi.amap.com/v3/place/text?key=' + key + '&keywords=' + shop_Name + \
            '&types=&city=' + shop_Area_Id + '&children=1&offset=20&page=1&extensions=all'
        r = requests.get(url)
        content_origin = r.text
        content_json = json.loads(content_origin)    # 转json格式，dict
        print('**查询:', shop_Name, file=f_url)
        print('**URL:', url, file=f_url)
        # print('------POIS------', file=f_url)
        # print(content_json.get('pois'), file=f_url)
        # print('------JSONS------', file=f_url)
        # print(content_origin, file=f_url)

        # 处理json数据
        if type(content_json.get('count')) == str:
            count = int(content_json.get('count'))
            if count != 0:
                pois_pairs = []
                for poi in content_json.get('pois'):    # poi为dict类型
                    if len(poi) > 0:
                        poi_id = poi.get('id')
                        if poi_id not in poiId_set:
                            poiId_set.add(poi_id)

                            poi_parent = poi.get('parent') if type(
                                poi.get('parent')) == str else None
                            poi_recommend_food = poi.get('tag') if type(
                                poi.get('tag')) == str else None
                            poi_name = poi.get('name')

                            type_list = poi.get('type').split(';')
                            poi_big_category = type_list[0]
                            poi_mid_category = type_list[1]
                            poi_sub_category = type_list[2]

                            if poi_big_category == "餐饮服务":
                                poi_typecode = poi.get('typecode')
                                poi_biz_type = poi.get('biz_type') if (
                                    type(poi.get('biz_type')) == str) else None
                                poi_address = poi.get('address') if (
                                    type(poi.get('address')) == str) else None

                                # print(shop_Name, ' ', poi_name, ' ', Jaccrad(poi_name_, shop_Name_), ' ', Jaccrad(shop_Address_, poi_address_))

                                location_list = poi.get('location').split(',')
                                poi_longitude = location_list[0]
                                poi_latitude = location_list[1]

                                poi_tel = poi.get('tel') if (
                                    type(poi.get('tel')) == str) else None
                                poi_adcode = poi.get('adcode') if (
                                    type(poi.get('adcode')) == str) else None
                                poi_adname = poi.get('adname') if (
                                    type(poi.get('adname')) == str) else None
                                poi_gridcode = poi.get('gridcode') if (
                                    type(poi.get('gridcode')) == str) else None

                                indoor_data = poi.get('indoor_data')
                                poi_cpid = indoor_data.get('cpid') if type(
                                    indoor_data.get('cpid')) == str else None
                                poi_floor = indoor_data.get('floor') if type(
                                    indoor_data.get('floor')) == str else None

                                poi_business_area = poi.get('business_area') if type(
                                    poi.get('business_area')) == str else None

                                biz_ext = poi.get('biz_ext')
                                poi_rating = biz_ext.get('rating') if type(
                                    biz_ext.get('rating')) == str else None
                                poi_cost = biz_ext.get('cost') if type(
                                    biz_ext.get('cost')) == str else None

                                # 写入数据表
                                writer.writerow(
                                    [poi_id, poi_name, poi_parent, poi_recommend_food, poi_big_category, poi_mid_category,
                                     poi_sub_category, poi_typecode, poi_biz_type, poi_address, poi_longitude, poi_latitude,
                                     poi_tel, poi_adcode, poi_adname, poi_gridcode, poi_cpid, poi_floor, poi_business_area,
                                     poi_rating, poi_cost])

                                # 综合gate
                                if type(shop_Address) is not str:
                                    shop_Address = ''
                                if type(poi_address) is not str:
                                    poi_address = ''

                                shop_Name_ = re.sub("\(.*?\)", "", shop_Name)
                                poi_name_ = re.sub("\(.*?\)", "", poi_name)
                                shop_Address_ = re.sub(
                                    "\(.*?\)", "", shop_Address)
                                poi_address_ = re.sub(
                                    "\(.*?\)", "", poi_address)

                                shop_Name_ = shop_Name_.replace(' ', '')
                                poi_name_ = poi_name_.replace(' ', '')

                                name_ratio = Jaccrad(shop_Name_, poi_name_)
                                # print(shop_Name_, poi_name_, name_ratio)

                                shop_Address_ = shop_Address_.replace(' ', '')
                                poi_address_ = poi_address_.replace(' ', '')

                                if shop_Address_ is '' or poi_address_ is '':
                                    address_ratio = -1.0
                                else:

                                    address_ratio = Jaccrad(
                                        shop_Address_, poi_address_)

                                if poi_longitude is '' or poi_latitude is '' or shop_Longitude is '' or shop_Latitude is '':
                                    distance_ratio = -1.0
                                else:
                                    distance_ratio = poi_distance(float(poi_longitude), float(
                                        poi_latitude), float(shop_Longitude), float(shop_Latitude))

                                if '(' in shop_Name and ')' in shop_Name and '(' in poi_name and ')' in poi_name:
                                    shop_Name_dict = re.findall(
                                        r'[(](.*?)[)]', shop_Name)
                                    poi_name_dict = re.findall(
                                        r'[(](.*?)[)]', poi_name)
                                    shop_Name_dict = (shop_Name_dict[-1]).replace(
                                        ' ', '').replace('店', '')
                                    poi_name_dict = (poi_name_dict[-1]).replace(
                                        ' ', '').replace('店', '')
                                    # print("::", shop_Name_dict, poi_name_dict)
                                    dict_ratio = Jaccrad(
                                        shop_Name_dict, poi_name_dict)
                                else:
                                    dict_ratio = -1.0

                                gate_pass = gate(
                                    name_ratio, address_ratio, distance_ratio, dict_ratio)

                                pois_pairs = []
                                if gate_pass is False:
                                    print('*', shop_Name, poi_name, "{:.2f}".format(name_ratio), "{:.2f}".format(
                                        address_ratio), "{:.5f}".format(distance_ratio), "{:.2f}".format(dict_ratio), file=f_results_false)

                                    pass
                                else:
                                    # print(shop_Name,poi_name,"{:.2f}".format(name_ratio),"{:.2f}".format(address_ratio),"{:.5f}".format(distance_ratio),"{:.2f}".format(dict_ratio))
                                    pois_pairs.append(
                                        (shop_Name, poi_name, name_ratio, address_ratio, distance_ratio, dict_ratio))

                                    pass

                def ratio_sort(elem):
                    return (elem[2], elem[3], -elem[4])

                pois_pairs.sort(key=ratio_sort, reverse=True)
                for i in pois_pairs[0:4]:
                    print(i[0], i[1], "{:.2f}".format(i[2]), "{:.2f}".format(
                        i[3]), "{:.5f}".format(i[4]), "{:.2f}".format(i[5]), file=f_results_true)

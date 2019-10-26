import sys
sys.path.append('/usr/local/lib/python3.7/site-packages')
import pandas as pd
import numpy as np
import os
from pandas import DataFrame, Series
import re

# import jieba


df1 = pd.read_excel(
    r'/Users/nianyiren/Documents/seu-cloud/团队共享/RS_data/dianping-shop.xlsx', sheet_name=0)
df2 = pd.read_csv(
    r'/Users/nianyiren/Documents/seu-cloud/团队共享/RS_data/poi_restaurant.csv', encoding='gbk')


def cos_dist(vec1, vec2):
    dist1 = float(np.dot(vec1, vec2) /
                  (np.linalg.norm(vec1)*np.linalg.norm(vec2)))
    return dist1


def get_word_ratio(s1, s2):
    # 分词
    cut1 = jieba.cut(s1)
    cut2 = jieba.cut(s2)
    list_word1 = (','.join(cut1)).split(',')
    list_word2 = (','.join(cut2)).split(',')

    # 列出所有的词,取并集
    key_word = list(set(list_word1 + list_word2))
    # 给定形状和类型的用0填充的矩阵存储向量
    word_vector1 = np.zeros(len(key_word))
    word_vector2 = np.zeros(len(key_word))

    # 计算词频
    # 依次确定向量的每个位置的值
    for i in range(len(key_word)):
        # 遍历key_word中每个词在句子中的出现次数
        for j in range(len(list_word1)):
            if key_word[i] == list_word1[j]:
                word_vector1[i] += 1
        for k in range(len(list_word2)):
            if key_word[i] == list_word2[k]:
                word_vector2[i] += 1
    return cos_dist(word_vector1, word_vector2)


def Jaccrad(model, reference):
    grams_model = list(model)
    grams_reference = list(reference)

    temp = 0
    for i in grams_reference:
        if i in grams_model:
            temp = temp+1
    fenmu = len(grams_model)+len(grams_reference)-temp  # 并集
    jaccard_coefficient = float(temp/fenmu)  # 交集

    return jaccard_coefficient


def text_comparison(text1, text2):
    # 默认text1更长
    if len(text1) < len(text2):
        text1, text2 = text2, text1

    length = len(text2)

    same_length = 0
    for i in text2:
        if i in text1:
            same_length = same_length + 1

    return same_length/length


def poi_distance(df1_longitude, df1_latitude, df2_longitude, df2_latitude):
    distance = np.sqrt(np.square(df2_latitude-df1_latitude) +
                       np.square(df2_longitude-df1_longitude))
    return distance


def take_distance(elem):
    return (elem[1], -elem[2])


df1_data = df1[0:1000]
df2_data = df2[0:1000]

df1_names_long_lati = df1_data[['shopName', '经度', '纬度']]
df2_names_long_lati = df2_data[['poi_name', 'poi_longitude', 'poi_latitude']]

# print(df1_names)
# print(df1_names)

# print(df1_names_long_lati['经度'][0])

# exit()

f = open("./output_simple.txt", 'w+')

ratio_gate = 0.5
larger_ratio_gate = 0.8
distance_gate = 0.02

for (i_name, i_lo, i_la) in zip(df1_names_long_lati['shopName'], df1_names_long_lati['纬度'], df1_names_long_lati['经度']):
    name_distance_pairs = []
    local_ratio_gate = ratio_gate
    for (j_name, j_lo, j_la) in zip(df2_names_long_lati['poi_name'], df2_names_long_lati['poi_longitude'], df2_names_long_lati['poi_latitude']):
        i_name = i_name.replace(" ", '')
        j_name = j_name.replace(" ", '')

        # if '(' in i_name and ')' in i_name and '(' in j_name and ')' in j_name:
        #     i_name_ = re.sub("\(.*?\)", "", i_name)
        #     j_name_ = re.sub("\(.*?\)", "", j_name)
        #     same_ratio = text_comparison(i_name_, j_name_)
        #     # same_ratio = Levenshtein.distance(i_name_,j_name_)
        #     if same_ratio > ratio_gate:
        #         same_ratio = text_comparison(i_name, j_name)
        # else:
        #     i_name_ = re.sub("\(.*?\)", "", i_name)
        #     j_name_ = re.sub("\(.*?\)", "", j_name)
        #     same_ratio = text_comparison(i_name_, j_name_)
        if '(' in i_name and ')' in i_name and '(' in j_name and ')' in j_name:
            i_words = re.findall(r'[(](.*?)[)]', i_name)
            j_words = re.findall(r'[(](.*?)[)]', j_name)
            i_word = i_words[-1]
            j_word = j_words[-1]
            i_word = i_word.replace('旗舰', '').replace('店', '')
            j_word = j_word.replace('旗舰', '').replace('店', '')
            word_same_ratio = text_comparison(i_word, j_word)
            # print('**',i_name, ' ', j_name, ' ', i_word, ' ',
            #       j_word, ' ', word_same_ratio, file=f)
            if word_same_ratio < 0.5:
                break

        i_name_ = re.sub("\(.*?\)", "", i_name)
        j_name_ = re.sub("\(.*?\)", "", j_name)
        # same_ratio = Levenshtein.distance(i_name_, j_name_)

        # same_ratio = text_comparison(i_name_, j_name_)

        distance = poi_distance(float(i_lo), float(i_la),
                                float(j_lo), float(j_la))

        # same_ratio = get_word_ratio(i_name_, j_name_)
        same_ratio = Jaccrad(i_name_, j_name_)

        # if same_ratio > 0.5 and distance < 0.018:
        #     print(i_name, ";", j_name, ": ", "{:.2f}".format(
        #         same_ratio), " ", "{:.5f}".format(distance), file=f)
        # if min(len(i_name_), len(j_name_)) <= 3:
        #     local_ratio_gate = larger_ratio_gate

        # if same_ratio > local_ratio_gate and distance < distance_gate:
        #     name_distance_pairs.append((j_name, same_ratio, distance))
        if same_ratio > 0.1:
            name_distance_pairs.append((j_name, same_ratio, distance))
    name_distance_pairs.sort(key=take_distance, reverse=True)

    for i in name_distance_pairs[0:3]:
        # if i[1] > 0.5:
        #     if i[1] < 0.8 and i[2] < 0.01:
        #         print(i_name, ";", i[0], ":", "{:.2f}".format(
        #             i[1]), " ", "{:.5f}".format(i[2]), file=f)
        #     elif i[1] >= 0.8:
        #         print(i_name, ";", i[0], ":", "{:.2f}".format(
        #             i[1]), " ", "{:.5f}".format(i[2]), file=f)
        print(i_name, ";", i[0], ":", "{:.2f}".format(
            i[1]), " ", "{:.5f}".format(i[2]), file=f)

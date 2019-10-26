import sys
sys.path.append('/usr/local/lib/python3.7/site-packages')
import jieba
import numpy as np

def Jaccrad(model, reference):  # terms_reference为源句子，terms_model为候选句子
    # terms_reference = jieba.cut(reference)  # 默认精准模式
    # terms_model = jieba.cut(model)
    # grams_reference = list(terms_reference)  # 去重；如果不需要就改为list
    # grams_model = list(terms_model)

    grams_model = list(model)
    grams_reference = list(reference)
    print(grams_model)
    print(grams_reference)
    temp = 0
    for i in grams_reference:
        if i in grams_model:
            temp = temp+1
    print('temp',temp)
    fenmu = len(grams_model)+len(grams_reference)-temp  # 并集
    jaccard_coefficient = float(temp/fenmu)  # 交集
    return jaccard_coefficient


s1 = '土豆uncle'
s2 = '1831土豆uncle'
jaccard_coefficient = Jaccrad(s1, s2)
print(jaccard_coefficient)

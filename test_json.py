import json

# 入力JSONデータ
input_json = '[{"states": [0, 0, 0, 0, 0], "duration": 100}, {"states": [0, 2, 0, 0, 0], "duration": 100}, {"states": [0, 0, 0, 0, 0], "duration": 100}, {"states": [0, 0, 0, 0, 0], "duration": 100}, {"states": [0, 0, 0, 0, 0], "duration": 100}, {"states": [0, 0, 0, 0, 0], "duration": 100}, {"states": [0, 0, 0, 0, 0], "duration": 100}, {"states": [0, 0, 0, 0, 0], "duration": 100}, {"states": [0, 0, 0, 0, 0], "duration": 100}, {"states": [0, 0, 0, 0, 0], "duration": 100}]'

# JSONデータをロード
data = json.loads(input_json)

# 各オブジェクトを改行なしで出力し、statesの値のみ改行
for obj in data:
    # print('{{"states": [{0}]}}'.format(
    #     ', '.join(map(str, obj['states'])),
    #     obj['duration']
    # ))
    # print(obj['duration'])
    
    print('{{"states": [{0}], "duration": {1}}}'.format(
        ', '.join(map(str, obj['states'])),
        obj['duration']
    ))
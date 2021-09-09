# 0907：舒意恒学长的代码基础上，添加新的功能
import collections
import json
import re

from functools import reduce
# from utils.similarity_utils import literal_similarity


class KQAProJsonLoader:
    len: int

    def __init__(self, file_path: str):
        with open(file_path, 'r', encoding='UTF-8') as file:
            f = json.load(file)
            self.data = f
            self.len = len(self.data)

    def get_question_by_idx(self, idx) -> str:
        return self.data[idx]['question']

    def get_len(self):
        return self.len

    def get_sparql_by_idx(self, idx):
        if 'sparql' not in self.data[idx]:
            print('[ERROR] no SPARQL in dataset')
            return None
        return self.data[idx]['sparql']

    def get_program_by_idx(self, idx):
        return self.data[idx]['program']

    def get_choices_list_by_qid(self, idx):
        return self.data[idx]['choices']

    def get_ans_list_by_idx(self, idx):
        return self.data[idx]['answer']

    def get_boolean_questions(self):
        # 对应 SPARQL ASK 关键字
        res = []
        for idx in range(0, self.len):
            question = self.get_question_by_idx(idx)
            sparql = self.get_sparql_by_idx(idx)
            if sparql.startswith('ASK { '):
                res.append((question, sparql))
        return res

    def get_sparql_list(self):
        # return all sparql in list format
        return list(map(lambda item: item['sparql'], self.data))


def print_boolean_questions(dataloader: KQAProJsonLoader):
    dataloader.data.sort(key=lambda x: (len(x['sparql'].split('\n')), len(x['sparql'])))

    boolean_questions = dataloader.get_boolean_questions()
    for q in boolean_questions:
        print(q[0])
        print(q[1])
        print()
    print('len: ' + str(len(boolean_questions)))


def print_sparql(dataloader: KQAProJsonLoader, order=True):
    if order:
        dataloader.data.sort(key=lambda x: (len(x['sparql'].split('\n')), len(x['sparql'])))
    for idx in range(0, dataloader.get_len()):
        print('[question ' + str(idx) + '] ' + dataloader.get_question_by_idx(idx))
        print(dataloader.get_sparql_by_idx(idx))
        print()


def print_sparql_templates(dataloader: KQAProJsonLoader):
    res = set()
    for idx in range(0, dataloader.get_len()):
        sparql = dataloader.get_sparql_by_idx(idx)
        literals = re.findall('".*?"', sparql)
        for literal in literals:
            sparql = sparql.replace(literal, '""')

        relations = re.findall('<.*?>', sparql)
        for relation in relations:
            if relation.startswith('<pred:'):
                continue
            sparql = sparql.replace(relation, '<relation>')

        numbers = re.findall(' [0-9]+', sparql) + re.findall(' -[0-9]+', sparql)
        for number in numbers:
            sparql = sparql.replace(number, ' number')

        res.add(sparql.replace('^^xsd:double', '').replace('^^xsd:date', ''))

    res = list(res)
    res.sort(key=lambda x: len(x))
    for sparql in res:
        print(sparql)


def print_similar_questions(dataloader: KQAProJsonLoader):
    for idx in range(0, dataloader.get_len()):
        question = dataloader.get_question_by_idx(idx)
        sparql = dataloader.get_sparql_by_idx(idx)
        program = dataloader.get_program_by_idx(idx)
        print('[question ' + str(idx) + '] ' + question)
        print(sparql)
        # print(program)

        for idx1 in range(0, dataloader.get_len()):
            if idx == idx1:
                continue
            question1 = dataloader.get_question_by_idx(idx1)
            sparql1 = dataloader.get_sparql_by_idx(idx1)
            if abs(len(sparql1) - len(sparql)) > 5:
                continue
            # if literal_similarity(question, question1) > 0.9:
            #     print('[' + str(idx) + '] ' + question1)
            #     print(sparql1)
        print()


def print_programs(dataloader: KQAProJsonLoader):
    for idx in range(0, dataloader.get_len()):
        question = dataloader.get_question_by_idx(idx)
        program = dataloader.get_program_by_idx(idx)
        print('[question ' + str(idx) + '] ' + question)
        print(program)
        print()


def print_program_templates(dataloader: KQAProJsonLoader):
    res = dict()
    for idx in range(0, dataloader.get_len()):
        question = dataloader.get_question_by_idx(idx)
        program = str(dataloader.get_program_by_idx(idx))
        # print('[question ' + str(idx) + '] ' + question)

        inputs = re.findall('inputs\': \[.*?\]', program)
        for i in inputs:
            program = program.replace(i, 'inputs\': []')
        if program not in res:
            res[program] = []
        res[program].append(question)

    idx = 0
    for program in res:
        print('[Program ' + str(idx) + '] ' + program + ', len: ' + str(len(res[program])))
        if len(res[program]) > 50:
            for question in res[program]:
                print(question)
        print()
        idx += 1


def entities_relation_num(name1, name2, sparql_list):
    # 关系示例：?e_1 <part_of> ?e
    return reduce(
        lambda x, y: x + len(re.findall(rf'{name1}\s<[^>]*>\s{name2}', y)),
        sparql_list,
        0
    )


def entities_constraints(entity_name, sparql_list):
    # 类型约束示例：?e <pred:instance_of> ?c
    return reduce(
        lambda x, y: x + len(re.findall(rf'{entity_name}\s<pred:instance_of>\s\?c', y)),
        sparql_list,
        0
    )


def extract_entities_information(dataloader: KQAProJsonLoader):
    sparql_list = dataloader.get_sparql_list()
    res = dict()
    res['dataset_len'] = dataloader.get_len()

    # 统计各种 entity 的数量
    res['nums'] = dict()
    res['nums']['e1'] = reduce(lambda x, y: x+1 if '?e_1' in y else x, sparql_list, 0)
    res['nums']['e2'] = reduce(lambda x, y: x + 1 if '?e_2' in y else x, sparql_list, 0)
    res['nums']['e3'] = reduce(lambda x, y: x + 1 if '?e_3' in y else x, sparql_list, 0)
    res['nums']['e4'] = reduce(lambda x, y: x + 1 if '?e_4' in y else x, sparql_list, 0)

    # 统计 entities 之间的关系数量
    res['relations'] = dict()
    res['relations']['e_e1'] = entities_relation_num('\?e', '\?e_1', sparql_list)
    res['relations']['e_e2'] = entities_relation_num('\?e', '\?e_2', sparql_list)
    res['relations']['e_e3'] = entities_relation_num('\?e', '\?e_3', sparql_list)
    res['relations']['e_e4'] = entities_relation_num('\?e', '\?e_4', sparql_list)
    res['relations']['e1_e'] = entities_relation_num('\?e_1', '\?e', sparql_list)
    res['relations']['e1_e2'] = entities_relation_num('\?e_1', '\?e_2', sparql_list)
    res['relations']['e1_e3'] = entities_relation_num('\?e_1', '\?e_3', sparql_list)
    res['relations']['e1_e4'] = entities_relation_num('\?e_1', '\?e_4', sparql_list)
    res['relations']['e2_e'] = entities_relation_num('\?e_2', '\?e', sparql_list)
    res['relations']['e2_e1'] = entities_relation_num('\?e_2', '\?e_1', sparql_list)
    res['relations']['e2_e3'] = entities_relation_num('\?e_2', '\?e_3', sparql_list)
    res['relations']['e2_e4'] = entities_relation_num('\?e_2', '\?e_4', sparql_list)
    res['relations']['e3_e'] = entities_relation_num('\?e_3', '\?e', sparql_list)
    res['relations']['e3_e1'] = entities_relation_num('\?e_3', '\?e_1', sparql_list)
    res['relations']['e3_e2'] = entities_relation_num('\?e_3', '\?e_2', sparql_list)
    res['relations']['e3_e4'] = entities_relation_num('\?e_3', '\?e_4', sparql_list)
    res['relations']['e4_e'] = entities_relation_num('\?e_4', '\?e', sparql_list)
    res['relations']['e4_e1'] = entities_relation_num('\?e_4', '\?e_1', sparql_list)
    res['relations']['e4_e2'] = entities_relation_num('\?e_4', '\?e_2', sparql_list)
    res['relations']['e4_e3'] = entities_relation_num('\?e_4', '\?e_3', sparql_list)

    # entity 上的约束数量
    res['constraints'] = dict()
    res['constraints']['e'] = entities_constraints('\?e', sparql_list)
    res['constraints']['e1'] = entities_constraints('\?e_1', sparql_list)
    res['constraints']['e2'] = entities_constraints('\?e_2', sparql_list)
    res['constraints']['e3'] = entities_constraints('\?e_3', sparql_list)
    res['constraints']['e4'] = entities_constraints('\?e_4', sparql_list)

    return res


def extract_attribute_information(dataloader: KQAProJsonLoader):
    # 观察得出，典型的属性值 sparql 表达有两种模式:
    # ?e <population> ?pv . ?pv <pred:unit> \"1\" . ?pv <pred:value> \"24416\"^^xsd:double .
    # [三元组] <proportion> ?qpv . ?qpv <pred:unit> \"1\" . ?qpv <pred:value> \"0.154\"^^xsd:double .
    # 我们关注 (<population>, "1")
    res = dict()
    res['dataset_len'] = dataloader.get_len()

    # 一个 sparql 语句中，出现属性值的数量
    res['attribute_num'] = collections.defaultdict(int)
    # 计算每个属性-单位对 (<population>, "1") 的出现频率
    res['frequency'] = collections.defaultdict(int)
    for idx in range(0, dataloader.get_len()):
        sparql = dataloader.get_sparql_by_idx(idx)
        freq_list = \
            re.findall(r'(?:\[[^\]]*\]|\?e(?:_\d)?) <([^>]*)> \?q?pv(?:_\d)? \. \?q?pv(?:_\d)? <pred:unit> "(.*?)" \.', sparql)
        # e.g. [('number_of_children', '1'), ('height', 'kilometer')]
        if freq_list:
            res['attribute_num'][len(freq_list)] += 1
            for item in freq_list:
                res['frequency'][', '.join(item)] += 1

    # 按照出现频率排序
    res['frequency'] = {k: v for k, v in sorted(res['frequency'].items(), key=lambda x: x[1], reverse=True)}

    return res


def extract_filter_information(dataloader: KQAProJsonLoader):
    # 关注的模式 ?(q)pv(_1) <pred:year> ?v(_1) . FILTER () .
    res = dict()
    res['dataset_len'] = dataloader.get_len()
    res['FILTER_num'] = 0
    # 总共有多少句 sparql 中存在 FILTER 运算符 （每一句可能含多个 FILTER)
    res['Sparql_contains_FILTER'] = 0
    res['FITLER_on_qpv'] = 0
    # 一句 sparql 中 FITLER 出现的频率表（只记录>1）
    res['FILTER_freq'] = collections.defaultdict(int)
    for idx in range(0, dataloader.get_len()):
        sparql = dataloader.get_sparql_by_idx(idx)
        patterns = re.findall(r'q?pv(?:_\d)? <[^>]*> \?v(?:_\d)? . FILTER \([^)]*\) .', sparql)
        res['FILTER_num'] += len(patterns)
        qpv_len = len(list(filter(lambda x: re.search(r'qpv(?:_\d)?', x), patterns)))
        if qpv_len > 0:
            res['FITLER_on_qpv'] += qpv_len
        if len(patterns) > 1:
            res['FILTER_freq'][len(patterns)] += 1
        if len(patterns) >= 1:
            res['Sparql_contains_FILTER'] += 1
    return res


def extract_ORDERBY_information(dataloader: KQAProJsonLoader):
    # 首先观察 ORDER_BY 关键字出现的次数；每个 sparql 语句中是否包含多次 ORDER BY 操作
    # 其次含ORDER BY 问题可以划分为三个 pattern:
    # 1. "SELECT ?e WHERE { { ...  } UNION { ...  } ?e <duration> ?pv . ?pv <pred:value> ?v .  } ORDER BY DESC(?v) LIMIT 1"
    # 示例: Who has a smaller Erds number, Enrico Fermi or Natalie Portman?
    # 2. SELECT ?e WHERE { ... FILTER ...} ORDER BY DESC(?v) LIMIT 1
    # 示例：Among counties of Indiana, established before 1827, which one covers the largest area ?
    # 3. SELECT ?e WHERE { ... } ORDER BY DESC(?v) LIMIT 1
    # 示例: What animated series produced by Fox Broadcasting Company has the least episodes?
    res = dict()
    res['dataset_len'] = dataloader.get_len()
    res['ORDER_BY_NUM'] = 0
    res['SPARQL_CONTAINS_ORDER_BY'] = 0
    res['union_pattern_nums'] = 0
    union_pattern_regex = r'{ {[^}]*} UNION {[^}]*}.* ORDER BY .* LIMIT'
    res['filter_pattern_nums'] = 0
    filter_pattern_regex = r'{[^}]*FILTER[^}]*} ORDER BY .* LIMIT'
    res['normal_pattern_nums'] = 0
    normal_pattern_nums = r'{[^}]*} ORDER BY .* LIMIT'

    for idx in range(0, dataloader.get_len()):
        sparql = dataloader.get_sparql_by_idx(idx)
        order_by_nums = len(re.findall('ORDER BY', sparql))
        res['ORDER_BY_NUM'] += order_by_nums
        if order_by_nums >= 1:
            # 确认一下 ORDER BY 不与 qpv 同时出现
            # if re.search(r'qpv(?:_\d)?', sparql):
            #     print(sparql)
            res['SPARQL_CONTAINS_ORDER_BY'] += 1
            if re.search(union_pattern_regex, sparql):
                res['union_pattern_nums'] += 1
            if re.search(filter_pattern_regex, sparql):
                res['filter_pattern_nums'] += 1
            elif re.search(normal_pattern_nums, sparql):
                res['normal_pattern_nums'] += 1

    return res


def get_verify_template(dataloader: KQAProJsonLoader):
    templates = dataloader.get_sparql_templates()

    verify_templates = filter(lambda x: 'ASK' in x, templates)
    length = 0
    for template in verify_templates:
        print(template)
        length += 1
    print(length)
    print(len(templates))


def write_json_file(data_train, data_val, path, func):
    info = dict()
    info['train'] = func(data_train)
    info['val'] = func(data_val)
    with open(path, 'w+') as f:
        json.dump(info, f, indent=4)


if __name__ == "__main__":
    train_data = KQAProJsonLoader('./dataset/KQA-Pro-v1.0/train.json')
    val_data = KQAProJsonLoader('./dataset/KQA-Pro-v1.0/val.json')
    # test_data = KQAProJsonLoader('./dataset/KQA-Pro-v1.0/test.json')
    # print_boolean_questions(train_data)
    # print_similar_questions(train_data)
    # print_sparql(train_data)
    # print_sparql_templates(train_data)
    # print_programs(train_data)
    # print_program_templates(val_data)
    # print(val_data.get_program_by_idx(5))
    # print_boolean_questions(val_data)

    # write_json_file(train_data, val_data, './output/entities_info.json', extract_entities_information)

    # write_json_file(train_data, val_data, './output/attribute_info.json', extract_attribute_information)

    # write_json_file(train_data, val_data, './output/FILTER_info.json', extract_filter_information)

    # write_json_file(train_data, val_data, './output/ORDER_BY_info.json', extract_ORDERBY_information)

    # templates = val_data.get_sparql_templates()
    # for template in templates:
    #     if 'COUNT' in template:
    #         print(template)
    print_program_templates(val_data)

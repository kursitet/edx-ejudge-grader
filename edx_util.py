# coding=utf8
import re

import voluptuous as vol
import jinja2 as j2
import error as e
from ejudge_util import lang_id_get


def answer_msg(answer):
    loader = j2.FileSystemLoader('./template')
    env = j2.Environment(loader=loader, trim_blocks=True, lstrip_blocks=True)
    template = env.get_template('answer_popup.html')
    if 'error' in answer:
        answer['error'] = answer['error'].decode('utf-8')
    else:
        for item in answer['tests'].keys():
            answer['tests'][item] = answer['tests'][item].decode('utf-8')
    popup = template.render(answer=answer)
    return popup.encode('utf-8')


def validate_payload(grader_payload, resp):
    schem = vol.Schema({
        'course_name': vol.All(str, vol.Length(min=2, max=50)),
        'problem_type': 'standart',
        'problem_name': vol.All(str, vol.Length(min=1, max=3)),
        'lang_short_name': str,
        'input_data': vol.All(list, vol.Length(min=1, max=15)),
        'output_data': vol.All(list, vol.Length(min=1, max=15)),
        'prohibited_operators': list,
    }, extra=vol.REMOVE_EXTRA, required=True)
    try:
        schem(grader_payload)
    except vol.er.MultipleInvalid, err:
        raise e.ValidationError(str(err)[str(err).find('@') + 2:])
    contest_name = grader_payload['course_name']
    problem_name = grader_payload['problem_name']
    lang_name = grader_payload['lang_short_name']
    test_data = grader_payload['input_data']
    answer_data = grader_payload['output_data']
    operators = grader_payload['prohibited_operators']
    cyrilic = re.compile(u'[а-яё]', re.I)
    metasymbol = re.compile(r'[%$#@&<>!]', re.I)
    for key in grader_payload:
        if len(grader_payload[key]) == 0:
            raise e.EmptyPayload(key)
    if not lang_id_get(lang_name):
        raise e.ValidationError('lang_short_name')
    if len(test_data) != len(answer_data):
        raise e.ValidationError('in\output_data')
    if re.search(cyrilic, contest_name) is not None and re.search(metasymbol,
                                                                  contest_name) is not None:
        raise e.ValidationError('contest_name')
    if re.search(cyrilic, problem_name) is not None and re.search(metasymbol,
                                                                  problem_name) is not None:
        raise e.ValidationError('problem_name')
    check_prohibited_operators(operators, resp)
    return True


def answer_after_error(err):
    answer = dict()
    answer['error'] = err.msg
    answer['success'] = None
    answer['score'] = None
    return answer


def check_prohibited_operators(operators, student_respose):
    if not operators:
        return None
    command = [op.strip() for op in operators]
    regexp = re.compile(r'\b(?:%s)\b' % '|'.join(command), re.I)
    result = re.search(regexp, student_respose)
    if result is not None:
        raise e.ProhibitedOperatorsError(','.join(operators))

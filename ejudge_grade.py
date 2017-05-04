# coding=utf8
import re
import subprocess
import xml.etree.ElementTree as etree
from os import devnull

import voluptuous as vol

import ejudge_util
import error as e


def grader(response, grader_payload):
    contest_id = ejudge_util.get_contest_id(grader_payload['course_name'])
    problem_exist = ejudge_util.problem_exist(contest_id,
                                              grader_payload['problem_name'])
    if not contest_id or not problem_exist:
        ejudge_util.create_task(grader_payload)
        contest_id = ejudge_util.get_contest_id(grader_payload['course_name'])
    check_payload = ejudge_util.check_grader_payload(grader_payload,
                                                     ejudge_util.get_contest_path(
                                                         contest_id),
                                                     grader_payload[
                                                         'problem_name'])
    if check_payload:
        ejudge_util.update_payload(check_payload, grader_payload)
    result = run_grade_in_ejudge(response, grader_payload)
    return result


def run_grade_in_ejudge(response, grader_payload):
    response_file = open('response.txt', 'w')
    response_file.write(response.encode('utf-8'))
    response_file.close()
    contest_id = ejudge_util.get_contest_id(grader_payload['course_name'])
    problem_name = grader_payload['problem_name']
    lang = grader_payload['lang_short_name']
    run_id = ejudge_submit_run(contest_id, problem_name, lang)
    if not run_id:
        ejudge_util.update_session_file(contest_id)
        run_id = ejudge_submit_run(contest_id, problem_name, lang)
    run_id = run_id.strip()
    report = ejudge_dump_report(contest_id, run_id)
    if not report:
        pass
    result = pars_report(contest_id, run_id)
    return result


def pars_report(contest_id, run_id):
    result = dict()
    contest_path = ejudge_util.get_contest_path(contest_id)
    name_report_file = 'report_' + run_id + '.xml'
    del_str_in_report_xml(contest_path, name_report_file)
    result_xml = etree.parse(contest_path + 'report/' + name_report_file)
    test_tag = result_xml.getroot().find("tests").findall("test")
    test_ok = 0
    tests = {}
    if not test_tag:
        result['success'] = False
        result['score'] = 0
        return result
    for i in test_tag:
        status = i.attrib['status']
        num = str(i.attrib['num'])
        if status == 'OK':
            test_ok += 1
            tests[num] = 'OK'
        elif status == 'WA':
            tests[num] = 'Неправильный ответ'
        elif status == 'RT':
            tests[num] = 'Ошибка выполнения'
        elif status == 'CE':
            tests[num] = 'Ошибка компиляции'
        elif status == 'PT':
            tests[num] = 'Частичное решение'
        elif status == 'PE':
            tests[num] = 'Ошибка представления ответа'
    print "number success test = ", test_ok
    result['tests'] = tests
    if test_ok != len(test_tag):
        result['success'] = False
        result['score'] = 0
    else:
        result['success'] = True
        result['score'] = 1
    compiler_out = result_xml.getroot().find("compiler_output").text
    if compiler_out:
        result['compiler_output'] = compiler_out
    print "Report pars.\nresult=", result
    return result


def del_str_in_report_xml(contest_path, name_report):
    report_full_name = contest_path + 'report/' + name_report
    file_r = open(report_full_name, 'r')
    f_line = list()
    for line in file_r:
        f_line.append(line)
    file_r.close()
    f = open(report_full_name, 'w')
    for line in f_line[2:]:
        f.write(line)
    f.close()


def ejudge_submit_run(contest_id, problem_name, lang):
    session_key = ejudge_util.get_session_key(contest_id)
    command = ['/opt/ejudge/bin/ejudge-contests-cmd',
               str(contest_id),
               'submit-run',
               '--session',
               session_key,
               problem_name,
               lang,
               'response.txt']
    submit_run = subprocess.Popen(command, stdout=subprocess.PIPE)
    run_id, err = submit_run.communicate()
    print 'run id = ', run_id, 'contest_id = ', contest_id
    return run_id


def ejudge_dump_report(contest_id, run_id):
    name_report_file = 'report_' + run_id + '.xml'
    contest_path = ejudge_util.get_contest_path(contest_id)
    report_path = contest_path + 'report/' + name_report_file
    session_key = ejudge_util.get_session_key(contest_id)
    command = ['/opt/ejudge/bin/ejudge-contests-cmd',
               contest_id,
               'dump-report',
               '--session',
               session_key,
               run_id, '>',
               report_path]
    cmd_str = ''
    for arg in command:
        cmd_str += arg + ' '
    report_file = 1
    DEVNULL = open(devnull, 'wb')
    while report_file != 0:
        report_file = subprocess.call(cmd_str, shell=True,
                                      stdout=DEVNULL, stderr=DEVNULL)
    return True


def answer_msg(answer):
    if 'error' not in answer:
        message = result_test_table(answer['tests'])
    else:
        message = answer['error']
    button = '''<button id="answer_grader">Результат</button>'''
    css = '''<style type="text/css">
    #modal_form {
    width: 300px;
    height: 300px; /* Рaзмеры дoлжны быть фиксирoвaны */
    border-radius: 5px;
    border: 3px #000 solid;
    background: #fff;
    position: fixed; /* чтoбы oкнo былo в видимoй зoне в любoм месте */
    top: 45%; /* oтступaем сверху 45%, oстaльные 5% пoдвинет скрипт */
    left: 50%; /* пoлoвинa экрaнa слевa */
    margin-top: -150px;
    margin-left: -150px;
    display: none; /* в oбычнoм сoстoянии oкнa не дoлжнo быть */
    opacity: 0; /* пoлнoстью прoзрaчнo для aнимирoвaния */
    z-index: 6; /* oкнo дoлжнo быть нaибoлее бoльшем слoе */
    padding: 20px 10px;
}
/* Кнoпкa зaкрыть для тех ктo в тaнке) */
#modal_form #modal_close {
    width: 21px;
    height: 21px;
    position: absolute;
    top: 10px;
    right: 10px;
    cursor: pointer;
    display: block;
}
/* Пoдлoжкa */
#overlay {
    z-index:5; /* пoдлoжкa дoлжнa быть выше слoев элементoв сaйтa, нo ниже слoя мoдaльнoгo oкнa */
    position:fixed; /* всегдa перекрывaет весь сaйт */
    background-color:#000; /* чернaя */
    opacity:0.8; /* нo немнoгo прoзрaчнa */
    -moz-opacity:0.8; /* фикс прозрачности для старых браузеров */
    filter:alpha(opacity=80);
    width:100%;
    height:100%; /* рaзмерoм вo весь экрaн */
    top:0; /* сверху и слевa 0, oбязaтельные свoйствa! */
    left:0;
    cursor:pointer;
    display:none; /* в oбычнoм сoстoянии её нет) */
}
</style>'''
    modal = '''<div id="modal_form">
      <span id="modal_close">X</span>
      <h3>Результат проверки задания</h3>''' + message + '''
</div>
<div id="overlay"></div><!-- Пoдлoжкa -->'''
    script = '''<script type="text/javascript">
    $(document).ready(function() { // вся мaгия пoсле зaгрузки стрaницы
    $('#answer_grader').click( function(event){ // лoвим клик пo ссылки
        $("html,body").css("overflow","hidden");
        event.preventDefault(); // выключaем стaндaртную рoль элементa
        $('#overlay').fadeIn(400, // снaчaлa плaвнo пoкaзывaем темную пoдлoжку
             function(){ // пoсле выпoлнения предъидущей aнимaции
                $('#modal_form')
                    .css('display', 'block') // убирaем у мoдaльнoгo oкнa display: none;
                    .animate({opacity: 1, top: '50%'}, 200); // плaвнo прибaвляем прoзрaчнoсть oднoвременнo сo съезжaнием вниз
        });
    });
    /* Зaкрытие мoдaльнoгo oкнa, тут делaем тo же сaмoе нo в oбрaтнoм пoрядке */
    $('#modal_close, #overlay').click( function(){ // лoвим клик пo крестику или пoдлoжке
        $('#modal_form')
            .animate({opacity: 0, top: '45%'}, 200,  // плaвнo меняем прoзрaчнoсть нa 0 и oднoвременнo двигaем oкнo вверх
                function(){ // пoсле aнимaции
                    $(this).css('display', 'none'); // делaем ему display: none;
                    $('#overlay').fadeOut(400); // скрывaем пoдлoжку
                    $("html,body").css("overflow","auto");
                }
            );
    });
});
</script>'''
    ans = button + modal + css + script
    return ans


def result_test_table(tests):
    rows = ''
    for i in tests:
        row = '<tr><td>'+i+'</td><td>'+tests[i]+'</td></tr>'
        rows +=row
    start_tag = '''<table border="1" align="center"><tr>
                   <th>Тест</th>
                     <th>Результат</th>
                     </tr>'''
    end_tag = '</table>'
    table = start_tag + rows + end_tag
    return table


def validate_payload(grader_payload):
    schem = vol.Schema({
        'course_name': vol.All(str, vol.Length(min=2, max=50)),
        'problem_type': 'standart',
        'problem_name': vol.All(str, vol.Length(min=1, max=3)),
        'lang_short_name': str,
        'input_data': vol.All(list, vol.Length(min=1, max=15)),
        'output_data': vol.All(list, vol.Length(min=1, max=15)),
    }, extra=vol.REMOVE_EXTRA, required=True)
    try:
        schem(grader_payload)
    except vol.er.MultipleInvalid, err:
        raise e.ValidationError(str(err)[str(err).find('@')+2:])
    contest_name = grader_payload['course_name']
    problem_name = grader_payload['problem_name']
    lang_name = grader_payload['lang_short_name']
    test_data = grader_payload['input_data']
    answer_data = grader_payload['output_data']
    cyrilic = re.compile(u'[а-яё]', re.I)
    metasymbol = re.compile(r'[%$#@&<>!]', re.I)
    for key in grader_payload:
        if len(grader_payload[key]) == 0:
            raise e.EmptyPayload(key)
    if not ejudge_util.get_lang_id(lang_name):
        raise e.ValidationError('lang_short_name')
    if len(test_data) != len(answer_data):
        raise e.ValidationError('in\output_data')
    if re.search(cyrilic, contest_name) is not None and re.search(metasymbol, contest_name) is not None:
        raise e.ValidationError('contest_name')
    if re.search(cyrilic, problem_name) is not None and re.search(metasymbol,
                                                                  problem_name) is not None:
        raise e.ValidationError('problem_name')
    return True


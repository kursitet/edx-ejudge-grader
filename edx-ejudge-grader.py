# coding=utf8

import ast
import json
import logging
import time
import urllib2
import urlparse

import ejudge_grade as ejudge
import project_urls
import settings
import xqueue_util as util

log = logging.getLogger(__name__)

QUEUE_NAME = settings.QUEUE_NAME


def each_cycle():
    print('[*]Logging in to xqueue')
    session = util.xqueue_login()
    success_length, queue_length = get_queue_length(QUEUE_NAME, session)
    if success_length and queue_length > 0:
        success_get, queue_item = get_from_queue(QUEUE_NAME, session)
        print(queue_item)
        success_parse, content = util.parse_xobject(queue_item, QUEUE_NAME)
        if success_get and success_parse:
            answer = grade(content)
            content_header = json.loads(content['xqueue_header'])
            content_body = json.loads(content['xqueue_body'])
            xqueue_header, xqueue_body = util.create_xqueue_header_and_body(
                content_header['submission_id'],
                content_header['submission_key'],
                answer['success'],
                answer['score'],
                answer_msg(answer))
            (success, msg) = util.post_results_to_xqueue(session, json.dumps(
                xqueue_header), json.dumps(xqueue_body), )
            if success:
                print("successfully posted result back to xqueue")


def grade(content):
    body = json.loads(content['xqueue_body'])
    student_info = json.loads(body.get('student_info', '{}'))
    grader_payload = ast.literal_eval(body['grader_payload'].strip())
    resp = body.get('student_response', '')
    print "grader payload = ", grader_payload
    answer = ejudge.grader(resp, grader_payload)
    files = json.loads(content['xqueue_files'])
    for (filename, fileurl) in files.iteritems():
        response = urllib2.urlopen(fileurl)
        with open(filename, 'w') as f:
            f.write(response.read())
        f.close()
        response.close()
    return answer


def answer_msg(answer):
    exclamation = ''
    if answer['success']:
        exclamation = 'Good Job!'
    else:
        exclamation = 'Incorrect unswer!'
  #   button = '''<a class="instructor-info-action" id="grader-answer-btn" href="#grader-answer-modal">Подробнее</button>'''
  #   modal_window = '''<section aria-hidden="true" class="modal staff-modal" id="grader-answer-modal" style="height: 75%; display: none; position: fixed; opacity: 1; z-index: 11000; left: 50%; margin-left: -481px; top: 100px;">
  #   <div class="inner-wrapper" style="color: black; overflow: auto;">
  #     <header><h2><span class="display_name">Результат тестов</span></h2></header>
  #     <div id="grade-info" style="display: block;">
  #     	Здесь будет результат проверки
  #     </div>
  #   </div>
  # </section>'''
    # ans = button + modal_window
    ans = '''<div>
	<button id="answer_grader">Answer</button>
</div>
<div id="modal_form"><!-- Сaмo oкнo -->
      <span id="modal_close">X</span> <!-- Кнoпкa зaкрыть -->
      <h3>Результат проверки задания</h3>
</div>
<div id="overlay"></div><!-- Пoдлoжкa -->
<style type="text/css">
	#modal_form {
	width: 500px;
	height: 500px; /* Рaзмеры дoлжны быть фиксирoвaны */
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
	z-index: 5; /* oкнo дoлжнo быть нaибoлее бoльшем слoе */
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
	z-index:3; /* пoдлoжкa дoлжнa быть выше слoев элементoв сaйтa, нo ниже слoя мoдaльнoгo oкнa */
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
</style>
<script type="text/javascript">
	$(document).ready(function() { // вся мaгия пoсле зaгрузки стрaницы
	$('#answer_grader').click( function(event){ // лoвим клик пo ссылки с id="go"
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
				}
			);
	});
});
</script>'''
    if 'error' in answer:
        return answer['error']
    return ans


def get_from_queue(queue_name, xqueue_session):
    """
        Get a single submission from xqueue
        """
    try:
        success, response = util._http_get(xqueue_session,
                                           urlparse.urljoin(
                                               settings.XQUEUE_INTERFACE['url'],
                                               project_urls.XqueueURLs.get_submission),
                                           {'queue_name': queue_name})
    except Exception as err:
        return False, "Error getting response: {0}".format(err)

    return success, response


def get_queue_length(queue_name, xqueue_session):
    """
        Returns the length of the queue
        """
    try:
        success, response = util._http_get(xqueue_session,
                                           urlparse.urljoin(
                                               settings.XQUEUE_INTERFACE['url'],
                                               project_urls.XqueueURLs.get_queuelen),
                                           {'queue_name': queue_name})

        if not success:
            return False, "Invalid return code in reply"

    except Exception as e:
        log.critical("Unable to get queue length: {0}".format(e))
        return False, "Unable to get queue length."

    return True, response


try:
    logging.basicConfig()
    while True:
        each_cycle()
        time.sleep(2)
except KeyboardInterrupt:
    print '^C received, shutting down'

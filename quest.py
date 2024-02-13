from playwright.sync_api import Page, ElementHandle, Frame
from playwright.sync_api import sync_playwright
from unidecode import unidecode
import time
import json
import re

email = ""
password = ""

courses = ["JFo Java Foundations Learner - English",
           "DFo Database Foundations Learner - English", "JF Java Fundamentals Learner - English"]


loginURL = "https://myacademy.oracle.com/lmt/xlr8login.login?site=oa"
homeURL = "https://myacademy.oracle.com/lmt/"
default_timeout = 60*1000
sleepTime = 1
isScraping = True

currentCourse = "JFo Java Foundations Learner - English"


users = json.loads(open("./jf.json").read())
questioned: list = json.loads(open("./questioned.json").read())


modules = ["JFo Section 2 Quiz", "JFo Section 3 Quiz 1 - L1-L2",
           "JFo Section 3 Quiz 2 - L3-L5", "JFo Section 4 Quiz 1 - L1-L2",
           "JFo Section 4 Quiz 2 - L3-L5", "JFo Section 5 Quiz",  "JFo Section 8 Quiz",
           "JFo Java Foundations Midterm Exam", "JFo Section 7 Quiz 1 - L1-L3", "JFo Section 7 Quiz 2 - L4-L6", "DFo Section 2 Quiz", "DFo Section 1 Quiz"
           ]

"""
modules = ["JFo Section 2 Quiz", "JFo Section 3 Quiz 1 - L1-L2",
           "JFo Section 3 Quiz 2 - L3-L5", "JFo Section 4 Quiz 1 - L1-L2", 
           "JFo Section 4 Quiz 2 - L3-L5", "JFo Section 5 Quiz", "JFo Section 6 Quiz",
           "JFo Java Foundations Midterm Exam", "JFo Section 6 Quiz"
           ]

"""

course = ""


def login(page: Page):
    global courses, currentCourse, course
    page.query_selector("#inputUsername").type(email)
    page.query_selector("#inputPassword").type(password)
    page.query_selector(".primary.btn.login").click()
    page.wait_for_selector(selector=".card", state='visible')
    time.sleep(sleepTime)
    page.query_selector(".card").query_selector("a").click()
    time.sleep(sleepTime)
    page.wait_for_selector(
        selector=".card__body.result-detail", state='visible')
    titles = page.query_selector_all('.title')
    for title in titles:
        course = title.text_content().strip()
        if course in courses:
            if course == currentCourse:
                title.click()
                doModules(page)


def doModules(page: Page):
    page.wait_for_selector(
        selector=".learning-path--detail__section", state='visible')
    sections = page.query_selector_all(".learning-path--detail__section")
    for section in sections:
        if isScraping:
            content = getContentScrape(section)
            if content != None:
                print(content.query_selector(".title").text_content().strip())
                scrapeExam(content, page)
        else:
            if isMandatory(section):
                """completed = isModuleComplete(section)
                if (completed != None):
                    if (completed == False):"""
                content = getContentIndex(section)
                if content != None:
                    doContent(content, page, True)


def isModuleComplete(section: ElementHandle) -> bool:
    try:
        progress = section.query_selector(
            ".percentage-chart").get_attribute("data-defaultcenterlabel").split("/")
        if (len(progress) == 2):
            if (progress[0] == progress[1]):
                return True
            else:
                return False
    except Exception as e:
        pass


def doScrapeContents(section: ElementHandle, page: Page):
    try:
        pageUrl = page.url
        content = getContentScrape(section)
        title = content.query_selector('.title').text_content().strip()
        type = content.query_selector(
            ".label--type").text_content()
        if title not in modules:
            if content != None:
                isExam = False
                if type == "Exam":
                    isExam = True
                print(title)
                if isScraping:
                    if isExam:
                        scrapeExam(content, page)
                else:
                    if isCompleted(content):
                        print("Exam Is Already Completed")
                    elif isExam:
                        input("Please Complete Exam...!")
                    """else:
                        print(content.query_selector(
                            '.title').text_content())
                        doContent(content, page, isExam)"""
    except Exception as e:
        pass
    page.goto(pageUrl)


def doContents(section: ElementHandle, page: Page):
    try:
        global course
        pageUrl = page.url
        content = getContentIndex(section)
        if content != None:
            isExam = False
            type = content.query_selector(".label--type").text_content()
            if type == "Exam":
                isExam = True
            if isScraping:
                if isExam:
                    course = content.query_selector(
                        '.title').text_content().strip()
                    print(f"course : {course}")
                    modules.append()
                    scrapeExam(content, page)
            else:
                if isCompleted(content):
                    print("Exam Is Already Completed")
                elif isExam:
                    input("Please Complete Exam...!")
                else:
                    print(content.query_selector('.title').text_content())
                    doContent(content, page, isExam)
    except Exception as e:
        pass
    page.goto(pageUrl)


def getContentScrape(section: ElementHandle) -> ElementHandle:
    try:
        contents = section.query_selector_all(".card")
        for content in contents:
            title = content.query_selector('.title').text_content().strip()
            type = content.query_selector(
                ".label--type").text_content()
            if title not in modules and type == "Exam":
                return content
    except:
        pass


def getContentIndex(section: ElementHandle) -> ElementHandle:
    try:
        global mods
        contents = section.query_selector_all(".card")
        for content in contents:
            type = content.query_selector(".label--type").text_content()
            if type == "Exam" and content.query_selector('.title').text_content().strip() not in mods:
                return content
    except Exception as e:
        print(e)
        pass


def scrapeExam(content: ElementHandle, page: Page):
    try:
        content.query_selector("a").click()
        page.wait_for_selector(
            ".course-details__cta.cta").query_selector(".play").click()
        with page.context.expect_page() as popup:
            exam = popup.value
            exam.set_default_timeout(60000)
            exam.set_default_navigation_timeout(60000)
            doContinue(exam)
            iframe = exam.wait_for_selector(selector="iframe", state='visible')
            doExamFrameScrape(iframe.content_frame(), exam)
            exam.close()
    except:
        pass


def doExam(frame: Frame, page: Page, title: str):
    try:
        frame.wait_for_selector(".btn", state='visible').click()
        time.sleep(sleepTime)
        startFromOne(frame)
        total = int(frame.wait_for_selector(
            ".text-center", state='visible').query_selector_all("span")[1].text_content().replace("of ", ""))
        for index in range(total):
            topics = frame.query_selector_all(".card-body")
            for topic in topics:
                question = getQuestion(topic)
                options = getOptions(topic)
                correct_answers = getAnswers(question, options, title)
                for correct_answer in correct_answers:
                    selectOption(topic, correct_answer)
                if "two" in question:
                    checkTicked(topic, 2)
                else:
                    checkTicked(topic, 1)
                checkRadio(topic)
            getNextPage(frame)
        time.sleep(sleepTime)
        submitExam(frame)
    except Exception as e:
        print(e)


def clean_string(input_str):
    cleaned_str = unidecode(input_str)
    cleaned_str = re.sub(r'[^\x00-\x7F]+', ' ', cleaned_str)
    cleaned_str = cleaned_str.strip().encode(
        "ascii", "ignore").decode().replace("\\", "")
    return cleaned_str


def getAnswers(question: str, options: list, title: str) -> list:
    answers: list = json.loads(open(title+"_answers.json", 'r').read())
    for data in answers:
        title = clean_string(data['question'])
        if (question == title):
            return data['correct_options']
    print(question)
    for data in answers:
        correct_options = data['correct_options']
        for correct in correct_options:
            for option in options:
                if option == correct:
                    return correct_options
    return []


def doExamFrameScrape(frame: Frame, exam: Page):
    global course
    count = 0
    body = json.loads(open('./questions.json').read())
    try:
        try:
            frame.wait_for_selector(
                ".message-box-buttons-panel__window-button", state='visible', timeout=10000)
            frame.query_selector_all(
                ".message-box-buttons-panel__window-button")[1].click()
        except:
            pass
        frame.wait_for_selector(".btn", state='visible').click()
        time.sleep(sleepTime)
        startFromOne(frame)
        total = int(frame.wait_for_selector(
            ".text-center", state='visible').query_selector_all("span")[1].text_content().replace("of ", ""))
        for index in range(total):
            topics = frame.query_selector_all(".card-body")
            for topic in topics:
                question = getQuestion(topic)
                options = getOptions(topic)
                data = {'question': question, 'options': options}
                body.append(data)
                count += 1
            getNextPage(frame)
            time.sleep(sleepTime)
        data = json.dumps(body)
        open("questions.json", 'w').write(data)
    except Exception as e:
        open("questions.json", 'w').write(data)
        pass
    print(count)


def startFromOne(frame: Frame):
    try:
        starting = int(frame.wait_for_selector(
            ".text-center", state='visible').query_selector_all("span")[0].text_content().replace("Page ", ""))
        while (starting > 1):
            if (starting <= 1):
                break
            buttons = frame.wait_for_selector(
                ".text-center").query_selector_all(".btn")
            for button in buttons:
                if button.text_content() == "Previous":
                    button.click()
                    starting -= 1
                    time.sleep(sleepTime)
                    break
    except Exception as e:
        print("EXpection :", e)


def getNextPage(frame: Frame):
    try:
        buttons = frame.wait_for_selector(
            ".text-center").query_selector_all(".btn")
        for button in buttons:
            if button.text_content() == "Next":
                button.click()
                time.sleep(sleepTime)
                break
    except Exception as e:
        print("EXpection :", e)


def submitExam(frame: Frame):
    try:
        buttons = frame.wait_for_selector(
            ".text-center").query_selector_all(".btn")
        for button in buttons:
            if button.text_content() == "Finish Test":
                button.click()
                time.sleep(sleepTime)
                break
        buttons = frame.query_selector_all(".btn")
        for button in buttons:
            if button.text_content() == "Submit Test":
                button.click()
                time.sleep(sleepTime)
                break
    except Exception as e:
        pass


def selectOption(topic: ElementHandle, correct_answer: str):
    options = topic.query_selector(
        '.col-sm-10').query_selector(".col-sm-10").query_selector_all(".lbl")
    for option in options:
        title = clean_string(option.text_content().strip())
        if title == correct_answer:
            option.click()


def checkTicked(topic: ElementHandle, times: int):
    try:
        isChecked = topic.query_selector(
            '.col-sm-10').query_selector(".col-sm-10").query_selector_all(".ctrl.ck:checked")
        if (len(isChecked) <= 0):
            options = topic.query_selector(
                '.col-sm-10').query_selector(".col-sm-10").query_selector_all(".ctrl.ck")
            for option in options:
                option.click()
                times -= 1
                if times <= 0:
                    break
    except:
        pass


def checkRadio(topic: ElementHandle):
    try:
        isChecked = topic.query_selector(
            '.col-sm-10').query_selector(".col-sm-10").query_selector_all(".ctrl.rd:checked")
        if (len(isChecked) <= 0):
            option = topic.query_selector(
                '.col-sm-10').query_selector(".col-sm-10").query_selector(".ctrl.rd").click()
    except:
        pass


def getQuestion(topic: ElementHandle) -> str:
    return clean_string(topic.query_selector(
        '.col-sm-10').query_selector("div").query_selector_all("span")[1].text_content().strip())


def getOptions(topic: ElementHandle) -> list:
    data = []
    options = topic.query_selector(
        '.col-sm-10').query_selector(".col-sm-10").query_selector_all(".lbl")
    for option in options:
        data.append(clean_string(option.text_content().strip()))
    return data


def doContinue(exam: Page):
    try:
        exam.wait_for_selector(selector=".btn.btn-primary",
                               state='visible', timeout=5000).click()
    except:
        pass


def doContent(content: ElementHandle, page: Page, isExam: bool):
    try:
        title = content.query_selector(".title").text_content().strip()
        content.query_selector("a").click()
        page.wait_for_selector(
            ".course-details__cta.cta").query_selector(".play").click()
        with page.context.expect_page() as popup:
            exam = popup.value
            doContinue(exam)
            iframe = exam.wait_for_selector(selector="iframe", state='visible')
            if isExam:
                frame = iframe.content_frame()
                doExam(frame, page, title)
            else:
                src = iframe.get_attribute("src")
                if src != None:
                    if (src.lower().endswith(".pdf")) == False:
                        frame = iframe.content_frame()
                        if frame != None:
                            doFrame(frame, exam)
            exam.close()
    except Exception as e:
        print(e)
        pass


def doFrame(frame: Frame, exam: Page):
    try:
        frame.wait_for_selector(
            ".message-box-buttons-panel__window-button", state='visible', timeout=10000)
        frame.query_selector_all(
            ".message-box-buttons-panel__window-button")[0].click()
    except:
        pass
    nextState = True
    time.sleep(sleepTime)
    while nextState:
        try:
            next = frame.wait_for_selector(
                selector='.universal-control-panel__button_next', state='visible', timeout=5000)
            nextState = next.is_enabled()
            if nextState == False:
                break
            next.click()
        except:
            input("Please Complete Quiz...!")


def doQuiz(frame: Frame) -> bool:
    try:
        container = frame.wait_for_selector(
            selector=".quiz-control-panel", state='visible', timeout=10000)
        if container != None:
            run = True
            while run:
                try:
                    frame.query_selector(
                        ".choice-view__choice-container").click()
                except:
                    pass
                buttons = frame.query_selector_all(
                    ".quiz-control-panel__button")
                for button in buttons:
                    if (button.is_visible()):
                        print(button.text_content())
                        if (button.text_content() != "PREV"):
                            button.click()
                        if (button.text_content() == "NEXT"):
                            run = False
            return False
    except Exception as e:
        pass
    return True


def isCompleted(element: ElementHandle):
    if element.query_selector(".completed") != None:
        return True
    return False


def isMandatory(element: ElementHandle):
    try:
        if ("Mandatory" in element.query_selector("a").text_content()):
            return True
    except:
        pass
    return False


def isOptional(element: ElementHandle):
    if ("Optional" in element.query_selector("a").text_content()):
        return True
    return False


"""

"JF Section 2 Quiz 1 - L1-L7", "JF Section 2 Quiz 2 - L8-L14"

"""

for user in users:
    email = user['username']
    password = user['password']
    with sync_playwright() as player:
        if email != "" and password != "":
            print("Username :", email)
            print("Password :", password)
            browser = player.chromium.launch(channel='msedge',
                                             headless=False, args=["--start-maximized"])
            context = browser.new_context(no_viewport=True)
            context.set_default_timeout(default_timeout)
            context.set_default_navigation_timeout(default_timeout)
            page = context.new_page()
            page.goto(loginURL, wait_until='domcontentloaded')
            login(page)
            print("Course Ended...!")

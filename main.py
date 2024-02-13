from playwright.sync_api import Page, ElementHandle, Frame
from playwright.sync_api import sync_playwright
from unidecode import unidecode
import time
import json
import re

email = ""
password = ""

users = json.loads(open("./users.json").read())


for user in users:
    if user['status'] == False:
        email = user['username']
        password = user['password']
        user['status'] = True
        open("./users.json", 'w').write(json.dumps(users))
        break

courses = ["JFo Java Foundations Learner - English",
           "DFo Database Foundations Learner - English", "JF Java Fundamentals Learner - English"]


loginURL = "https://myacademy.oracle.com/lmt/xlr8login.login?site=oa"
homeURL = "https://myacademy.oracle.com/lmt/"
default_timeout = 20*1000
sleepTime = 1
isAll = True
currentCourse = "DFo Database Foundations Learner - English"
failedCourse = []


def getTitle(element: ElementHandle):
    return element.text_content().strip()


def login(page: Page) -> bool:
    try:
        global courses, currentCourse, failedCourse
        try:
            page.query_selector("#inputUsername").type(email, delay=100)
            page.query_selector("#inputPassword").type(password, delay=100)
            time.sleep(sleepTime)
            page.query_selector(".primary.btn.login").click()
        except:
            return True
        page.wait_for_selector(
            selector=".card__body.result-detail", state='visible')
        time.sleep(sleepTime)
        if currentCourse != "":
            print(currentCourse)
            page.query_selector(".card").query_selector("a").click()
            time.sleep(sleepTime*4)
            page.wait_for_selector(".title")
            titles = page.query_selector_all(".title")
            if (currentCourse not in list(map(getTitle, titles))):
                print(f"{currentCourse} is Not Enrolled...!")
                return True
            for title in titles:
                if title.text_content().strip() == currentCourse:
                    title.click()
                    return doModules(page)
        return False
    except Exception as e:
        print(f"Error : {e}")
        return False


def doModules(page: Page) -> bool:
    global isAll, failedCourse
    page.wait_for_selector(
        selector=".learning-path--detail__section", state='visible')
    sections = page.query_selector_all(".learning-path--detail__section")
    notSelected = True
    for section in sections:
        if isMandatory(section):
            completed = isModuleComplete(section)
            if (completed != None):
                if (completed == False):
                    content = getContentIndex(section)
                    if ("collapse" in section.get_attribute("class")):
                        section.click()
                    if content != None:
                        title = content.query_selector(".title").text_content()
                        contentType = content.query_selector(
                            ".label--type").text_content()
                        print(title)
                        # not in ["JFo Section 6 Quiz", "JFo Section 7 Quiz 2 - L4-L6"]:
                        if title.strip():
                            if contentType == "Exam":
                                doContent(content, page, True)
                                notSelected = False
                                break
                            else:
                                doContent(content, page, False)
                            notSelected = False
                            if isCompleted(content) and "Final Exam" in content.query_selector(".title").text_content().strip():
                                if len(failedCourse) > 0:
                                    return False
                                return True
                            break
    if len(failedCourse) > 0:
        return False
    return notSelected


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


def getContentIndex(section: ElementHandle) -> ElementHandle:
    try:
        global isAll, failedCourse
        contents = section.query_selector_all(".card")
        for content in contents:
            title = content.query_selector(".title").text_content().strip()
            contentType = content.query_selector(
                ".label--type").text_content()
            completed = isCompleted(content)
            if completed == False and title not in failedCourse:
                if contentType == "Exam" and isAll:
                    return content
                elif contentType != "Exam":
                    return content

    except Exception as e:
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
                if (question != "Which of the following wild card character is used to import all the classes in a particular package?"):
                    options = getOptions(topic)
                    correct_answers = getAnswers(question, options, title)
                    for correct_answer in correct_answers:
                        selectOption(topic, correct_answer)
                    if topic.query_selector(".checkbox") == None:
                        checkRadio(topic)
                    else:
                        checkTicked(topic, 2)
                else:
                    input("Please Select Option : ")
            getNextPage(frame)
            time.sleep(sleepTime)
        submitExam(frame)
    except Exception as e:
        print(f"Expection : ${e}")
        pass


def clean_string(input_str):
    cleaned_str = unidecode(input_str)
    cleaned_str = re.sub(r'[^\x00-\x7F]+', ' ', cleaned_str)
    cleaned_str = cleaned_str.strip().encode(
        "ascii", "ignore").decode().replace("\\", "")
    return cleaned_str


def getAnswers(question: str, options: list, title: str) -> list:
    answers: list = json.loads(open("./data/answers.json", 'r').read())
    for data in answers:
        title = data['question']
        if (question == title):
            return data['correct_options']
    return []


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
        pass


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
        pass


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
            topic.query_selector(
                '.col-sm-10').query_selector(".col-sm-10").query_selector_all(".lbl")[0].click()
            topic.query_selector(
                '.col-sm-10').query_selector(".col-sm-10").query_selector_all(".lbl")[1].click()
            print("None Is Ticked...!")

    except:
        pass


def checkRadio(topic: ElementHandle):
    try:
        isChecked = topic.query_selector(
            '.col-sm-10').query_selector(".col-sm-10").query_selector_all(".ctrl.rd:checked")
        if (len(isChecked) <= 0):
            topic.query_selector(
                '.col-sm-10').query_selector(".col-sm-10").query_selector_all(".lbl")[0].click()
            print("None Is Checked...!")
    except:
        pass


def getQuestion(topic: ElementHandle) -> str:
    return topic.query_selector(
        '.col-sm-10').query_selector("div").query_selector_all("span")[1].text_content().strip()


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
        global failedCourse
        title = content.query_selector(".title").text_content().strip()
        content.query_selector("a").click()
        play = page.wait_for_selector(
            ".course-details__cta.cta").query_selector(".play")
        if play.get_attribute("data-tooltip") == "Maximum number of attempts reached":
            failedCourse.append(title)
            page.close()
        else:
            page.wait_for_selector(
                ".course-details__cta.cta").query_selector(".play").click()
            with page.context.expect_page() as popup:
                exam = popup.value
                doContinue(exam)
                iframe = exam.wait_for_selector(
                    selector="iframe", state='visible')
                frame = iframe.content_frame()
                if isExam:
                    doExam(frame, page, title)
                    exam.close()
                else:
                    src = iframe.get_attribute("src")
                    if src != None:
                        if (src.lower().endswith(".pdf")) == False:
                            if frame != None:
                                doFrame(frame, exam, title)
                exam.close()
    except Exception as e:
        pass


def doFrame(frame: Frame, exam: Page, title: str):
    try:
        try:
            box = frame.wait_for_selector(".message-box", timeout=10000)
            box.query_selector_all("button")[0].click()
        except:
            pass
        nextState = True
        time.sleep(sleepTime)
        while nextState:
            try:
                buttons = frame.wait_for_selector(
                    selector='.universal-control-panel', state='visible', timeout=5000).query_selector_all("button")
                for button in buttons:
                    if (button.text_content().strip().lower() == "next"):
                        nextState = button.is_enabled()
                        if nextState == False:
                            break
                        button.click()
            except Exception as e:
                break
        if title.strip().startswith("JFo 1") == False:
            doQuiz(frame)
            next = frame.wait_for_selector(
                selector='.universal-control-panel__button_next', state='visible', timeout=5000)
            nextState = next.is_enabled()
            if nextState:
                next.click()
    except:
        pass


def doQuiz(frame: Frame) -> bool:
    try:
        frame.wait_for_selector(
            selector='.universal-control-panel__button_next', state='visible', timeout=5000).click()
        return True
    except:
        pass
    try:
        frame.wait_for_selector(".player-shape-view")
        elements = frame.query_selector_all(".player-shape-view")
        element = elements[len(elements)-1]
        if element != None:
            title = element.text_content().strip()
            if title == "RETRY QUIZ":
                element.click()

    except:
        pass
    try:
        container = frame.wait_for_selector(
            selector=".quiz-control-panel", state='visible', timeout=10000)
        if container != None:
            run = True
            while run:
                try:
                    question = frame.query_selector(
                        ".player-shape-view").query_selector("span").text_content().strip()
                    options = frame.query_selector_all(".choice-view")
                    data: list = json.loads(
                        open("./data/quiz_answers.json", 'r').read())
                    for quest in data:
                        text = quest['question'].strip()
                        if text == question:
                            for option in options:
                                for op in quest['correct_options']:
                                    opText = str(op).strip()
                                    seText = option.text_content().strip()
                                    if opText == seText:
                                        option.query_selector(
                                            ".choice-view__choice-container").click()

                except:
                    pass
                buttons = frame.query_selector(
                    ".quiz-control-panel").query_selector_all("button")
                for button in buttons:
                    if (button.is_visible()):
                        if (button.text_content().strip() != "PREV"):
                            button.click()
                        if (button.text_content() == "NEXT"):
                            if button.is_enabled() == False:
                                input("Please Complete Quiz & Press Enter : ")
                            run = False
            frame.wait_for_selector(
                ".universal-control-panel", state='visible')
            buttons = frame.query_selector_all(".universal-control-panel")
            for button in buttons:
                if (button.is_enabled()):
                    if (button.text_content() == "NEXT"):
                        button.click()
            return False
    except Exception as e:
        pass
    return True


def isCompleted(element: ElementHandle):
    if element.query_selector(".completed") != None:
        return True
    return False


def isMandatory(section: ElementHandle):
    try:
        if ("Mandatory".lower() in section.query_selector(".completion-rules-span").text_content().strip().lower()):
            return True
    except Exception as e:
        pass
    return False


def isOptional(element: ElementHandle):
    if ("Optional" in element.query_selector("a").text_content()):
        return True
    return False


with sync_playwright() as player:
    if email != "" and password != "":
        print("Username :", email)
        print("Password :", password)
        # time.sleep(120)
        while True:
            browser = player.chromium.launch(
                headless=False, args=["--start-maximized"])
            context = browser.new_context(no_viewport=True)
            context.set_default_timeout(default_timeout)
            context.set_default_navigation_timeout(default_timeout)
            page = context.new_page()
            page.goto(loginURL)
            status = login(page)
            browser.close()
            if status:
                break
        print("Course Finished...!")

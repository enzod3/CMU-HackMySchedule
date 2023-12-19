#Main file
import pandas as pd
from cmu_graphics import drawLabel,drawRect,rgb,runApp,app
from courseFunctions import generateSchedules,addCourse,addCourseHelper
from UI import NavBar,CourseView,ScheduleView,SectionsView,Button

#cmu graphics on app start
def onAppStart(app: any):
    app.course_df = pd.read_csv("./data/spring_24.dat", delimiter='\t')
    mask = app.course_df['Location'].str.contains('Qatar', na=False)
    app.course_df = app.course_df[~mask].reset_index(drop=True) #remove Qatar courses
    app.course_df = app.course_df.dropna(thresh=2).reset_index(drop=True)#remove blank and 1 val rows
    #Course info come from https://enr-apps.as.cmu.edu/open/SOC/SOCServlet/completeSchedule
    app.rating_df = pd.read_json("./data/TeacherRatings.json")
    #Ratings from Scotty Lab's CMU Courses, site: https://cmucourses.com/
    app.primaryFontSize = 14
    app.secondaryFontSize = 12
    app.minUnits = 36
    app.navbar = NavBar(app,350)
    app.courseview = CourseView(app,350)
    app.scheduleview = ScheduleView(app,350)
    app.sectionsview = SectionsView(app,350)
    app.popupUnitButton = Button(lambda: (app.state.update({"unitPopup":False}),
                                                addCourse(app,app.state["unitPopupGroupID"],app.state["unitPopupCourseID"],units=app.state["unitPopupInput"]),
                                                app.state.update({"unitPopupInput":""})),
                                                app.width//2 - 40,app.height//2 + 66,100,24,fill=rgb(45,45,45))
    app.popupCourseSaveButton = Button(lambda: (app.state.update({"courseEditPopup":False}),
                                                app.state["editPopupCourse"].overrideWorkloads(app.state["editPopupCourseWorkloadInput"]),
                                                app.state.update({"editPopupCourseWorkloadInput":""}),
                                                generateSchedules(app)),
                                                app.width//2 - 40,app.height//2 + 66,100,24,fill=rgb(45,45,45))
    app.popupCourseCancelButton = Button(lambda: app.state.update({"courseEditPopup":False}),app.width//2 +65,app.height//2 + 66,50,24,fill=rgb(45,45,45))

    app.workloadWeight = 0.33
    app.ratingWeight = 0.33
    app.breakWeight = 0.33

    #------------- APP STORAGE --------------
    app.schedules = []
    app.courseGroup = dict()# Key: list[Course]
    #-----------------------------------------

    # ---------- APP VIEW STATE --------------
    app.state = dict()
    app.state["selectedMenu"] = "schedules" 
    app.state["activeButtons"] = []
    app.state["courseInput"] = ""
    app.state["groupInput"] = ""
    app.state["courseInputError"] = ""
    app.state["selectedScheduleIndex"] = 0
    app.state["schedulePage"] = 0
    app.state["sectionsPage"] = 0
    app.state["unitPopup"] = False
    app.state["unitPopupInput"] = ""
    app.state["courseEditPopup"] = False
    app.state["editPopupCourse"] = None
    app.state["editPopupCourseWorkloadInput"] = ""
    #-----------------------------------------
    with open('./data/courses.txt', 'r') as file:
        for line in file:
            courses = line.split(':')
            group = courses[0].strip()
            course_ids = courses[1].split(',')
            for course_id in course_ids:
                try:
                    addCourse(app, group, course_id.strip(),init=True)
                except Exception as e:
                    print(e)
    generateSchedules(app)
    
#cmu graphics redraw all function
def redrawAll(app: any):
    app.state["activeButtons"] = []
    app.navbar.draw()
    match app.state["selectedMenu"]:
        case "builder":
            app.courseview.draw()
        case "schedules":
            app.scheduleview.draw()
        case "sections":
            app.sectionsview.draw()
    drawPopups(app)

#draws any popups that are active
def drawPopups(app:any):
    if app.state["unitPopup"]:
        app.state["activeButtons"] = [app.popupUnitButton]
        drawRect(0,0,app.width,app.height,opacity=80)
        drawRect(app.width//2 - 125, app.height//2 - 100, 250,200, fill="White", border="Black")
        app.popupUnitButton.draw()
        drawLabel("Save & Close",app.width//2 +10,app.height//2 + 78,fill="White",size=app.primaryFontSize)

        drawLabel("Add Units for Variable Course: " + app.state["unitPopupCourseID"],app.width//2,app.height//2-78,size=app.primaryFontSize)
        unitInput = "0" if app.state["unitPopupInput"] == "" else app.state["unitPopupInput"]
        drawRect(5+app.width//2,app.height//2,40, 24,fill="White",border="Black")
        drawLabel(unitInput,34+app.width//2, app.height//2+12,fill="Black",size=app.primaryFontSize, align="right")
        drawLabel("Units:",app.width//2-5, app.height//2+12,fill="Black",size=app.primaryFontSize, align="right")


    elif app.state["courseEditPopup"]:
        app.state["activeButtons"] = [app.popupCourseSaveButton,app.popupCourseCancelButton]
        drawRect(0,0,app.width,app.height,opacity=80)
        drawRect(app.width//2 - 125, app.height//2 - 100, 250,200, fill="White", border="Black")
        app.popupCourseSaveButton.draw()
        app.popupCourseCancelButton.draw()
        drawLabel("Save & Close",app.width//2 +10,app.height//2 + 78,fill="White",size=app.primaryFontSize)
        drawLabel("Cancel",app.width//2 +90,app.height//2 + 78,fill="White",size=app.primaryFontSize)

        drawLabel("Edit Course: " + app.state["editPopupCourse"].courseID,app.width//2,app.height//2-78,size=app.primaryFontSize)
        workloadInput = "0" if app.state["editPopupCourseWorkloadInput"] == "" else app.state["editPopupCourseWorkloadInput"]
        drawRect(5+app.width//2,app.height//2,40, 24,fill="White",border="Black")
        drawLabel(workloadInput,34+app.width//2, app.height//2+12,fill="Black",size=app.primaryFontSize, align="right")
        drawLabel("Workload:",app.width//2-5, app.height//2+12,fill="Black",size=app.primaryFontSize, align="right")

#Handles button clicks for active buttons
def onMousePress(app, mouseX: int, mouseY:int):
    for button in app.state["activeButtons"]:
        button.checkClick(mouseX,mouseY)

#Handles button hovers for active buttons
def onMouseMove(app, mouseX: int, mouseY:int):
    for button in app.state["activeButtons"]:
        button.checkHover(mouseX,mouseY)

#Handles all app/key inputs
def onKeyPress(app,key):
    app.state["courseInputError"] = ""
    if app.state["courseEditPopup"]:
        if ((key.isnumeric() or (key == "." and "." not in app.state["editPopupCourseWorkloadInput"])) and
            float(app.state["editPopupCourseWorkloadInput"] + key) <=30 and len( app.state["editPopupCourseWorkloadInput"]) <= 4):
            app.state["editPopupCourseWorkloadInput"] += key
        elif key == "backspace":
            app.state["editPopupCourseWorkloadInput"] = app.state["editPopupCourseWorkloadInput"][:-1]
    
    elif app.state["unitPopup"]:
        if ((key.isnumeric() or (key == "." and "." not in app.state["unitPopupInput"])) and
            float(app.state["unitPopupInput"] + key) <=30 and len( app.state["unitPopupInput"]) <= 4):
            app.state["unitPopupInput"] += key
        elif key == "backspace":
            app.state["unitPopupInput"] = app.state["unitPopupInput"][:-1]


    elif app.state["selectedMenu"] =="sections":
        coursesLength = len([x for courses in app.courseGroup.values() for x in courses])
        if key == "right" and app.state["sectionsPage"] < ((coursesLength-1)//2):
            app.state["sectionsPage"] += 1
        elif key == "left" and app.state["sectionsPage"] > 0:
            app.state["sectionsPage"] -= 1
        elif key.isnumeric() and len(app.state["courseInput"]) < 5:
            app.state["courseInput"] += key
        elif key.isalpha() and len(key) == 1 and len(app.state["groupInput"]) < 20:
            app.state["groupInput"] += key
        elif key =="backspace" :
            app.state["courseInput"] = ""
            app.state["groupInput"] = ""
        elif key =="enter" and len(app.state["courseInput"]) == 5:
            addCourseHelper(app)
    
    elif app.state["selectedMenu"] =="schedules":
        if key == "left" and app.state["schedulePage"] > 0:
            app.state["schedulePage"] -= 1
        elif key == "right" and app.state["schedulePage"] < (len(app.schedules)//((app.height - 50)/40)):
            app.state["schedulePage"] += 1
        elif key.isnumeric() and len(app.state["courseInput"]) < 5:
            app.state["courseInput"] += key
        elif key.isalpha() and len(key) == 1 and len(app.state["groupInput"]) < 20:
            app.state["groupInput"] += key
        elif key =="backspace" :
            app.state["courseInput"] = ""
            app.state["groupInput"] = ""
        elif key =="enter" and len(app.state["courseInput"]) == 5:
            addCourseHelper(app)

    elif app.state["selectedMenu"] =="builder":
        if key == "left" and app.state["selectedScheduleIndex"] > 0:
            app.state["selectedScheduleIndex"] -= 1
        elif key == "right" and app.state["selectedScheduleIndex"] < (len(app.schedules) -1):
            app.state["selectedScheduleIndex"] += 1



if __name__ == "__main__":
    runApp(1280,720)

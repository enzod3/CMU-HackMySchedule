import pandas as pd
from cmu_graphics import *
from typing import Set,List,Dict,Callable
import random
from colorsys import hsv_to_rgb



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
    app.navbar = NavBar(app,300)
    app.courseview = CourseView(app,300)
    app.scheduleview = ScheduleView(app,300)
    # should be loaded/stored
    #------------- APP STORAGE --------------
    app.schedules = dict()
    # app.courseGroups = {}
    app.courseGroup = dict()# Key: List[Course]
        # "test": CourseGroup({"Required":{Course('15112','Fundamentals of Programming and Computer Science',['Mike'],48)}})
    #-----------------------------------------

    # ---------- APP VIEW STATE --------------
    app.state = dict()
    app.state["selectedMenu"] = "builder" 
    # app.state["selectedCourseGroup"] = None
    app.state["activeButtons"] = []
    app.state["courseInput"] = ""
    app.state["groupInput"] = ""
    app.state["courseInputError"] = ""
    #-----------------------------------------
    addCourse(app, "Required",'15122')
    addCourse(app, "Required",'21122')
    addCourse(app, "Required",'15151')

    addCourse(app, "Humanities",'80330')
    addCourse(app, "Humanities",'85211')
    addCourse(app, "Humanities",'85241')

    addCourse(app, "Business",'73102')

    generateSchedules(app)
    exit()
    

def redrawAll(app: any):
    app.state["activeButtons"] = []
    app.navbar.draw()
    match app.state["selectedMenu"]:
        case "builder":
            app.courseview.draw()
        case "schedules":
            app.scheduleview.draw()

def onMousePress(app, mouseX: int, mouseY:int):
    for button in app.state["activeButtons"]:
        button.checkClick(mouseX,mouseY)


def onKeyPress(app,key):
    app.state["courseInputError"] = ""
    if key.isnumeric() and app.state["selectedMenu"] =="builder" and len(app.state["courseInput"]) < 5:
        app.state["courseInput"] += key
    elif key.isalpha() and len(key) == 1 and app.state["selectedMenu"] =="builder" and len(app.state["groupInput"]) < 20:
        app.state["groupInput"] += key
    elif key =="backspace":
        # app.state["courseInput"] = app.state["courseInput"][:-1]
        app.state["courseInput"] = ""
        app.state["groupInput"] = ""
    elif key =="enter" and len(app.state["courseInput"]) == 5:
        addCourseHelper(app)


def addCourseHelper(app):
    try:
        groupID = app.state["groupInput"] if app.state["groupInput"] != "" else "Required"
        addCourse(app,groupID,app.state["courseInput"])
    except Exception as e:
        app.state["courseInputError"] = e
    app.state["courseInput"] = ""
    app.state["groupInput"] = ""

def addCourse(app:any, groupID: str, courseID: int):
    if (df_filtered := app.course_df[app.course_df["Course"] == courseID]).empty:
        raise ValueError("Course does not exist")
    courseIndex = df_filtered.index[0]
    course = app.course_df.iloc[courseIndex]
    courseInfo = dict()
    courseInfo["courseID"] = courseID
    courseInfo["title"] = course["Title"]
    courseInfo["units"] = float(course["Units"])
    courseInfo["lectures"] = set()
    courseInfo["sections"] = set()

    courseIndex += 1 #nextLine
    if pd.isnull(courseInfo["units"]):
        course = app.course_df.iloc[courseIndex]
        courseInfo["units"] = float(course["Units"])

    while pd.isnull((courseSection := app.course_df.iloc[courseIndex])["Course"]) and courseIndex < len(app.course_df): #get all times for course
        newSection = Section(courseSection["Lec/Sec"],courseSection["Days"],courseSection["Begin"],courseSection["End"],courseSection["Bldg/Room"],courseSection["Location"],courseSection["Instructor(s)"])		
        courseIndex += 1
        while pd.isnull((courseSection := app.course_df.iloc[courseIndex])["Lec/Sec"]) and courseIndex < len(app.course_df): #multiple days/times/locations per section
            if pd.isnull(app.course_df.iloc[courseIndex]["Days"]):
                break
            newSection.addDays(courseSection["Days"],courseSection["Begin"],courseSection["End"],courseSection["Bldg/Room"],courseSection["Location"],courseSection["Instructor(s)"])
            courseIndex += 1
        if "lec" in newSection.section.lower():
            courseInfo["lectures"].add(newSection)
        else:
            courseInfo["sections"].add(newSection)

    newCourse = Course(**courseInfo)
    if groupID in app.courseGroup:
        app.courseGroup[groupID] += [newCourse]
    else:
        app.courseGroup[groupID] = [newCourse]

    if sum([len(app.courseGroup[groupID]) for groupID in app.courseGroup]) >= 4:
        # generateSchedules(app)
        pass

def generateSchedules(app: any):


    print(generateSchedulesHelper(app.courseGroup,[3,3,1],None,None))


    # for groupID in app.courseGroup:
    #     for course in app.courseGroup[groupID]:
    #         print(course.title)
    #         print(course.units)


def generateSchedulesHelper(courses, targetSize, schedule, solutions):
    if all(len(courses[k]) == s for (k,s) in zip(courses,targetSize)): #Check if we have reach target schedule format https://docs.python.org/3.3/library/functions.html#zip
        print(True)


class Period():
    def __init__(self, day: str, begin: str,end: str):
        self.day = day
        self.time = (self.convertToMinutes(begin),self.convertToMinutes(end)) #(begin mins, end mins)
    def convertToMinutes(self,timeString):
        minutes = 0
        if "PM" in timeString:
            minutes += 60 * 12
        (hrs, mins) = timeString.split(':')
        minutes += int(hrs) *60 + int(mins[:2])
        return minutes

class Day():
    def __init__(self,day:str,begin:str,end:str,bld_room:str,location:str,instructors: List[str]):
        self.day = day
        self.period = Period(day,begin,end)
        self.bld_room = bld_room
        self.location = location
        self.instructors = instructors

class Section(): #lectures/sections
    def __init__(self,section:str,days:str,begin:str,end:str,bld_room:str,location:str, instructors: List[str]):
        self.section = section
        self.days = set()
        self.addDays(days,begin,end,bld_room,location,instructors)

    def addDays(self, days:str, begin:str,end:str,bld_room:str,location:str, instructors: List[str]):
        for day in days:    
            self.days.add(Day(day,begin,end,bld_room,location,instructors))

class Course():
    def __init__(self,courseID: int, title:str,units:float,lectures: Set[Section],sections: Set[Section]):
        self.courseID = courseID
        self.title = title
        self.units = units
        self.lectures = lectures
        self.sections = sections
        self.color = rgb(*getRandomColor())

# Rank, CourseCodes, Workload, Instructor Score, Average Break(Median or Mean),Overall
class Schedule():
    def __init__(self,courses: List[Course]):
        self.name = None
        self.courses = courses
        self.totalUnits = self.getTotalUnits()
    def getTotalUnits(self) -> float:
        return sum([course.units for course in self.courses])
    def getWorkload(self) -> float:
        pass
    def getInstructorScore(self) -> float:
        pass
    def getAverageBreak(self) -> float:
        pass
    def getOverall(self) -> float:
        pass

class CourseGroup():
    def __init__(self,courseGroups: Dict[str, Set[Course]] = dict()):
        self.courseGroups = courseGroups

class NavBar():
    def __init__(self,app: any, width: int):
        self.app = app
        self.width = width
        self.coursesOffset = 140
        self.bg_color = rgb(245,246,248)
        self.builderButton =  Button(lambda: app.state.update({"selectedMenu":"builder"}) ,30,25,self.width-60,40,fill=rgb(45,45,45))
        self.schedulesButton =  Button(lambda: app.state.update({"selectedMenu":"schedules"}) ,30,70,self.width-60,40,fill=rgb(45,45,45))
        # self.addButton = Button(lambda: addCourseHelper(self.app),)
    def draw(self):
        drawRect(0,0,self.width,self.app.height,fill=self.bg_color)

        self.builderButton.draw()
        drawLabel("Course View",self.width//2,45,fill="White",size=self.app.primaryFontSize)
        self.app.state["activeButtons"] += [self.builderButton]

        self.schedulesButton.draw()
        drawLabel("Schedules View",self.width//2,90,fill="White",size=self.app.primaryFontSize)
        self.app.state["activeButtons"] += [self.schedulesButton]

        match self.app.state["selectedMenu"]:
            case "builder":
                self.drawNavCourses()
            case "schedules":
                pass


    def drawNavCourses(self):

        yOff = self.coursesOffset

        drawLabel("Add Courses",10,yOff,size=self.app.primaryFontSize,align="left")
        yOff+= self.app.primaryFontSize 

        #search bar
        courseInput = self.app.state["courseInput"] 
        courseFillColor = rgb(48,48,48) if courseInput == "" else "Black"
        courseInput = "Course ID" if courseInput == "" else courseInput
        drawRect(10,yOff,80, 24,fill="White",border="Black")
        drawLabel(courseInput, 15, yOff+12,fill=courseFillColor,size=self.app.primaryFontSize, align="left")
        
        groupInput = self.app.state["groupInput"] 
        groupFillColor = rgb(48,48,48) if groupInput == "" else "Black"
        groupInput = "Group Name" if groupInput == "" else groupInput
        drawRect(100 ,yOff, self.width//2 +10 , 24,fill="White",border="Black")
        drawLabel(groupInput, 105, yOff+12,fill=groupFillColor,size=self.app.primaryFontSize, align="left")
        # drawRect(self.width//2 +20 ,yOff,self.width//2 - 60, 24,fill=rgb(48,48,48))
        # drawLabel("Add",self.width//2 +20  +(self.width//2 - 60)//2,yOff+12,fill="White",size=self.app.primaryFontSize)
        if self.app.state["courseInputError"] != "":
            drawLabel(self.app.state["courseInputError"],self.width//2,yOff+38,size=self.app.primaryFontSize,fill="Red")
        yOff += 54  
        if "Required" in self.app.courseGroup:
            drawLabel("Required",10,yOff,size=self.app.primaryFontSize,align="left")
            yOff += 10
            for course in self.app.courseGroup["Required"]:
                yOff += self.drawCourse(course,yOff)
        for key in self.app.courseGroup:
            if key == "Required": continue
            yOff += 15
            drawLabel(key,10,yOff,size=self.app.primaryFontSize,align="left")
            yOff += 10
            for course in self.app.courseGroup[key]:
                yOff += self.drawCourse(course,yOff)
                
    def drawCourse(self, course: Course, yOff: int) -> int: #returns added yOff
        drawRect(10,yOff,self.width-20,35,fill=course.color)
        drawLabel(course.title[:40],15,yOff+10,size=self.app.secondaryFontSize,align="left",fill="White")
        drawLabel(course.courseID,15,yOff+25,size=self.app.secondaryFontSize,align="left",fill="White")
        return 40
    


class Button():
    def __init__(self,onclick: Callable,*args,**kwargs):
        self.onclick = onclick
        self.rectArgs = args
        self.rectKwargs = kwargs
        (self.left,self.top,self.width,self.height) = args
    def draw(self):
        drawRect(*self.rectArgs,**self.rectKwargs)
    def checkClick(self,mouseX:int, mouseY: int):
        if mouseX > self.left and mouseY > self.top and mouseX - self.left < self.width and mouseY - self.top < self.height:
            self.onclick()

class CourseView():
    def __init__(self,app: any,coursesOffset: int):
        self.app = app
        self.coursesOffset = coursesOffset
        self.times = ["8:00 AM","9:00 AM","10:00 AM","11:00 AM","12:00 PM","1:00 PM","2:00 PM","3:00 PM","4:00 PM","5:00 PM"]
        self.days = ["Monday","Tuesday","Wednesday","Thursday","Friday"]
        self.timeWidth = 80
    def draw(self):
        self.drawGrid()
        self.drawGridCourses()

    def drawGrid(self):
        xOff = self.coursesOffset + self.timeWidth
        viewWidth = self.app.width - xOff
        for i, time in enumerate(self.times):
            drawLabel(time,xOff-10,35+i*((self.app.height-40)//len(self.times)),align="right",size=self.app.secondaryFontSize)
            drawLine(xOff,35+i*((self.app.height-40)//len(self.times)),self.app.width,35+i*((self.app.height-40)//len(self.times)),fill=rgb(235,236,238),lineWidth=3)
            drawLine(xOff,35+i*((self.app.height-40)//len(self.times))+(self.app.height-40)//(len(self.times)*2),self.app.width,35+i*((self.app.height-40)//len(self.times))+(self.app.height-40)//(len(self.times)*2),fill=rgb(235,236,238),lineWidth=1)
        for i,day in enumerate(self.days):
            drawLabel(day,xOff+i*viewWidth//len(self.days)+viewWidth//(len(self.days)*2), 20, size=self.app.primaryFontSize)
            drawLine(xOff+i*viewWidth//len(self.days),0,xOff + i*viewWidth//len(self.days),self.app.height,fill=rgb(235,236,238),lineWidth=3)

    def drawGridCourses(self):
        pass

class ScheduleView():
    def __init__(self, app:any, xOffset: int):
        self.app = app
        self.xOffset = xOffset
    
    def draw(self):
        viewWidth = self.app.width - self.xOffset
        drawLabel("Schedules",self.xOffset + viewWidth//2,20,size=20)


def getRandomColor() -> tuple[int,int,int]:
    rgbDecimal = hsv_to_rgb(random.random(),0.7,0.65)
    return map(lambda x: int(x*255),rgbDecimal)


def distance(x1,y1,x2,y2):
    return ((x2-x1)**2+(y2-y1)**2)**0.5





if __name__ == "__main__":
    runApp(1280,720)







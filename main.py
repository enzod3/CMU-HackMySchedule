import pandas as pd
from cmu_graphics import *
from typing import Optional,Callable
import random
from colorsys import hsv_to_rgb
from copy import copy, deepcopy
import math

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
    app.schedules = []
    # app.courseGroups = {}
    app.courseGroup = dict()# Key: list[Course]
        # "test": CourseGroup({"Required":{Course('15112','Fundamentals of Programming and Computer Science',['Mike'],48)}})
    #-----------------------------------------

    # ---------- APP VIEW STATE --------------
    app.state = dict()
    app.state["selectedMenu"] = "schedules" 
    # app.state["selectedCourseGroup"] = None
    app.state["activeButtons"] = []
    app.state["courseInput"] = ""
    app.state["groupInput"] = ""
    app.state["courseInputError"] = ""
    #-----------------------------------------
    addCourse(app, "Required",'15122')
    addCourse(app, "Required",'21122')
    addCourse(app, "Required",'15151')
    # addCourse(app, "Required",'85211')
    # addCourse(app, "Required",'07180')


    addCourse(app, "Humanities",'80330')
    addCourse(app, "Humanities",'85211')
    addCourse(app, "Humanities",'85241')

    addCourse(app, "Business",'73102')

    generateSchedules(app)

    

class Period():
    def __init__(self, day: str, begin: str,end: str):
        self.day = day
        self.timeRange = (self.convertToMinutes(begin),self.convertToMinutes(end)) #(begin mins, end mins)
    def convertToMinutes(self,timeString):
        minutes = 0
        if "PM" in timeString:
            minutes += 60 * 12
        (hrs, mins) = timeString.split(':')
        minutes += int(hrs) *60 + int(mins[:2])
        return minutes
    def overlaps(self, other):
        return (other.timeRange[0] <= self.timeRange[1] and other.timeRange[0] >= self.timeRange[0] or
                other.timeRange[1] >= self.timeRange[0] and other.timeRange[1] <= self.timeRange[1])
    def __eq__(self, other):
        return isinstance(other,type(self)) and self.day == other.day and self.timeRange == other.timeRange
    def __hash__(self): #https://docs.python.org/3.5/reference/datamodel.html#object.__hash__
        return hash((self.day, self.timeRange))

class Day():
    def __init__(self,day:str,begin:str,end:str,bld_room:str,location:str,instructors: list[str]):
        self.weekday = day
        self.period = Period(day,begin,end)
        self.bld_room = bld_room
        self.location = location
        self.instructors = instructors
    def __eq__(self,other):
        return isinstance(other,type(self)) and ((self.weekday,self.period,self.bld_room,self.location,self.instructors)==(other.weekday,other.period,other.bld_room,other.location,other.instructors))
    def __hash__(self):#https://docs.python.org/3.5/reference/datamodel.html#object.__hash__
        return hash((self.weekday,self.period,self.bld_room,self.location,self.instructors))


class Section(): #sections/recitations
    def __init__(self,courseID: str, title:str,units:float, section:str,days:str,begin:str,end:str,bld_room:str,location:str, instructors: list[str]):
        self.courseID = courseID
        self.title = title
        self.units = units
        self.section = section
        self.days = set()
        self.addDays(days,begin,end,bld_room,location,instructors)
    def __repr__(self):
        dayString = "".join([day.weekday for day in self.days])
        return f"{self.courseID} {self.section} {dayString}"
    def addDays(self, days:str, begin:str,end:str,bld_room:str,location:str, instructors: list[str]):
        for day in days:    
            self.days.add(Day(day,begin,end,bld_room,location,instructors))
    def getInstructors(self):
        return {day.instructors for day in self.days if day.instructors != "NaN"}
    def conflicts(self,other):
        for day1 in self.days:
            for day2 in other.days:
                if day1.weekday == day2.weekday:
                    if day1.period.overlaps(day2.period):
                        return True
        return False
    def __eq__(self,other):
        return isinstance(other,type(self)) and ((self.courseID,self.title,self.units,self.section,self.days)==(other.courseID,other.title,other.units,other.section,other.days))
    def __hash__(self): #https://docs.python.org/3.5/reference/datamodel.html#object.__hash__
        return hash((self.courseID,self.title,self.units,self.section,frozenset(self.days))) #https://docs.python.org/3/library/stdtypes.html#set-types-set-frozenset



class Lecture(): #Every Class has a lecture taught by main professor --> some contain sections
    def __init__(self,lecture: Section, sections: Optional[list[Section]] = []):
        self.lecture = lecture
        self.sections = set(sections)




class Course():
    def __init__(self,courseID: str, title:str,units:float,lectures: list[Lecture]):
        self.courseID = courseID
        self.title = title
        self.units = units
        self.lectures = lectures
        self.color = rgb(*getRandomColor())
    def __repr__(self):
        return f"{self.courseID}"
    def __eq__(self,other):
        return isinstance(other,type(self)) and ((self.courseID,self.title,self.units,self.lectures,self.sections)==(other.courseID,other.title,other.units,other.lectures,other.sections))
    def __hash__(self): #https://docs.python.org/3.5/reference/datamodel.html#object.__hash__
        return hash((self.courseID,self.title,self.units,self.lectures,self.sections))
    def getSectionLectureCombos(self):
        combos = []
        for lecture in self.lectures:
            sections = [None] if len(lecture.sections) == 0 else lecture.sections
            combos += createCombos([[lecture.lecture],sections])
        return combos
        
# Rank, CourseCodes, Workload, Instructor Score, Average Break(Median or Mean),Overall
class Schedule():
    def __init__(self,app: any,sections: Optional[list[Section]] = []):
        self.app = app
        self.name = None
        self.sections = set(sections)
        self.workload = None
        self.instructorScore = None
        self.averageBreak = None
        self.overall = None
    
    def __repr__(self):
        return f"{[s for s in self.sections]}"
    def canAdd(self,section):
        for s in self.sections:
            if s.conflicts(section):
                return False
        return True
    def add(self,section):
        if isinstance(section,Section):
            self.sections.add(section)
    def remove(self,section):
        if isinstance(section,Section):
            self.sections.remove(section)
    def getScheduleCount(self):
        return len(self.courses)
    def getCourseIDs(self):
        return list({section.courseID for section in self.sections})
    def getTotalUnits(self) -> float:
        return sum([u for (s,u) in {(section.courseID,section.units) for section in self.sections}])
    def updateInfo(self):
        self.averageBreak = calculateMedianBreak(self.sections)
        (self.workload,self.instructorScore) = getCourseReview(self.app,self.sections)
    def getWorkload(self) -> float:
        return self.workload
    def getInstructorScore(self) -> float:
        return self.instructorScore
    def getAverageBreak(self) -> float:
        return self.averageBreak
    def getOverall(self) -> float:
        pass

class CourseGroup():
    def __init__(self,courseGroups: dict[str, set[Course]] = dict()):
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
                pass
            case "schedules":
                self.drawNavCourses()


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
        self.yOffset = 50
        self.rowHeight = 40
    
    def draw(self):
        viewWidth = self.app.width - self.xOffset
        # drawLabel("Schedules",self.xOffset + viewWidth//2 - 5,20,size=20)
        drawLabel("ID",self.xOffset +25,30,size=18,bold=True)
        drawLabel("Courses",self.xOffset +200,30,size=18,bold=True)
        drawLabel("Units",self.xOffset +380,30,size=18,bold=True )
        drawLabel("Workload",self.xOffset +480,30,size=18,bold=True )
        drawLabel("Instructor",self.xOffset +580,15,size=18,bold=True )
        drawLabel("Rating",self.xOffset +580,35,size=18,bold=True )
        drawLabel("Median",self.xOffset +680,15,size=18,bold=True )
        drawLabel("Break",self.xOffset +680,35,size=18,bold=True )
        self.drawSchedules()
    
    def drawSchedules(self):
        yOff = self.yOffset
        viewWidth = self.app.width - self.xOffset
        for i, schedule in enumerate(self.app.schedules):
            drawLine(self.xOffset,yOff,self.xOffset+viewWidth,yOff,lineWidth=.5,fill=rgb(175,175,175))
            drawLabel(i,self.xOffset + 25,yOff + self.rowHeight//2,size=14)
            drawLabel(", ".join(sorted(schedule.getCourseIDs())),self.xOffset + 200,yOff + self.rowHeight//2,size=14,bold=True)
            drawLabel(schedule.getTotalUnits(),self.xOffset +380,yOff + self.rowHeight//2,size=16,bold=True)
            drawLabel(schedule.getWorkload(),self.xOffset +480,yOff + self.rowHeight//2,size=16,bold=True)
            drawLabel(schedule.getInstructorScore(),self.xOffset + 580,yOff + self.rowHeight//2,size=16,bold=True)
            drawLabel(schedule.getAverageBreak(),self.xOffset + 680,yOff + self.rowHeight//2,size=16,bold=True)
            yOff += self.rowHeight
        if len(self.app.schedules) > 0: #border rect
            drawLine(self.xOffset,yOff,self.xOffset+viewWidth,yOff,lineWidth=.5,fill=rgb(175,175,175))
        
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
    courseInfo["lectures"] = []

    courseIndex += 1 #nextLine
    if pd.isnull(courseInfo["units"]):
        course = app.course_df.iloc[courseIndex]
        courseInfo["units"] = float(course["Units"])

    allLectures = []
    allSections = []
    while pd.isnull((courseSection := app.course_df.iloc[courseIndex])["Course"]) and courseIndex < len(app.course_df): #get all times for course
        newSection = Section(courseInfo["courseID"],courseInfo["title"],courseInfo["units"],courseSection["Lec/Sec"],courseSection["Days"],courseSection["Begin"],courseSection["End"],courseSection["Bldg/Room"],courseSection["Location"],courseSection["Instructor(s)"])	
        
        courseIndex += 1
        while pd.isnull((courseSection := app.course_df.iloc[courseIndex])["Lec/Sec"]) and courseIndex < len(app.course_df): #multiple days/times/locations per section
            if pd.isnull(app.course_df.iloc[courseIndex]["Days"]):
                break
            newSection.addDays(courseSection["Days"],courseSection["Begin"],courseSection["End"],courseSection["Bldg/Room"],courseSection["Location"],courseSection["Instructor(s)"])
            courseIndex += 1
        if "lec" in newSection.section.lower():
            allLectures += [newSection]
        else:
            allSections += [newSection]
    
    for i, lecture in enumerate(allLectures):
        chunkSize = len(allSections)//len(allLectures) #1 if len(allSections) == 0 else len(allSections)//len(allLectures)
        courseInfo["lectures"] += [Lecture(lecture,allSections[i*chunkSize:(i+1)*chunkSize])]
    if courseInfo["lectures"] == []:
        for section in allSections:
            courseInfo["lectures"] += [Lecture(section)]
    # if courseInfo["courseID"] == "85211":
    #     print(courseInfo["lectures"])

    # courseInfo["lectures"] = [None] if len(courseInfo["lectures"]) == 0 else courseInfo["lectures"]
    # courseInfo["sections"] = [None] if len(courseInfo["sections"]) == 0 else courseInfo["sections"]
    newCourse = Course(**courseInfo)
    if groupID in app.courseGroup:
        app.courseGroup[groupID] += [newCourse]
    else:
        app.courseGroup[groupID] = [newCourse]

    if sum([len(app.courseGroup[groupID]) for groupID in app.courseGroup]) >= 4:
        # generateSchedules(app)
        pass

def generateSchedules(app: any):
    courseGroupList = [app.courseGroup[id] for id in app.courseGroup if id != "Required"]
    requiredCourses = app.courseGroup["Required"] if "Required" in app.courseGroup else []
    allSchedules = []
    # print(requiredCourses[4].getSectionLectureCombos())

    
    for courseCombos in createCombos(courseGroupList):
        allSchedules += [generateSchedulesHelper(requiredCourses + courseCombos,Schedule(app))]
    for schedule in allSchedules:
        schedule.updateInfo()
    app.schedules = allSchedules

def createCombos(groups: list[list[any]]):
    if len(groups) == 0: 
        return [[]]
    else:
        rest = createCombos(groups[1:])
        return [[item] + r for r in rest for item in groups[0]]

def generateSchedulesHelper(courses: list[Course], schedule: Schedule):
    if courses == []:
        return schedule
    else:
        for i in range(len(courses)):
            for (sec,lec) in courses[i].getSectionLectureCombos():
                if (sec == None or schedule.canAdd(sec)) and (lec == None or schedule.canAdd(lec)):
                    oldCourses = copy(courses)
                    courses.pop(i)
                    schedule.add(sec)
                    schedule.add(lec)
                    solution = generateSchedulesHelper(courses,schedule)
                    if solution != None:
                        return solution
                    schedule.remove(sec)
                    schedule.remove(lec)
                    courses = oldCourses
        return None

def getRandomColor() -> tuple[int,int,int]:
    rgbDecimal = hsv_to_rgb(random.random(),0.7,0.65)
    return map(lambda x: int(x*255),rgbDecimal)


def calculateMedianBreak(sections: list[Section]):
    allBreaks = []
    for d in "MTWRF":
        periodList = []
        for section in sections:
            for day in section.days:
                if d == day.weekday:
                    periodList += [day.period]
        periodList = sorted(periodList,key=lambda period: period.timeRange[0]) #https://docs.python.org/3/howto/sorting.html#key-functions
        allBreaks += [periodList[i+1].timeRange[0] - periodList[i].timeRange[1] for i in range(len(periodList)-1)]
    print(allBreaks)
    mindex = len(allBreaks)//2
    return (allBreaks[mindex]+allBreaks[-mindex-1])/2


def getCourseReview(app: any, sections: set[Section]) ->  set[float,float]: 
    workloads = []
    ratings = []
    totalWorkload = None
    totalRating = None
    for section in sections:
        sectionWorkload = []
        sectionRating = []
        for instructors in section.getInstructors():
            if isinstance(instructors,str):
                for instructor in instructors.split(','):
                    rating = getProfessorCourseRating(app,section.courseID,instructor.lower())
                    if rating != None:
                        sectionWorkload += [rating[0]]
                        sectionRating += [rating[1]]
        if len(sectionWorkload) > 0:
            workloads += [sum(sectionWorkload)/len(sectionWorkload)]
        if len(sectionRating) > 0:
            ratings += [sum(sectionRating)/len(sectionRating)]
    if len(workloads) > 0:
        totalWorkload = pythonRound(sum(workloads),2)
    if len(ratings) > 0:
        totalRating = pythonRound(sum(ratings)/len(ratings),2)
    return(totalWorkload,totalRating)

def getProfessorCourseRating(app,courseID,professor):
    courseID = courseID[:2] + "-"+ courseID[2:] if "-" not in courseID else courseID
    courses = app.rating_df[app.rating_df["courseID"] == courseID]
    coursesByProf = courses[courses["instructor"].str.contains(professor,na=False, case=False)]
    
    if len(coursesByProf) == 0:
        return None
    else:
        return getRatings(coursesByProf)

def getRatings(rows):
    allRatings = [x for L in rows["rating"] for x in L]
    averageLoad = sum(rows["hrsPerWeek"])/len(rows["hrsPerWeek"])
    averageRating = sum(allRatings)/len(allRatings)
    return (averageLoad,averageRating)



if __name__ == "__main__":
    runApp(1280,720)







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
    app.navbar = NavBar(app,350)
    app.courseview = CourseView(app,350)
    app.scheduleview = ScheduleView(app,350)
    app.popupUnitButton = Button(lambda: app.state.update({"unitPopup":False}) ,app.width//2 - 20,app.height//2 + 20,40,20,fill=rgb(45,45,45))
    app.popupCourseSaveButton = Button(lambda: (app.state.update({"courseEditPopup":False}),
                                                app.state["editPopupCourse"].setWorkload(app.state["editPopupCourseWorkloadInput"]),
                                                app.state["editPopupCourse"].updateSectionWorkloads(app.state["editPopupCourseWorkloadInput"]),
                                                app.state.update({"editPopupCourseWorkloadInput":""}),
                                                generateSchedules(app)),
                                                app.width//2 - 40,app.height//2 + 66,100,24,fill=rgb(45,45,45))
    app.popupCourseCancelButton = Button(lambda: app.state.update({"courseEditPopup":False}),app.width//2 +65,app.height//2 + 66,50,24,fill=rgb(45,45,45))

    app.workloadWeight = 0.33
    app.ratingWeight = 0.33
    app.breakWeight = 0.33
    # should be loaded/stored
    #------------- APP STORAGE --------------
    app.schedules = []
    app.courseGroup = dict()# Key: list[Course]
    #-----------------------------------------

    # ---------- APP VIEW STATE --------------
    app.state = dict()
    app.state["selectedMenu"] = "schedules" 
    # app.state["selectedCourseGroup"] = None
    app.state["activeButtons"] = []
    app.state["courseInput"] = ""
    app.state["groupInput"] = ""
    app.state["courseInputError"] = ""
    app.state["selectedScheduleIndex"] = 0
    app.state["schedulePage"] = 0
    app.state["unitPopup"] = False
    app.state["unitPopupCourseID"] = ""
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
                addCourse(app, group, course_id.strip(),init=True)
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
        minutes += (int(hrs)%12) *60 + int(mins[:2])
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
        return isinstance(other,type(self)) and ((self.weekday,self.period,self.location,self.instructors)==(other.weekday,other.period,other.location,other.instructors))
    def __hash__(self):#https://docs.python.org/3.5/reference/datamodel.html#object.__hash__
        return hash((self.weekday,self.period,self.location,self.instructors))
    def __copy__(self): #https://stackoverflow.com/questions/1500718/how-to-override-the-copy-deepcopy-operations-for-a-python-object
        cls = self.__class__
        result = cls.__new__(cls)
        result.__dict__.update(self.__dict__)
        return result
    def __repr__(self):
        return f"{self.weekday}, {self.location}, {self.instructors}"

    def __deepcopy__(self, memo): #https://stackoverflow.com/questions/1500718/how-to-override-the-copy-deepcopy-operations-for-a-python-object
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result
        for k, v in self.__dict__.items():
            setattr(result, k, deepcopy(v, memo))
        return result

class Section(): #sections/recitations
    def __init__(self,courseID: str, title:str,units:float, color, section:str,days:str,begin:str,end:str,bld_room:str,location:str, instructors: list[str]):
        self.courseID = courseID
        self.title = title
        self.units = units
        self.color = color
        self.section = section
        self.overrideWorkload = None
        self.days = set()
        self.addDays(days,begin,end,bld_room,location,instructors)
    def __repr__(self):
        # dayString = "".join([day.weekday for day in self.days])
        return f"{self.courseID} {self.section}"
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
    def __copy__(self): #https://stackoverflow.com/questions/1500718/how-to-override-the-copy-deepcopy-operations-for-a-python-object
        cls = self.__class__
        result = cls.__new__(cls)
        result.__dict__.update(self.__dict__)
        return result
    def __deepcopy__(self, memo): #https://stackoverflow.com/questions/1500718/how-to-override-the-copy-deepcopy-operations-for-a-python-object
        cls = self.__class__
        result = cls.__new__(cls)
        result.__dict__.update(self.__dict__)
        return result
    

class Lecture(): #Every Class has a lecture taught by main professor --> some contain sections
    def __init__(self,lecture: Section, sections: Optional[list[Section]] = []):
        self.lecture = lecture
        self.sections = set(sections)
    def __copy__(self): #https://stackoverflow.com/questions/1500718/how-to-override-the-copy-deepcopy-operations-for-a-python-object
        cls = self.__class__
        result = cls.__new__(cls)
        result.__dict__.update(self.__dict__)
        return result
    def __deepcopy__(self, memo): #https://stackoverflow.com/questions/1500718/how-to-override-the-copy-deepcopy-operations-for-a-python-object
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result
        for k, v in self.__dict__.items():
            if k == 'app':
                setattr(result, k, self.app)
            else:
                setattr(result, k, deepcopy(v, memo))
        return result

class Course():
    def __init__(self,courseID: str, title:str,units:float,lectures: list[Lecture],color):
        self.courseID = courseID
        self.title = title
        self.units = units
        self.workload = None
        self.lectures = lectures
        self.color = color
    def __repr__(self):
        return f"{self.courseID}"
    def __eq__(self,other):
        print(((self.courseID,self.title,self.units,self.lectures),(other.courseID,other.title,other.units,other.lectures)))
        return isinstance(other,type(self)) and ((self.courseID,self.title,self.units,self.lectures)==(other.courseID,other.title,other.units,other.lectures))
    def __hash__(self): #https://docs.python.org/3.5/reference/datamodel.html#object.__hash__
        return hash((self.courseID,self.title,self.units,self.lectures,self.sections))
    def setWorkload(self,workload:float):
        self.workload = workload
    def updateSectionWorkloads(self,workload):
        for lecture in self.lectures:
            lecture.overrideWorkload = float(workload)
            for section in lecture.sections:
                section.overrideWorkload = float(workload)

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
        (self.workload,self.instructorScore) = getCourseReview(self.app,self.sections)
    def getWorkload(self) -> float:
        # if self.workload == None:
        self.updateInfo()
        return self.workload
    def getInstructorScore(self) -> float:
        if self.instructorScore == None:
            self.updateInfo()
        return self.instructorScore
    def getAverageBreak(self) -> float:
        if self.averageBreak == None:
            self.averageBreak = calculateMedianBreak(self.sections)
        return self.averageBreak
    def getOverall(self) -> float:
        #10 min median break is most desirable
        #rating is 0-5 and can make or break a course
        workloadDiff = max(min(self.getWorkload() - self.getTotalUnits(),-10),10)
        workloadPercent = (workloadDiff +10)/20
        ratingPercent = (self.getInstructorScore() - 1)/4
        breakPercent = min((120 - (self.getAverageBreak()-10)),0)/120 #10min best 120min+ worst

        return pythonRound((workloadPercent*self.app.workloadWeight + ratingPercent*self.app.ratingWeight
               + breakPercent*self.app.breakWeight)*10,1)
    def __copy__(self): #https://stackoverflow.com/questions/1500718/how-to-override-the-copy-deepcopy-operations-for-a-python-object
        cls = self.__class__
        result = cls.__new__(cls)
        result.__dict__.update(self.__dict__)
        return result
    def __deepcopy__(self, memo): #https://stackoverflow.com/questions/1500718/how-to-override-the-copy-deepcopy-operations-for-a-python-object
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result
        for k, v in self.__dict__.items():
            if k == 'app':
                setattr(result, k, self.app)
            else:
                setattr(result, k, deepcopy(v, memo))
        return result

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
        self.clearButton = Button(lambda: clearCourses(self.app),30,app.height - 80,self.width-60,30,fill=rgb(145,145,145))
        self.saveButton = Button(lambda: saveCourses(self.app),30,app.height - 40,self.width-60,30,fill=rgb(145,145,145))

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
                self.drawScheduleSection()
            case "schedules":
                self.drawNavCourses()

    def drawNavCourses(self):

        yOff = self.coursesOffset


        self.clearButton.draw()
        drawLabel("Clear Courses",self.width//2,self.app.height - 65,fill="White",size=self.app.primaryFontSize)
        self.app.state["activeButtons"] += [self.clearButton]

        self.saveButton.draw()
        drawLabel("Save Courses",self.width//2,self.app.height - 25,fill="White",size=self.app.primaryFontSize)
        self.app.state["activeButtons"] += [self.saveButton]


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
                newY = self.drawCourse(course,yOff)
                courseEditButton = Button(lambda x=course: (self.app.state.update({"courseEditPopup":True}),self.app.state.update({"editPopupCourse":x})),self.width-60,7.5+yOff,20,20,fill="White",opacity=50) #self.app.state.update({"editPopupCourseWorkloadInput":str(x.units)})
                self.app.state["activeButtons"] += [courseEditButton]
                courseEditButton.draw()
                drawImage("./assets/pencil-60-16.png",self.width-58,9.5+yOff)
                courseRemoveButton = Button(lambda x=course: (self.app.courseGroup["Required"].remove(x),generateSchedules(self.app)),self.width-35,7.5+yOff,20,20,fill="White",opacity=50)
                self.app.state["activeButtons"] += [courseRemoveButton]
                courseRemoveButton.draw()
                drawImage("./assets/x-19-16.png",self.width-33,9.5+yOff)

                yOff += newY
        for key in self.app.courseGroup:
            if key == "Required": continue
            yOff += 15
            drawLabel(key,10,yOff,size=self.app.primaryFontSize,align="left")
            yOff += 10
            for course in self.app.courseGroup[key]:
                newY = self.drawCourse(course,yOff)
                courseEditButton = Button(lambda x=course: (self.app.state.update({"courseEditPopup":True}),self.app.state.update({"editPopupCourseWorkloadInput":str(x.units)}),self.app.state.update({"editPopupCourse":x})),self.width-60,7.5+yOff,20,20,fill="White",opacity=50)
                self.app.state["activeButtons"] += [courseEditButton]
                courseEditButton.draw()
                drawImage("./assets/pencil-60-16.png",self.width-58,9.5+yOff)
                courseRemoveButton = Button(lambda x=course,key=key: (self.app.courseGroup[key].remove(x),generateSchedules(self.app)),self.width-35,7.5+yOff,20,20,fill="White",opacity=50)
                self.app.state["activeButtons"] += [courseRemoveButton]
                courseRemoveButton.draw()
                drawImage("./assets/x-19-16.png",self.width-33,9.5+yOff)
                
    def drawCourse(self, course: Course, yOff: int) -> int: #returns added yOff
        drawRect(10,yOff,self.width-20,35,fill=course.color)
        drawLabel(course.title[:40],15,yOff+10,size=self.app.secondaryFontSize,align="left",fill="White")
        drawLabel(course.courseID,15,yOff+25,size=self.app.secondaryFontSize,align="left",fill="White")
        return 40

    def drawScheduleSection(self):
        yOff = self.coursesOffset
        viewIndex = (self.app.state["selectedScheduleIndex"]+1)
        label = f"Viewing Schedule {viewIndex} of {len(self.app.schedules)}" if len(self.app.schedules) != 0 else "Go Add Some Courses!"
        drawLabel(label,self.width//2,yOff,size=16)
        yOff+= 18
    
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
        self.dayIndexs = {
            "M":0,
            "T":1,
            "W":2,
            "R":3,
            "F":4,
        }
        self.timeWidth = 80
        self.yOffset = 35
    def draw(self):
        
        self.drawGrid()
        self.drawSectionsOnSchedule()

    def drawGrid(self):
        xOff = self.coursesOffset + self.timeWidth
        viewWidth = self.app.width - xOff
        for i, time in enumerate(self.times):
            drawLabel(time,xOff-10,self.yOffset+i*((self.app.height-40)//len(self.times)),align="right",size=self.app.secondaryFontSize)
            drawLine(xOff,self.yOffset+i*((self.app.height-40)//len(self.times)),self.app.width,35+i*((self.app.height-40)//len(self.times)),fill=rgb(235,236,238),lineWidth=3)
            drawLine(xOff,self.yOffset+i*((self.app.height-40)//len(self.times))+(self.app.height-40)//(len(self.times)*2),self.app.width,35+i*((self.app.height-40)//len(self.times))+(self.app.height-40)//(len(self.times)*2),fill=rgb(235,236,238),lineWidth=1)
        for i,day in enumerate(self.days):
            drawLabel(day,xOff+i*viewWidth//len(self.days)+viewWidth//(len(self.days)*2), 20, size=self.app.primaryFontSize)
            drawLine(xOff+i*viewWidth//len(self.days),0,xOff + i*viewWidth//len(self.days),self.app.height,fill=rgb(235,236,238),lineWidth=3)

    def drawSectionsOnSchedule(self):
        if self.app.schedules:
            xOff = self.coursesOffset + self.timeWidth
            viewHeight = self.app.height - self.yOffset
            viewWidth = self.app.width - xOff
            viewPeriod = Period("",self.times[0],self.times[-1]) 
            minsBegin = viewPeriod.timeRange[0]
            minsEnd = viewPeriod.timeRange[1] + 60  #add 60 because an hour extra is showed on schedule
            minsLength = minsEnd - minsBegin
            # drawRect(xOff,self.yOffset,viewWidth//5,viewHeight-2)
            
            for section in self.app.schedules[self.app.state["selectedScheduleIndex"]].sections:
                for day in section.days:
                    beginP = (day.period.timeRange[0] - minsBegin)/minsLength 
                    endP = (day.period.timeRange[1] - minsBegin)/minsLength 
                    x = self.dayIndexs[day.weekday]*viewWidth//5 +3 + xOff
                    y = viewHeight * beginP + self.yOffset
                    width = viewWidth//5 - 6
                    height = viewHeight * (endP-beginP)
                    drawRect(x,y,width,height,fill=section.color)
                    drawLabel(section,x+width//2,y+10,fill="White",size=self.app.primaryFontSize)
                    drawLine(x,y+20,x+width,y+20,fill = "White",opacity=30,lineWidth=3)

class ScheduleView():
    def __init__(self, app:any, xOffset: int):
        self.app = app
        self.xOffset = xOffset
        self.yOffset = 50
        self.rowHeight = 40
    
    def draw(self):
        # drawLabel("Schedules",self.xOffset + viewWidth//2 - 5,20,size=20)
        drawLabel("ID",self.xOffset +25,30,size=18,bold=True)
        drawLabel("Courses",self.xOffset +200,30,size=18,bold=True)
        drawLabel("Units",self.xOffset +380,30,size=18,bold=True )
        drawLabel("Workload",self.xOffset +480,30,size=18,bold=True )
        drawLabel("Instructor",self.xOffset +580,15,size=18,bold=True )
        drawLabel("Rating",self.xOffset +580,35,size=18,bold=True )
        drawLabel("Median",self.xOffset +680,15,size=18,bold=True )
        drawLabel("Break",self.xOffset +680,35,size=18,bold=True )
        drawLabel("Overall",self.xOffset +780,30,size=18,bold=True )
        self.drawSchedules()
    
    def drawSchedules(self):
        rowCount = (self.app.height - self.yOffset)//self.rowHeight

        yOff = self.yOffset
        viewWidth = self.app.width - self.xOffset
        for i in range(self.app.state["schedulePage"]*rowCount,(self.app.state["schedulePage"]+1)*rowCount):
            schedule = self.app.schedules[i:i+1]
            if schedule == []:
                break
            schedule = schedule[0]
            drawLine(self.xOffset,yOff,self.xOffset+viewWidth,yOff,lineWidth=.5,fill=rgb(175,175,175))
            drawLabel(i,self.xOffset + 25,yOff + self.rowHeight//2,size=14)
            drawLabel(", ".join(sorted(schedule.getCourseIDs())),self.xOffset + 200,yOff + self.rowHeight//2,size=14,bold=True)
            drawLabel(schedule.getTotalUnits(),self.xOffset +380,yOff + self.rowHeight//2,size=16,bold=True)
            drawLabel(schedule.getWorkload(),self.xOffset +480,yOff + self.rowHeight//2,size=16,bold=True)
            drawLabel(schedule.getInstructorScore(),self.xOffset + 580,yOff + self.rowHeight//2,size=16,bold=True)
            drawLabel(schedule.getAverageBreak(),self.xOffset + 680,yOff + self.rowHeight//2,size=16,bold=True)
            drawLabel(schedule.getOverall(),self.xOffset + 780,yOff + self.rowHeight//2,size=16,bold=True)
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
    drawPopups(app)

def drawPopups(app:any):
    if app.state["unitPopup"]:
        app.state["activeButtons"] = [app.popupUnitButton]
        drawRect(0,0,app.width,app.height,opacity=80)
        drawRect(app.width//2 - 125, app.height//2 - 100, 250,200, fill="White", border="Black")
        app.popupUnitButton.draw()
    elif app.state["courseEditPopup"]:
        app.state["activeButtons"] = [app.popupCourseSaveButton,app.popupCourseCancelButton]
        drawRect(0,0,app.width,app.height,opacity=80)
        drawRect(app.width//2 - 125, app.height//2 - 100, 250,200, fill="White", border="Black")
        app.popupCourseSaveButton.draw()
        app.popupCourseCancelButton.draw()
        drawLabel("Save & Close",app.width//2 +10,app.height//2 + 78,fill="White",size=app.primaryFontSize)
        drawLabel("Cancel",app.width//2 +90,app.height//2 + 78,fill="White",size=app.primaryFontSize)

        drawLabel("Edit Course: " + app.state["editPopupCourse"].courseID,app.width//2,app.height//2-78,size=app.primaryFontSize)

        #unit input
        # courseInput = app.state["editPopupCourseWorkloadInput"]
        # courseFillColor = rgb(48,48,48) if courseInput == "" else "Black"
        # courseInput = "0" if courseInput == "" else courseInput
        unitInput = "0" if app.state["editPopupCourseWorkloadInput"] == "" else app.state["editPopupCourseWorkloadInput"]
        drawRect(5+app.width//2,app.height//2,40, 24,fill="White",border="Black")
        drawLabel(unitInput,34+app.width//2, app.height//2+12,fill="Black",size=app.primaryFontSize, align="right")
        drawLabel("Workload:",app.width//2-5, app.height//2+12,fill="Black",size=app.primaryFontSize, align="right")


def onMousePress(app, mouseX: int, mouseY:int):
    for button in app.state["activeButtons"]:
        button.checkClick(mouseX,mouseY)

def onKeyPress(app,key):
    app.state["courseInputError"] = ""
    if app.state["courseEditPopup"]:
        if ((key.isnumeric() or (key == "." and "." not in app.state["editPopupCourseWorkloadInput"])) and
            float(app.state["editPopupCourseWorkloadInput"] + key) <=30 and len( app.state["editPopupCourseWorkloadInput"]) <= 4):
            app.state["editPopupCourseWorkloadInput"] += key
        elif key == "backspace":
            app.state["editPopupCourseWorkloadInput"] = app.state["editPopupCourseWorkloadInput"][:-1]

    elif key.isnumeric() and app.state["selectedMenu"] =="schedules" and len(app.state["courseInput"]) < 5:
        app.state["courseInput"] += key
    elif key.isalpha() and len(key) == 1 and app.state["selectedMenu"] =="schedules" and len(app.state["groupInput"]) < 20:
        app.state["groupInput"] += key
    elif key =="backspace"  and app.state["selectedMenu"] =="schedules":
        app.state["courseInput"] = ""
        app.state["groupInput"] = ""
    elif key =="enter" and len(app.state["courseInput"]) == 5 and app.state["selectedMenu"] =="schedules":
        addCourseHelper(app)
    elif key == "left" and app.state["selectedScheduleIndex"] > 0 and app.state["selectedMenu"] =="builder":
        app.state["selectedScheduleIndex"] -= 1
    elif key == "right" and app.state["selectedScheduleIndex"] < (len(app.schedules) -1) and app.state["selectedMenu"] =="builder":
        app.state["selectedScheduleIndex"] += 1
    elif key == "left" and app.state["schedulePage"] > 0 and app.state["selectedMenu"] =="schedules":
        app.state["schedulePage"] -= 1
    elif key == "right" and app.state["schedulePage"] < (len(app.schedules)//((app.height - 50)/40)) and app.state["selectedMenu"] == "schedules":
        app.state["schedulePage"] += 1

def clearCourses(app):
    app.courseGroup = dict()
    app.schedules = []

def saveCourses(app):
    with open('./data/courses.txt', 'w') as file:
        for group, courseIDs in app.courseGroup.items():
            courseIDs = ', '.join(map(str, courseIDs))
            file.write(f"{group}: {courseIDs}\n")

def addCourseHelper(app):
    try:
        groupID = app.state["groupInput"] if app.state["groupInput"] != "" else "Required"
        addCourse(app,groupID,app.state["courseInput"])
    except Exception as e:
        app.state["courseInputError"] = e
    app.state["courseInput"] = ""
    app.state["groupInput"] = ""

def addCourse(app:any, groupID: str, courseID: int, init: Optional[bool]=False):
    if (df_filtered := app.course_df[app.course_df["Course"] == courseID]).empty:
        raise ValueError("Course does not exist")
    courseIndex = df_filtered.index[0]
    course = app.course_df.iloc[courseIndex]
    courseInfo = dict()
    courseInfo["courseID"] = courseID
    courseInfo["title"] = course["Title"]
    courseInfo["units"] = course["Units"]
    courseInfo["lectures"] = []
    courseInfo["color"] = rgb(*getRandomColor())

    courseIndex += 1 #nextLine
    if pd.isnull(courseInfo["units"]):
        course = app.course_df.iloc[courseIndex]
        courseInfo["units"] = course["Units"]

    if courseInfo["units"] == "VAR":
        return 
        # courseInfo["units"] = getCourseUnits(app,courseID)
        # print("got")
    else:
        courseInfo["units"] = float(courseInfo["units"])

    allLectures = []
    allSections = []
    while pd.isnull((courseSection := app.course_df.iloc[courseIndex])["Course"]) and courseIndex < len(app.course_df): #get all times for course
        newSection = Section(courseInfo["courseID"],courseInfo["title"],courseInfo["units"],courseInfo["color"],courseSection["Lec/Sec"],courseSection["Days"],courseSection["Begin"],courseSection["End"],courseSection["Bldg/Room"],courseSection["Location"],courseSection["Instructor(s)"])	
        
        courseIndex += 1
        while pd.isnull((courseSection := app.course_df.iloc[courseIndex])["Lec/Sec"]) and courseIndex < len(app.course_df): #multiple days/times/locations per section
            if pd.isnull(app.course_df.iloc[courseIndex]["Days"]):
                break
            newSection.addDays(courseSection["Days"],courseSection["Begin"],courseSection["End"],courseSection["Bldg/Room"],courseSection["Location"],courseSection["Instructor(s)"])
            courseIndex += 1
        if "lec" in newSection.section.lower():
            allLectures += [newSection]
        else:
            if (allSections == [] or allSections[-1].days != newSection.days or allSections[-1].courseID != newSection.courseID):
                allSections += [newSection]
    for i, lecture in enumerate(allLectures):
        chunkSize = len(allSections)//len(allLectures) #1 if len(allSections) == 0 else len(allSections)//len(allLectures)
        courseInfo["lectures"] += [Lecture(lecture,allSections[i*chunkSize:(i+1)*chunkSize])]
    if courseInfo["lectures"] == []:
        for section in allSections:
            courseInfo["lectures"] += [Lecture(section)]

    newCourse = Course(**courseInfo)
    if groupID in app.courseGroup:
        app.courseGroup[groupID] += [newCourse]
    else:
        app.courseGroup[groupID] = [newCourse]
    if sum([len(app.courseGroup[groupID]) for groupID in app.courseGroup]) >= 4 and not init:
        generateSchedules(app)

def getCourseUnits(app,courseID:str):
    app.state["unitPopup"] = True
    app.state["unitPopupCourseID"] = courseID
    while app.state["unitPopup"]:
        pass


def generateSchedules(app: any):
    courseGroupList = [app.courseGroup[id] for id in app.courseGroup if id != "Required"]
    requiredCourses = app.courseGroup["Required"] if "Required" in app.courseGroup else []
    allSchedules = []
    
    for courseCombos in createCombos(courseGroupList):
        allSchedules += generateSchedulesHelper(requiredCourses + courseCombos,Schedule(app))
    allSchedules = [schedule for schedule in allSchedules if schedule != None]

    app.state["selectedScheduleIndex"] = 0
    app.schedules = allSchedules

def createCombos(groups: list[list[any]]):
    if len(groups) == 0: 
        return [[]]
    else:
        rest = createCombos(groups[1:])
        return [[item] + r for r in rest for item in groups[0]]

def generateSchedulesHelper(courses: list[Course], schedule: Schedule):
    if courses == []:
        return [deepcopy(schedule)]  
    else:
        solutions = [] 
        for i in range(len(courses)):
            for (sec,lec) in courses[i].getSectionLectureCombos():
                if (sec == None or schedule.canAdd(sec)) and (lec == None or schedule.canAdd(lec)):
                    oldCourses = copy(courses)  # Deep copy of courses
                    courses.pop(i)
                    schedule.add(sec)
                    schedule.add(lec)
                    solutions += generateSchedulesHelper(courses,schedule) 
                    schedule.remove(sec)
                    schedule.remove(lec)    
                    courses = oldCourses
        return solutions 

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
    mindex = len(allBreaks)//2
    return (allBreaks[mindex]+allBreaks[-mindex-1])/2

def getCourseReview(app: any, sections: set[Section]) ->  set[float,float]: 
    workloads = dict()
    ratings = dict()
    totalWorkload = 0
    totalRating = 4 #default average rating
    for section in sections:
        sectionWorkload = []
        sectionRating = []
        if section.overrideWorkload != None:
            sectionWorkload = [section.overrideWorkload]
        else:
            for instructors in section.getInstructors():
                if isinstance(instructors,str):
                    for instructor in instructors.split(','):
                        rating = getProfessorCourseRating(app,section.courseID,instructor.lower())
                        if rating != None:
                            sectionWorkload += [rating[0]]
                            sectionRating += [rating[1]]
        existingLoad = workloads.get(section.courseID,[])
        if len(sectionWorkload) > 0:
            workloads.update({section.courseID:[sum(sectionWorkload)/len(sectionWorkload)]+existingLoad})
        else:
            workloads.update({section.courseID:[section.units]+existingLoad})
        existingRating = ratings.get(section.courseID,[])
        if len(sectionRating) > 0:
            ratings.update({section.courseID:[sum(sectionRating)/len(sectionRating)]+existingRating})
    if len(workloads) > 0:
        totalWorkload = pythonRound(sum([sum(v)/len(v) for v in workloads.values()]),2)
    if len(ratings) > 0:
        totalRating = pythonRound(sum([sum(v)/len(v) if len(v) > 0 else 4 for v in ratings.values()])/len(ratings),2)
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









#getNextSection / eliminate the section u just added in solution and check for more solutions with that section because
#you already got them all
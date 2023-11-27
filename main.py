import pandas as pd
from cmu_graphics import *
from cmu_graphics import Rect
from typing import Set,List,Dict,Callable
import random
from colorsys import hsv_to_rgb



def onAppStart(app: any):
    app.course_df = pd.read_csv("./data/spring_24.dat", delimiter='\t')
    app.rating_df = pd.read_json("./data/TeacherRatings.json")
    app.primaryFontSize = 14
    app.secondaryFontSize = 12
    app.navbar = NavBar(app,300)
    app.courseview = CourseView(app,300)
    app.scheduleview = ScheduleView(app,300)
    # should be loaded/stored
    #------------- APP STORAGE --------------
    app.schedules = dict()
    app.courseGroups = {
        "test": CourseGroup({"Required":{Course('15112','Fundamentals of Programming and Computer Science',['Mike'],48)}})
    }
    #-----------------------------------------

    # ---------- APP VIEW STATE --------------
    app.state = dict()
    app.state["selectedMenu"] = "builder" 
    app.state["selectedCourseGroup"] = "test"
    app.state["activeButtons"] = []
    #-----------------------------------------

    

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


class Course():
    def __init__(self,code: str, title:str,units:int,instructors: List[str]):
        self.code = code
        self.title = title
        self.instructors = instructors
        self.units = units
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
        self.coursesOffset = 200
        self.bg_color = rgb(245,246,248)
        self.builderButton =  Button(lambda: app.state.update({"selectedMenu":"builder"}) ,30,40,self.width-60,40,fill=rgb(45,45,45))
        self.schedulesButton =  Button(lambda: app.state.update({"selectedMenu":"schedules"}) ,30,90,self.width-60,40,fill=rgb(45,45,45))
        self.courseInput = ""
        
    def draw(self):
        drawRect(0,0,self.width,self.app.height,fill=self.bg_color)

        self.builderButton.draw()
        drawLabel("Course View",self.width//2,60,fill="White",size=self.app.primaryFontSize)
        self.app.state["activeButtons"] += [self.builderButton]

        self.schedulesButton.draw()
        drawLabel("Schedules View",self.width//2,110,fill="White",size=self.app.primaryFontSize)
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
        drawRect(10,yOff,self.width//2, 24,fill="White",border="Black")
        drawLabel("Course ID", 20, yOff+12,fill=rgb(150,150,150),size=self.app.secondaryFontSize, align="left")
        drawRect(self.width//2 +20 ,yOff,self.width//2 - 60, 24,fill=rgb(48,48,48))
        drawLabel("Add",self.width//2 +20  +(self.width//2 - 60)//2,yOff+12,fill="White",size=self.app.primaryFontSize)
        yOff += 54


        courseGroups = self.app.courseGroups[self.app.state["selectedCourseGroup"]].courseGroups
        if "Required" in courseGroups:
            drawLabel("Required",10,yOff,size=self.app.primaryFontSize,align="left")
            yOff += self.app.primaryFontSize
            for course in courseGroups["Required"]:
                yOff += self.drawCourse(course,yOff)
        for key in courseGroups:
            if key == "Required": continue
            drawLabel(key,10,yOff,size=self.app.primaryFontSize,align="left")
            yOff += self.app.primaryFontSize + 5
            for course in courseGroups[key]:
                yOff += self.drawCourse(course,yOff)
                
    def drawCourse(self, course: Course, yOff: int) -> int: #returns added yOff
        drawRect(10,yOff,self.width-20,60,fill=course.color)
        drawLabel(course.title[:40],15,yOff+15,size=self.app.secondaryFontSize,align="left",fill="White")
        drawLabel(course.code,15,yOff+30,size=self.app.secondaryFontSize,align="left",fill="White")
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
    rgbDecimal = hsv_to_rgb(random.random(),0.7,0.9)
    return map(lambda x: int(x*255),rgbDecimal)


def distance(x1,y1,x2,y2):
    return ((x2-x1)**2+(y2-y1)**2)**0.5




runApp(1280,720)







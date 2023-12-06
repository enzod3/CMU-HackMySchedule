from cmu_graphics import drawLabel,drawRect,drawImage,rgb,drawLine
from courseFunctions import clearCourses,saveCourses,generateSchedules
from typing import Callable
from courseClasses import Course, Period

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
                drawImage("../assets/pencil-60-16.png",self.width-58,9.5+yOff)
                courseRemoveButton = Button(lambda x=course: (self.app.courseGroup["Required"].remove(x),generateSchedules(self.app)),self.width-35,7.5+yOff,20,20,fill="White",opacity=50)
                self.app.state["activeButtons"] += [courseRemoveButton]
                courseRemoveButton.draw()
                drawImage("../assets/x-19-16.png",self.width-33,9.5+yOff)

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
                drawImage("../assets/pencil-60-16.png",self.width-58,9.5+yOff)
                courseRemoveButton = Button(lambda x=course,key=key: (self.app.courseGroup[key].remove(x),generateSchedules(self.app)),self.width-35,7.5+yOff,20,20,fill="White",opacity=50)
                self.app.state["activeButtons"] += [courseRemoveButton]
                courseRemoveButton.draw()
                drawImage("../assets/x-19-16.png",self.width-33,9.5+yOff)
                
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
        if self.rectKwargs.get("align") == "center":
            left = self.left - self.width//2
            top = self.top - self.height//2
        else:
            left,top = self.left,self.top
        if mouseX > left and mouseY > top and mouseX - left < self.width and mouseY - top < self.height:
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
        self.headerTextSize = 16
        self.sortWorkloadButton = Button(lambda:(app.schedules.sort(key=lambda schedule: schedule.getWorkload()) or app.state.update({"schedulePage":0})),self.xOffset +520,30,80,30,opacity=20,align="center")
        self.sortRatingButton = Button(lambda:(app.schedules.sort(key=lambda schedule: schedule.getInstructorRating(),reverse=True) or app.state.update({"schedulePage":0})),self.xOffset +620,25,80,40,opacity=20,align="center")
        self.sortBreakButton = Button(lambda:(app.schedules.sort(key=lambda schedule: schedule.getAverageBreak()) or app.state.update({"schedulePage":0})),self.xOffset +720,25,80,40,opacity=20,align="center")
        self.sortOverallButton = Button(lambda:(app.schedules.sort(key=lambda schedule: schedule.getOverall(),reverse=True) or app.state.update({"schedulePage":0})),self.xOffset +820,30,80,30,opacity=20,align="center")
            
    def draw(self):
        # drawLabel("Schedules",self.xOffset + viewWidth//2 - 5,20,size=20)
        drawLabel("ID",self.xOffset +25,30,size=self.headerTextSize,bold=True)
        drawLabel("Courses",self.xOffset +200,30,size=self.headerTextSize,bold=True)
        drawLabel("Units",self.xOffset +420,30,size=self.headerTextSize,bold=True )
        drawLabel("Workload",self.xOffset +520,30,size=self.headerTextSize,bold=True)
        drawLabel("Prof",self.xOffset +620,15,size=self.headerTextSize,bold=True)
        drawLabel("Rating",self.xOffset +620,35,size=self.headerTextSize,bold=True)
        drawLabel("Median",self.xOffset +720,15,size=self.headerTextSize,bold=True)
        drawLabel("Break",self.xOffset +720,35,size=self.headerTextSize,bold=True)
        drawLabel("Overall",self.xOffset +820,30,size=self.headerTextSize,bold=True)
        self.sortWorkloadButton.draw()
        self.sortRatingButton.draw()
        self.sortBreakButton.draw()
        self.sortOverallButton.draw()
        self.app.state["activeButtons"] += [self.sortWorkloadButton,self.sortRatingButton,self.sortBreakButton,self.sortOverallButton]
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
            drawLabel(str(i),self.xOffset + 25,yOff + self.rowHeight//2,size=14)
            drawLabel(", ".join(sorted(schedule.getCourseIDs())),self.xOffset + 200,yOff + self.rowHeight//2,size=14,bold=True)
            drawLabel(str(schedule.getTotalUnits()),self.xOffset +420,yOff + self.rowHeight//2,size=16,bold=True)
            drawLabel(str(schedule.getWorkload()),self.xOffset +520,yOff + self.rowHeight//2,size=16,bold=True)
            drawLabel(str(schedule.getInstructorRating()),self.xOffset + 620,yOff + self.rowHeight//2,size=16,bold=True)
            drawLabel(str(schedule.getAverageBreak()),self.xOffset + 720,yOff + self.rowHeight//2,size=16,bold=True)
            drawLabel(str(schedule.getOverall()),self.xOffset + 820,yOff + self.rowHeight//2,size=16,bold=True)
            yOff += self.rowHeight
        if len(self.app.schedules) > 0: #border rect
            drawLine(self.xOffset,yOff,self.xOffset+viewWidth,yOff,lineWidth=.5,fill=rgb(175,175,175))
    
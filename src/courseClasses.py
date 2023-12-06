#All Classes used for Schedules And Courses
from typing import Optional
from courseRatings import getSectionReview,calculateMedianBreak
from copy import deepcopy
from utils import createCombos

#Represents a specific day + begin and end time
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

#Represents a specific class day for a given section
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

#Section is a collection of Days that make up a Lecture or Section
class Section(): 
    def __init__(self,app:any,courseID: str, title:str,units:float, color, section:str,days:str,begin:str,end:str,bld_room:str,location:str, instructors: list[str]):
        self.app = app
        self.courseID = courseID
        self.title = title
        self.units = units
        self.color = color
        self.section = section
        self.overrideWorkload = None
        self.workload = None
        self.instructorRating = None
        self.days = set()
        self.addDays(days,begin,end,bld_room,location,instructors)
    def __repr__(self):
        return f"{self.courseID} {self.section}"
    def addDays(self, days:str, begin:str,end:str,bld_room:str,location:str, instructors: list[str]):
        for day in days:    
            self.days.add(Day(day,begin,end,bld_room,location,instructors))
    def getInstructors(self):
        return {day.instructors for day in self.days if day.instructors != "NaN"}
    def updateSectionInfo(self):
        (workload,rating) = getSectionReview(self.app,self)
        self.workload = self.units if workload == None else workload
        self.instructorRating = rating
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
    
#Every Class has a lecture taught by main professor --> some contain sections
#Lecture contains a single lecture and multiple sections that are optional for that lecture
class Lecture(): 
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

#Course Class, 1 course per CourseID that is added, contains lecturs
class Course():
    def __init__(self,courseID: str, title:str,units:float,lectures: list[Lecture],color):
        self.courseID = courseID
        self.title = title
        self.units = units
        self.lectures = lectures
        self.color = color
    def __repr__(self):
        return f"{self.courseID}"
    def __eq__(self,other):
        return isinstance(other,type(self)) and ((self.courseID,self.title,self.units,self.lectures)==(other.courseID,other.title,other.units,other.lectures))
    def __hash__(self): #https://docs.python.org/3.5/reference/datamodel.html#object.__hash__
        return hash((self.courseID,self.title,self.units,self.lectures,self.sections))
    def overrideWorkloads(self,workload:str):
        workload = 0 if workload == "" else float(workload)
        for lecture in self.lectures:
            lecture.lecture.overrideWorkload = workload
            for section in lecture.sections:
                section.overrideWorkload = workload


    def getSectionLectureCombos(self):
        combos = []
        for lecture in self.lectures:
            sections = [None] if len(lecture.sections) == 0 else lecture.sections
            combos += createCombos([[lecture.lecture],sections])
        return combos
        
#Schedule is a collection of sections that make up the schedule you view
#Has multiple methods to retrieve statistics about the schedule
class Schedule():
    def __init__(self,app: any,sections: Optional[list[Section]] = []):
        self.app = app
        self.name = None
        self.sections = set(sections)
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
    def getWorkload(self) -> float:
        courseDict = dict()
        for section in self.sections:
            load = section.overrideWorkload if section.overrideWorkload != None else section.workload
            courseDict.update({section.courseID:courseDict.get(section.courseID,[])+[load]})
        return round(sum([sum(loads)/len(loads) for loads in courseDict.values()]),2)
    def getInstructorRating(self) -> float:
        allRatings = [section.instructorRating for section in self.sections]
        return round(sum(allRatings)/len(allRatings),2)
    def getAverageBreak(self) -> float:
        if self.averageBreak == None:
            self.averageBreak = calculateMedianBreak(self.sections)
        return self.averageBreak
    def getOverall(self) -> float:
        #10 min median break is most desirable
        #rating is 0-5 and can make or break a course
        workloadDiff = max(min(self.getTotalUnits() -self.getWorkload(),8),-8)
        workloadPercent = (workloadDiff +8)/16
        ratingPercent = (self.getInstructorRating() - 1)/4
        breakPercent = max((120 - (self.getAverageBreak()-10)),0)/120 #10min best 120min+ worst
        totalPercent = (workloadPercent*self.app.workloadWeight + ratingPercent*self.app.ratingWeight
               + breakPercent*self.app.breakWeight)
        return ((totalPercent*100 +.5)//1 )/10 #1 decimal point round and make out of 10
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
    def __hash__(self):
        return hash(frozenset(self.sections))

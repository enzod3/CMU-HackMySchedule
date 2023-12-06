#all functions that modify schedules and courses 
from copy import copy,deepcopy
from courseClasses import Schedule, Course, Lecture,Section
import pandas as pd
from utils import createCombos,getRandomColor
from typing import Optional
from cmu_graphics import rgb

#Creates Combinations of Courses and calls helper function to generate schedules
def generateSchedules(app: any):
    for k in list(app.courseGroup.keys()): #clear emptyGroups
        if len(app.courseGroup[k]) == 0:
            del app.courseGroup[k]
    courseGroupList = [app.courseGroup[id] for id in app.courseGroup if id != "Required"]
    requiredCourses = app.courseGroup["Required"] if "Required" in app.courseGroup else []
    allSchedules = []

    for courseCombos in createCombos(courseGroupList):
        validSchedules = []
        generateSchedulesHelper(requiredCourses + courseCombos,Schedule(app),validSchedules,set())
        allSchedules += validSchedules
    allSchedules = [schedule for schedule in allSchedules if schedule != None]

    app.state["selectedScheduleIndex"] = 0
    app.state["schedulePage"] = 0
    allCourses = [x for courses in app.courseGroup.values() for x in courses]
    app.state["sectionsPage"] = min(app.state["sectionsPage"],(len(allCourses)-1)//2)
    allSchedules = sorted(allSchedules,key=lambda schedule: schedule.getOverall(),reverse=True)
    app.schedules = allSchedules

#Recursive schedule generator that finds all unique schedules for a given list of courses
def generateSchedulesHelper(courses: list[Course], schedule: Schedule, validSchedules: list[Schedule], seen:set):
    if courses == [] and schedule.getTotalUnits() >= schedule.app.minUnits:
        validSchedules.append(deepcopy(schedule))
    else:
        solutions = [] 
        for i in range(len(courses)):
            for (sec,lec) in courses[i].getSectionLectureCombos():
                if (sec == None or schedule.canAdd(sec)) and (lec == None or schedule.canAdd(lec)):
                    schedule.add(sec)
                    schedule.add(lec)
                    schedule_hash = hash(schedule)
                    if schedule_hash not in seen:
                        seen.add(schedule_hash)
                        newCourses = courses[:i] + courses[i+1:]
                        generateSchedulesHelper(newCourses, schedule, validSchedules, seen)
                    schedule.remove(sec)
                    schedule.remove(lec)    
        return solutions 

#Clear all courses
def clearCourses(app):
    app.courseGroup = dict()
    app.schedules = []

#Save Courses to Save file
def saveCourses(app):
    with open('../data/courses.txt', 'w') as file:
        for group, courseIDs in app.courseGroup.items():
            courseIDs = ', '.join(map(str, courseIDs))
            file.write(f"{group}: {courseIDs}\n")

#addCourse() helper that handles errors and resets inputs
def addCourseHelper(app):
    try:
        groupID = app.state["groupInput"] if app.state["groupInput"] != "" else "Required"
        addCourse(app,groupID,app.state["courseInput"])
    except Exception as e:
        app.state["courseInputError"] = e
    app.state["courseInput"] = ""
    app.state["groupInput"] = ""

#Finds a course in the springcourses data file and creates the proper Course Object
def addCourse(app:any, groupID: str, courseID: int, init: Optional[bool]=False,units: Optional[int]=None):
    if courseID in {c.courseID for courses in app.courseGroup.values() for c in courses}:
        raise ValueError("Course already added")
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
    
    if units != None:
        try:
            courseInfo["units"] = float(units)
        except:
            courseInfo["units"] = 0
    elif courseInfo["units"] == "VAR":
        app.state["unitPopup"] = True
        app.state["unitPopupCourseID"] = courseID
        app.state["unitPopupGroupID"] = groupID
        return
    else:
        courseInfo["units"] = float(courseInfo["units"])

    allLectures = []
    allSections = []
    while pd.isnull((courseSection := app.course_df.iloc[courseIndex])["Course"]) and courseIndex < len(app.course_df): #get all times for course
        newSection = Section(app,courseInfo["courseID"],courseInfo["title"],courseInfo["units"],courseInfo["color"],courseSection["Lec/Sec"],courseSection["Days"],courseSection["Begin"],courseSection["End"],courseSection["Bldg/Room"],courseSection["Location"],courseSection["Instructor(s)"])	
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
        chunkSize = len(allSections)//len(allLectures)
        courseInfo["lectures"] += [Lecture(lecture,allSections[i*chunkSize:(i+1)*chunkSize])]
    if courseInfo["lectures"] == []:
        for section in allSections:
            courseInfo["lectures"] += [Lecture(section)]

    #getAllRatings and workloads
    for section in allLectures + allSections:
        section.updateSectionInfo()

    newCourse = Course(**courseInfo)
    if groupID in app.courseGroup:
        app.courseGroup[groupID] += [newCourse]
    else:
        app.courseGroup[groupID] = [newCourse]
    if not init:
        generateSchedules(app)

from copy import deepcopy
from courseClasses import Schedule, Course, Lecture,Section
import pandas as pd
from utils import createCombos,getRandomColor
from typing import Optional
from cmu_graphics import rgb

def generateSchedules(app: any):
    courseGroupList = [app.courseGroup[id] for id in app.courseGroup if id != "Required"]
    requiredCourses = app.courseGroup["Required"] if "Required" in app.courseGroup else []
    allSchedules = []
    
    for courseCombos in createCombos(courseGroupList):
        validSchedules = []
        generateSchedulesHelper(requiredCourses + courseCombos,Schedule(app),validSchedules,set())
        allSchedules += validSchedules
    allSchedules = [schedule for schedule in allSchedules if schedule != None]

    app.state["selectedScheduleIndex"] = 0
    allSchedules = sorted(allSchedules,key=lambda schedule: schedule.getOverall(),reverse=True)
    app.schedules = allSchedules


def generateSchedulesHelper(courses: list[Course], schedule: Schedule, validSchedules: list[Schedule], seen:set):
    if courses == [] and schedule.getTotalUnits() >= schedule.app.minUnits:
        print(schedule.getTotalUnits())
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

    if courseInfo["units"] == "VAR":
        return 
        # courseInfo["units"] = getCourseUnits(app,courseID)
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
        chunkSize = len(allSections)//len(allLectures) #1 if len(allSections) == 0 else len(allSections)//len(allLectures)
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

def getCourseUnits(app,courseID:str):
    app.state["unitPopup"] = True
    app.state["unitPopupCourseID"] = courseID
    while app.state["unitPopup"]:
        pass


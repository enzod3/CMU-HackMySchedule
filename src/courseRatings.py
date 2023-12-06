def getSectionReview(app: any, section: any) ->  set[float,float]: 
    workloads = []
    ratings = []
    totalWorkload = None
    totalRating = 4 #default average rating
    for instructors in section.getInstructors():
        if isinstance(instructors,str):
            for instructor in instructors.split(','):
                rating = getProfessorCourseRating(app,section.courseID,instructor.lower())
                if rating != None:
                    workloads += [rating[0]]
                    ratings += [rating[1]]
    if len(workloads) > 0:
        totalWorkload = round(sum([load for load in workloads])/len(workloads),2)
    if len(ratings) > 0:
        totalRating = round(sum([rate for rate in ratings])/len(ratings),2)
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

def calculateMedianBreak(sections: list[any]):
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
    allBreaks = sorted(allBreaks)
    return (allBreaks[mindex]+allBreaks[-mindex-1])/2


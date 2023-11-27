import pandas as pd
from cmu_graphics import *



def onAppStart(app):
    app.course_df = pd.read_csv("./data/spring_24.htm", delimiter='\t')
    app.rating_df = pd.read_json("./data/TeacherRatings.json")
    getProfessorCourseRating(app,"15112","taylor")
    
    
def redrawAll(app):
    pass



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
    averageRating = sum(allRatings)/len(allRatings)
    averageLoad = sum(rows["hrsPerWeek"])/len(rows["hrsPerWeek"])
    print(rows["instructor"].iat[0],averageRating,averageLoad)

runApp()




    # app._app.updateScreen(True)
    # app._screen = pygame.display.set_mode((app.width, app.height), pygame.NOFRAME)



# def main():
#     # course_df = pd.read_csv("./data/spring_24.dat", delimiter='\t')
#     # rating_df = pd.read_json("./data/TeacherRatings.json")

#     # rows = rating_df[rating_df["courseID"] == "15-112"]
#     # print(set(rows[rows["year"] >= 2023]["instructor"]))

#     # course_history = rating_df[rating_df["instructor"] == "TAYLOR, MICHAEL"]
#     # print(course_history["rating"])


# if __name__ == "__main__":
#     main()

from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from flask import Flask, redirect, request, url_for, render_template, jsonify, Response, session, flash
import json, os, sys 

# Connect to our local MongoDB
mongodb_hostname = os.environ.get("MONGO_HOSTNAME","localhost")
client = MongoClient('mongodb://'+mongodb_hostname+':27017/')

# Choose InfoSys database
db = client['MovieFlix']
users = db['Users']
movies = db['Movies']

# Initiate Flask App
app = Flask(__name__)
app.secret_key = "MySecretKey"

@app.route("/MovieFlix", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        user = users.find_one({"email":email, "password":password})
        if user == None:
            flash("Wrong email or password!","info")
            return render_template("Login_And_Register/login.html")
        jsUser = {"email":user["email"], "password":user["password"], "name":user["name"]}
        if user["isAdmin"] == True:
            session["admin"]=jsUser
            session["user"]=jsUser
            flash("Admin logged in successfully.","info")
            return redirect(url_for("admin"))
        elif user["isAdmin"] == False:
            session["user"]=jsUser
            flash("User logged in successfully.","info")
            return redirect(url_for("user"))
    else:
        if "user" in session:
            flash("You are already logged in!","info")
            return redirect(url_for("user"))
        elif "admin" in session:
            flash("You are already logged in!","info")
            return redirect(url_for("admin"))
        if users.find({"isAdmin":True}).count() == 0:
            users.insert_one({"name":"Admin", "password":"admin", "email":"admin@admin.com", "isAdmin":True})
        return render_template("Login_And_Register/login.html")
########################################################################################################################################################### logout
@app.route("/MovieFlix/logout")
def logout():
    if "user" in session:
        session.pop("user", None)
        flash("You have been logged out!","info")
    if "admin" in session:
        session.pop("admin", None)
    return redirect(url_for("login"))
########################################################################################################################################################### register
@app.route("/MovieFlix/Register", methods=["POST", "GET"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        if email == "" or password == "" or name == "":
            flash("All fields must be filled!","info")
            return render_template("Login_And_Register/register.html")
        if users.find({"email":email}).count() == 0:
            users.insert_one({"email":email, "password":password, "name":name, "isAdmin": False})
            flash("The account has been registered.","info")
            return redirect(url_for("login"))
        else:
            flash("An account with this email address already exists!","info")
            return render_template("Login_And_Register/register.html")
    else:
        if "user" in session:
            flash("You are already logged in!","info")
            return redirect(url_for("user"))
        elif "admin" in session:
            flash("You are already logged in!","info")
            return redirect(url_for("admin"))
        return render_template("Login_And_Register/register.html")
########################################################################################################################################################### admin
@app.route("/MovieFlix/admin")
def admin():
    if "admin" in session:
        return render_template("index/index.html", name=session["admin"]["name"], admin=True)
    elif "user" in session:
        return redirect(url_for("user"))
    else:
        flash("You need to log in!","info")
        return redirect(url_for("login"))
########################################################################################################################################################### user
@app.route("/MovieFlix/user")
def user():
    if "admin" in session:
        return redirect(url_for("admin"))
    if "user" in session:
        return render_template("index/index.html", name=session["user"]["name"])
    else:
        flash("You need to log in!","info")
        return redirect(url_for("login"))
########################################################################################################################################################### new Movie
@app.route("/MovieFlix/NewMovie", methods=["POST", "GET"])
def newMovie():
    if request.method == "POST":
        title = request.form["title"]
        year = request.form["year"]
        descr = request.form["descr"]
        if title == "":
            flash("You can't add a movie without a title!","info")
            return render_template("newMovie/newMovie.html", admin=True)
        movie = {"title":title, "rating": -1}
        if year != "" and year.isdigit() == True:
            movie["year"]=int(year)
        elif year.isdigit() == False and year != "":
            flash("Your year was not a possitive integer!","info")
            return render_template("newMovie/newMovie.html", admin=True)
        if descr != "":
            movie["descr"]=descr
        session["movie"]=movie
        return redirect(url_for("actors"))
    else:
        if "admin" in session:
            return render_template("newMovie/newMovie.html", admin=True)
        else:
            return redirect(url_for("user"))
########################################################################################################################################################### new Movie Actors
@app.route("/MovieFlix/NewMovie/Actors", methods=["POST", "GET"])
def actors():
    if request.method == "POST":
        actor = request.form["actor"]
        if actor == "":
            flash("Actor's field must be filled!","info")
            return render_template("newMovie/actors.html", admin=True)
        if "actors" in session:
            session["actors"].append(actor)
        else:
            session["actors"] = [actor]
        flash("The actor has been added.","info")
        return render_template("newMovie/actors.html", admin=True)
    else:
        if "movie" in session:
            return render_template("newMovie/actors.html", admin=True)
        else:
            return redirect(url_for("user"))
########################################################################################################################################################### new Movie Test
@app.route("/MovieFlix/TestMovie", methods=["POST", "GET"])
def testMovie():
    if request.method == "POST":
        ans = request.form["ans"]
        if ans != "YES" and ans != "NO":
            flash("You must type exactly YES or NO.","info")
            if "year" in session["movie"] and "descr" in session["movie"]:
                return render_template("newMovie/testMovie.html", title=session["movie"]["title"], year=session["movie"]["year"], descr=session["movie"]["descr"], actors=session["actors"], admin=True)
            elif "year" in session["movie"]:
                return render_template("newMovie/testMovie.html", title=session["movie"]["title"], year=session["movie"]["year"], actors=session["actors"], admin=True)
            elif "descr" in session["movie"]:
                return render_template("newMovie/testMovie.html", title=session["movie"]["title"], descr=session["movie"]["descr"], actors=session["actors"], admin=True)
            else:
                return render_template("newMovie/testMovie.html", title=session["movie"]["title"], actors=session["actors"], admin=True)
        if ans == "NO":  
            del session["movie"]
            del session["actors"]
            flash("The information of the movie has been cleared.","info")
            return redirect(url_for("newMovie"))
        elif ans == "YES":
            movie = session["movie"]
            movie["actors"] = session["actors"]
            if movies.find_one({"count": {"$exists":True}}) == None:
                movies.insert_one({"count":0})
            num = movies.find_one({"count": {"$exists":True}}) 
            movie["_id"] = num["count"]+1
            movies.update_one({"count": {"$exists":True}}, {"$set": {"count":num["count"]+1}})
            movies.insert_one(movie)
            flash("The movie has been added.","info")
            del session["movie"]
            del session["actors"]
            return redirect(url_for("admin"))
    else:
        if "actors" in session and "user" in session:
            if "year" in session["movie"] and "descr" in session["movie"]:
                return render_template("newMovie/testMovie.html", title=session["movie"]["title"], year=session["movie"]["year"], descr=session["movie"]["descr"], actors=session["actors"], admin=True)
            elif "year" in session["movie"]:
                return render_template("newMovie/testMovie.html", title=session["movie"]["title"], year=session["movie"]["year"], actors=session["actors"], admin=True)
            elif "descr" in session["movie"]:
                return render_template("newMovie/testMovie.html", title=session["movie"]["title"], descr=session["movie"]["descr"], actors=session["actors"], admin=True)
            else:
                return render_template("newMovie/testMovie.html", title=session["movie"]["title"], actors=session["actors"], admin=True)
        elif "user" in session and "movie" in session:
            flash("At least one protagonist must exist in a movie!","info")
            return redirect(url_for("user"))
        else:
            return redirect(url_for("user"))
########################################################################################################################################################### Search by what?
@app.route("/MovieFlix/Search")
def searchMovie():
    if "admin" in session:
        return render_template("searchMovie/By/searchBy.html", admin=True)
    elif "user" in session:
        return render_template("searchMovie/By/searchBy.html")
    else:
        return redirect(url_for("user"))
########################################################################################################################################################### By Title
@app.route("/MovieFlix/Search/ByTitle", methods=["POST", "GET"])
def searchByTitle():
    if request.method == "POST":
        title = request.form["title"]
        if title == "":
            flash("You need to fill the title field!","info")
            if "admin" in session:
                return render_template("searchMovie/By/ByTitle.html", admin=True)
            return render_template("searchMovie/By/ByTitle.html")
        session["titleSearch"]=title
        return redirect(url_for("searchResults"))
    else:
        if "admin" in session:
            return render_template("searchMovie/By/ByTitle.html", admin=True)
        elif "user" in session:
            return render_template("searchMovie/By/ByTitle.html")
        else:
            return redirect(url_for("user"))
########################################################################################################################################################### By Year
@app.route("/MovieFlix/Search/ByYear", methods=["POST", "GET"])
def searchByYear():
    if request.method == "POST":
        year = request.form["year"]
        if year == "" or year.isdigit() == False:
            flash("You need to fill the year field with a positive number!","info")
            if "admin" in session:
                return render_template("searchMovie/By/ByYear.html", admin=True)
            return render_template("searchMovie/By/ByYear.html")
        session["yearSearch"]=int(year)
        return redirect(url_for("searchResults"))
    else:
        if "admin" in session:
            return render_template("searchMovie/By/ByYear.html", admin=True)
        elif "user" in session:
            return render_template("searchMovie/By/ByYear.html")
        else:
            return redirect(url_for("user"))
########################################################################################################################################################### By Actor
@app.route("/MovieFlix/Search/ByActor", methods=["POST", "GET"])
def searchByActor():
    if request.method == "POST":
        actor = request.form["actor"]
        if actor == "":
            flash("You need to fill the actor field!","info")
            if "admin" in session:
                return render_template("searchMovie/By/ByActor.html", admin=True)
            return render_template("searchMovie/By/ByActor.html")
        session["actorSearch"]=actor
        return redirect(url_for("searchResults"))
    else:
        if "admin" in session:
            return render_template("searchMovie/By/ByActor.html", admin=True)
        elif "user" in session:
            return render_template("searchMovie/By/ByActor.html")
        else:
            return redirect(url_for("user"))
########################################################################################################################################################### user search
@app.route("/MovieFlix/Search/Results", methods=["POST", "GET"])
def searchResults():
    if request.method == "POST":
        myID = request.form["ID"]
        if myID == "":
            flash("When searching, the ID field must be filled to proceed!","info")
            return redirect(url_for("searchMovie"))
        if myID.isdigit() == False:
            flash("This ID does not exist!","info")
            return redirect(url_for("searchMovie"))
        ID = int(myID)
        if movies.find({"_id":ID}).count() == 0:
            flash("This ID does not exist!","info")
            return redirect(url_for("searchMovie"))
        session["searchID"]=ID
        return redirect(url_for("movie"))
    else:
        if "user" in session:
            searchedMoviesList = []
            if "titleSearch" in session:
                searchedMovies = movies.find({"title":session["titleSearch"]})
                searchedMoviesList = list(searchedMovies)
                del session["titleSearch"]
            elif "yearSearch" in session:
                searchedMovies = movies.find({"year":session["yearSearch"]})
                searchedMoviesList = list(searchedMovies)
                del session["yearSearch"]
            elif "actorSearch" in session:
                searchedMovies = movies.find({"actors":session["actorSearch"]})
                searchedMoviesList = list(searchedMovies)
                del session["actorSearch"]
            if len(searchedMoviesList) == 0:
                flash("No movies found.","info")
                return redirect(url_for("searchMovie"))
            if "admin" in session:
                return render_template("searchMovie/MoviesFound.html", moviesFound=searchedMoviesList, admin=True)
            return render_template("searchMovie/MoviesFound.html", moviesFound=searchedMoviesList)
        else:
            return redirect(url_for("user"))
########################################################################################################################################################### Movie
@app.route("/MovieFlix/Movie", methods=["POST", "GET"])
def movie():
    if request.method == "POST":
        userComments = users.find_one({"$and":[{"email":session["user"]["email"]},{"comments":{"$exists":True}}]})
        if userComments == None:
            comment = ""
            rating = -1
        else:
            userComments = users.find_one({"$and":[{"email":session["user"]["email"]},{"comments":{"$elemMatch":{"ID":session["searchID"]}}}]})
            if userComments == None:
                comment = ""
                rating = -1
            else:
                allComments= userComments["comments"]
                for com in allComments:
                    if com["ID"] == session["searchID"]:
                        comment = com["comment"] 
                        rating = com["rating"] 
        movie = list(movies.find({"_id" : session["searchID"]}))
        ans = request.form["ans"]
        if ans == "" or ans.isdigit() == False:
            flash("You need to fill the field with a positive number!","info")
            if  "admin" in session:
                return render_template("searchMovie/Movie.html", movie = movie, admin=True, comment=comment, rating=rating)
            return render_template("searchMovie/Movie.html", movie = movie, comment=comment, rating=rating)
        answer = int(ans)
        if ("admin" in session) and (answer < 1 or answer > 7):
            flash("You need to fill the field with a number between 1 and 7!","info")
            return render_template("searchMovie/Movie.html", movie = movie, admin=True, comment=comment, rating=rating)
        elif (not ("admin" in session)) and (answer < 1 or answer > 4):
            flash("You need to fill the field with a number between 1 and 4!","info")
            return render_template("searchMovie/Movie.html", movie = movie, comment=comment, rating=rating)
        if answer == 1:
            return redirect(url_for("makeComment"))
        elif answer == 2:
            return redirect(url_for("makeRating"))
        elif answer == 3:
            return redirect(url_for("deleteComment"))
        elif answer == 4:
            return redirect(url_for("deleteRating"))
        elif answer == 5:
            return redirect(url_for("deleteUserComments"))
        elif answer == 6:
            return redirect(url_for("updateMovie"))
        elif answer == 7:
            return redirect(url_for("deleteMovie"))
    else:
        if "user" in session:
            userComments = users.find_one({"$and":[{"email":session["user"]["email"]},{"comments":{"$exists":True}}]})
            if userComments == None:
                comment = ""
                rating = -1
            else:
                userComments = users.find_one({"$and":[{"email":session["user"]["email"]},{"comments":{"$elemMatch":{"ID":session["searchID"]}}}]})
                if userComments == None:
                    comment = ""
                    rating = -1
                else:
                    allComments= userComments["comments"]
                    for com in allComments:
                        if com["ID"] == session["searchID"]:
                            comment = com["comment"] 
                            rating = com["rating"] 
            movie = list(movies.find({"_id" : session["searchID"]}))
            if "admin" in session:
                return render_template("searchMovie/Movie.html", movie = movie, admin=True, comment=comment, rating=rating)
            return render_template("searchMovie/Movie.html", movie = movie, comment=comment, rating=rating)
        else:
            return redirect(url_for("user"))
########################################################################################################################################################### Make Comment           
@app.route("/MovieFlix/Movie/makeComment", methods=["POST", "GET"])
def makeComment():
    if request.method == "POST":
        comment = request.form["comment"]
        moviedict = movies.find_one({"_id" : session["searchID"]})
        if comment == "":
            flash("You must fill the comment field!","info")
            if "admin" in session:
                return render_template("searchMovie/Selections/MakeComment.html", title = moviedict["title"], admin=True)
            return render_template("searchMovie/Selections/MakeComment.html", title = moviedict["title"])
        movieComment = {}
        if session["addComment"] == 0:
            movieComment = {"email":session["user"]["email"], "comment":comment, "rating": -1}
            users.update_one({"email":session["user"]["email"]},{"$set":{"comments":[{"comment":comment, "rating": -1, "ID":moviedict["_id"]}]}})
        elif session["addComment"] == 1:
            movieComment = {"email":session["user"]["email"], "comment":comment, "rating": -1}
            doc = users.find_one({"email":session["user"]["email"]})
            comList = doc["comments"]
            comList.append({"comment":comment, "rating": -1, "ID":moviedict["_id"]})
            users.update_one({"email":session["user"]["email"]},{"$set":{"comments":comList}})
        else:
            movieComment = {"email":session["user"]["email"], "comment":comment, "rating": session["theRating"]}
            doc = users.find_one({"email":session["user"]["email"]})
            comList = doc["comments"]
            newComList = []
            coms = {}
            for com in comList:
                coms = com
                if com["ID"] == moviedict["_id"]:
                    coms = {"comment":comment, "rating": session["theRating"], "ID":moviedict["_id"]}
                newComList.append(coms)
            users.update_one({"email":session["user"]["email"]},{"$set":{"comments":newComList}})
            del session["theRating"]
        commentsExists = movies.find_one({"$and":[{"_id":moviedict["_id"]},{"comments":{"$exists":True}}]})
        if commentsExists == None:
            movies.update_one({"_id":moviedict["_id"]},{"$set":{"comments":[movieComment]}})
        else:
            usersComment = movies.find_one({"$and":[{"_id":moviedict["_id"]},{"comments":{"$elemMatch":{"email":session["user"]["email"]}}}]})
            if usersComment == None:
                doc = movies.find_one({"_id":moviedict["_id"]})
                comList = doc["comments"]
                comList.append(movieComment)
                movies.update_one({"_id":moviedict["_id"]},{"$set":{"comments":comList}})
            else:
                doc = movies.find_one({"_id":moviedict["_id"]})
                comList = doc["comments"]
                coms = {}
                comsList = []
                for com in comList:
                    coms = com
                    if com["email"] == session["user"]["email"]:
                        coms = movieComment
                    comsList.append(coms)
                movies.update_one({"_id":moviedict["_id"]},{"$set":{"comments":comsList}})
        flash("Your comment is now registered.","info")
        del session["addComment"]
        return redirect(url_for("movie"))
    else:
        if "user" in session:
            moviedict = movies.find_one({"_id" : session["searchID"]})
            doc = users.find_one({"$and":[{"email":session["user"]["email"]},{"comments":{"$exists":True}}]})
            if doc == None:
                session["addComment"] = 0
                if "admin" in session:
                    return render_template("searchMovie/Selections/MakeComment.html", title = moviedict["title"], admin=True)
                return render_template("searchMovie/Selections/MakeComment.html", title = moviedict["title"])
            doc_for_this = users.find_one({"$and":[{"email":session["user"]["email"]},{"comments":{"$elemMatch":{"ID":moviedict["_id"]}}}]})
            if doc_for_this == None:
                session["addComment"] = 1
                if "admin" in session:
                    return render_template("searchMovie/Selections/MakeComment.html", title = moviedict["title"], admin=True)
                return render_template("searchMovie/Selections/MakeComment.html", title = moviedict["title"])
            for com in doc_for_this["comments"]:
                if com["ID"] == moviedict["_id"] and com["comment"] == "":
                    session["addComment"] = 2
                    session["theRating"] = com["rating"]
                    if "admin" in session:
                        return render_template("searchMovie/Selections/MakeComment.html", title = moviedict["title"], admin=True)
                    return render_template("searchMovie/Selections/MakeComment.html", title = moviedict["title"])
            flash("You have already made a comment for this movie!","info")
            return redirect(url_for("movie"))
        else:
            return redirect(url_for("user"))
########################################################################################################################################################### Make Rating   
@app.route("/MovieFlix/Movie/makeRating", methods=["POST", "GET"])
def makeRating():
    if request.method == "POST":
        myRating = request.form["rating"]
        moviedict = movies.find_one({"_id" : session["searchID"]})
        if myRating == "":
            flash("You must fill the rating field!","info")
            if "admin" in session:
                return render_template("searchMovie/Selections/MakeRating.html", title = moviedict["title"], admin=True)
            return render_template("searchMovie/Selections/MakeRating.html", title = moviedict["title"])
        if myRating.isdigit() == False:
            flash("Ratings are integers between 0 and 5!","info")
            if "admin" in session:
                return render_template("searchMovie/Selections/MakeRating.html", title = moviedict["title"], admin=True)
            return render_template("searchMovie/Selections/MakeRating.html", title = moviedict["title"])
        rating = int(myRating)
        if rating != 0 and rating != 1 and rating != 2 and rating != 3 and rating != 4 and rating != 5:
            flash("Ratings are integers between 0 and 5!","info")
            if "admin" in session:
                return render_template("searchMovie/Selections/MakeRating.html", title = moviedict["title"], admin=True)
            return render_template("searchMovie/Selections/MakeRating.html", title = moviedict["title"])
        movieComment = {}
        if session["addRating"] == 0:
            movieComment = {"email":session["user"]["email"], "comment":"", "rating": rating}
            users.update_one({"email":session["user"]["email"]},{"$set":{"comments":[{"comment":"", "rating": rating, "ID":moviedict["_id"]}]}})
        elif session["addRating"] == 1:
            movieComment = {"email":session["user"]["email"], "comment":"", "rating": rating}
            doc = users.find_one({"email":session["user"]["email"]})
            comList = doc["comments"]
            comList.append({"comment":"", "rating": rating, "ID":moviedict["_id"]})
            users.update_one({"email":session["user"]["email"]},{"$set":{"comments":comList}})
        else:
            movieComment = {"email":session["user"]["email"], "comment":session["theComment"], "rating": rating}
            doc = users.find_one({"email":session["user"]["email"]})
            comList = doc["comments"]
            newComList = []
            coms = {}
            for com in comList:
                coms = com
                if com["ID"] == moviedict["_id"]:
                    coms = {"comment":session["theComment"], "rating": rating, "ID":moviedict["_id"]}
                newComList.append(coms)
            users.update_one({"email":session["user"]["email"]},{"$set":{"comments":newComList}})
            del session["theComment"]
        commentsExists = movies.find_one({"$and":[{"_id":moviedict["_id"]},{"comments":{"$exists":True}}]})
        if commentsExists == None:
            movies.update_one({"_id":moviedict["_id"]},{"$set":{"comments":[movieComment]}})
        else:
            usersComment = movies.find_one({"$and":[{"_id":moviedict["_id"]},{"comments":{"$elemMatch":{"email":session["user"]["email"]}}}]})
            if usersComment == None:
                doc = movies.find_one({"_id":moviedict["_id"]})
                comList = doc["comments"]
                comList.append(movieComment)
                movies.update_one({"_id":moviedict["_id"]},{"$set":{"comments":comList}})
            else:
                doc = movies.find_one({"_id":moviedict["_id"]})
                comList = doc["comments"]
                coms = {}
                comsList = []
                for com in comList:
                    coms = com
                    if com["email"] == session["user"]["email"]:
                        coms = movieComment
                    comsList.append(coms)
                movies.update_one({"_id":moviedict["_id"]},{"$set":{"comments":comsList}})
        summ = 0
        amm = 0
        movieToRate = movies.find_one({"_id":moviedict["_id"]})
        allComments = movieToRate["comments"]
        for com in allComments:
            if com["rating"] != -1:
                amm = amm + 1
                summ = summ + com["rating"] 
        moviesRating = summ / amm
        movies.update_one({"_id":moviedict["_id"]}, {"$set":{"rating":moviesRating}})
        flash("Your rating is now registered.","info")
        del session["addRating"]
        return redirect(url_for("movie"))
    else:
        if "user" in session:
            moviedict = movies.find_one({"_id" : session["searchID"]})
            doc = users.find_one({"$and":[{"email":session["user"]["email"]},{"comments":{"$exists":True}}]})
            if doc == None:
                session["addRating"] = 0
                if "admin" in session:
                    return render_template("searchMovie/Selections/MakeRating.html", title = moviedict["title"], admin=True)
                return render_template("searchMovie/Selections/MakeRating.html", title = moviedict["title"])
            doc_for_this = users.find_one({"$and":[{"email":session["user"]["email"]},{"comments":{"$elemMatch":{"ID":moviedict["_id"]}}}]})
            if doc_for_this == None:
                session["addRating"] = 1
                if "admin" in session:
                    return render_template("searchMovie/Selections/MakeRating.html", title = moviedict["title"], admin=True)
                return render_template("searchMovie/Selections/MakeRating.html", title = moviedict["title"])
            for com in doc_for_this["comments"]:
                if com["ID"] == moviedict["_id"] and com["rating"] ==  -1:
                    session["addRating"] = 2
                    session["theComment"] = com["comment"]
                    if "admin" in session:
                        return render_template("searchMovie/Selections/MakeRating.html", title = moviedict["title"], admin=True)
                    return render_template("searchMovie/Selections/MakeRating.html", title = moviedict["title"])
            flash("You have already made a rating for this movie!","info")
            return redirect(url_for("movie"))
        else:
            return redirect(url_for("user"))
########################################################################################################################################################### Delete Comment    
@app.route("/MovieFlix/Movie/deleteComment", methods=["POST", "GET"])
def deleteComment():
    if request.method == "POST":
        moviedict = movies.find_one({"_id" : session["searchID"]})
        ans = request.form["ans"]
        if ans == "YES":
            myUser = users.find_one({"email":session["user"]["email"]})
            userComments = myUser["comments"]
            userNewComments = []
            newCom = {}
            for com in userComments:
                newCom = com
                if com["ID"] == session["searchID"]:
                    newCom["comment"]=""
                userNewComments.append(newCom)
            myMovie = movies.find_one({"_id":session["searchID"]})
            movieComments = myMovie["comments"]
            movieNewComments = []
            newCom = {}
            for com in movieComments:
                newCom = com
                if com["email"] == session["user"]["email"]:
                    newCom["comment"]=""
                movieNewComments.append(newCom)
            movies.update_one({"_id":session["searchID"]},{"$set":{"comments":movieNewComments}})
            users.update_one({"email":session["user"]["email"]},{"$set":{"comments":userNewComments}})
            flash("Your comment has been deleted.","info")
            return redirect(url_for("movie"))
        elif ans == "NO":
            flash("Your comment has not been deleted.","info")
            return redirect(url_for("movie"))
        else:
            flash("You must fiil the field below with YES or NO!","info")
            if "admin" in session:
                return render_template("searchMovie/Selections/DeleteComment.html", title = moviedict["title"], admin=True, comment=session["commentToDelete"])
            return render_template("searchMovie/Selections/DeleteComment.html", title = moviedict["title"], comment=session["commentToDelete"])
    else:
        if "user" in session:
            moviedict = movies.find_one({"_id" : session["searchID"]})
            userComments = users.find_one({"$and":[{"email":session["user"]["email"]},{"comments":{"$exists":True}}]})
            if userComments == None:
                flash("You have not made any comment yet!","info")
                return redirect(url_for("movie"))
            MovieComments = users.find_one({"$and":[{"email":session["user"]["email"]},{"comments":{"$elemMatch":{"ID":moviedict["_id"]}}}]})
            if MovieComments == None:
                flash("You have not made any comment yet!","info")
                return redirect(url_for("movie"))
            comments = MovieComments["comments"]
            for com in comments:
                if com["ID"] == moviedict["_id"] and com["comment"] == "":
                    flash("You have not made any comment yet!","info")
                    return redirect(url_for("movie"))
                elif com["ID"] == moviedict["_id"] and com["comment"] != "":
                    session["commentToDelete"] = com["comment"]
            if "admin" in session:
                return render_template("searchMovie/Selections/DeleteComment.html", title = moviedict["title"], admin=True, comment=session["commentToDelete"])
            return render_template("searchMovie/Selections/DeleteComment.html", title = moviedict["title"], comment=session["commentToDelete"])
        else:
            return redirect(url_for("user"))
########################################################################################################################################################### Delete Rating    
@app.route("/MovieFlix/Movie/deleteRating", methods=["POST", "GET"])
def deleteRating():
    if request.method == "POST":
        moviedict = movies.find_one({"_id" : session["searchID"]})
        ans = request.form["ans"]
        if ans == "YES":
            myUser = users.find_one({"email":session["user"]["email"]})
            userComments = myUser["comments"]
            userNewComments = []
            newCom = {}
            for com in userComments:
                newCom = com
                if com["ID"] == session["searchID"]:
                    newCom["rating"]= -1
                userNewComments.append(newCom)
            myMovie = movies.find_one({"_id":session["searchID"]})
            movieComments = myMovie["comments"]
            movieNewComments = []
            newCom = {}
            for com in movieComments:
                newCom = com
                if com["email"] == session["user"]["email"]:
                    newCom["rating"]= -1
                movieNewComments.append(newCom)
            movies.update_one({"_id":session["searchID"]},{"$set":{"comments":movieNewComments}})
            users.update_one({"email":session["user"]["email"]},{"$set":{"comments":userNewComments}})
            summ = 0
            amm = 0
            movieToRate = movies.find_one({"_id":moviedict["_id"]})
            allComments = movieToRate["comments"]
            for com in allComments:
                if com["rating"] != -1:
                    amm = amm + 1
                    summ = summ + com["rating"] 
            if amm == 0:
                moviesRating = -1
                movies.update_one({"_id":moviedict["_id"]}, {"$set":{"rating":moviesRating}})
            else:
                moviesRating = summ / amm
                movies.update_one({"_id":moviedict["_id"]}, {"$set":{"rating":moviesRating}})
            flash("Your rating has been deleted.","info")
            return redirect(url_for("movie"))
        elif ans == "NO":
            flash("Your rating has not been deleted.","info")
            return redirect(url_for("movie"))
        else:
            flash("You must fiil the field below with YES or NO!","info")
            if "admin" in session:
                return render_template("searchMovie/Selections/DeleteRating.html", title = moviedict["title"], admin=True, rating=session["ratingToDelete"])
            return render_template("searchMovie/Selections/DeleteRating.html", title = moviedict["title"], rating=session["ratingToDelete"])
    else:
        if "user" in session:
            moviedict = movies.find_one({"_id" : session["searchID"]})
            userComments = users.find_one({"$and":[{"email":session["user"]["email"]},{"comments":{"$exists":True}}]})
            if userComments == None:
                flash("You have not made any rating yet!","info")
                return redirect(url_for("movie"))
            MovieComments = users.find_one({"$and":[{"email":session["user"]["email"]},{"comments":{"$elemMatch":{"ID":moviedict["_id"]}}}]})
            if MovieComments == None:
                flash("You have not made any rating yet!","info")
                return redirect(url_for("movie"))
            comments = MovieComments["comments"]
            for com in comments:
                if com["ID"] == moviedict["_id"] and com["rating"] ==  -1:
                    flash("You have not made any rating yet!","info")
                    return redirect(url_for("movie"))
                elif com["ID"] == moviedict["_id"] and com["rating"] !=  -1:
                    session["ratingToDelete"] = com["rating"]
            if "admin" in session:
                return render_template("searchMovie/Selections/DeleteRating.html", title = moviedict["title"], admin=True, rating=session["ratingToDelete"])
            return render_template("searchMovie/Selections/DeleteRating.html", title = moviedict["title"], rating=session["ratingToDelete"])
        else:
            return redirect(url_for("user"))
########################################################################################################################################################### Delete User Comments
@app.route("/MovieFlix/Movie/deleteUserComments", methods=["POST", "GET"])
def deleteUserComments():
    if request.method == "POST":
        movie = list(movies.find({"_id":session["searchID"]}))
        email = request.form["email"]
        if email == "":
            flash("You must fill the email field!","info")
            return render_template("searchMovie/Selections/admins/DeleteUserComments.html", movie = movie, admin = True)
        theEmailExists = movies.find_one({"$and":[{"_id":session["searchID"]},{"comments":{"$elemMatch":{"email":email}}}]})
        if theEmailExists == None:
            flash("This user has not made any comment in this movie!","info")
            return render_template("searchMovie/Selections/admins/DeleteUserComments.html", movie = movie, admin = True)
        movieComments = theEmailExists["comments"]
        newMovieComments = []
        newCom = {}
        for com in movieComments:
            newCom = com
            if com["email"] == email:
                newCom["comment"] = "" 
            newMovieComments.append(newCom)
        theUser = users.find_one({"email":email})
        userComments = theUser["comments"]
        newUserComments = []
        newCom = {}
        for com in userComments:
            newCom = com
            if com["ID"] == session["searchID"]:
                newCom["comment"] = "" 
            newUserComments.append(newCom)
        movies.update_one({"_id":session["searchID"]},{"$set":{"comments":newMovieComments}})
        users.update_one({"email":email},{"$set":{"comments":newUserComments}})
        flash("The comment has been removed.","info")
        return redirect(url_for("movie"))
    else:
        if "admin" in session:
            movieComments = movies.find_one({"$and":[{"_id":session["searchID"]},{"comments":{"$exists":True}}]})
            if movieComments == None:
                flash("This movie does not have comments!","info")
                return redirect(url_for("movie"))
            myComments = movieComments["comments"]
            for com in myComments:
                if com["comment"] != "":
                    movie = list(movies.find({"_id":session["searchID"]}))
                    return render_template("searchMovie/Selections/admins/DeleteUserComments.html", movie = movie, admin = True)
            flash("This movie does not have comments!","info")
            return redirect(url_for("movie"))
        else:
            return redirect(url_for("user"))
########################################################################################################################################################### Update Movie
@app.route("/MovieFlix/updateMovie", methods=["POST", "GET"])
def updateMovie():
    if request.method == "POST":
        title = request.form["title"]
        year = request.form["year"]
        descr = request.form["descr"]
        if title == "":
            flash("You can't update a movie without a title!","info")
            return render_template("searchMovie/Selections/admins/UpdateMovie/UpdateMovie.html", admin=True)
        movie = movies.find_one({"_id":session["searchID"]})
        movie["title"] = title
        if year != "" and year.isdigit() == True:
            movie["year"]=int(year)
        elif year.isdigit() == False and year != "":
            flash("Your year was not a possitive integer!","info")
            return render_template("searchMovie/Selections/admins/UpdateMovie/UpdateMovie.html", admin=True)
        elif "year" in movie:
            del movie["year"]
        if descr != "":
            movie["descr"]=descr
        elif "descr" in movie:
            del movie["descr"]
        session["movie"]=movie
        return redirect(url_for("updateActors"))
    else:
        if "admin" in session:
            return render_template("searchMovie/Selections/admins/UpdateMovie/UpdateMovie.html", admin=True)
        else:
            return redirect(url_for("user"))
########################################################################################################################################################### Update Movie Actors
@app.route("/MovieFlix/NewMovie/updateActors", methods=["POST", "GET"])
def updateActors():
    if request.method == "POST":
        actor = request.form["actor"]
        if actor == "":
            flash("Actor's field must be filled!","info")
            return render_template("searchMovie/Selections/admins/UpdateMovie/UpdateActors.html", admin=True)
        if "actors" in session:
            session["actors"].append(actor)
        else:
            session["actors"] = [actor]
        flash("The actor has been added.","info")
        return render_template("searchMovie/Selections/admins/UpdateMovie/UpdateActors.html", admin=True)
    else:
        if "movie" in session:
            return render_template("searchMovie/Selections/admins/UpdateMovie/UpdateActors.html", admin=True)
        else:
            return redirect(url_for("user"))
########################################################################################################################################################### Update Movie Test
@app.route("/MovieFlix/updateTestMovie", methods=["POST", "GET"])
def updateTestMovie():
    if request.method == "POST":
        ans = request.form["ans"]
        if ans != "YES" and ans != "NO":
            flash("You must type exactly YES or NO.","info")
            if "year" in session["movie"] and "descr" in session["movie"]:
                return render_template("searchMovie/Selections/admins/UpdateMovie/UpdateTestMovie.html", title=session["movie"]["title"], year=session["movie"]["year"], descr=session["movie"]["descr"], actors=session["actors"], admin=True)
            elif "year" in session["movie"]:
                return render_template("searchMovie/Selections/admins/UpdateMovie/UpdateTestMovie.html", title=session["movie"]["title"], year=session["movie"]["year"], actors=session["actors"], admin=True)
            elif "descr" in session["movie"]:
                return render_template("searchMovie/Selections/admins/UpdateMovie/UpdateTestMovie.html", title=session["movie"]["title"], descr=session["movie"]["descr"], actors=session["actors"], admin=True)
            else:
                return render_template("searchMovie/Selections/admins/UpdateMovie/UpdateTestMovie.html", title=session["movie"]["title"], actors=session["actors"], admin=True)
        if ans == "NO":  
            del session["movie"]
            del session["actors"]
            flash("The movie has not been updated.","info")
            return redirect(url_for("updateMovie"))
        elif ans == "YES":
            movie = session["movie"]
            movie["actors"] = session["actors"]
            movies.delete_one({"_id":session["searchID"]})
            movies.insert_one(movie)
            flash("The movie has been updated.","info")
            del session["movie"]
            del session["actors"]
            return redirect(url_for("movie"))
    else:
        if "actors" in session and "user" in session:
            if "year" in session["movie"] and "descr" in session["movie"]:
                return render_template("searchMovie/Selections/admins/UpdateMovie/UpdateTestMovie.html", title=session["movie"]["title"], year=session["movie"]["year"], descr=session["movie"]["descr"], actors=session["actors"], admin=True)
            elif "year" in session["movie"]:
                return render_template("searchMovie/Selections/admins/UpdateMovie/UpdateTestMovie.html", title=session["movie"]["title"], year=session["movie"]["year"], actors=session["actors"], admin=True)
            elif "descr" in session["movie"]:
                return render_template("searchMovie/Selections/admins/UpdateMovie/UpdateTestMovie.html", title=session["movie"]["title"], descr=session["movie"]["descr"], actors=session["actors"], admin=True)
            else:
                return render_template("searchMovie/Selections/admins/UpdateMovie/UpdateTestMovie.html", title=session["movie"]["title"], actors=session["actors"], admin=True)
        elif "user" in session and "movie" in session:
            flash("At least one protagonist must exist in a movie!","info")
            return redirect(url_for("user"))
        else:
            return redirect(url_for("user"))
########################################################################################################################################################### Delete Movie
@app.route("/MovieFlix/DeleteMovie", methods=["POST", "GET"])
def deleteMovie():
    if request.method == "POST":
        moviedict = movies.find_one({"_id" : session["searchID"]})
        ans = request.form["ans"]
        if ans == "":
            flash("You must fill the answer field!","info")
            return render_template("searchMovie/Selections/admins/DeleteMovie.html", admin=True,title = moviedict["title"])
        if ans == "YES":
            myMovie = movies.find_one({"$and":[{"_id":moviedict["_id"]},{"comments":{"$exists":True}}]})
            if myMovie == None:
                movies.delete_one({"_id":moviedict["_id"]})
                flash("The movie has been deleted.","info")
                return redirect(url_for("user"))
            comments = myMovie["comments"]
            for comment in comments:
                email = comment["email"]
                user = users.find_one({"email":email})
                userComments = user["comments"]
                userNewCommentList = []
                for com in userComments:
                    if com["ID"] != moviedict["_id"]:
                        userNewCommentList.append(com)
                users.update_one({"email":email},{"$set":{"comments":userNewCommentList}})
            movies.delete_one({"_id":moviedict["_id"]})
            flash("The movie has been deleted.","info")
            return redirect(url_for("user"))
        elif ans == "NO":
            flash("The movie has not been deleted.","info")
            return redirect(url_for("movie"))
        else:
            flash("You must fill the answer field by typing YES or NO!","info")
            return render_template("searchMovie/Selections/admins/DeleteMovie.html", admin=True,title = moviedict["title"])
    else:
        if "admin" in session:
            moviedict = movies.find_one({"_id" : session["searchID"]})
            return render_template("searchMovie/Selections/admins/DeleteMovie.html", admin=True,title = moviedict["title"])
        else:
            return redirect(url_for("user"))
########################################################################################################################################################### Comments
@app.route("/MovieFlix/Comments")
def comments():
    if "user" in session:
        myUser = users.find_one({"$and":[{"email":session["user"]["email"]},{"comments":{"$exists":True}}]})
        if myUser == None:
            flash("You have not made any comment yet.","info")
            return redirect(url_for("user"))
        comments = myUser["comments"]
        validComments = []
        for comment in comments:
            if comment["comment"] != "":
                movie = movies.find_one({"_id":comment["ID"]})
                title = movie["title"]
                validComments.append({"title":title, "comment":comment["comment"]})
        if len(validComments) == 0:
            flash("You have not made any comment yet.","info")
            return redirect(url_for("user"))
        if "admin" in session:
            return render_template("AllComments/Comments.html", allComments = validComments, admin=True)
        return render_template("AllComments/Comments.html", allComments = validComments)
    else:
        return redirect(url_for("user"))
########################################################################################################################################################### Ratings
@app.route("/MovieFlix/Ratings")
def ratings():
    if "user" in session:
        myUser = users.find_one({"$and":[{"email":session["user"]["email"]},{"comments":{"$exists":True}}]})
        if myUser == None:
            flash("You have not made any ratings yet.","info")
            return redirect(url_for("user"))
        comments = myUser["comments"]
        validRatings = []
        for comment in comments:
            if comment["rating"] != -1:
                movie = movies.find_one({"_id":comment["ID"]})
                title = movie["title"]
                validRatings.append({"title":title, "rating":comment["rating"]})
        if len(validRatings) == 0:
            flash("You have not made any rating yet.","info")
            return redirect(url_for("user"))
        if "admin" in session:
            return render_template("AllRatings/Ratings.html", allRatings = validRatings, admin=True)
        return render_template("AllRatings/Ratings.html", allRatings = validRatings)
    else:
        return redirect(url_for("user"))
########################################################################################################################################################### Delete My Account
@app.route("/MovieFlix/DeleteAccount", methods=["POST", "GET"])
def deleteMyAccount():
    if request.method == "POST":
        ans = request.form["ans"]
        if ans != "I AM SURE":
            flash("To delete your account, you must type I AM SURE !","info")
            if ("admin" in session) and (session["admin"]["email"]=="admin@admin.com"):
                return render_template("DeleteMyAccount/DeleteMyAccount.html", admin=True, iAmAdmin = True)
            elif "admin" in session:
                return render_template("DeleteMyAccount/DeleteMyAccount.html", admin=True)
            return render_template("DeleteMyAccount/DeleteMyAccount.html")
        myUser = users.find_one({"$and":[{"email":session["user"]["email"]},{"comments":{"$exists":True}}]})
        if myUser == None:
            users.delete_one({"email":session["user"]["email"]})
            flash("Your account has been deleted from MovieFlix.","info")
            return redirect(url_for("logout"))
        comments = myUser["comments"]
        for comment in comments:
            ID = comment["ID"]
            movie = movies.find_one({"_id":ID})
            movieComments = movie["comments"]
            movieNewCommentList = []
            summ = 0
            amm = 0
            for com in movieComments:
                if (com["email"] != session["user"]["email"]) and (com["rating"] != -1):
                    summ = summ + com["rating"]
                    amm = amm + 1
                if com["email"] != session["user"]["email"]:
                    movieNewCommentList.append(com)
            movies.update_one({"_id":ID},{"$set":{"comments":movieNewCommentList}})
            if amm != 0:
                rating = summ/amm
            else:
                rating = -1
            movies.update_one({"_id":ID},{"$set":{"rating":rating}})
        users.delete_one({"email":session["user"]["email"]})
        flash("Your account has been deleted from MovieFlix.","info")
        return redirect(url_for("logout"))
    else:
        if ("admin" in session) and (session["admin"]["email"]=="admin@admin.com"):
            return render_template("DeleteMyAccount/DeleteMyAccount.html", admin=True, iAmAdmin = True)
        elif "admin" in session:
            return render_template("DeleteMyAccount/DeleteMyAccount.html", admin=True)
        elif "user" in session:
            return render_template("DeleteMyAccount/DeleteMyAccount.html")
        else:
            return redirect(url_for("user"))
########################################################################################################################################################### View all Users
@app.route("/MovieFlix/ViewUsers", methods=["POST", "GET"])
def viewUsers():
    if request.method == "POST":
        movieFlixUsers = list(users.find({}))
        email = request.form["email"]
        if email == "":
            flash("You must fill the email field!","info")
            return render_template("ViewAllUsers/AllUsers.html", admin=True, movieFlixUsers = movieFlixUsers)
        userExists = users.find_one({"email":email})
        if userExists == None:
            flash("There is no user with this email address!","info")
            return render_template("ViewAllUsers/AllUsers.html", admin=True, movieFlixUsers = movieFlixUsers)
        normalUser = users.find_one({"$and":[{"email":email},{"isAdmin":False}]})
        if normalUser == None:
            flash("This user is an admin!","info")
            return render_template("ViewAllUsers/AllUsers.html", admin=True, movieFlixUsers = movieFlixUsers)
        session["userPicked"] = normalUser["email"]
        return redirect(url_for("deleteOrAdmin"))
    else:
        if "admin" in session:
            movieFlixUsers = list(users.find({}))
            return render_template("ViewAllUsers/AllUsers.html", admin=True, movieFlixUsers = movieFlixUsers)
        else:
            return redirect(url_for("user"))
########################################################################################################################################################### Delete a User or Make it Admin
@app.route("/MovieFlix/DeleteOrAdmin")
def deleteOrAdmin():
    if ("admin" in session) and ("userPicked" in session):
        session["emailPicked"] = session["userPicked"]
        del session["userPicked"]
        return render_template("ViewAllUsers/DeleteOrAdmin.html", admin=True, user = session["emailPicked"])
    else:
        return redirect(url_for("user"))
########################################################################################################################################################### Delete a User's Account by Admin
@app.route("/MovieFlix/DeleteUsersAccount")
def deleteUsersAccount():
    if ("admin" in session) and ("emailPicked" in session):
        myUser = users.find_one({"$and":[{"email":session["emailPicked"]},{"comments":{"$exists":True}}]})
        if myUser == None:
            users.delete_one({"email":session["emailPicked"]})
            flash("The account has been deleted from MovieFlix.","info")
            return redirect(url_for("user"))
        comments = myUser["comments"]
        for comment in comments:
            ID = comment["ID"]
            movie = movies.find_one({"_id":ID})
            movieComments = movie["comments"]
            movieNewCommentList = []
            summ = 0
            amm = 0
            for com in movieComments:
                if (com["email"] != session["emailPicked"]) and (com["rating"] != -1):
                    summ = summ + com["rating"]
                    amm = amm + 1
                if com["email"] != session["emailPicked"]:
                    movieNewCommentList.append(com)
            movies.update_one({"_id":ID},{"$set":{"comments":movieNewCommentList}})
            if amm != 0:
                rating = summ/amm
            else:
                rating = -1
            movies.update_one({"_id":ID},{"$set":{"rating":rating}})
        users.delete_one({"email":session["emailPicked"]})
        del session["emailPicked"]
        flash("The account has been deleted from MovieFlix.","info")
        return redirect(url_for("user"))
    else:
        return redirect(url_for("user"))
########################################################################################################################################################### Promote a user to Admin
@app.route("/MovieFlix/UserToAdmin")
def userToAdmin():
    if ("admin" in session) and ("emailPicked" in session):
        users.update_one({"email":session["emailPicked"]},{"$set":{"isAdmin":True}})
        del session["emailPicked"]
        flash("The user has been upgraded to admin.","info")
        return redirect(url_for("user"))
    else:
        return redirect(url_for("user"))

# Run Flask App
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

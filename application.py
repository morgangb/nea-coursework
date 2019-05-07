# import the necessary libraries
from flask import Flask, render_template, request, redirect, session, make_response, url_for, Markup, flash
import sqlite3
import time
import math

app = Flask(__name__)

app.secret_key = b'a4ds+fg84fkhg#]/'

users = []
curlevel = 0 # 0 - uberadmin 1 - admins 2 - teachers 3 - students
loggedin = False
toprequest = []

registrationrequestlist = [] # Initialise the registration request list outside of a function so it can be global
username = ""
postid = []

# Home/Landing page
@app.route("/")
def home():
    return render_template("home.html")

# Handles login requests
@app.route("/dologin", methods=["POST"])
def dologin():
    # Gets data inputted by user in /login
    global username
    username = request.form.get("username")
    password = request.form.get("password")

    correctpwextract = []

    # Requests password from database
    conn = sqlite3.connect('database.db') # Makes connection to the database

    cursor = conn.execute("SELECT * FROM users WHERE username LIKE ?", (username,))

    for row in cursor:
        correctpwextract = row

    conn.close() # Ends connection to database

    # If password matches the password for the relevant username, allow log in. If not inform user of failure.
    if correctpwextract and correctpwextract[1] and password == correctpwextract[1]:
        session['username'] = username
        session['accesslevel'] = correctpwextract[3]
        flash('Login-Successful')
        return redirect(url_for('posts', filters='null', page=1))
    else:
        flash('Login-Failed')
        return redirect(url_for('home'))

# Files a registration request for the new user
@app.route("/doregister", methods=["POST"])
def doregister():
    # Gets data fields inputted by the user
    username = request.form.get("username")
    password = request.form.get("password")
    email = request.form.get("email")

    conn = sqlite3.connect('database.db') # Connect to the database

    conn.execute("INSERT INTO registrationrequests (username,password,email,timestamp) \
        VALUES (?, ?, ?, ?)", (username, password, email, str(time.time()))) # Inserts the new registration request
    conn.commit() # Commits the table
    conn.close() # Ends the connection to the database

    flash('Request-Sent') # Informs the user that the registration has been completed
    return redirect(url_for('home'))

# Displays registration requests
@app.route("/registrationrequests")
def registrationrequests():
    # Try to verify login
    if not verifylogin():
        return redirect(url_for('home')) # redirect to login if not logged in

    # Check access levels
    if not checkaccess(1):
        return redirect(url_for('requestaccess')) # Redirect to where the user can request access higher levels

    # Init variables for function
    registrationrequestshtml = "" # Will be returned to build the page

    conn = sqlite3.connect('database.db') # Connect to database

    # Handle set up of array in the program
    global registrationrequestlist # Accesses registrationrequestlist on global scope
    registrationrequestlist = [] # Clears out the registration request list before we go ahead

    cursor = conn.execute("SELECT * FROM registrationrequests ORDER BY timestamp DESC") # Finds all the registration requests from most recent

    #Puts registration requests into a list
    for row in cursor:
        registrationrequestlist.append(row)

    conn.close() # End connection to the database

    # Handle displaying of posts
    for i in registrationrequestlist:
        registrationrequestshtml = registrationrequestshtml + '''<div class="w3-padding w3-grey w3-display-container" style="border: 2px solid black;">
                Username: '''+i[0]+'''<br>Password: '''+i[1]+'''<br>Email: '''+i[2]+'''<br>Request made at: '''+str(i[3])+'''
            </div>'''
        registrationrequestshtml = registrationrequestshtml + '''<footer class="w3-container w3-orange" style="border: 2px dotted black;">
                    <form action="/doregistrationrequest/accept/'''+i[0]+'''/'''+i[1]+'''/'''+str(i[2])+'''" method="post" id="inlinebutton1">
                <input type="submit" value="Accept">
                </form>
                <form action="/doregistrationrequest/deny/'''+i[0]+'''/null/null" method="post" id="inlinebutton2">
                    <input type="submit" value="Deny">
                </form>
            </footer>'''

    return render_template("registrationrequests.html", requests=Markup(registrationrequestshtml)) # Output the posts

# Accepting a registration request
@app.route("/doregistrationrequest/<option>/<username>/<password>/<email>", methods=["POST"])
def doregistrationrequest(option, username, password, email):
    # Try to verify login
    if not verifylogin():
        return redirect(url_for('home')) # redirect to login if not logged in

    # Check access levels
    if not checkaccess(1):
        return redirect(url_for('requestaccess')) # Redirect to where the user can request access higher levels

    conn = sqlite3.connect('database.db') # Makes a connection to the database

    if option == "accept":
        # Adds the new user to the table
        conn.execute("INSERT INTO users (username,password,email,accesslevel) \
            VALUES (?, ?, ?, 3)", (username, password, email,))
        flash('Request-Accepted') # Informs the user that request has been accepted
    else:
        flash('Request-Denied') # Informs the user that the request has been denied

    conn.execute("DELETE FROM registrationrequests WHERE username='"+username+"'") # Deletes the registration request

    # End the connection and commit changes
    conn.commit()
    conn.close()

    return redirect(url_for('registrationrequests'))

# Render the page for writing a post
@app.route("/writepost")
def writepost():
    # Try to verify login
    if not verifylogin():
        return redirect(url_for('home')) # redirect to login if not logged in

    # Check access levels
    if not checkaccess(2):
        return redirect(url_for('requestaccess')) # Redirect to where the user can request access higher levels

    return render_template("writepost.html")

# Stores posts created in database
@app.route("/createpost", methods=["POST"])
def createpost():
    # Try to verify login
    if not verifylogin():
        return redirect(url_for('home')) # redirect to login if not logged in

    # Check access levels
    if not checkaccess(2):
        return redirect(url_for('requestaccess')) # Redirect to where the user can request access higher levels

    # Get information from /writepost
    global postid
    title = request.form.get("title")
    description = request.form.get("description")
    posttype = request.form.get("type")

    tags = [
        request.form.get("year7"),
        request.form.get("year8"),
        request.form.get("year9"),
        request.form.get("year10"),
        request.form.get("year11"),
        request.form.get("year12"),
        request.form.get("year13"),
        request.form.get("english"),
        request.form.get("maths"),
        request.form.get("naturalscience"),
        request.form.get("socialscience"),
        request.form.get("languages"),
        request.form.get("computing")
    ]

    tagstring = ""

    for i in tags:
        if i:
            if tagstring != "":
                tagstring = tagstring + ","
            tagstring = tagstring + i

    # Database connection and modification
    conn = sqlite3.connect('database.db') # Makes connection to the database

    # Get the current id
    cursor = conn.execute("SELECT id FROM posts ORDER BY id DESC")

    for row in cursor:
        postid.append(row)

    conn.execute("INSERT INTO posts (id,timestamp,title,description,posttype,creator,tags) \
        VALUES (?, ?, ?, ?, ?, ?, ?)", (str(int(postid[0][0])+1), str(time.time()), title, description, posttype, session["username"], tagstring,))

    # Save changes and end database connection
    conn.commit()
    conn.close()

    # Inform user of success
    flash('Post-Created')
    return redirect(url_for('posts', filters='null', page=1))

# Displays posts
@app.route("/posts/<filters>/<page>", methods=["GET"])
def posts(filters,page):
    # Try to verify login
    if not verifylogin():
        return redirect(url_for('home')) # redirect to login if not logged in

    poststable = [] # Will store contents of posts table
    posts = "" # Will be returned to build the page

    conn = sqlite3.connect('database.db') # Connect to database

    cursor = conn.execute('SELECT * FROM posts ORDER BY id DESC') # Pull all posts from database

    allposts = []

    # Loop through the contents of table and store them in a variable
    for row in cursor:
        allposts.append(row)

    filterstable = filters.split(',')

    # Loop through list and find the items with matching filters
    for i in allposts:
        if i[0] >= len(allposts)-((int(page))*10) and i[0] <= len(allposts)-((int(page))*10)+10-abs(int(page)-1)*1:
            if filters != "null":
                tagstable = i[6].split(',')
                for j in filterstable:
                    for k in tagstable:
                        canappend = False
                        if j == k:
                            canappend = True
                            for l in poststable:
                                if l == i:
                                    canappend = False
                            if canappend:
                                poststable.append(i)
            else:
                poststable.append(i)

    # Handle displaying of posts
    for i in poststable:
        posts = posts + '''<header class="w3-container w3-orange">
                <h2><u><b>'''+i[2]+'''</u></b></h2>
                <h5><i>by '''+i[5]+'''</i></h5>
                <h6>Tags: '''+str(i[6])+'''</h6>
            </header>
            <div class="w3-padding w3-grey w3-display-container" style="border: 2px solid black;">
                <p>'''+i[3]+'''</p>

                <a href="/deletepost/'''+str(i[0])+'''">Delete Post</a>
            </div>''' # Add base stuff that will appear in all posts

        # Make additional features dependent on type of post
        if i[4] == "Poll": # If the post is a poll
            # Init lists
            yesballots = [] # Will store all ballots for yes
            noballots = [] # Will store all ballots for no

            cursor = conn.execute('SELECT id FROM ballots WHERE postid = ? AND option="Yes"', (str(i[0]),)) # Extracts all yes ballots

            # Adds all yes ballots to the yes ballots list
            for row in cursor:
                yesballots.append(row)

            cursor = conn.execute('SELECT id FROM ballots WHERE postid = ? AND option="No"', (str(i[0]),)) # Extracts all no ballots

            # Adds all no ballots to the no ballots list
            for row in cursor:
                noballots.append(row)

            # Calculates the proportion of ballots that were yes
            if len(yesballots)+len(noballots) > 0:
                yesproportion = round(len(yesballots)/(len(yesballots)+len(noballots))*100)
            else:
                yesproportion = 0 # This line avoids division by zero errors

            # Adds polling features including a proportion of yes votes and buttons to vote
            posts = posts + '''<footer class="w3-container w3-orange" style="border: 2px dotted black;">
                    <h5><b>'''+str(yesproportion)+'''% voted yes</h5></b>
                    <form action="/vote/yes/'''+str(i[0])+'''" method="post" id="inlinebutton1">
                        <input type="submit" value="Vote Yes">
                    </form>
                    <form action="/vote/no/'''+str(i[0])+'''" method="post" id="inlinebutton2">
                        <input type="submit" value="Vote No">
                    </form>
                </footer>'''
        elif i[4] == "Event": # If the post is an event
            # Init lists
            attendees = [] # Will store all ballots for ye
            curattendee = []

            cursor = conn.execute('SELECT id FROM attendees WHERE eventid = '+str(i[0])+'') # Extracts all attendees

            # Adds all yes ballots to the yes ballots list
            for row in cursor:
                attendees.append(row)

            cursor = conn.execute("SELECT * FROM attendees WHERE user = ? AND eventid = ?", (session['username'], str(i[0]),)) # Extract attendee with same username as current

            # Adds all yes ballots to the yes ballots list
            for row in cursor:
                curattendee.append(row)

            if len(curattendee) != 0:
                attendingstring = "Currently attending"
            else:
                attendingstring = "Not attending"

            # Add an attend button
            posts = posts + '''<footer class="w3-container w3-orange" style="border: 2px dotted black;">
                    <h5><b>Attending:'''+str(len(attendees))+'''</b></h5>
                    <form action="/attend/'''+str(i[0])+'''" method="post">
                        <input type="submit" value="Attend">
                    </form>
                    <a href="/attendees/'''+str(i[0])+'''">Attendees</a>
                    <br>'''+attendingstring+'''
                </footer>'''
        posts = posts + "<br>" # Add a break at the end of the bost

    pagination = ""

    if int(page) >= 2:
        pagination = pagination + "<a href = '"+str(url_for('posts', filters = filters, page = str(int(page)-1)))+"'> BACK </a>"

    pagination = pagination + "<span style='text-align:center;'>PAGE "+str(page)+"</span>"

    if int(page) <= math.floor(len(allposts)/10):
        pagination = pagination + "<a href = '"+str(url_for('posts', filters = filters, page = str(int(page)+1)))+"' style='float:right;'> NEXT </a>"

    conn.close() # End the connection to the database

    return render_template("posts.html", posts=Markup(posts), pagination=Markup(pagination)) # Output the posts

@app.route("/filter", methods=["POST"])
def dofilter():
    tags = [
        request.form.get("year7"),
        request.form.get("year8"),
        request.form.get("year9"),
        request.form.get("year10"),
        request.form.get("year11"),
        request.form.get("year12"),
        request.form.get("year13"),
        request.form.get("english"),
        request.form.get("maths"),
        request.form.get("naturalscience"),
        request.form.get("socialscience"),
        request.form.get("languages"),
        request.form.get("computing")
    ]

    tagstring = ""

    for i in tags:
        if i:
            if tagstring != "":
                tagstring = tagstring + ","
            tagstring = tagstring + i

    if tagstring == "":
        tagstring = "null"

    return redirect(url_for('posts', filters=tagstring, page='1'))

@app.route("/deletepost/<post>")
def deletepost(post):
    # Try to verify login
    if not verifylogin():
        return redirect(url_for('home')) # redirect to login if not logged in

    # Check access levels
    if not checkaccess(2):
        return redirect(url_for('requestaccess')) # Redirect to where the user can request access higher levels

    conn = sqlite3.connect('database.db') # Connect to database

    cursor = conn.execute('DELETE FROM posts WHERE id=?', (post,)) # Delete post in database
    cursor = conn.execute('DELETE FROM attendees WHERE eventid=?', (post,)) # Delete post in database
    cursor = conn.execute('DELETE FROM ballots WHERE postid=?', (post,)) # Delete post in database

    conn.commit()
    conn.close()

    flash('Post-Deleted')
    return redirect(url_for('posts', filters='null', page=1))

# Handle yes votes in polls.
@app.route("/vote/<option>/<post>", methods=["POST"])
def vote(option,post):
    # Try to verify login
    if not verifylogin():
        return redirect(url_for('home')) # redirect to login if not logged in

    conn = sqlite3.connect('database.db') # Connect to database

    curballot = []

    cursor = conn.execute("SELECT * FROM ballots WHERE username = ? AND postid = ?", (session['username'], post,)) # Extract ballot with same username as current

    for row in cursor:
        curballot.append(row)

    if len(curballot) != 0:
        conn.close()
        flash('Already-Voted')
        return redirect(url_for('posts', filters='null', page=1))

    # Get the current id
    cursor = conn.execute("SELECT id FROM ballots ORDER BY id DESC")

    ballotid=[]

    for row in cursor:
        ballotid.append(row)

    if option == "yes":
        # Create new ballot with sequential ID and reference to relevant post.
        conn.execute("INSERT INTO ballots (id,option,postid,username) \
            VALUES (?, 'Yes', ?, ?)", (str(int(ballotid[0][0])+1), str(post), session['username'],))
        flash('Voted-Yes')
    elif option =="no":
        # Create new ballot with sequential ID and reference to relevant post.
        conn.execute("INSERT INTO ballots (id,option,postid,username) \
            VALUES (?, 'No', ?, ?)", (str(int(ballotid[0][0])+1), post, session['username'],))
        flash('Voted-No')

    # Save changes and close connection
    conn.commit()
    conn.close()

    return redirect(url_for('posts', filters='null', page=1))

# Handle attendance enrolment
@app.route("/attend/<post>", methods=["POST"])
def attend(post):
    # Try to verify login
    if not verifylogin():
        return redirect(url_for('home')) # redirect to login if not logged in

    conn = sqlite3.connect('database.db') # Connect to database

    curattendee = []

    cursor = conn.execute("SELECT * FROM attendees WHERE user = ? AND eventid = ?", (session['username'], post,)) # Extract attendee with same username as current

    # Adds all yes ballots to the yes ballots list
    for row in cursor:
        curattendee.append(row)

    if len(curattendee) != 0:
        conn.close()
        flash('Already-Attending')
        return redirect(url_for('posts', filters='null', page=1))

    # Get the current id
    cursor = conn.execute("SELECT id FROM attendees ORDER BY id DESC")

    attendeeid=[]

    for row in cursor:
        attendeeid.append(row)

    # Create new attendee with sequential ID and reference to relevant post.
    conn.execute("INSERT INTO attendees (id,user,eventid) \
        VALUES (?, ?, ?)", (str(int(attendeeid[0][0])+1), session['username'], post,))

    # Save changes and close connection
    conn.commit()
    conn.close()

    flash('Attending')
    return redirect(url_for('posts', filters='null', page=1))

# Allow user to view attendees of an event
@app.route("/attendees/<post>")
def attendees(post):
    # Try to verify login
    if not verifylogin():
        return redirect(url_for('home')) # Redirect to login if not logged in

    # Check access levels
    if not checkaccess(2):
        return redirect(url_for('requestaccess')) # Redirect to where the user can request access higher levels

    # Init variables for function
    attendeestable = [] # Will store contents of attendees table
    attendeeemails = [] # Will store attendee emails
    attendees = "" # Will be returned to build the page

    conn = sqlite3.connect('database.db') # Connect to database

    cursor = conn.execute('SELECT * FROM attendees WHERE eventid = ? ORDER BY id DESC', (post,)) # Pull event attendees

    # Loop through the contents of table and store them in a variable
    for row in cursor:
        attendeestable.append(row)

    # Handle displaying of posts
    for i in attendeestable:
        cursor = conn.execute('SELECT email FROM users WHERE username = ?', (i[1],)) # Pull email from users

        # Loop through the contents of table and store them in a variable
        for row in cursor:
            attendeeemails.append(row)

        attendees = attendees + '''<div class="w3-padding w3-grey w3-display-container" style="border: 2px solid black;">
                User: '''+i[1]+'''<br>Email: '''+attendeeemails[0][0]+'''
            </div>'''# Display username and email
        attendees = attendees + '''<footer class="w3-container w3-orange" style="border: 2px dotted black;">
                <form action="/kick/'''+str(i[0])+'''" method="post">
                    <input type="submit" value="Kick">
                </form>
            </footer>''' # Allow kicking

        attendeeemails = [] # Clear attendeeemails for next use

    conn.close() # End the connection to the database

    return render_template("attendees.html", attendees=Markup(attendees)) # Output the posts

# Function for kicking attendees from events
@app.route("/kick/<attendee>", methods=["POST"])
def kick(attendee):
    # Try to verify login
    if not verifylogin():
        return redirect(url_for('home')) # Redirect to login if not logged in

    # Check access levels
    if not checkaccess(2):
        return redirect(url_for('requestaccess')) # Redirect to where the user can request access higher levels

    conn = sqlite3.connect('database.db') # Connect to database

    conn.execute("DELETE FROM attendees WHERE id = ?", (str(attendee),)) # Delete attendee

    # Save changes and close connection
    conn.commit()
    conn.close()

    flash('Attendee-Kicked')
    return redirect(url_for('posts', filters='null', page=1))

# Allows uers to make requests for higher access levels
@app.route("/requestaccess")
def requestaccess():
    if session['accesslevel'] == 0:
        return redirect(url_for('accessrequests'))

    # Try to verify login
    if not verifylogin():
        return redirect(url_for('home')) # redirect to login if not logged in

    return render_template("requestaccess.html")

# Adds a new row to the accessrequests table so that the uber-admin may verify the request and change the access level of the user accordingly
@app.route("/dorequestaccess", methods=["POST"])
def dorequestaccess():
    # Try to verify login
    if not verifylogin():
        return redirect(url_for('home')) # redirect to login if not logged in

    # Obtain data as inputted by user previously.
    newlevel = request.form.get("newlevel")
    reason = request.form.get("reason")

    # Access database and make new row with sequential id and data as entered by user.
    conn = sqlite3.connect('database.db')

    # Get the current id
    cursor = conn.execute("SELECT id FROM accessrequests ORDER BY id DESC")

    accessrequestid=[]

    for row in cursor:
        accessrequestid.append(row)

    conn.execute("INSERT INTO accessrequests (id,timestamp,newlevel,reason,username) \
        VALUES (?, ?, ?, ?, ?)", (str(accessrequestid[0][0]+1), str(time.time()), str(newlevel), reason, session['username'],))

    # Save changes and close connection
    conn.commit()
    conn.close()

    flash('Access-Requested')
    return redirect(url_for('posts', filters='null', page=1))

# Handle displaying of access requests allowing users to accept or refuse each
@app.route("/accessrequests")
def accessrequests():
    # Try to verify login
    if not verifylogin():
        return redirect(url_for('home')) # redirect to login if not logged in

    # Check access levels
    if not checkaccess(1):
        return redirect(url_for('requestaccess')) # Redirect to where the user can request access higher levels

    # Init variables for function
    requeststable = [] # Will store contents of accessrequests table
    requests = "" # Will be returned to build the page

    conn = sqlite3.connect('database.db') # Connect to database

    cursor = conn.execute('SELECT * FROM accessrequests ORDER BY id DESC') # Pull all posts from database

    # Loop through the contents of table and store them in a variable
    for row in cursor:
        requeststable.append(row)

    # Handle displaying of posts
    for i in requeststable:
        requests = requests + '''<div class="w3-padding w3-grey w3-display-container" style="border: 2px solid black;">
                    '''+str(i[0])+''' - '''+i[4]+''' wants access level '''+str(i[2])+''' because '''+i[3]+'''<br>Request made at: '''+str(i[1])+'''
                </div>'''
        requests = requests + '''<footer class="w3-container w3-orange" style="border: 2px dotted black;">
                <br><form action="/changeaccess/accept/'''+str(i[0])+'''/'''+i[4]+'''/'''+str(i[2])+'''" method="post" id="inlinebutton1">
                    <input type="submit" value="Accept">
                </form>
                <form action="/changeaccess/deny/'''+str(i[0])+'''/null/null" method="post" id="inlinebutton2">
                    <input type="submit" value="Deny">
                </form><br>
            </footer><br>'''

    conn.close() # End the connection to the database

    return render_template("accessrequests.html", requests=Markup(requests))  # Output the access requests

# Accepting access requests
@app.route("/changeaccess/<option>/<requestid>/<username>/<newlevel>", methods=["POST"])
def changeaccess(option, requestid, username, newlevel):
    # Try to verify login
    if not verifylogin():
        return redirect(url_for('home')) # redirect to login if not logged in

    # Check access levels
    if not checkaccess(1):
        return redirect(url_for('requestaccess')) # Redirect to where the user can request access higher levels

    conn = sqlite3.connect('database.db') # Connect to the database

    if option == "accept":
        conn.execute("UPDATE users SET accesslevel = ? WHERE username = ?", (newlevel, username,)) # Change access level
        flash('Request-Accepted')
    else:
        flash('Request-Denied')

    conn.execute("DELETE FROM accessrequests WHERE id = ?", (requestid,)) # Delete access request

    # Save changes and close database connection
    conn.commit()
    conn.close()

    return redirect(url_for('accessrequests'))

# Delete registered users
@app.route("/registered")
def registered():
    # Try to verify login
    if not verifylogin():
        return redirect(url_for('home')) # redirect to login if not logged in

    # Check access levels
    if not checkaccess(0):
        return redirect(url_for('requestaccess')) # Redirect to where the user can request access higher levels

    # Init variables for function
    registeredtable = [] # Will store contents of users table
    registered = "" # Will be returned to build the page

    conn = sqlite3.connect('database.db') # Connect to database

    cursor = conn.execute('SELECT * FROM users ORDER BY username DESC') # Pull all users from database

    # Loop through the contents of table and store them in a variable
    for row in cursor:
        registeredtable.append(row)

    # Handle displaying of users
    for i in registeredtable:
        if i[0] != "uber": # Omit display of uber user
            registered = registered + '''<header class="w3-container w3-orange">
                    <h2>User: '''+i[0]+'''</h2>
                </header>
                <div class="w3-padding w3-grey w3-display-container" style="border: 2px solid black;">
                    Password: '''+i[1]+'''<br>Email: '''+i[2]+'''<br>Access Level: '''+str(i[3])+'''
                </div>'''
            registered = registered + '''<footer class="w3-container w3-orange" style="border: 2px dotted black;">
                    <form action="/deleteuser/'''+i[0]+'''" method="post">
                        <input type="submit" value="Delete User">
                    </form>
                </footer><br>'''

    conn.close() # End the connection to the database

    return render_template("registered.html", registered=Markup(registered)) # Output the users

# Delete user from registered page
@app.route("/deleteuser/<user>", methods=["POST"])
def deleteuser(user):
    # Try to verify login
    if not verifylogin():
        return redirect(url_for('home')) # redirect to login if not logged in

    # Check access levels
    if not checkaccess(0):
        return redirect(url_for('requestaccess')) # Redirect to where the user can request access higher levels

    conn = sqlite3.connect('database.db') # Connect to the database

    conn.execute("DELETE FROM users WHERE username = ?", (user,)) # Delete user

    # Save changes and close database connection
    conn.commit()
    conn.close()

    flash('User-Deleted')
    return redirect(url_for('registered'))

# Logout current user
@app.route("/logout")
def logout():
    session['username'] = ""
    session['accesslevel'] = 3
    flash('Logged-Out')
    return redirect(url_for('home'))

#Verify the user has logged in
def verifylogin():
    try:
        username = session['username'] # Attempt to find username in cookies
        if username != "":
            return True
        else:
            return False
    except:
        return False

# Check the user has sufficient access levels to perform an action
def checkaccess(reqaccess):
    try:
        if session['accesslevel'] <= reqaccess: # Check if the access level is sufficent
            return True
        else:
            return False
    except:
        return False
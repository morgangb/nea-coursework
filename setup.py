import sqlite3 # import the sqlite library which allows me to interface with and modify the contents of a database

conn = sqlite3.connect('database.db') # establish a connection to the relevant database

# insert values

# create uber-admin
conn.execute('''INSERT INTO users (username,password,email,accesslevel) \
         VALUES ("uber","temp","13.BrownM@stantonbury.org.uk",0)''')

# create test admin
conn.execute('''INSERT INTO users (username,password,email,accesslevel) \
         VALUES ("testadmin","temp","13.BrownM@stantonbury.org.uk",1)''')

# create test teacher
conn.execute('''INSERT INTO users (username,password,email,accesslevel) \
         VALUES ("testteacher","temp","13.BrownM@stantonbury.org.uk",2)''')

# create test student
conn.execute('''INSERT INTO users (username,password,email,accesslevel) \
         VALUES ("teststudent","temp","13.BrownM@stantonbury.org.uk",3)''')

conn.commit() # commit the changes to the database

conn.close() # end connection to the database
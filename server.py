#Made by Tibor Péter Szabó

import socket
import threading
import re
import os
import sqlite3

port = 80
print("Starting server")
server = socket.socket()
server.bind(("localhost",port))
server.listen(0)
print("server listening on port",port)

def executeDB(com):
    con = sqlite3.connect("database.db")
    cur = con.cursor()
    cur.execute(com)
    dBresponse = cur.fetchall()
    response = ""
    if len(dBresponse) != 0:
        for resLine in dBresponse:
            for data in resLine:
                response+=str(data)+"-"
            response = response[:-1]
            response+="\n"
    response = response[:-1]
    con.close()
    return response

def readFromFile(fileName):
    hasExt = re.search(".*\..*",fileName)
    if not hasExt:
        fileName += ".html"
    content = ""
    try:
        file = open(fileName)
    except Exception as e:
        return
    
    content += file.read()
    file.close()
    return content

def writeToFile(fileName,content):
    if os.path.isfile("files\\"+fileName):
        fileName=fileName[0:fileName.rfind(".")]+"_copy"+fileName[fileName.rfind("."):]
        writeToFile(fileName,content)
        return
    file = open("files\\"+fileName,'w',encoding="UTF-8")
    file.write(content.replace("%58",":").replace("%10","\n"))
    file.close

def handleRequest(request,url,content="Nothing was sent"):
    answer = ""
    match url:
        case "GET /":
            answer ="HTTP/1.1 301 Moved Permanently\nLocation: Login"
        case "GET /fileSystem":
            filesystem = os.popen("dir /O:N /B files")
            
            answer = "HTTP/1.1 200 Success\nContent-Type: text/text\n\n"
            answer += filesystem.read()
        case "GET /getUsers":
            answer += "HTTP/1.1 200 Success\nContent-Type: text/text\n\n"
            answer += executeDB("select user.name,AccessType.name,LoginState.name from user inner join LoginState on LoginState.id = User.loginState left join AccessType on user.AccessType = AccessType.id")
        case "GET /getTasks":
            answer += "HTTP/1.1 200 Success\nContent-Type: text/text\n\n"
            answer += executeDB("select isSubtask,description,name,users,startTime,endTime from task inner join status on status.id = task.status")
        case "GET /getIssues":
            answer += "HTTP/1.1 200 Success\nContent-Type: text/text\n\n"
            answer += executeDB("select * from issue")
        case "POST /fileSystem":
            writeToFile(content.split(":")[0],content.split(":")[1])
            answer = "201 Created"
        case _:
            fileName = re.search("/.*",url).group()[1:]
            fileContent = readFromFile(fileName)
            if fileContent:
                answer = fileContent
            else:
                answer = "HTTP/1.1 404 Not Found\n\n"
                answer = readFromFile("404")
    return answer


def clientManager(con,addr):
    try:
        request = con.recv(2048).decode()
        url = re.search(".* /.* ",request).group().strip()
        content = request.split("\n")[len(request.split("\n"))-1]
        
        print(request)

        response = handleRequest(request,url,content)
        print ("-------------------------------\n","DEBUG:",addr,":",url,content,"=>","\n"+response)
        con.send(response.encode())
    except Exception as e:
        print (e)
    con.close()
    return

clients = []
while (True):
    con,addr = server.accept()
    clients.append(threading.Thread(target=clientManager,args=(con,addr)))
    clients[len(clients)-1].start()
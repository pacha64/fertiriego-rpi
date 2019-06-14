with open('userpass') as f:
    content = f.readlines()
# you may also want to remove whitespace characters like `\n` at the end of each line
content = [x.strip() for x in content]

def getUsername():
    return content[0]

def getPassword():
    return content[1]

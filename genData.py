with open("STARSCOUTDATA(1).txt", "r+") as file:
    lines = []
    ms = 0
    for line in file:
        lines.insert(0,line)
        ms = int(line.strip()[line.strip().rindex(" "):])
    for line in lines:
        ms += 200
        line = (line.strip()[:line.strip().rindex(" ")]).strip()
        line += " " + str(ms)
        file.write("\n" + line)
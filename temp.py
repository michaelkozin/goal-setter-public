import schedule

def job():
    print("I'm working...")

schedule.every(10).seconds.do(job)

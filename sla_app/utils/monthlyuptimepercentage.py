import calendar
import datetime


def totaluptime():
    now = datetime.datetime.now()
    totalsecondsinmonth = calendar.monthrange(now.year, now.month)[1] * (24 * (60 * 60))
    return totalsecondsinmonth


def totalimpactedseconds(impactduration):
    if impactduration.find("day") != -1:
        hrsminutetime = impactduration[impactduration.index(",") + 1:].strip()
        hrs, minutes = hrsminutetime.split(":", 1)
        convertdayinseconds = int(impactduration[0:impactduration.index("d")].strip()) * 24 * 60 * 60
        print("downtime in seconds:",
              (convertdayinseconds + int(hrs) * 60 * 60) + (int(minutes[0:minutes.index(":")]) * 60) + (
                  int(minutes[-2:])))
        return (convertdayinseconds + int(hrs) * 60 * 60) + (int(minutes[0:minutes.index(":")]) * 60) + (
            int(minutes[-2:]))

    else:
        hrs, minutes = impactduration.split(":", 1)
        print("downtime in seconds:",
              (int(hrs) * 60 * 60) + (int(minutes[0:minutes.index(":")]) * 60) + (int(minutes[-2:])))
        return (int(hrs) * 60 * 60) + (int(minutes[0:minutes.index(":")]) * 60) + (int(minutes[-2:]))


def percentagecal(impactduration):
    monthlypercentage = float(
        "{:.2f}".format((totaluptime() - totalimpactedseconds(impactduration)) / totaluptime() * 100))
    return monthlypercentage


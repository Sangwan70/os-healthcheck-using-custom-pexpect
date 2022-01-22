def Con_secs(seconds):
    seconds = int(seconds)
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    if days > 0:
        return '%d days %d hrs %d mins' % (days, hours, minutes)
    elif hours > 0:
        return '%d hrs %d mins'  % (hours, minutes)
    elif minutes > 0:
        return '%d mins %d secs' % (minutes, seconds)
    else:
        return '%d secs' % (seconds,)

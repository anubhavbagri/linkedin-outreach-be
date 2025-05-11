from mailscout import Scout
scout = Scout()

names = "Riya Jain"
domain = "zeptonow.com"

emails = scout.find_valid_emails(domain, names)

print(emails)



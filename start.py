#!/usr/bin/env python

import web
from web import form
import youtubeup as yup
import argparse
import csv
from datetime import datetime
import time
import sys

render = web.template.render('webpage/')

urls = ('/', 'index')
app = web.application(urls, globals())

dataform = form.Form(
	form.Dropdown("where",
		[("../","Parent Folder to Scripts"),("", "Same Folder as Scripts")],
		description="Match Files Location"),
	form.Textbox("prodteam", description="Production Team", size=41),
	form.Textbox("twit", description="Twitter Handle", size=41),
	form.Textbox("fb", description="Facebook Name", size=41),
	form.Textbox("weblink", description="Website Link", size=41),
	form.Textbox("ename", description="Event Name", size=41),
	form.Textbox("ecode", description="Event Code (ex. 2016arc)"),
	form.Textbox("pID",
		form.regexp("^PL", "Must be a playlist ID, all of which start with 'PL'"),
		form.regexp("^\s*\S+\s*$", "Can not contain spaces."),
		description="Playlist ID",
		size=41),
	form.Textbox("tbaID",
		description="TBA Event ID",
		value="Contact 'contact@thebluealliance.com' to get keys",
		size=41),
	form.Textbox("tbaSecret",
		description="TBA Event Secret",
		value="Contact 'contact@thebluealliance.com' to get keys",
		size=41),
	form.Textarea("description",
		description="Video description",
		value="Add alternate description here."),
	form.Textbox("mnum",
		form.notnull,
		form.regexp("\d+", "Cannot contain letters"),
		form.Validator("Must be more than 0", lambda x:int(x)>0),
		description="Match Number"),
	form.Dropdown("mcode",
		[("qm", "Qualifications"), ("qf","Quarterfinals"), ("sf", "Semifinals"), ("f1m", "Finals")],
		description="Match Type"),
	form.Dropdown("tiebreak",[(0,"False"),(1,"True")],description="Tiebreaker"),
    form.Dropdown("tba",[(1,"True"),(0,"False")],description="Update TBA"),
    form.Dropdown("ceremonies",[(0,"None"),(1,"Opening Ceremonies"),(2,"Alliance Selection"),(3,"Closing Ceremonies")],description="Ceremonies"),
	form.Textbox("end", 
		description="Last Match Number", 
		value="Only for batch uploads"),
		validators = [form.Validator("Last Match Number must be greater than Match Number", 
		lambda i: i.end == "Only for batch uploads" or int(i.end) > int(i.mnum))]
	)

class index():
	def GET(self):
		form = dataform()
		with open('form_values.csv', 'rb') as csvfile:
			reader = csv.reader(csvfile, delimiter=',', quotechar='|')
			i = 0
			for row in reader:
				for value in row:
					if value is not "":
						switcher = {
							0: form.where,
							1: form.prodteam,
							2: form.twit,
							3: form.fb,
							4: form.weblink,
							5: form.ename,
							6: form.ecode,
							7: form.pID,
							8: form.tbaID,
							9: form.tbaSecret,
							10: form.description,
							11: form.mnum,
							12: form.mcode,
							13: form.tiebreak,
							14: form.tba,
							15: form.ceremonies,
							16: form.end,
						}
						switcher[i].set_value(value)
					i = i + 1
				break
		return render.forms(form)

	def POST(self):
		form = dataform()
		if not form.validates():
			return render.forms(form)
		else:
			then = datetime.now()
			reader = csv.reader(open('form_values.csv'))
			try:
				row = next(reader)
			except StopIteration:
				with open("form_values.csv", "wb") as csvf:
					csvf.write(''.join(str(x) for x in [","]*30))
					csvf.close()
					row = next(reader)
			parser = argparse.ArgumentParser(description='Upload videos to YouTube for FRC matches')
			args = parser.parse_args()
			formdata = web.input()
			args.then = then
			args.gui = True
			args.where = row[0] = form.d.where
			args.prodteam = row[1] = form.d.prodteam
			args.twit = row[2] = form.d.twit
			args.fb = row[3] = form.d.fb
			args.weblink = row[4] = form.d.weblink
			args.ename = row[5] = form.d.ename
			args.ecode = row[6] = form.d.ecode
			args.pID = row[7] = form.d.pID
			args.tbaID = row[8] = form.d.tbaID
			args.tbaSecret = row[9] = form.d.tbaSecret
			args.description = row[10] = form.d.description
			args.mnum = row[11] = int(form.d.mnum)
			args.mcode = row[12] = form.d.mcode
			args.tiebreak = row[13] = form.d.tiebreak
			args.tba = row[14] = form.d.tba
			args.ceremonies = row[15] = form.d.ceremonies
			args.end = row[16] = form.d.end
			yup.init(args)
			if int(form.d.ceremonies) == 0:
                                if form.d.end == "Only for batch uploads":
                                        form.mnum.set_value(str(int(form.d.mnum) + 1))
                                else:
                                        form.mnum.set_value(str(int(form.d.end) + 1))
                                        form.end.set_value("Only for batch uploads")
			row[11] = int(form.d.mnum)
			row[16] = form.d.end
			writer = csv.writer(open('form_values.csv', 'w'))
			writer.writerow(row)
			return render.forms(form)
			
def main():
	web.internalerror = web.debugerror
	app.run()

if __name__=="__main__":
	main()
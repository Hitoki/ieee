import os
os.system('rd /s /q ..\\docs')
os.system('epydoc.py --html -o ..\\docs --name "IEEE Technology Navigator" --parse-only ..\\')
#os.system('pause')

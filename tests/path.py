import sys, os

def go():
	if 'interpret.py' in os.listdir('..') and\
		not 'interpret.py' in os.listdir('.'):
		os.chdir('..')

	sys.path.append('.')
